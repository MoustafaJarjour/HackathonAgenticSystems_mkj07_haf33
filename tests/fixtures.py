"""Synthetic test data and an offline HTTP harness, never a paper-specific answer."""
import json
import os
import time
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import httpx

import agent


SOURCE_URL = "https://example.org/synthetic-fixture"
QUOTE = "The relation is y = a*x + b."
SOURCE = (
    "Synthetic test fixture, Section 1. " + QUOTE + " The coefficient a scales the input x, "
    "and b adds an offset to the result y. This is invented test data, not a research paper. "
    "For a small worked demonstration, choose x = 2 and vary a and b."
)
_HTTP_CLIENT = httpx.Client


def lesson():
    """Return fresh test data so tests can mutate it independently."""
    return {
        "schema_version": 1,
        "title": "Synthetic test fixture: affine relationship",
        "concept_summary": "In this synthetic test, a scales x and b adds an offset: y = a*x + b.",
        "why_it_matters": "A small calculation makes changes in scale and offset visible.",
        "terms": [{"symbol": "a", "meaning": "Scale coefficient"},
                  {"symbol": "b", "meaning": "Offset"},
                  {"symbol": "x", "meaning": "Input, fixed at 2 in this demo"},
                  {"symbol": "y", "meaning": "Calculated output"}],
        "equations": [{"expression": "y = a*x + b", "explanation": "Scale, then add the offset.",
                       "provenance": "source_supported", "evidence_ids": ["relation"]}],
        "controls": [
            {"id": "slope", "label": "Scale a", "meaning": "Coefficient multiplying x.",
             "kind": "range", "default": 2, "min": -4, "max": 4, "step": 0.1},
            {"id": "intercept", "label": "Offset b", "meaning": "Value added after scaling.",
             "kind": "number", "default": 1, "min": -5, "max": 5, "step": 0.1}],
        "computations": [{"id": "result", "label": "Output y at x = 2",
                          "expression": "slope * 2 + intercept", "unit": "arbitrary units",
                          "show": True, "provenance": "teaching_simplification", "evidence_ids": []}],
        "visualizations": [{"id": "relationship", "kind": "line", "title": "Output as scale changes",
                            "source": "result", "sweep_control": "slope",
                            "x_label": "Scale a", "y_label": "Output y at x = 2"}],
        "explorations": [
            {"change": "Set a to zero.", "observe": "The output equals b.",
             "why": "Multiplying the fixed input by zero removes its contribution."},
            {"change": "Increase b by one.", "observe": "The output and entire curve rise by one.",
             "why": "The offset is added to every calculated value."}],
        "limitations": ["This is synthetic test data; x is fixed at 2 and no experiment is reproduced."],
        "grounding": {
            "paper_title": "Synthetic fixture, not a research paper", "source_url": SOURCE_URL,
            "source_claims": [{"id": "relation", "claim": "The fixture defines an affine relation.",
                               "locator": "Synthetic fixture, Section 1", "quote": QUOTE}],
            "teaching_simplifications": ["Fix x at 2 to expose scale and offset with two controls."]},
    }


def case():
    return {"source_url": SOURCE_URL, "focus": "Explain scale and offset in the supplied fixture.",
            "audience": "Engineering undergraduate", "excerpt": SOURCE}


def completion(spec, usage=True):
    body = {"id": "offline-fixture-response", "choices": [
        {"finish_reason": "stop", "message": {"content": json.dumps(spec)}}]}
    if usage:
        body["usage"] = {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}
    return body


@contextmanager
def mock_http(handler):
    def factory(**kwargs):
        return _HTTP_CLIENT(transport=httpx.MockTransport(handler), **kwargs)
    with patch("src.openrouter_client.httpx.Client", side_effect=factory):
        yield


def run_fixture(output: Path, responses=None, input_case=None, model="offline/test-model"):
    """Exercise actual agent.main and client; intercept every HTTP request in memory."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    input_path = output / "case.json"
    input_path.write_text(json.dumps(case() if input_case is None else input_case), encoding="utf-8")
    responses = [completion(lesson())] if responses is None else list(responses)
    payloads = []

    def handler(request):
        assert str(request.url) == "https://openrouter.ai/api/v1/chat/completions"
        payloads.append(json.loads(request.content))
        assert len(payloads) <= len(responses), "Unexpected extra API request"
        return httpx.Response(200, json=responses[len(payloads) - 1])

    env = {"OPENROUTER_API_KEY": "offline-test-key-never-valid", "PTP_ALLOW_SOURCE_FETCH": "",
           "PTP_SOURCE_FILE": "", "PTP_SOURCE_DIR": ""}
    with patch.dict(os.environ, env), mock_http(handler), patch.object(agent, "PROCESS_STARTED", time.monotonic()):
        code = agent.main(["--input", str(input_path), "--output", str(output), "--model", model])
    events = [json.loads(line) for line in (output / "trace.jsonl").read_text(encoding="utf-8").splitlines()]
    return code, events, payloads
