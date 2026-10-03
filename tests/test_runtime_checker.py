"""Numerical/runner engineering evidence; independent source review is still required."""
import copy
import json
import math
import subprocess
import sys
import time
import unittest

from src.expressions import compile_computations, compile_expression
from src.models import SpecError
from src.runtime_checker import check_runtime, execute_states
from tests.fixtures import lesson


def math_spec(controls, expressions):
    return {"controls": controls,
            "computations": [{"id": name, "label": name, "expression": expression}
                             for name, expression in expressions.items()]}


class RuntimeChecks(unittest.TestCase):
    def run_math(self, spec, states):
        compiled, _ = compile_computations(spec)
        return execute_states(spec, compiled, states)

    def test_entropy_zero_one_two_bits_and_invalid_total(self):
        spec = math_spec([{"id": "weights", "label": "Weights", "kind": "array",
                           "default": [1, 1, 1, 1], "min_items": 1, "max_items": 8, "min": 0, "max": 10}],
                         {"probabilities": "weights / sum(weights)",
                          "entropy": "-sum(xlogx(probabilities))", "outcomes": "length(weights)"})
        results = self.run_math(spec, [{"weights": v} for v in ([1], [1, 1], [1, 1, 1, 1],
                                                               [1, 0, 0, 0], [0, 0], [-1, 1])])
        for result, bits in zip(results[:4], (0, 1, 2, 0)):
            self.assertTrue(result["ok"])
            self.assertEqual(result["outputs"]["entropy"], bits)
        self.assertFalse(results[4]["ok"])
        self.assertFalse(results[5]["ok"])

    def test_attention_scaling_from_real_dimensions(self):
        controls = [{"id": name, "label": name, "kind": "array", "default": value}
                    for name, value in {"queries": [[1, 0]], "keys": [[1, 0], [0, 1]],
                                        "values": [[2], [6]]}.items()]
        controls += [{"id": "scaling", "label": "Scaling", "kind": "toggle", "default": 1,
                      "min": 0, "max": 1, "step": 1}]
        spec = math_spec(controls, {"scores": "matmul(queries, transpose(keys)) / (1 + scaling * (sqrt(ncols(queries)) - 1))",
                                   "weights": "softmax(scores)", "output": "matmul(weights, values)"})
        state = {c["id"]: c["default"] for c in controls}
        result = self.run_math(spec, [state, {**state, "scaling": 0}])
        for actual, scale in zip(result, (math.sqrt(2), 1)):
            first = math.exp(1 / scale) / (math.exp(1 / scale) + 1)
            self.assertTrue(actual["ok"])
            self.assertAlmostEqual(actual["outputs"]["weights"][0][0], first)
            self.assertAlmostEqual(sum(actual["outputs"]["weights"][0]), 1)
            self.assertAlmostEqual(actual["outputs"]["output"][0][0], 2 * first + 6 * (1 - first))

    def test_wrong_math_and_domain_failure_are_detected(self):
        spec = lesson()
        spec["computations"][0]["expression"] = "slope * 3 + intercept"
        compiled, _ = compile_computations(spec)
        failures = [r for r in check_runtime(spec, compiled) if r["status"] == "failed"]
        self.assertEqual({r["name"] for r in failures}, {"default_case", "legal_boundary"})
        self.assertEqual(failures[0]["actual"]["result"], 7)
        self.assertEqual(failures[0]["expected"]["result"], 5)
        spec["computations"][0]["expression"] = "log(slope) + intercept"
        compiled, _ = compile_computations(spec)
        self.assertTrue(any(r["status"] == "failed" for r in check_runtime(spec, compiled)))

    def test_complete_state_fixed_shape_and_no_mutation(self):
        spec = math_spec([{"id": "matrix", "label": "Matrix", "kind": "array", "default": [[1, 2]]}],
                         {"output": "matrix * 2"})
        state = {"matrix": [[1, 2]]}
        before = copy.deepcopy(state)
        results = self.run_math(spec, [state, {}, {**state, "unknown": 1}, {"matrix": [[1], [2]]}])
        self.assertEqual(results[0]["outputs"]["output"], [[2, 4]])
        self.assertEqual(state, before)
        self.assertTrue(all(not result["ok"] for result in results[1:]))

    def test_js_limits_and_wall_timeout(self):
        code = """import quickjs
c=quickjs.Context();c.set_memory_limit(32*1024*1024);c.set_time_limit(.05)
for code in ('const =', 'while(true){}', 'new Array(10000000).fill(1)'):
 try: c.eval(code)
 except quickjs.JSException: print('rejected')
 else: raise SystemExit(2)
"""
        result = subprocess.run([sys.executable, "-c", code], timeout=5, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.splitlines(), ["rejected"] * 3)
        spec = lesson()
        compiled, _ = compile_computations(spec)
        with self.assertRaisesRegex(SpecError, "wall timeout"):
            execute_states(spec, compiled, [spec["checks"][0]["state"]], timeout=.0001)

    def test_line_sweep_detects_domain_failure_outside_expected_cases(self):
        spec = lesson()
        spec["computations"][0]["expression"] = "log(slope + 2) + intercept"
        spec["checks"] = [
            {"id": "one", "state": {"slope": 2, "intercept": 1}, "expected": {"result": math.log(4) + 1}},
            {"id": "two", "state": {"slope": 0, "intercept": 1}, "expected": {"result": math.log(2) + 1}}]
        compiled, _ = compile_computations(spec)
        records = check_runtime(spec, compiled)
        self.assertTrue(all(r["status"] == "passed" for r in records if r["name"] in {"one", "two"}))
        sweep = next(r for r in records if r["name"] == "line_sweep:relationship")
        self.assertEqual(sweep["status"], "failed")
        self.assertEqual(sweep["sample_count"], 48)

    def test_resize_exception_requires_measured_effect(self):
        spec = lesson()
        spec["controls"] = [{"id": "values", "label": "Values", "kind": "array", "default": [1, 2],
                             "min_items": 1, "max_items": 3}]
        spec["computations"][0]["expression"] = "sum(values)"
        spec["visualizations"] = []
        spec["checks"] = [{"id": "one", "state": {"values": [1, 2]}, "expected": {"result": 3}},
                          {"id": "two", "state": {"values": [1]}, "expected": {"result": 1}}]
        compiled, _ = compile_computations(spec)
        self.assertTrue(any(r["name"] == "resize_effect:values" and r["status"] == "passed"
                            for r in check_runtime(spec, compiled)))

    def test_oversized_intermediate_arrays_and_constants_are_rejected(self):
        with self.assertRaises(SpecError):
            compile_expression("9" * 400, set())
        rows = "[" + ",".join("[" + ",".join("1" for _ in range(32)) + "]" for _ in range(4)) + "]"
        spec = math_spec([], {"output": "ncols(" + rows + ")"})
        self.assertFalse(self.run_math(spec, [{}])[0]["ok"])


if __name__ == "__main__":
    unittest.main()
