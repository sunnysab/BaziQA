from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any, Mapping
from urllib.parse import urlsplit, urlunsplit

from dotenv import load_dotenv
import httpx


def parse_model_list(value: str) -> list[str]:
    return [item.strip() for item in value.split("|") if item.strip()]


@dataclass(frozen=True)
class OpenAICompatibleConfig:
    base_url: str
    api_key: str
    models: tuple[str, ...]
    temperature: float | None = None
    max_tokens: int | None = None
    timeout: float | None = None


class OpenAICompatibleClient:
    def __init__(self, config: OpenAICompatibleConfig) -> None:
        self.config = config
        self._client = httpx.Client(timeout=config.timeout or 180.0)

    @classmethod
    def from_env(cls) -> "OpenAICompatibleClient":
        load_dotenv()
        return cls(build_config_from_env(os.environ))

    def create_chat_completion(self, *, model: str, messages: list[dict[str, str]]) -> Any:
        payload = build_chat_completion_payload(
            model=model,
            messages=messages,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
        )

        response = self._client.post(
            build_chat_completions_url(self.config.base_url),
            headers={
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            return response.json()
        return response.text


def _parse_optional_float(value: str | None) -> float | None:
    if value is None or not value.strip():
        return None
    return float(value)


def _parse_optional_int(value: str | None) -> int | None:
    if value is None or not value.strip():
        return None
    return int(value)


def build_config_from_env(env: Mapping[str, str]) -> OpenAICompatibleConfig:
    base_url = env.get("OPENAI_BASE_URL") or env.get("URL")
    api_key = env.get("OPENAI_API_KEY") or env.get("KEY")
    model_value = env.get("OPENAI_MODEL") or env.get("MODEL") or ""
    models = tuple(parse_model_list(model_value))
    if not base_url or not api_key or not models:
        raise ValueError("Missing OPENAI_BASE_URL/URL, OPENAI_API_KEY/KEY, or OPENAI_MODEL/MODEL")

    return OpenAICompatibleConfig(
        base_url=normalize_base_url(base_url),
        api_key=api_key,
        models=models,
        temperature=_parse_optional_float(env.get("OPENAI_TEMPERATURE")),
        max_tokens=_parse_optional_int(env.get("OPENAI_MAX_TOKENS")),
        timeout=_parse_optional_float(env.get("OPENAI_TIMEOUT")),
    )


def normalize_base_url(base_url: str) -> str:
    parts = urlsplit(base_url)
    path = parts.path.rstrip("/")
    if path in {"", "/"}:
        path = "/v1"
    elif path.endswith("/chat/completion") or path.endswith("/chat/completions"):
        path = path.rsplit("/chat/", 1)[0] or "/v1"
    normalized = parts._replace(path=path)
    return urlunsplit(normalized)


def build_chat_completions_url(base_url: str) -> str:
    normalized = normalize_base_url(base_url).rstrip("/")
    return f"{normalized}/chat/completions"


def build_chat_completion_payload(
    *,
    model: str,
    messages: list[dict[str, str]],
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
    }
    if temperature is not None:
        payload["temperature"] = temperature
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    return payload
