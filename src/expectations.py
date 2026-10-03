"""Evaluate model-authored test derivations before freezing numerical expectations."""
import copy

from .expressions import compile_expression
from .models import SpecError
from .runtime_checker import execute_states


def materialize_expectations(spec, timeout=5.0):
    """Expressions may use controls only, never the computation being tested."""
    result = copy.deepcopy(spec)
    controls = result.get("controls", [])
    names = {control["id"] for control in controls}
    changes = []
    for case in result.get("checks", []):
        expected = case.get("expected", {})
        derivations = {key: value for key, value in expected.items() if isinstance(value, str)}
        if not derivations:
            continue
        if "expected_expressions" in case and case["expected_expressions"] != derivations:
            raise SpecError("Test derivation metadata conflicts with its expression expectations.")
        compiled = {key: compile_expression(expression, names)[0] for key, expression in derivations.items()}
        # Separate computations: neither outputs nor implementation expressions are
        # copied into the oracle. This checks consistency, not scientific truth.
        oracle = {"controls": controls, "computations": [{"id": key} for key in derivations]}
        response = execute_states(oracle, compiled, [case["state"]], timeout=timeout)[0]
        if not response["ok"]:
            raise SpecError("Test expectation derivation failed: " + response["error"])
        expected.update(response["outputs"])
        case["expected_expressions"] = derivations
        changes.append({"case_id": case["id"], "outputs": sorted(derivations)})
    return result, changes
