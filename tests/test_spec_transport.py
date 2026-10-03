"""Case transport normalization must not relax scientific or execution gates."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from src.expressions import compile_computations
from src.models import SpecError
from src.planner import parse_json
from src.spec_transport import normalize_references
from tests.fixtures import completion, lesson, run_fixture


class SpecTransport(unittest.TestCase):
    def test_known_aliases_preserve_values_and_literal_expression_bytes(self):
        original = lesson()
        original["computations"][0]["expression"] = "SLOPE * 2e0 + Intercept"
        original["checks"][0]["state"] = {"SLOPE": 2, "Intercept": 1}
        original["checks"][0]["expected"] = {"RESULT": 5}
        original["visualizations"][0].update(source="RESULT", sweep_control="SLOPE")
        snapshot = copy.deepcopy(original)
        normalized, records = normalize_references(original)
        self.assertEqual(original, snapshot)
        self.assertEqual(normalized["computations"][0]["expression"], "slope * 2e0 + intercept")
        self.assertEqual(normalized["checks"][0]["state"], {"slope": 2, "intercept": 1})
        self.assertEqual(normalized["checks"][0]["expected"], {"result": 5})
        self.assertEqual(normalized["grounding"], original["grounding"])
        self.assertEqual(normalized["equations"], original["equations"])
        self.assertTrue(records)
        self.assertEqual(normalize_references(normalized), (normalized, []))
        compile_computations(normalized)

    def test_case_collision_is_rejected_without_losing_either_value(self):
        spec = lesson()
        spec["checks"][0]["state"]["SLOPE"] = 999
        with self.assertRaisesRegex(SpecError, "collide"):
            normalize_references(spec)

    def test_unknown_function_code_and_forward_reference_still_reject(self):
        for expression in ("SLOPE2 + intercept", "SUM([slope,intercept])",
                           "slope.__class__", "RESULT + intercept"):
            with self.subTest(expression=expression):
                spec = lesson()
                spec["computations"][0]["expression"] = expression
                normalized, _ = normalize_references(spec)
                with self.assertRaises(SpecError):
                    compile_computations(normalized)

    def test_declarations_and_unknown_case_keys_are_not_manufactured(self):
        spec = lesson()
        spec["checks"][0]["state"]["Q2"] = 7
        normalized, _ = normalize_references(spec)
        self.assertIn("Q2", normalized["checks"][0]["state"])
        spec["controls"][0]["id"] = "SLOPE"
        normalized, records = normalize_references(spec)
        self.assertEqual(normalized, spec)
        self.assertEqual(records, [])

    def test_duplicate_json_members_do_not_silently_discard_values(self):
        with self.assertRaises(SpecError):
            parse_json('{"checks":[{"state":{"q":1,"q":9}}]}')

    def test_malformed_checks_reach_the_schema_gate_without_parser_crash(self):
        for value in (None, 42, "invalid"):
            spec = lesson()
            spec["checks"] = value
            normalized, _ = normalize_references(spec)
            self.assertEqual(normalized["checks"], value)

    def test_live_pipeline_shape_preserves_canonical_cases_during_repair(self):
        wrong = lesson()
        wrong["computations"][0]["expression"] = "SLOPE * 3 + Intercept"
        for case in wrong["checks"]:
            case["state"] = {key.upper(): value for key, value in case["state"].items()}
            case["expected"] = {key.upper(): value for key, value in case["expected"].items()}
        corrected = copy.deepcopy(lesson()["computations"])
        corrected[0]["expression"] = "SLOPE * 2 + INTERCEPT"
        patch = {"controls": [], "computations": corrected, "visualizations": [], "teaching": {}}
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            code, events, _ = run_fixture(output, [completion(wrong), completion(patch)])
            self.assertEqual(code, 0)
            saved = json.loads((output / "lesson.json").read_text())
        self.assertEqual(saved["checks"], lesson()["checks"])
        cases = [event["metadata"]["check"] for event in events
                 if event["action"] == "runtime_case" and event["metadata"]["check"]["name"] == "default_case"]
        self.assertEqual([record["actual"]["result"] for record in cases], [7, 5, 5])
        self.assertEqual([record["status"] for record in cases], ["failed", "passed", "passed"])
        normalizations = [event for event in events if event["action"] == "reference_normalization"]
        self.assertEqual(len(normalizations), 2)
        self.assertTrue(all(event["metadata"]["numeric_values_changed"] is False for event in normalizations))
