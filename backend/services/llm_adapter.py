"""
LLM Adapter — Routes completions to Ollama (local) or Google Gemini API.
Controlled by LLM_PROVIDER in config.py / environment variable.
"""

import asyncio
from typing import AsyncIterator, Literal

import httpx

from backend.config import settings


class LLMAdapter:
    def __init__(self, provider: Literal["ollama", "gemini"] | None = None):
        self.provider = provider or settings.LLM_PROVIDER

    async def complete(self, prompt: str, stream: bool = False) -> AsyncIterator[str]:
        if self.provider == "ollama":
            async for chunk in self._ollama_complete(prompt, stream):
                yield chunk
        else:
            async for chunk in self._gemini_complete(prompt, stream):
                yield chunk

    # ── Ollama ─────────────────────────────────────────────────────────────────

    async def _ollama_complete(self, prompt: str, stream: bool) -> AsyncIterator[str]:
        url = f"{settings.OLLAMA_BASE_URL}/api/generate"
        payload = {"model": "llama3", "prompt": prompt, "stream": stream}
        async with httpx.AsyncClient(timeout=120) as client:
            if stream:
                async with client.stream("POST", url, json=payload) as resp:
                    import json
                    async for line in resp.aiter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                yield data.get("response", "")
                            except Exception:
                                continue
            else:
                resp = await client.post(url, json=payload)
                import json
                data = resp.json()
                yield data.get("response", "")

    # ── Gemini ─────────────────────────────────────────────────────────────────

    async def _gemini_complete(self, prompt: str, stream: bool) -> AsyncIterator[str]:
        if not settings.GEMINI_API_KEY:
            yield "[Error: GEMINI_API_KEY is not configured. Set it in config.py or environment.]"
            return

        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-2.0-flash")

            if stream:
                response = await asyncio.to_thread(
                    model.generate_content, prompt, stream=True
                )
                for chunk in response:
                    yield chunk.text or ""
            else:
                response = await asyncio.to_thread(model.generate_content, prompt)
                yield response.text or ""
        except ImportError:
            yield "[Error: google-generativeai package not installed. Run: pip install google-generativeai]"
        except Exception as e:
            yield f"[LLM Error: {str(e)}]"


# Default adapter instance
llm_adapter = LLMAdapter()
