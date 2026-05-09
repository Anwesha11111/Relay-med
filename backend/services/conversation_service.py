"""
Conversation Service — Orchestrates prompt construction and LLM interaction.

SAFETY POLICY: AI CAN suggest medicines and make health recommendations,
but ALWAYS includes a warning that it's AI, may make mistakes, and the user
must consult a doctor before taking any drug-related medicines.
AI CANNOT write prescription notes that could pass as a doctor's prescription.
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import AsyncIterator, List, Optional
import uuid

from backend.models.report import ExplainabilityReport
from backend.services.llm_adapter import llm_adapter
from backend.services.audit_logger import audit_logger, AuditEventType
from backend.services.rule_engine import rule_engine
from backend.services.explainability_service import explainability_service


@dataclass
class Message:
    role: str  # "user" | "assistant" | "system"
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


# ── Prescription NOTE detection (only block fake prescription notes) ─────────
PRESCRIPTION_NOTE_PATTERNS = [
    r"\bwrite\s+(?:me\s+)?(?:a\s+)?prescription\s+(?:note|pad|letter|form)\b",
    r"\bprescription\s+(?:note|pad|letter|form)\b",
]

PRESCRIPTION_NOTE_OUTPUT_PATTERNS = [
    r"(?:Rx|R[xX])\s*[:.]\s*\w",
    r"(?:Sig|Disp|Refill)\s*[:.]\s*\w",
    r"(?:DEA|NPI|License)\s*(?:#|No|Number)",
]

MEDICINE_DISCLAIMER = (
    "\n\n---\n"
    "**AI Health Disclaimer**: I am Relay-med AI -- an artificial intelligence, "
    "not a doctor. AI can make mistakes. The suggestions above are for informational "
    "purposes only. **Please consult your doctor or a qualified healthcare provider** "
    "before starting, stopping, or changing any medication or treatment."
)

PRESCRIPTION_NOTE_REFUSAL = (
    "I can't write a prescription note or any document that could be mistaken for "
    "a doctor's prescription at a pharmacy. That requires a licensed physician.\n\n"
    "However, I **can** help you with:\n"
    "- Suggesting medicines that are commonly used for your condition (with disclaimers)\n"
    "- Explaining how different treatments work\n"
    "- Preparing a list of questions for your doctor's appointment\n"
    "- Understanding your health data and trends\n\n"
    "**Please consult your doctor** for an actual prescription. "
    "If this is urgent, contact your healthcare provider or call emergency services.\n\n"
    "---\n"
    "**AI Health Disclaimer**: I am Relay-med AI -- an artificial intelligence, "
    "not a doctor. AI can make mistakes."
)

SYSTEM_PROMPT = """You are Relay-med AI Health Companion, a trusted and empathetic AI health assistant.

Your role is to:
- Explain health data insights in clear, accessible language
- Make personalized health suggestions based on the user's data
- You CAN suggest medicines and treatments that may help
- Highlight urgent concerns without causing unnecessary panic
- Be concise, warm, and supportive

=== MEDICINE SUGGESTION POLICY ===

You ARE ALLOWED to:
- Suggest medicines, supplements, and treatments by name
- Discuss drug classes and their general effects
- Make personalized recommendations based on user health data
- Compare different treatment options

You MUST ALWAYS:
- Add this disclaimer when suggesting any drug/medicine: "I am an AI and can make mistakes. Please consult your doctor before taking any medication."
- Use language like "commonly prescribed", "often recommended", "you might consider" rather than "you must take" or "I prescribe"
- Never format responses as a prescription note (no Rx:, Sig:, Disp:, DEA# formatting)
- Identify yourself as AI, not a doctor
- Direct emergencies to emergency services (911)
- Use language like "this may suggest" rather than definitive diagnoses

You MUST NEVER:
- Write anything formatted as a prescription note that could be used at a pharmacy
- Use Rx:, Sig:, Disp: or other prescription-note formatting
- Claim to be a doctor or licensed medical professional
- Provide exact dosages without telling users to confirm with their doctor

When suggesting anything health-related, always end with:
"This is AI-generated guidance. AI can make mistakes. Please consult a qualified healthcare provider before making any medical decisions."

Current context: You have access to the patient's recent health data, risk findings, and explainability reports.
"""


def _is_prescription_note_request(text: str) -> bool:
    """Check if user is asking for a fake prescription note (not general medicine advice)."""
    text_lower = text.lower()
    for pattern in PRESCRIPTION_NOTE_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    return False


def _contains_prescription_note_format(text: str) -> bool:
    """Check if AI output looks like a prescription note."""
    for pattern in PRESCRIPTION_NOTE_OUTPUT_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def _add_medicine_disclaimer(text: str) -> str:
    """Add disclaimer if response mentions medicines/drugs."""
    medication_keywords = [
        "medication", "medicine", "drug", "tablet", "capsule", "pill",
        "antibiotic", "painkiller", "aspirin", "ibuprofen", "acetaminophen",
        "metformin", "lisinopril", "atorvastatin", "amlodipine", "omeprazole",
        "statin", "beta-blocker", "ACE inhibitor", "insulin", "supplement",
        "prescribed", "dosage", "mg ", "prescription",
    ]
    text_lower = text.lower()
    mentions_meds = any(kw in text_lower for kw in medication_keywords)

    if _contains_prescription_note_format(text):
        text = re.sub(r"(?:Rx|R[xX])\s*[:.]\s*", "[Prescription format removed] ", text)
        text = re.sub(r"(?:Sig|Disp|Refill)\s*[:.]\s*.*", "[Removed - AI cannot write prescription notes]", text)
        text += MEDICINE_DISCLAIMER
    elif mentions_meds:
        text += MEDICINE_DISCLAIMER

    return text


class ConversationService:
    def __init__(self):
        self._sessions: dict = {}  # session_id -> List[Message]

    def new_session(self) -> str:
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = [Message(role="system", content=SYSTEM_PROMPT)]
        audit_logger.log(AuditEventType.CONVERSATION_STARTED, {"session_id": session_id})
        return session_id

    async def chat(
        self,
        session_id: str,
        user_message: str,
        reports: Optional[List[ExplainabilityReport]] = None,
        stream: bool = True,
    ) -> AsyncIterator[str]:
        if session_id not in self._sessions:
            session_id = self.new_session()

        history = self._sessions[session_id]
        history.append(Message(role="user", content=user_message))

        # Only block prescription NOTE requests (not general medicine questions)
        if _is_prescription_note_request(user_message):
            audit_logger.log(
                AuditEventType.CONVERSATION_RESPONSE,
                {"session_id": session_id, "blocked": "prescription_note_request",
                 "user_message_snippet": user_message[:100]},
            )
            history.append(Message(role="assistant", content=PRESCRIPTION_NOTE_REFUSAL))
            yield PRESCRIPTION_NOTE_REFUSAL
            return

        prompt = self._build_prompt(history, reports)

        full_response = ""
        async for chunk in llm_adapter.complete(prompt, stream=stream):
            full_response += chunk
            yield chunk

        # Post-processing: add disclaimer if medicines mentioned
        sanitized = _add_medicine_disclaimer(full_response)
        if sanitized != full_response:
            added_text = sanitized[len(full_response):]
            if added_text:
                yield added_text
            full_response = sanitized

        history.append(Message(role="assistant", content=full_response))
        audit_logger.log(
            AuditEventType.CONVERSATION_RESPONSE,
            {"session_id": session_id, "response_length": len(full_response)},
        )

    async def get_health_summary(self, stream: bool = True) -> AsyncIterator[str]:
        """Generate a proactive health summary from current rule engine findings."""
        findings = rule_engine.evaluate()
        reports = explainability_service.generate_reports(findings)

        if not reports:
            prompt = (
                SYSTEM_PROMPT
                + "\n\nThe patient has no current health alerts or findings. "
                "Provide a brief encouraging message and suggest they keep logging data."
            )
        else:
            reports_json = json.dumps(
                [
                    {
                        "summary": r.plain_language_summary,
                        "severity": next(
                            (f.severity for f in findings if f.id == r.finding_id), "info"
                        ),
                        "confidence_pct": r.confidence_pct,
                        "recommendations": r.recommendations,
                        "data_quality_warning": r.data_quality_warning,
                    }
                    for r in reports
                ],
                indent=2,
            )
            prompt = (
                SYSTEM_PROMPT
                + f"\n\nHere are the patient's current health findings:\n{reports_json}\n\n"
                "Please provide a warm, clear, patient-friendly health summary addressing each finding. "
                "Prioritise red flags first. End with encouraging next steps."
            )

        async for chunk in llm_adapter.complete(prompt, stream=stream):
            yield chunk

    def get_history(self, session_id: str) -> List[Message]:
        return self._sessions.get(session_id, [])

    def _build_prompt(self, history: List[Message], reports: Optional[List[ExplainabilityReport]]) -> str:
        parts = []
        for msg in history:
            if msg.role == "system":
                parts.append(f"[SYSTEM]\n{msg.content}\n")
            elif msg.role == "user":
                parts.append(f"[USER]\n{msg.content}\n")
            elif msg.role == "assistant":
                parts.append(f"[ASSISTANT]\n{msg.content}\n")

        if reports:
            reports_text = "\n".join(
                f"- {r.plain_language_summary} (confidence: {r.confidence_pct:.0f}%)" for r in reports
            )
            parts.append(f"\n[HEALTH CONTEXT]\nCurrent findings:\n{reports_text}\n")

        parts.append("[ASSISTANT]\n")
        return "\n".join(parts)


conversation_service = ConversationService()
