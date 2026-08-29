from __future__ import annotations

import json
import logging
from typing import Optional, Any

from app.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class ModelClient:
    """
    Provider-agnostic model client.
    Keeps provider-specific code behind a single interface.
    """

    def __init__(self):
        self._openai_client = None

    def _get_openai_client(self):
        if self._openai_client is None:
            try:
                from openai import OpenAI
                if settings.llm_api_key:
                    self._openai_client = OpenAI(api_key=settings.llm_api_key)
            except ImportError:
                pass
        return self._openai_client

    async def complete(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
        max_tokens: int = 1000,
        response_format: str = "json",
    ) -> Optional[dict | str]:
        """
        Call the configured LLM. Returns parsed JSON dict or string.
        Falls back to None if unavailable (caller must handle).
        """
        if not settings.enable_llm_judge or not settings.llm_api_key:
            return None

        try:
            client = self._get_openai_client()
            if client is None:
                return None

            kwargs: dict[str, Any] = {
                "model": settings.llm_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            if response_format == "json":
                kwargs["response_format"] = {"type": "json_object"}

            response = client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content

            if response_format == "json":
                return json.loads(content)
            return content

        except Exception as e:
            logger.warning(f"LLM call failed: {e}")
            return None

    async def get_embedding(self, text: str) -> Optional[list[float]]:
        """Get embedding vector for text."""
        if not settings.llm_api_key:
            return None
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.llm_api_key)
            response = client.embeddings.create(
                model=settings.embedding_model,
                input=text[:8000],
            )
            return response.data[0].embedding
        except Exception as e:
            logger.warning(f"Embedding call failed: {e}")
            return None


_client: Optional[ModelClient] = None


def get_model_client() -> ModelClient:
    global _client
    if _client is None:
        _client = ModelClient()
    return _client
