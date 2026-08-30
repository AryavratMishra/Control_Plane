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
        self._clients = {}

    def _get_client(self, provider: str):
        if provider not in self._clients:
            if provider == "openai":
                from openai import OpenAI
                self._clients[provider] = OpenAI(api_key=settings.llm_api_key)
            elif provider == "gemini":
                from google import genai
                self._clients[provider] = genai.Client(api_key=settings.llm_api_key)
            elif provider == "anthropic":
                from anthropic import Anthropic
                self._clients[provider] = Anthropic(api_key=settings.llm_api_key)
            else:
                raise ValueError(f"Unsupported LLM provider: {provider}")
        return self._clients[provider]

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

        provider = settings.llm_provider.lower()
        
        try:
            client = self._get_client(provider)
            
            if provider == "openai":
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
                
            elif provider == "gemini":
                from google.genai import types
                
                sys_prompt = system_prompt
                if response_format == "json":
                    sys_prompt += "\nOutput JSON."
                    
                config_kwargs = {
                    "system_instruction": sys_prompt,
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                }
                if response_format == "json":
                    config_kwargs["response_mime_type"] = "application/json"
                    
                config = types.GenerateContentConfig(**config_kwargs)
                
                response = client.models.generate_content(
                    model=settings.llm_model,
                    contents=user_prompt,
                    config=config,
                )
                content = response.text
                
            elif provider == "anthropic":
                sys_prompt = system_prompt
                if response_format == "json":
                    sys_prompt += "\nOutput valid JSON without markdown wrapping."
                    
                response = client.messages.create(
                    model=settings.llm_model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=sys_prompt,
                    messages=[
                        {"role": "user", "content": user_prompt}
                    ]
                )
                content = response.content[0].text
                
            if response_format == "json":
                content = content.strip()
                if content.startswith("```json"):
                    content = content[7:]
                if content.startswith("```"):
                    content = content[3:]
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()
                
                return json.loads(content)
                
            return content

        except Exception as e:
            logger.warning(f"LLM call failed ({provider}): {e}")
            return None

    async def generate_response(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: int = 400,
    ) -> str | None:
        """
        Generate a plain-text AI response (used to produce live demo responses).
        Unlike complete(), this does NOT require enable_llm_judge=True â€”
        it is used to simulate the downstream AI agent, not the judge.
        Returns the raw text string, or None on failure.
        """
        if not settings.llm_api_key:
            return None

        provider = settings.llm_provider.lower()

        try:
            client = self._get_client(provider)

            if provider == "openai":
                response = client.chat.completions.create(
                    model=settings.llm_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return response.choices[0].message.content.strip()

            elif provider == "gemini":
                from google.genai import types
                config = types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                )
                response = client.models.generate_content(
                    model=settings.llm_model,
                    contents=user_message,
                    config=config,
                )
                return response.text.strip()

            elif provider == "anthropic":
                response = client.messages.create(
                    model=settings.llm_model,
                    max_tokens=max_tokens,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_message}],
                )
                return response.content[0].text.strip()

        except Exception as e:
            logger.warning(f"generate_response failed ({provider}): {e}")
            return None

    async def get_embedding(self, text: str) -> Optional[list[float]]:
        """Get embedding vector for text."""
        if not settings.llm_api_key:
            return None
            
        provider = settings.llm_provider.lower()
        
        try:
            client = self._get_client(provider)
            
            if provider == "openai":
                response = client.embeddings.create(
                    model=settings.embedding_model,
                    input=text[:8000],
                )
                return response.data[0].embedding
            elif provider == "gemini":
                response = client.models.embed_content(
                    model=settings.embedding_model,
                    contents=text[:8000],
                )
                return response.embeddings[0].values
            elif provider == "anthropic":
                logger.warning("Anthropic does not support native text embeddings via their SDK. Configure a different provider (like voyage) or fallback.")
                return None
                
        except Exception as e:
            logger.warning(f"Embedding call failed ({provider}): {e}")
            return None


_client: Optional[ModelClient] = None


def get_model_client() -> ModelClient:
    global _client
    if _client is None:
        _client = ModelClient()
    return _client

