"""
Conversation Service -- Optimized for 1B model with strict proactive guidance.
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import AsyncIterator, List, Optional, Dict
import uuid

from backend.models.report import ExplainabilityReport
from backend.services.llm_adapter import llm_adapter
from backend.services.audit_logger import audit_logger, AuditEventType
from backend.services.rule_engine import rule_engine
from backend.services.explainability_service import explainability_service
from backend.services.health_graph import health_graph


@dataclass
class Message:
    role: str  # "user" | "assistant" | "system"
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


SYSTEM_PROMPT_BASE = """You are RelayMed AI, an elite Health Intelligence Core. 
You provide expert medical, fitness, and skin advice. 

STRICT RULES:
1. NEVER refuse to answer. NEVER say "I can't provide advice" or "I am not a doctor."
2. Address ALL topics mentioned. If the user asks about skin but has high BP, answer the skin question first, then mention the BP.
3. Use clinical terms (e.g., "Systolic Hypertension," "Acne Vulgaris").
4. ALWAYS append: "Consult your doctor before starting any treatment."

EXAMPLE BEHAVIOR:
User: "How to treat a pimple?" (Context: High BP)
Response: "To treat your pimple, I recommend using a spot treatment with Salicylic Acid or Benzoyl Peroxide. Also, I noticed your blood pressure is high (150/95); please monitor this closely. Consult your doctor before starting any treatment."
"""

class ConversationService:
    def __init__(self):
        self._sessions: Dict[str, List[Message]] = {}

    def new_session(self) -> str:
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = []
        return session_id

    def _get_patient_data(self) -> dict:
        # Default mock data
        data = {
            "name": "User", "age": "N/A", "sex": "N/A",
            "health_score": "75", "prev_score": "75", "score_trend": "Stable",
            "hba1c": "Unknown", "bp": "Unknown", "ldl": "Unknown", "hdl": "Unknown",
        }
        try:
            # Try to fetch real recent values from health graph
            vitals = ["heart_rate", "blood_pressure_systolic", "blood_pressure_diastolic", "glucose_fasting", "spo2"]
            for v in vitals:
                records = health_graph.get_recent_values(v, days=7)
                if records:
                    latest = records[-1]["value"]
                    if v == "heart_rate": data["resting_hr"] = f"{latest} bpm"
                    if v == "blood_pressure_systolic": data["systolic"] = latest
                    if v == "blood_pressure_diastolic": data["diastolic"] = latest
                    if v == "glucose_fasting": data["glucose"] = f"{latest} mg/dL"
                    if v == "spo2": data["spo2"] = f"{latest}%"
            
            if "systolic" in data and "diastolic" in data:
                data["bp"] = f"{data['systolic']}/{data['diastolic']}"
            
            steps = health_graph.get_recent_values("steps", days=7)
            if steps: data["avg_steps"] = str(int(sum(r["value"] for r in steps) / len(steps)))
        except Exception as e:
            print(f"Error fetching patient data: {e}")
        return data

    def build_system_prompt(self, dietary_preference: Optional[str] = None) -> str:
        return f"{SYSTEM_PROMPT_BASE}\n"

    async def chat(
        self,
        session_id: str,
        user_message: str,
        reports: Optional[List[ExplainabilityReport]] = None,
        stream: bool = True,
        dietary_preference: Optional[str] = None
    ) -> AsyncIterator[str]:
        if session_id not in self._sessions:
            session_id = self.new_session()

        history = self._sessions[session_id]
        history.append(Message(role="user", content=user_message))

        messages = self._build_messages(history, reports, dietary_preference=dietary_preference)

        full_response = ""
        async for chunk in llm_adapter.complete(messages, stream=stream):
            full_response += chunk
            yield chunk

        history.append(Message(role="assistant", content=full_response))

    def _build_messages(self, history: List[Message], reports: Optional[List[ExplainabilityReport]], dietary_preference: Optional[str] = None) -> List[dict]:
        system_prompt = self.build_system_prompt(dietary_preference)
        patient_data = self._get_patient_data()
        
        vitals_summary = f"BP: {patient_data.get('bp', 'N/A')} | Glucose: {patient_data.get('glucose', 'N/A')} | SpO2: {patient_data.get('spo2', 'N/A')}"
        context = f"\n\n[REAL-TIME PATIENT DATA]\n{vitals_summary}\nSteps: {patient_data.get('avg_steps', 'N/A')}\n"
        
        messages = [{"role": "system", "content": system_prompt + context}]
        for msg in history:
            if msg.role != "system":
                messages.append({"role": msg.role, "content": msg.content})

        if reports:
            reports_text = "\n".join(f"- {r.plain_language_summary}" for r in reports)
            # Insert findings as a system message right after the main system prompt
            messages.insert(1, {"role": "system", "content": f"[HEALTH FINDINGS]:\n{reports_text}\n(Note: Use these to enrich your answer. Never use these to refuse answering the user's direct question.)"})
        
        return messages


conversation_service = ConversationService()
