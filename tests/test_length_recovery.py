"""Mocked CLI failure paths; these do not establish live model quality."""
import json
import tempfile
import unittest
from pathlib import Path

from tests.fixtures import completion, lesson, run_fixture


class LengthRecovery(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.output = Path(temporary.name) / "out"

    def test_compact_generation_truncation_fails_without_duplicate_request(self):
        truncated = completion(lesson())
        truncated["choices"][0]["finish_reason"] = "length"
        # The third response would succeed if the CLI blindly repeated compact
        # generation. It must leave that response unused and report failure.
        code, events, payloads = run_fixture(
            self.output, [truncated, truncated, completion(lesson())])
        self.assertEqual(code, 1)
        self.assertEqual(len(payloads), 2)
        self.assertNotEqual(payloads[0]["messages"], payloads[1]["messages"])
        self.assertIn("smaller package", payloads[1]["messages"][1]["content"])
        recoveries = [event for event in events if event["action"] == "length_recovery"]
        self.assertEqual([event["result"] for event in recoveries], ["scheduled", "failed"])
        finish = events[-1]
        self.assertEqual(finish["result"], "failed")
        self.assertEqual(finish["metadata"]["error_type"], "TruncatedCompletion")
        self.assertEqual(finish["metadata"]["reserved_completion_tokens"], 16000)
        self.assertEqual(finish["metadata"]["requests"], 2)
        self.assertFalse((self.output / "lesson.json").exists())
        self.assertFalse((self.output / "index.html").exists())

    def test_two_targeted_repairs_still_recheck_original_expectations(self):
        wrong = lesson()
        wrong["computations"][0]["expression"] = "slope * 3 + intercept"
        unchanged = {"controls": [], "computations": [], "visualizations": [], "teaching": {}}
        corrected = {"controls": [], "computations": lesson()["computations"],
                     "visualizations": [], "teaching": {}}
        code, events, payloads = run_fixture(
            self.output, [completion(wrong), completion(unchanged), completion(corrected)])
        self.assertEqual(code, 0)
        self.assertEqual([payload["max_tokens"] for payload in payloads], [8000, 3500, 3500, 4000, 3500])
        replacements = [event for event in events if event["action"] == "component_replacements"]
        self.assertEqual(len(replacements), 2)
        self.assertTrue(all(event["metadata"]["preserved_numerical_cases"] for event in replacements))
        saved = json.loads((self.output / "lesson.json").read_text())
        self.assertEqual(saved["checks"], wrong["checks"])
        default_cases = [event["metadata"]["check"] for event in events
                         if event["action"] == "runtime_case"
                         and event["metadata"]["check"]["name"] == "default_case"]
        self.assertEqual([record["status"] for record in default_cases], ["failed", "failed", "passed", "passed"])
        self.assertEqual([record["actual"]["result"] for record in default_cases], [7, 7, 5, 5])
        self.assertEqual(events[-1]["metadata"]["reserved_completion_tokens"], 22500)


if __name__ == "__main__":
    unittest.main()
