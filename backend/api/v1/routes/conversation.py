"""
Conversation Route — POST /api/v1/conversation
Chat with the AI health companion. Supports streaming SSE responses.
"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from backend.services.conversation_service import conversation_service
from backend.services.rule_engine import rule_engine
from backend.services.explainability_service import explainability_service

router = APIRouter(prefix="/conversation", tags=["Conversation"])


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    include_health_context: bool = True
    stream: bool = True


class NewSessionResponse(BaseModel):
    session_id: str


@router.post("/session", response_model=NewSessionResponse)
async def new_session():
    session_id = conversation_service.new_session()
    return NewSessionResponse(session_id=session_id)


@router.post("/chat")
async def chat(payload: ChatRequest):
    session_id = payload.session_id or conversation_service.new_session()

    reports = None
    if payload.include_health_context:
        findings = rule_engine.evaluate()
        reports = explainability_service.generate_reports(findings)

    if payload.stream:
        async def event_stream():
            yield f"data: {{'session_id': '{session_id}'}}\n\n"
            async for chunk in conversation_service.chat(
                session_id, payload.message, reports=reports, stream=True
            ):
                safe = chunk.replace("\n", "\\n").replace('"', '\\"')
                yield f'data: {{"chunk": "{safe}"}}\n\n'
            yield "data: [DONE]\n\n"

        return StreamingResponse(event_stream(), media_type="text/event-stream")
    else:
        full = ""
        async for chunk in conversation_service.chat(
            session_id, payload.message, reports=reports, stream=False
        ):
            full += chunk
        return {"session_id": session_id, "response": full}


@router.get("/summary")
async def health_summary():
    async def stream():
        async for chunk in conversation_service.get_health_summary(stream=True):
            safe = chunk.replace("\n", "\\n").replace('"', '\\"')
            yield f'data: {{"chunk": "{safe}"}}\n\n'
        yield "data: [DONE]\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")


@router.get("/history/{session_id}", response_model=List[Dict[str, Any]])
async def get_history(session_id: str):
    history = conversation_service.get_history(session_id)
    return [
        {"role": m.role, "content": m.content, "timestamp": m.timestamp.isoformat()}
        for m in history
        if m.role != "system"
    ]
