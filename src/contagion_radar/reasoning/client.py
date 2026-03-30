"""OpenRouter AI client.

Uses OpenAI SDK with base_url pointed to OpenRouter.
Model-agnostic: swap models by changing config.ai.model.
"""

from __future__ import annotations

import json
import time
from typing import Any

from contagion_radar.core.config import AIConfig


class AIClient:
    """Thin wrapper around OpenAI SDK targeting OpenRouter."""

    def __init__(self, config: AIConfig):
        self._config = config
        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI(
                base_url=self._config.base_url,
                api_key=self._config.api_key,
            )
        return self._client

    async def generate(
        self,
        system: str,
        user: str,
        response_schema: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Generate a structured JSON response.

        Args:
            system: system prompt
            user: user message (the query)
            response_schema: optional JSON schema to enforce structured output

        Returns:
            Parsed JSON dict from the model response.
        """
        client = self._get_client()

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]

        kwargs: dict[str, Any] = {
            "model": self._config.model,
            "messages": messages,
            "max_tokens": self._config.max_tokens,
            "temperature": self._config.temperature,
        }

        if response_schema is not None:
            kwargs["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "response",
                    "strict": True,
                    "schema": response_schema,
                },
            }
        else:
            kwargs["response_format"] = {"type": "json_object"}

        start = time.time()
        response = client.chat.completions.create(**kwargs)
        latency_ms = int((time.time() - start) * 1000)

        content = response.choices[0].message.content
        result = json.loads(content)

        # Attach metadata for logging
        result["_meta"] = {
            "model": self._config.model,
            "latency_ms": latency_ms,
            "input_tokens": getattr(response.usage, "prompt_tokens", 0),
            "output_tokens": getattr(response.usage, "completion_tokens", 0),
        }

        return result

    @property
    def model(self) -> str:
        return self._config.model
