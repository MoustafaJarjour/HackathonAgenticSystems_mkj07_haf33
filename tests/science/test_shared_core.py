"""Compare the shared browser core with P2's independent scientific fixtures."""
import json
import unittest
from pathlib import Path

from src.expressions import compile_computations
from src.runtime_checker import close, execute_states

FIXTURES = json.loads(Path(__file__).with_name("fixtures.json").read_text(encoding="utf-8"))


def mechanism_spec(name, state):
    controls = []
    for identifier, value in state.items():
        c = {"id": identifier, "label": identifier, "default": value}
        if isinstance(value, list):
            c.update(kind="array")
            if not isinstance(value[0], list):
                c.update(min=0, min_items=1, max_items=64)
        else:
            c.update(kind="number", min=0, max=1000, step=0.01)
        if identifier == "km":
            c["min"] = 0.01
        if identifier == "initial":
            c["max"] = 1
        if identifier == "growth":
            c["max"] = 4
        if identifier == "scaled":
            c.update(kind="toggle", min=0, max=1, step=1)
        controls.append(c)
    expressions = {
        "entropy": [("probabilities", "weights / sum(weights)"),
                    ("entropy_bits", "-sum(xlogx(probabilities))"),
                    ("max_entropy_bits", "log2(length(weights))")],
        "attention": [("scores", "matmul(q, transpose(k)) / (1 + scaled * (sqrt(ncols(q)) - 1))"),
                      ("weights", "softmax(scores)"),
                      ("attention_output", "matmul(weights, v)")],
        "enzyme_kinetics": [("fraction", "substrate / (km + substrate)"),
                            ("rate", "vmax * fraction")],
        # A fixed four-step demonstration is possible by explicit unrolling.
        # This does not claim arbitrary iteration or a bifurcation plot is supported.
        "logistic_map": [("next_value", "growth * initial * (1 - initial)"),
                         ("step_two", "growth * next_value * (1 - next_value)"),
                         ("step_three", "growth * step_two * (1 - step_two)"),
                         ("step_four", "growth * step_three * (1 - step_three)"),
                         ("trajectory", "[initial, next_value, step_two, step_three, step_four]")],
    }[name]
    return {"controls": controls, "computations": [
        {"id": identifier, "label": identifier, "expression": expression}
        for identifier, expression in expressions]}


class SharedScienceCore(unittest.TestCase):
    def test_all_independent_expected_values(self):
        for name, fixture in FIXTURES.items():
            for case in fixture["cases"]:
                with self.subTest(mechanism=name, case=case["id"]):
                    # Fixed matrix dimensions are declared separately for each fixture.
                    spec = mechanism_spec(name, case["state"])
                    compiled, _ = compile_computations(spec)
                    result = execute_states(spec, compiled, [case["state"]])[0]
                    self.assertTrue(result["ok"], result)
                    for identifier, expected in case["expected"].items():
                        self.assertTrue(close(result["outputs"][identifier], expected, 1e-12, 1e-12),
                                        (identifier, result["outputs"][identifier], expected))

    def test_invalid_domains_fail_in_the_exact_core(self):
        for name, fixture in FIXTURES.items():
            for state in fixture["invalid_states"]:
                with self.subTest(mechanism=name, state=state):
                    spec = mechanism_spec(name, state)
                    compiled, _ = compile_computations(spec)
                    self.assertFalse(execute_states(spec, compiled, [state])[0]["ok"])


if __name__ == "__main__":
    unittest.main()
