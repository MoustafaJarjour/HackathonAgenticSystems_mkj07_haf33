"""Independent P2 arithmetic: these are development oracles, not a production evaluator."""
import json
import math
import unittest
from pathlib import Path

FIXTURES = json.loads(Path(__file__).with_name("fixtures.json").read_text(encoding="utf-8"))


def entropy(state):
    weights = state["weights"]
    if any(x < 0 for x in weights) or sum(weights) <= 0:
        raise ValueError("Use nonnegative weights with a positive sum.")
    p = [x / sum(weights) for x in weights]
    return {"probabilities": p, "entropy_bits": -sum(x * math.log2(x) for x in p if x > 0)}


def attention(state):
    q, k, v = (state[name] for name in ("q", "k", "v"))
    if any(len(row) != len(q[0]) for row in q + k) or len(k) != len(v):
        raise ValueError("Incompatible attention dimensions.")
    scale = math.sqrt(len(q[0])) if state["scaled"] else 1
    scores = [[sum(x*y for x, y in zip(query, key)) / scale for key in k] for query in q]
    weights = []
    for row in scores:
        exps = [math.exp(x - max(row)) for x in row]
        weights.append([x / sum(exps) for x in exps])
    output = [[sum(w[j] * v[j][col] for j in range(len(v))) for col in range(len(v[0]))] for w in weights]
    return {"scores": scores, "weights": weights, "attention_output": output}


def enzyme_kinetics(state):
    s, km, vmax = (state[name] for name in ("substrate", "km", "vmax"))
    if s < 0 or km <= 0 or vmax < 0:
        raise ValueError("Use S>=0, Km>0, Vmax>=0.")
    fraction = s / (km+s)
    return {"rate": vmax*fraction, "fraction": fraction}


def logistic_map(state):
    r, x = state["growth"], state["initial"]
    if not 0 <= r <= 4 or not 0 <= x <= 1:
        raise ValueError("Use 0<=r<=4 and 0<=x0<=1.")
    trajectory = [x]
    for _ in range(4):
        x = r*x*(1-x)
        trajectory.append(x)
    return {"next_value": trajectory[1], "trajectory": trajectory}


ORACLES = {"entropy": entropy, "attention": attention,
           "enzyme_kinetics": enzyme_kinetics, "logistic_map": logistic_map}


class IndependentReferences(unittest.TestCase):
    def compare(self, actual, expected):
        if isinstance(expected, list):
            self.assertIsInstance(actual, list)
            self.assertEqual(len(actual), len(expected))
            for a, e in zip(actual, expected):
                self.compare(a, e)
        else:
            self.assertTrue(math.isfinite(actual))
            self.assertAlmostEqual(actual, expected, delta=1e-12 + 1e-12*abs(expected))

    def test_independently_derived_cases(self):
        for mechanism, fixture in FIXTURES.items():
            for case in fixture["cases"]:
                with self.subTest(mechanism=mechanism, case=case["id"]):
                    actual = ORACLES[mechanism](case["state"])
                    for name, expected in case["expected"].items():
                        self.compare(actual[name], expected)
                    if mechanism == "attention":
                        for row in actual["weights"]:
                            self.assertAlmostEqual(sum(row), 1, delta=1e-12)

    def test_invalid_scientific_domains(self):
        for mechanism, fixture in FIXTURES.items():
            for state in fixture["invalid_states"]:
                with self.subTest(mechanism=mechanism, state=state), self.assertRaises(ValueError):
                    ORACLES[mechanism](state)


if __name__ == "__main__":
    unittest.main()
