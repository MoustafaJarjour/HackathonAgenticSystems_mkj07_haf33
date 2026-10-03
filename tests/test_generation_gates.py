"""Failure-path integration tests use mocked transport, not model quality evidence."""
import copy
import json
import tempfile
import time
import unittest
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import httpx

from src.models import LESSON_SCHEMA, SpecError
from src.openrouter_client import Budget, BudgetError, OpenRouterClient, OpenRouterError
from src.planner import apply_replacements
from src.trace import Trace
from tests.fixtures import completion, lesson, mock_http, run_fixture


class GenerationGates(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name) / "out"

    def test_numerical_failure_then_targeted_repair_rechecks_preserved_cases(self):
        wrong = lesson()
        wrong["computations"][0]["expression"] = "slope * 3 + intercept"
        replacement = {"controls": [], "computations": lesson()["computations"], "visualizations": [], "teaching": {}}
        code, events, payloads = run_fixture(self.output, [completion(wrong), completion(replacement)])
        self.assertEqual(code, 0)
        self.assertEqual([p["max_tokens"] for p in payloads], [8000, 3500, 4000, 3500])
        cases = [e["metadata"]["check"] for e in events if e["action"] == "runtime_case"]
        failed = next(c for c in cases if c["name"] == "default_case" and c["status"] == "failed")
        self.assertEqual(failed["actual"]["result"], 7)
        self.assertEqual(failed["expected"]["result"], 5)
        passed = next(c for c in cases if c["name"] == "default_case" and c["status"] == "passed")
        self.assertEqual(passed["actual"]["result"], 5)
        saved = json.loads((self.output / "lesson.json").read_text())
        self.assertEqual(saved["checks"], wrong["checks"])
        self.assertIn('"result": 7', payloads[1]["messages"][1]["content"])
        self.assertFalse((self.output / "partial.lesson.json").exists())

    def test_attempt_to_erase_failure_is_rejected_and_failure_keeps_partial_only(self):
        wrong = lesson()
        wrong["computations"][0]["expression"] = "slope * 3 + intercept"
        patch_body = {"controls": [], "computations": [], "visualizations": [], "teaching": {},
                      "checks": []}
        with self.assertRaises(SpecError):
            apply_replacements(wrong, patch_body)
        no_change = {key: value for key, value in patch_body.items() if key != "checks"}
        code, events, payloads = run_fixture(self.output, [completion(wrong), completion(no_change), completion(no_change)])
        self.assertNotEqual(code, 0)
        self.assertEqual(len(payloads), 3)
        self.assertFalse((self.output / "index.html").exists())
        self.assertFalse((self.output / "lesson.json").exists())
        self.assertTrue((self.output / "partial.lesson.json").exists())
        self.assertEqual(events[-1]["result"], "failed")

    def test_truncation_spends_usage_and_changes_generation_request(self):
        truncated = completion(lesson())
        truncated["choices"][0]["finish_reason"] = "length"
        code, events, payloads = run_fixture(self.output, [truncated, completion(lesson())])
        self.assertEqual(code, 0)
        self.assertNotEqual(payloads[0]["messages"], payloads[1]["messages"])
        self.assertIn("smaller package", payloads[1]["messages"][1]["content"])
        self.assertEqual(events[-1]["metadata"]["reserved_completion_tokens"], 23500)
        self.assertEqual(events[-1]["metadata"]["observed_completion_tokens"], 200)
        self.assertTrue(any(e["action"] == "length_recovery" for e in events))

    def test_missing_case_output_regenerates_and_preserves_the_expectation(self):
        wrong = lesson()
        wrong["checks"][0]["expected"] = {"missing_output": 5}
        regenerated = copy.deepcopy(wrong)
        extra = copy.deepcopy(regenerated["computations"][0])
        extra["id"] = "missing_output"
        regenerated["computations"].append(extra)
        code, events, payloads = run_fixture(self.output, [completion(wrong), completion(regenerated)])
        self.assertEqual(code, 0)
        self.assertEqual([payload["max_tokens"] for payload in payloads], [8000, 8000, 4000, 3500])
        self.assertTrue(any(event["action"] == "full_regeneration" for event in events))
        saved = json.loads((self.output / "lesson.json").read_text())
        self.assertEqual(saved["checks"], wrong["checks"])

    def test_strict_schema_rejection_records_deliberate_json_fallback(self):
        budget = Budget(time.monotonic())
        trace = Trace(Path(self.temp.name) / "fallback.jsonl")
        payloads = []
        def handler(request):
            payloads.append(json.loads(request.content))
            if len(payloads) == 1:
                return httpx.Response(400, json={"error": {"message": "json_schema unsupported"}})
            return httpx.Response(200, json=completion(lesson()))
        with mock_http(handler):
            client = OpenRouterClient("exact/model", trace, budget, api_key="dummy")
            try:
                client.complete([], max_tokens=1000, schema=LESSON_SCHEMA)
            finally:
                client.close()
        self.assertEqual([p["response_format"]["type"] for p in payloads], ["json_schema", "json_object"])
        self.assertEqual(budget.requests, 2)
        self.assertEqual(budget.reserved_completion_tokens, 2000)
        self.assertIn("schema_fallback", trace.path.read_text())

    def test_auth_failure_is_not_schema_fallback(self):
        budget = Budget(time.monotonic())
        trace = Trace(Path(self.temp.name) / "auth.jsonl")
        with mock_http(lambda request: httpx.Response(401, json={"error": {"message": "Unauthorized"}})):
            client = OpenRouterClient("exact/model", trace, budget, api_key="dummy")
            try:
                with self.assertRaises(OpenRouterError):
                    client.complete([], max_tokens=1000, schema=LESSON_SCHEMA)
            finally:
                client.close()
        self.assertEqual(budget.requests, 1)

    def test_generation_disables_optional_reasoning_without_unsupported_effort(self):
        # The live exact-model trace exhausted the cap while thinking. Lock down
        # the request setting; only a live run can establish provider behavior.
        budget = Budget(time.monotonic())
        trace = Trace(Path(self.temp.name) / "disabled-thinking.jsonl")
        payloads = []
        def handler(request):
            payloads.append(json.loads(request.content))
            return httpx.Response(200, json=completion(lesson()))
        with mock_http(handler):
            client = OpenRouterClient("deepseek/deepseek-v4.1-flash", trace, budget, api_key="dummy")
            try:
                client.complete([], max_tokens=8000, schema=LESSON_SCHEMA)
            finally:
                client.close()
        self.assertEqual(payloads[0]["reasoning"], {"enabled": False, "exclude": True})
        self.assertEqual(payloads[0]["model"], "deepseek/deepseek-v4.1-flash")
        self.assertEqual(budget.requests, 1)

    def test_reasoning_count_is_not_added_twice_and_private_text_is_redacted(self):
        budget = Budget(time.monotonic())
        budget.begin_attempt(100)
        recorded = budget.record_usage({"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30,
                                        "completion_tokens_details": {"reasoning_tokens": 5}})
        self.assertEqual(budget.completion_tokens, 20)
        self.assertEqual(budget.reasoning_tokens, 5)
        trace = Trace(Path(self.temp.name) / "reasoning.jsonl", secret="test-secret")
        trace.event("test", "redaction", "ok", reasoning_tokens=5, reasoning="private text",
                    reasoning_effort="low", reasoning_enabled=False, content="private content", label="test-secret")
        data = json.loads(trace.path.read_text())["metadata"]
        self.assertEqual(data["reasoning_tokens"], 5)
        self.assertEqual(data["reasoning_effort"], "low")
        self.assertIs(data["reasoning_enabled"], False)
        self.assertEqual(data["reasoning"], "[REDACTED]")
        self.assertNotIn("test-secret", trace.path.read_text())

    def test_soft_stop_allows_recheck_but_refuses_new_api_attempt(self):
        budget = Budget(time.monotonic() - 541)
        budget.check()
        with self.assertRaisesRegex(BudgetError, "soft stop"):
            budget.begin_attempt(1)
        self.assertEqual(budget.requests, 0)

    def test_watchdog_stops_a_blocked_source_stage(self):
        from tests.fixtures import case
        input_file = Path(self.temp.name) / "case.json"
        input_file.write_text(json.dumps(case()))
        code = """import sys,time,agent
from src.openrouter_client import Budget
agent.PROCESS_STARTED=time.monotonic()
agent.Budget=lambda started: Budget(started,max_seconds=.15,soft_seconds=.1)
agent.obtain_source=lambda *args: time.sleep(3)
raise SystemExit(agent.main(['--input',sys.argv[1],'--output',sys.argv[2],'--model','offline/test']))
"""
        result = subprocess.run([sys.executable, "-c", code, str(input_file), str(self.output)],
                                timeout=5, capture_output=True)
        self.assertEqual(result.returncode, 4)
        self.assertFalse((self.output / "index.html").exists())
        events = [json.loads(line) for line in (self.output / "trace.jsonl").read_text().splitlines()]
        self.assertEqual(events[-1]["action"], "deadline")
        self.assertEqual(events[-1]["result"], "failed")


if __name__ == "__main__":
    unittest.main()
