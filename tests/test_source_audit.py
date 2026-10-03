"""Mocked source-critique gates; live scientific quality is assessed separately."""
import json
import tempfile
import unittest
from pathlib import Path

from tests.fixtures import completion, lesson, run_fixture


def report(status="revised", patch=None):
    return completion({"status": status, "reason": "Concrete synthetic source comparison.",
                       "patch": patch or {"controls": [], "computations": lesson()["computations"],
                                           "visualizations": [], "teaching": {}}})


class SourceAuditTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.output = Path(temporary.name) / "out"

    def test_missed_nondefault_equation_is_reviewed_and_all_gates_rerun(self):
        wrong = lesson()
        # Both generated cases pass, while other states contradict the source.
        wrong["computations"][0]["expression"] += " + (slope-2)*(slope+4)"
        code, events, requests = run_fixture(self.output, [completion(wrong)], audit_responses=[report()])
        self.assertEqual(code, 0)
        self.assertEqual([request["max_tokens"] for request in requests], [8000, 3500])
        saved = json.loads((self.output / "lesson.json").read_text())
        self.assertEqual(saved["computations"], lesson()["computations"])
        self.assertEqual(saved["checks"], wrong["checks"])
        reviewed = [event for event in events if event["action"] == "runtime_case"
                    and event["metadata"].get("after_source_review")]
        self.assertTrue(reviewed)
        self.assertTrue(all(event["result"] == "passed" for event in reviewed))
        self.assertFalse(next(event for event in events if event["action"] == "source_semantics_review")
                         ["metadata"]["independent_science_verified"])

    def test_source_correction_conflicting_with_expectations_is_terminal(self):
        wrong = lesson()
        wrong["computations"][0]["expression"] = "slope*3+intercept"
        wrong["checks"][0]["expected"]["result"] = 7
        wrong["checks"][1]["expected"]["result"] = -11
        code, events, requests = run_fixture(self.output, [completion(wrong)], audit_responses=[report()])
        self.assertEqual(code, 1)
        self.assertEqual(len(requests), 2)
        self.assertEqual(events[-1]["metadata"]["error_type"], "SourceReviewError")
        self.assertFalse((self.output / "index.html").exists())
        partial = json.loads((self.output / "partial.lesson.json").read_text())
        self.assertEqual(partial["checks"], wrong["checks"])
        self.assertEqual(partial["computations"], lesson()["computations"])

    def test_unresolved_is_not_an_unchanged_success(self):
        empty = {"controls": [], "computations": [], "visualizations": [], "teaching": {}}
        code, events, requests = run_fixture(self.output, audit_responses=[report("unresolved", empty)])
        self.assertEqual(code, 1)
        self.assertEqual(len(requests), 2)
        self.assertEqual(events[-1]["metadata"]["error_type"], "SourceReviewError")
        self.assertFalse((self.output / "lesson.json").exists())

    def test_audit_cannot_erase_cases(self):
        patch = {"controls": [], "computations": [], "visualizations": [], "teaching": {}, "checks": []}
        code, events, requests = run_fixture(self.output, audit_responses=[report("revised", patch)])
        self.assertEqual(code, 1)
        self.assertEqual(len(requests), 2)
        self.assertFalse((self.output / "index.html").exists())

    def test_truncated_audit_fails_without_repeating_an_identical_request(self):
        truncated = report()
        truncated["choices"][0]["finish_reason"] = "length"
        code, events, requests = run_fixture(self.output, audit_responses=[truncated, report()])
        self.assertEqual(code, 1)
        self.assertEqual(len(requests), 2)
        self.assertEqual(events[-1]["metadata"]["reserved_completion_tokens"], 11500)
        self.assertFalse((self.output / "index.html").exists())


if __name__ == "__main__":
    unittest.main()
