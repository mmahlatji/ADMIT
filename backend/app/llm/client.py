"""LLM client: an Ollama backend"""

import json
from functools import lru_cache
from typing import Any, Protocol

import httpx

from app.config import get_settings
from app.llm import prompts
from app.llm.exceptions import LLMResponseError, LLMUnavailableError


class LLMClient(Protocol):
    """What the service layer needs from any LLM backend."""

    async def parse_intent(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]: ...


class OllamaLLMClient:
    """Talks to a local Ollama instance."""

    def __init__(
        self,
        url: str,
        model: str,
        timeout: float,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._model = model
        self._client = httpx.AsyncClient(
            base_url=url.rstrip("/"),
            timeout=timeout,
            transport=transport,
        )

    async def _chat(self, messages: list[dict[str, str]], *, json_mode: bool) -> str:
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "stream": False,
            # The schema-injected prompt is ~2.7k tokens; the default context of
            # 2048 would truncate it. num_predict caps how long generation runs.
            "options": {"num_ctx": 8192, "num_predict": 1024},
        }
        if json_mode:
            payload["format"] = "json"

        try:
            response = await self._client.post("/api/chat", json=payload)
        except httpx.HTTPError as exc:
            raise LLMUnavailableError(f"Could not reach Ollama: {exc}") from exc

        if response.status_code != 200:
            raise LLMUnavailableError(
                f"Ollama returned {response.status_code}: {response.text}"
            )

        try:
            content = response.json().get("message", {}).get("content")
        except json.JSONDecodeError as exc:
            raise LLMResponseError("Ollama returned a malformed response") from exc

        if not content:
            raise LLMResponseError("Ollama returned no message content")
        return content

    async def parse_intent(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        """Parse the JSON outputed by the LLM detailling intended query"""
        content = await self._chat(prompts.parse_messages(prompt, schema), json_mode=True)
        try:
            parsed = json.loads(prompts._extract_json(content))
        except (json.JSONDecodeError, ValueError) as exc:
            raise LLMResponseError(f"Could not parse LLM output as JSON: {content[:200]}") from exc
        if not isinstance(parsed, dict):
            raise LLMResponseError("LLM output was not a JSON object")
        return parsed


@lru_cache
def get_llm_client() -> LLMClient:
    """Build the configured LLM client once and reuse it."""
    settings = get_settings()
    return OllamaLLMClient(
        settings.ollama_url,
        settings.ollama_model,
        settings.ollama_timeout_seconds,
    )
