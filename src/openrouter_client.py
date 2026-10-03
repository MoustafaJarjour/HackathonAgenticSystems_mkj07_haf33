"""One OpenRouter client with conservative, attempt-based assessment limits."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

from .trace import Trace


class OpenRouterError(RuntimeError):
    """A controlled failure from configuration, transport, or API response."""


class BudgetError(RuntimeError):
    """The next action would exceed an assessment resource limit."""


@dataclass
class Budget:
    """Elapsed time uses time.monotonic(); every HTTP attempt consumes a request."""

    started: float
    max_seconds: float = 570.0
    requests: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    reserved_completion_tokens: int = 0
    _usage_responses: int = field(default=0, init=False)
    _unknown_prompt: int = field(default=0, init=False)
    _unknown_completion: int = field(default=0, init=False)
    _unknown_total: int = field(default=0, init=False)

    def remaining(self) -> float:
        return max(0.0, self.max_seconds - (time.monotonic() - self.started))

    def check(self) -> None:
        if self.remaining() <= 0:
            raise BudgetError("The execution time budget has been exhausted.")
        if self.requests > 10:
            raise BudgetError("The 10-request API budget has been exceeded.")
        if self.completion_tokens > 30_000:
            raise BudgetError("Reported completion usage exceeded 30,000 tokens.")
        if self.reserved_completion_tokens > 30_000:
            raise BudgetError("The 30,000-token completion budget has been exceeded.")

    def begin_attempt(self, max_tokens: int) -> None:
        self.check()
        if isinstance(max_tokens, bool) or not isinstance(max_tokens, int) or max_tokens < 1:
            raise ValueError("max_tokens must be a positive integer.")
        if self.requests >= 10:
            raise BudgetError("No API requests remain; retries count toward the limit.")
        if self.reserved_completion_tokens + max_tokens > 30_000:
            raise BudgetError("The next API attempt would exceed the completion budget.")
        # Reserve before transport, including attempts whose usage is unavailable.
        self.requests += 1
        self.reserved_completion_tokens += max_tokens

    def record_usage(self, usage: Any) -> dict[str, int | None]:
        self._usage_responses += 1
        usage = usage if isinstance(usage, dict) else {}
        recorded: dict[str, int | None] = {}
        for name in ("prompt_tokens", "completion_tokens", "total_tokens"):
            value = usage.get(name)
            if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                setattr(self, name, getattr(self, name) + value)
                recorded[name] = value
            else:
                setattr(self, "_unknown_" + name.removesuffix("_tokens"),
                        getattr(self, "_unknown_" + name.removesuffix("_tokens")) + 1)
                recorded[name] = None
        # completion_tokens already includes reasoning tokens when billed that way.
        return recorded

    def summary(self) -> dict[str, Any]:
        elapsed = max(0.0, time.monotonic() - self.started)
        return {
            "requests": self.requests,
            "request_limit": 10,
            "observed_prompt_tokens": self.prompt_tokens,
            "observed_completion_tokens": self.completion_tokens,
            "observed_total_tokens": self.total_tokens,
            "usage_is_complete": (
                self._usage_responses == self.requests
                and not any((self._unknown_prompt, self._unknown_completion, self._unknown_total))
            ),
            "attempts_missing_usage": {
                "prompt_tokens": self._unknown_prompt + self.requests - self._usage_responses,
                "completion_tokens": self._unknown_completion + self.requests - self._usage_responses,
                "total_tokens": self._unknown_total + self.requests - self._usage_responses,
            },
            "reserved_completion_tokens": self.reserved_completion_tokens,
            "completion_token_limit": 30_000,
            "elapsed_seconds": round(elapsed, 3),
            "remaining_seconds": round(self.remaining(), 3),
        }


class OpenRouterClient:
    ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(
        self, model: str, trace: Trace, budget: Budget, api_key: str | None = None
    ) -> None:
        key = api_key if api_key is not None else os.environ.get("OPENROUTER_API_KEY", "")
        if not key.strip():
            raise OpenRouterError("Set OPENROUTER_API_KEY before running the agent.")
        if not isinstance(model, str) or not model.strip():
            raise OpenRouterError("Pass a nonempty MODEL_ID through --model.")
        self.model = model
        self.trace = trace
        self.budget = budget
        # No SDK retries: this class owns and counts every attempt.
        self._client = httpx.Client(
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            follow_redirects=False,
            timeout=120.0,
        )

    def complete(self, messages: list[dict], max_tokens: int = 6000) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "provider": {"require_parameters": True},
        }
        for attempt in range(2):
            self.budget.begin_attempt(max_tokens)
            started = time.monotonic()
            number = self.budget.requests
            self.trace.event(
                "openrouter", "request", "started", request_number=number,
                model=self.model, retry=attempt, max_tokens=max_tokens,
                reserved_completion_tokens=self.budget.reserved_completion_tokens,
            )
            response: httpx.Response | None = None
            body: Any = None
            transport_failed = False
            try:
                response = self._client.post(
                    self.ENDPOINT, json=payload,
                    timeout=max(0.1, min(120.0, self.budget.remaining())),
                )
            except httpx.TransportError:
                transport_failed = True
            elapsed = time.monotonic() - started
            if response is not None:
                try:
                    body = response.json()
                except (ValueError, UnicodeError):
                    body = None
            usage = self.budget.record_usage(body.get("usage") if isinstance(body, dict) else None)
            status = response.status_code if response is not None else None
            response_id = body.get("id") if isinstance(body, dict) else None
            if not isinstance(response_id, str):
                response_id = None
            self.trace.event(
                "openrouter", "response", "transport_error" if transport_failed else "received",
                request_number=number, status_code=status,
                response_id=response_id, elapsed_seconds=round(elapsed, 3), usage=usage,
            )
            self.budget.check()
            transient = transport_failed or status == 429 or (status is not None and 500 <= status <= 599)
            if transient:
                if attempt == 0:
                    if self.budget.remaining() <= 1.0:
                        raise BudgetError("Insufficient time remains for an API retry.")
                    self.trace.event("openrouter", "retry", "scheduled", request_number=number)
                    time.sleep(min(1.0, self.budget.remaining()))
                    continue
                if transport_failed:
                    raise OpenRouterError("OpenRouter transport failed after one retry.")
                raise OpenRouterError(f"OpenRouter returned HTTP {status} after one retry.")
            if response is None:
                raise OpenRouterError("OpenRouter did not return a response.")
            if not 200 <= response.status_code <= 299:
                raise OpenRouterError(
                    f"OpenRouter returned HTTP {response.status_code}. Check the model ID, "
                    "account access, and support for JSON output and requested parameters."
                )
            if not isinstance(body, dict) or body.get("error"):
                raise OpenRouterError("OpenRouter returned an invalid response or API error.")
            choices = body.get("choices")
            if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
                raise OpenRouterError("OpenRouter returned no completion choices.")
            choice = choices[0]
            if choice.get("finish_reason") == "length":
                raise OpenRouterError("The model reached its token cap; no partial lesson will be rendered.")
            message = choice.get("message")
            content = message.get("content") if isinstance(message, dict) else None
            if not isinstance(content, str) or not content.strip():
                raise OpenRouterError("OpenRouter returned no usable JSON text.")
            return content
        raise OpenRouterError("OpenRouter request failed.")

    def close(self) -> None:
        self._client.close()
