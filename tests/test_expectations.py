"""Independent expectation arithmetic prevents guessed-decimal dead ends."""
import copy
import math
import tempfile
import unittest
from pathlib import Path

from src.expectations import materialize_expectations
from src.models import SpecError
from tests.fixtures import completion, lesson, run_fixture


class ExpectationDerivationTests(unittest.TestCase):
    def test_brownian_physical_constant_is_evaluated_without_using_implementation(self):
        spec = {"controls": [
            {"id": name, "kind": "number", "default": value, "min": low, "max": high, "step": step}
            for name, value, low, high, step in (("temp", 300, 250, 400, 1), ("eta", 1, .1, 5, .1),
                                               ("radius", 1, .1, 5, .1), ("elapsed", 1, 0, 60, 1))],
            "computations": [{"id": "diffusion", "expression": "0"}],
            "checks": [{"id": "default", "state": {"temp": 300, "eta": 1, "radius": 1, "elapsed": 1},
                        "expected": {"diffusion": "0.000732457043416274 * temp / (eta * radius)",
                                     "rms": "sqrt(2 * 0.000732457043416274 * temp * elapsed / (eta * radius))"}}]}
        before = copy.deepcopy(spec)
        derived, changes = materialize_expectations(spec)
        independent_d = 1.380649e-23 * 300 / (6 * math.pi * .001 * 1e-6) * 1e12
        self.assertAlmostEqual(derived["checks"][0]["expected"]["diffusion"], independent_d, places=12)
        self.assertAlmostEqual(derived["checks"][0]["expected"]["rms"], math.sqrt(2 * independent_d), places=12)
        self.assertEqual(spec, before)
        self.assertEqual(changes[0]["case_id"], "default")
        self.assertEqual(derived["checks"][0]["expected_expressions"], before["checks"][0]["expected"])

    def test_derivation_cannot_read_tested_outputs_or_execute_code(self):
        for expression in ("result", "__import__('os')"):
            spec = lesson()
            spec["checks"][0]["expected"]["result"] = expression
            with self.subTest(expression=expression), self.assertRaises(SpecError):
                materialize_expectations(spec)

    def test_pipeline_freezes_derived_values_and_preserves_them_during_repair(self):
        spec = lesson()
        spec["computations"][0]["expression"] = "slope*3+intercept"
        for case in spec["checks"]:
            case["expected"]["result"] = "slope*2+intercept"
        replacement = {"controls": [], "computations": lesson()["computations"], "visualizations": [], "teaching": {}}
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            code, events, _ = run_fixture(output, [completion(spec), completion(replacement)])
            self.assertEqual(code, 0)
            import json
            saved = json.loads((output / "lesson.json").read_text())
        self.assertEqual([case["expected"]["result"] for case in saved["checks"]], [5, -7])
        self.assertTrue(all(case["expected_expressions"] == {"result": "slope*2+intercept"}
                            for case in saved["checks"]))
        self.assertTrue(any(event["action"] == "expectation_derivation" for event in events))


if __name__ == "__main__":
    unittest.main()
