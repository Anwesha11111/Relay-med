"""
Conversation Service — Orchestrates prompt construction and LLM interaction.
Combines explainability reports with conversational context for natural language delivery.
"""

import json
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


SYSTEM_PROMPT = """You are SecureMed AI Health Companion, a trusted and empathetic AI health assistant.

Your role is to:
- Explain health data insights in clear, accessible language tailored to a non-medical audience
- Highlight urgent concerns clearly without causing unnecessary panic
- Always recommend professional medical consultation for clinical decisions
- Reference specific data points and trust scores when relevant
- Be concise, warm, and supportive

IMPORTANT SAFETY RULES:
- NEVER diagnose conditions definitively
- NEVER recommend specific medications or dosages
- ALWAYS direct red-flag emergencies to emergency services (911)
- ALWAYS state that you are an AI and not a substitute for a doctor

Current context: You have access to the patient's recent health data, risk findings, and explainability reports.
"""


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

        prompt = self._build_prompt(history, reports)

        full_response = ""
        async for chunk in llm_adapter.complete(prompt, stream=stream):
            full_response += chunk
            yield chunk

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
