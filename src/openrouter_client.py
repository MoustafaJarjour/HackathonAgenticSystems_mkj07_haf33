"""One OpenRouter client with conservative, attempt-based assessment limits."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

from .trace import Trace
from .models import provider_schema


class OpenRouterError(RuntimeError):
    """A controlled failure from configuration, transport, or API response."""


class BudgetError(RuntimeError):
    """The next action would exceed an assessment resource limit."""


class TruncatedCompletion(OpenRouterError):
    """Spent attempt reached its cap; caller must change the generation strategy."""


@dataclass
class Budget:
    """Elapsed time uses time.monotonic(); every HTTP attempt consumes a request."""

    started: float
    max_seconds: float = 570.0
    soft_seconds: float = 540.0
    requests: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    reserved_completion_tokens: int = 0
    held_completion_tokens: int = 0
    reasoning_tokens: int = 0
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
        if self.reserved_completion_tokens + self.held_completion_tokens > 30_000:
            raise BudgetError("The 30,000-token completion budget has been exceeded.")

    def begin_attempt(self, max_tokens: int) -> None:
        self.check()
        if time.monotonic() - self.started >= self.soft_seconds:
            raise BudgetError("The 540-second soft stop forbids further API attempts; reserve time for rechecks/writes.")
        if isinstance(max_tokens, bool) or not isinstance(max_tokens, int) or max_tokens < 1:
            raise ValueError("max_tokens must be a positive integer.")
        if self.requests >= 10:
            raise BudgetError("No API requests remain; retries count toward the limit.")
        if self.reserved_completion_tokens + self.held_completion_tokens + max_tokens > 30_000:
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
        details = usage.get("completion_tokens_details")
        reasoning = details.get("reasoning_tokens") if isinstance(details, dict) else None
        if type(reasoning) is int and reasoning >= 0:
            self.reasoning_tokens += reasoning
            recorded["reasoning_tokens"] = reasoning
        return recorded

    def summary(self) -> dict[str, Any]:
        elapsed = max(0.0, time.monotonic() - self.started)
        return {
            "requests": self.requests,
            "request_limit": 10,
            "observed_prompt_tokens": self.prompt_tokens,
            "observed_completion_tokens": self.completion_tokens,
            "observed_total_tokens": self.total_tokens,
            "observed_reasoning_tokens": self.reasoning_tokens,
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
            "held_completion_tokens": self.held_completion_tokens,
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

    def complete(self, messages: list[dict], max_tokens: int = 8000, schema: dict | None = None,
                 *, reasoning_enabled: bool = False, temperature: float = 0.2) -> str:
        if type(reasoning_enabled) is not bool:
            raise ValueError("reasoning_enabled must be a boolean.")
        if type(temperature) not in (int, float) or not 0 <= temperature <= 2:
            raise ValueError("temperature must be a finite number from 0 to 2.")
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
            "provider": {"require_parameters": True},
            # This model's low effort still spent the full completion cap on
            # reasoning in live runs. Its catalog marks reasoning optional.
            "reasoning": {"enabled": False, "exclude": True},
        }
        if reasoning_enabled:
            payload["reasoning"] = {"effort": "low", "exclude": True}
        if schema is not None:
            payload["response_format"] = {"type": "json_schema", "json_schema": {
                "name": "lesson", "strict": True, "schema": provider_schema(schema)}}
        transient_retries, schema_fallback = 0, False
        for attempt in range(3):
            self.budget.begin_attempt(max_tokens)
            started = time.monotonic()
            number = self.budget.requests
            self.trace.event(
                "openrouter", "request", "started", request_number=number,
                model=self.model, retry=attempt, max_tokens=max_tokens,
                format=payload["response_format"]["type"], reasoning_enabled=reasoning_enabled,
                temperature=temperature,
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
            resolved_model = body.get("model") if isinstance(body, dict) else None
            if not isinstance(response_id, str):
                response_id = None
            self.trace.event(
                "openrouter", "response", "transport_error" if transport_failed else "received",
                request_number=number, status_code=status,
                response_id=response_id, elapsed_seconds=round(elapsed, 3), usage=usage,
                resolved_model=resolved_model if isinstance(resolved_model, str) else None,
            )
            self.budget.check()
            error = body.get("error") if isinstance(body, dict) else None
            error_message = error.get("message", "") if isinstance(error, dict) else ""
            # Deliberate same-model fallback only for an explicit schema/format incompatibility.
            format_error = isinstance(error_message, str) and any(word in error_message.lower()
                           for word in ("json_schema", "response_format", "structured output", "schema"))
            if status in (400, 404, 422) and schema is not None and not schema_fallback and format_error:
                schema_fallback = True
                payload["response_format"] = {"type": "json_object"}
                self.trace.event("openrouter", "schema_fallback", "scheduled",
                                 reason="Provider rejected schema format; use JSON mode and local schema validation.")
                continue
            transient = transport_failed or status == 429 or (status is not None and 500 <= status <= 599)
            if transient:
                if transient_retries == 0:
                    transient_retries += 1
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
            finish_reason = choice.get("finish_reason")
            message = choice.get("message")
            content = message.get("content") if isinstance(message, dict) else None
            reasoning_count, completion_count = usage.get("reasoning_tokens"), usage.get("completion_tokens")
            self.trace.event("openrouter", "completion", "received", request_number=number,
                             finish_reason=finish_reason,
                             output_characters=len(content) if isinstance(content, str) else 0,
                             usage_consistent=(reasoning_count <= completion_count
                                               if type(reasoning_count) is int and type(completion_count) is int else None))
            if choice.get("finish_reason") == "length":
                raise TruncatedCompletion("The model reached its token cap; change output size before another attempt.")
            if finish_reason not in ("stop", "end_turn"):
                raise OpenRouterError("OpenRouter completion did not finish normally.")
            if isinstance(resolved_model, str) and resolved_model != self.model:
                raise OpenRouterError("OpenRouter returned a different model from the requested ID.")
            if not isinstance(content, str) or not content.strip():
                raise OpenRouterError("OpenRouter returned no usable JSON text.")
            return content
        raise OpenRouterError("OpenRouter request failed.")

    def close(self) -> None:
        self._client.close()
