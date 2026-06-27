"""Swappable, OpenAI-compatible LLM client (PROTOCOL.md §4.3).

`complete()` is the single entry point used by the router and the answer
generator. It reads LLM_BASE_URL / LLM_API_KEY / LLM_MODEL from config so the
provider can be swapped (cloud -> self-hosted open weights such as Qwen2.5,
Llama 3.x, Mistral-Small) without touching call sites.
"""
from __future__ import annotations

import json
from functools import lru_cache

from openai import OpenAI

from core.config import settings


@lru_cache(maxsize=1)
def _client() -> OpenAI:
    if not settings.llm_api_key:
        # Many self-hosted endpoints accept any key; default to a placeholder so
        # local open-model servers (vLLM/Ollama) work out of the box.
        api_key = "not-needed"
    else:
        api_key = settings.llm_api_key
    return OpenAI(base_url=settings.llm_base_url, api_key=api_key)


def complete(
    system: str,
    user: str,
    json_schema: dict | None = None,
    temperature: float = 0.2,
) -> str | dict:
    """Run a chat completion.

    Returns a parsed ``dict`` when ``json_schema`` is provided (structured
    output), otherwise the raw assistant string.
    """
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

    kwargs: dict = {
        "model": settings.llm_model,
        "messages": messages,
        "temperature": temperature,
    }
    if json_schema is not None:
        # Ask for JSON; OpenAI-compatible servers honor json_object response_format.
        kwargs["response_format"] = {"type": "json_object"}

    resp = _client().chat.completions.create(**kwargs)
    content = resp.choices[0].message.content or ""

    if json_schema is not None:
        return json.loads(content)
    return content
