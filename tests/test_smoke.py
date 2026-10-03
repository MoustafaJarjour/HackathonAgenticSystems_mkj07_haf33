"""Run with: python -m unittest discover -s tests -v. No key or network needed."""
import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import httpx

from src.expressions import compile_expression
from src.models import SpecError
from src.openrouter_client import Budget, BudgetError, OpenRouterClient
from src.renderer import render
from src.trace import Trace
from src.validator import validate_html, validate_spec
from tests.fixtures import SOURCE, SOURCE_URL, case, completion, lesson, mock_http, run_fixture


class SmokeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name) / "out"

    def test_actual_entry_point_outputs_and_usage(self):
        code, events, requests = run_fixture(self.output, model="exact/model-from-cli")
        self.assertEqual(code, 0)
        self.assertEqual(requests[0]["model"], "exact/model-from-cli")
        self.assertEqual(json.loads((self.output / "lesson.json").read_text()), lesson())
        self.assertTrue((self.output / "index.html").stat().st_size > 1000)
        response = next(e for e in events if e["action"] == "response")
        self.assertEqual(response["metadata"]["usage"],
                         {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150})
        self.assertEqual(events[-1]["result"], "success")
        self.assertEqual(events[-1]["metadata"]["observed_total_tokens"], 150)
        self.assertNotIn("offline-test-key-never-valid", (self.output / "trace.jsonl").read_text())

    def test_url_only_fails_without_network_or_stale_page(self):
        self.output.mkdir()
        (self.output / "index.html").write_text("stale page")
        input_case = case()
        del input_case["excerpt"]
        code, events, requests = run_fixture(self.output, responses=[], input_case=input_case)
        self.assertNotEqual(code, 0)
        self.assertEqual(requests, [])
        self.assertFalse((self.output / "index.html").exists())
        self.assertEqual(events[-1]["result"], "failed")
        self.assertEqual(events[-1]["metadata"]["error_type"], "SourceError")

    def test_invalid_spec_is_repaired_once(self):
        invalid = lesson()
        del invalid["why_it_matters"]
        replacement = {"controls": [], "computations": [], "visualizations": [],
                       "teaching": {"why_it_matters": lesson()["why_it_matters"]}}
        code, events, requests = run_fixture(self.output, [completion(invalid), completion(replacement)])
        self.assertEqual(code, 0)
        self.assertEqual(len(requests), 2)
        self.assertIn("TARGETED REPAIR CONTRACT", requests[1]["messages"][1]["content"])
        self.assertTrue(any(e["action"] == "revise" for e in events))
        self.assertTrue(any(e["action"] == "candidate" and e["result"] == "failed" for e in events))
        self.assertTrue(any(e["action"] == "runtime_case" and e["result"] == "passed" for e in events))

    def test_arbitrary_code_is_not_math(self):
        for expression in ("__import__('os')", "slope.__class__", "(lambda: 1)()", "slope[0]"):
            with self.subTest(expression=expression), self.assertRaises(SpecError):
                compile_expression(expression, {"slope"})

    def test_duplicate_identifiers_and_fabricated_quote_rejected(self):
        duplicate = lesson()
        duplicate["controls"][1]["id"] = "slope"
        fabricated = lesson()
        fabricated["grounding"]["source_claims"][0]["quote"] = "A quotation that is absent from the source."
        for spec in (duplicate, fabricated):
            with self.subTest(spec=spec["grounding"]["source_claims"][0]["quote"]):
                with self.assertRaises(SpecError):
                    validate_spec(spec, SOURCE, SOURCE_URL)

    def test_runtime_network_resources_and_duplicate_html_ids_rejected(self):
        spec = lesson()
        compiled, _ = validate_spec(spec, SOURCE, SOURCE_URL)
        html = render(spec, compiled)
        validate_html(html, spec)
        for injection in ('<script src="https://example.org/code.js"></script>',
                          '<style>@import "https://example.org/style.css";</style>',
                          '<script>fetch("https://example.org/data")</script>',
                          '<div id="concept"></div>'):
            with self.subTest(injection=injection), self.assertRaises(SpecError):
                validate_html(html.replace("</body>", injection + "</body>"), spec)

    def test_missing_usage_keeps_conservative_completion_limit(self):
        budget = Budget(time.monotonic())
        for _ in range(5):
            budget.begin_attempt(6000)
            self.assertIsNone(budget.record_usage(None)["completion_tokens"])
        self.assertFalse(budget.summary()["usage_is_complete"])
        self.assertEqual(budget.summary()["attempts_missing_usage"]["completion_tokens"], 5)
        with self.assertRaises(BudgetError):
            budget.begin_attempt(1)
        self.assertEqual(budget.requests, 5)

    def test_tenth_request_and_deadline_are_enforced(self):
        budget = Budget(time.monotonic())
        for _ in range(10):
            budget.begin_attempt(1)
        with self.assertRaises(BudgetError):
            budget.begin_attempt(1)
        self.assertEqual(budget.requests, 10)
        with self.assertRaises(BudgetError):
            Budget(time.monotonic() - 600).check()

    def test_transient_retry_counts_both_attempts_and_missing_usage(self):
        trace = Trace(Path(self.temp.name) / "retry.jsonl")
        budget = Budget(time.monotonic())
        calls = []

        def handler(request):
            calls.append(request)
            return httpx.Response(503, json={}) if len(calls) == 1 else httpx.Response(200, json=completion(lesson()))

        with mock_http(handler), patch("src.openrouter_client.time.sleep"):
            client = OpenRouterClient("retry/model", trace, budget, api_key="dummy")
            try:
                self.assertEqual(json.loads(client.complete([])), lesson())
            finally:
                client.close()
        self.assertEqual(budget.requests, 2)
        self.assertEqual(budget.reserved_completion_tokens, 16000)
        self.assertFalse(budget.summary()["usage_is_complete"])
        events = [json.loads(line) for line in trace.path.read_text().splitlines()]
        self.assertEqual(sum(e["action"] == "retry" for e in events), 1)
        self.assertIsNone(next(e for e in events if e["action"] == "response")["metadata"]["usage"]["completion_tokens"])


if __name__ == "__main__":
    unittest.main()
