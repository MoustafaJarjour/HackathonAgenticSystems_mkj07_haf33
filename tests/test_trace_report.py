"""Reports must preserve evidence and avoid inferring success from partial traces."""
from pathlib import Path
import tempfile
import unittest

from src.trace import Trace
from src.trace_report import write_report
from tests.fixtures import completion, lesson, run_fixture


class TraceReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "trace.jsonl"

    def test_recovered_failure_keeps_evidence_and_final_success(self):
        trace = Trace(self.path, secret="test-secret")
        trace.event("run", "start", "ok", model="test-model")
        trace.event("validation", "runtime_case", "failed", check={
            "name": "value|check", "details": "test-secret", "expected": {"value": 5}, "actual": {"value": 7}})
        trace.event("run", "finish", "success", requests=2, observed_completion_tokens=20,
                    usage_is_complete=False)
        before = self.path.read_bytes()
        report = write_report(self.path).read_text()
        self.assertIn("**Outcome: SUCCESS**", report)
        self.assertIn("failed: 1", report)
        self.assertIn('"value": 7', report)
        self.assertIn('"value": 5', report)
        self.assertIn("value&#124;check", report)
        self.assertIn("[REDACTED]", report)
        self.assertNotIn("test-secret", report)
        self.assertIn("| Prompt tokens (observed) | unknown |", report)
        self.assertIn("| Usage accounting complete | False |", report)
        self.assertEqual(self.path.read_bytes(), before)

    def test_partial_and_corrupt_trace_cannot_claim_success(self):
        trace = Trace(self.path)
        trace.event("validation", "spec_checks", "passed")
        self.assertIn("**Outcome: INCOMPLETE**", write_report(self.path).read_text())
        trace.event("run", "finish", "success")
        with self.path.open("a") as handle:
            handle.write('{"unfinished":')
        report = write_report(self.path).read_text()
        self.assertIn("**Outcome: INCOMPLETE**", report)
        self.assertIn("Line 3 is invalid or truncated", report)
        with self.assertRaises(ValueError):
            write_report(self.path, self.path)

    def test_cli_writes_reports_on_success_and_failure(self):
        output = Path(self.temp.name) / "success"
        code, _, _ = run_fixture(output, [completion(lesson())])
        self.assertEqual(code, 0)
        self.assertIn("**Outcome: SUCCESS**", (output / "trace.md").read_text())
        output = Path(self.temp.name) / "failure"
        bad = completion(lesson())
        bad["choices"][0]["finish_reason"] = "length"
        code, _, _ = run_fixture(output, [bad, bad])
        self.assertNotEqual(code, 0)
        self.assertIn("**Outcome: FAILED**", (output / "trace.md").read_text())


if __name__ == "__main__":
    unittest.main()
