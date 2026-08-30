from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MarkdownClientConfig:
    """Explicit runtime configuration for OpenAI-compatible markdown extraction."""

    base_url: str
    api_key: str = "not-needed"
    model: str = "qwen/qwen3.5-9b"
    timeout: float = 60.0
    prompt: str | None = None

    @property
    def client_kwargs(self) -> dict[str, str]:
        return {
            "base_url": self.base_url,
            "api_key": self.api_key,
        }

    @property
    def default_prompt(self) -> str:
        return self.prompt or "Convert the supplied content to clean Markdown. Output only Markdown."
