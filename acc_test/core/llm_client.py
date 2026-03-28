from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI


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
        self._client = OpenAI(
            base_url=config.base_url,
            api_key=config.api_key,
            timeout=config.timeout,
        )

    @classmethod
    def from_env(cls) -> "OpenAICompatibleClient":
        load_dotenv()
        base_url = os.getenv("OPENAI_BASE_URL")
        api_key = os.getenv("OPENAI_API_KEY")
        model_value = os.getenv("OPENAI_MODEL", "")
        models = tuple(parse_model_list(model_value))
        if not base_url or not api_key or not models:
            raise ValueError("Missing OPENAI_BASE_URL, OPENAI_API_KEY, or OPENAI_MODEL")

        temperature = _parse_optional_float(os.getenv("OPENAI_TEMPERATURE"))
        max_tokens = _parse_optional_int(os.getenv("OPENAI_MAX_TOKENS"))
        timeout = _parse_optional_float(os.getenv("OPENAI_TIMEOUT"))

        return cls(
            OpenAICompatibleConfig(
                base_url=base_url,
                api_key=api_key,
                models=models,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
            )
        )

    def create_chat_completion(self, *, model: str, messages: list[dict[str, str]]) -> Any:
        params: dict[str, Any] = {
            "model": model,
            "messages": messages,
        }
        if self.config.temperature is not None:
            params["temperature"] = self.config.temperature
        if self.config.max_tokens is not None:
            params["max_tokens"] = self.config.max_tokens
        return self._client.chat.completions.create(**params)


def _parse_optional_float(value: str | None) -> float | None:
    if value is None or not value.strip():
        return None
    return float(value)


def _parse_optional_int(value: str | None) -> int | None:
    if value is None or not value.strip():
        return None
    return int(value)
