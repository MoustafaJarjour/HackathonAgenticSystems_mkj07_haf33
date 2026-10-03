"""Execute the exact browser math core; numerical cases are separate evidence."""
import copy
import json
import math
import os
import subprocess
import sys
from pathlib import Path

from .models import SpecError


def execute_states(spec, compiled, states, timeout=5.0):
    payload = json.dumps({"spec": spec, "compiled": compiled, "states": states}, allow_nan=False)
    if len(payload.encode()) > 1024 * 1024:
        raise SpecError("Runtime request exceeds 1 MiB.")
    # A child has no professor key; QuickJS has no file/network/Python bindings.
    environment = {key: value for key, value in os.environ.items()
                   if key in {"PATH", "SYSTEMROOT", "WINDIR", "TMPDIR", "TEMP", "TMP"}}
    try:
        process = subprocess.run([sys.executable, str(Path(__file__).with_name("runtime_worker.py"))],
                                 input=payload, text=True, capture_output=True,
                                 timeout=max(.001, timeout), env=environment)
    except subprocess.TimeoutExpired as exc:
        raise SpecError("Math runner exceeded its child-process wall timeout.") from exc
    except OSError as exc:
        raise SpecError("Math runner could not start.") from exc
    try:
        response = json.loads(process.stdout)
    except ValueError as exc:
        raise SpecError("Math runner returned no valid JSON result.") from exc
    if process.returncode or "error" in response:
        raise SpecError(response.get("error", "Math runner failed."))
    return response["results"]


def shape(value):
    if isinstance(value, list):
        if not value:
            raise SpecError("Numerical values cannot contain empty arrays.")
        children = [shape(item) for item in value]
        if any(child != children[0] for child in children):
            raise SpecError("Numerical arrays must be rectangular.")
        return (len(value),) + children[0]
    if type(value) not in (int, float) or not math.isfinite(value):
        raise SpecError("Numerical values must be finite numbers.")
    return ()


def close(actual, expected, atol, rtol):
    if shape(actual) != shape(expected):
        return False
    if isinstance(expected, list):
        return all(close(a, e, atol, rtol) for a, e in zip(actual, expected))
    return abs(actual - expected) <= atol + rtol * abs(expected)


def view_errors(spec, outputs):
    errors = []
    for view in spec["visualizations"]:
        dims = shape(outputs[view["source"]])
        required = {"line": 0, "bars": 1, "heatmap": 2}[view["kind"]]
        if len(dims) != required:
            errors.append(f"{view['id']}: {view['kind']} requires {required} dimensions.")
    return errors


def perturbations(spec, state):
    """Bounded legal candidates. Flat default states do not settle sensitivity."""
    for control in spec["controls"]:
        values = []
        value = state[control["id"]]
        if control["kind"] != "array":
            values = [control["min"], control["max"], (control["min"] + control["max"]) / 2]
            if control["kind"] == "toggle":
                values = [0, 1]
        else:
            for delta in (1.0, -1.0):
                changed = copy.deepcopy(value)
                if isinstance(changed[0], list):
                    changed[0][0] += delta
                    edited = changed[0][0]
                else:
                    changed[0] += delta
                    edited = changed[0]
                if control.get("min", -math.inf) <= edited <= control.get("max", math.inf):
                    values.append(changed)
            if not isinstance(value[0], list):
                for size in (control.get("min_items", len(value)), control.get("max_items", len(value))):
                    values.append((value + [0] * size)[:size])
        for value in values:
            candidate = copy.deepcopy(state)
            candidate[control["id"]] = value
            if candidate != state:
                yield control["id"], candidate


def check_runtime(spec, compiled, timeout=5.0):
    default = {control["id"]: control["default"] for control in spec["controls"]}
    cases = spec["checks"]
    records = []
    probes = list(perturbations(spec, default))
    states = [default] + [case["state"] for case in cases] + [state for _, state in probes]
    results = execute_states(spec, compiled, states, timeout)
    for index, result in enumerate(results[:1 + len(cases)]):
        case = cases[index - 1] if index else None
        record = {"name": case["id"] if case else "default_state", "stage": "runtime",
                  "status": "passed", "details": "Exact shared JS core executed.",
                  "state": states[index]}
        errors = []
        if not result["ok"]:
            errors.append(result["error"])
        else:
            actual = result["outputs"]
            record["actual"] = actual
            errors += view_errors(spec, actual)
            if case:
                record["expected"] = case["expected"]
                for key, expected in case["expected"].items():
                    if not close(actual[key], expected, case.get("atol", 1e-6), case.get("rtol", 1e-6)):
                        errors.append(f"{key}: numerical result differs from the preserved expectation.")
        if errors:
            record.update(status="failed", details="; ".join(errors))
        records.append(record)
    visible = {item["id"] for item in spec["computations"] if item["show"]}
    visible.update(view["source"] for view in spec["visualizations"])
    baseline = results[0].get("outputs")
    for control in spec["controls"]:
        observations = [(state, result) for (key, state), result in zip(probes, results[1 + len(cases):])
                        if key == control["id"]]
        changed = [(state, result["outputs"]) for state, result in observations if result["ok"] and baseline
                   and any(not close(result["outputs"][key], baseline[key], 1e-10, 1e-10) for key in visible)]
        records.append({"name": "control_effect:" + control["id"], "stage": "runtime",
                        "status": "passed" if changed else "failed",
                        "details": "Legal perturbation changed a visible output." if changed else
                                   "No visible effect found in bounded legal probes; review the control/domain.",
                        "actual": changed[:1], "probe_failures": [r["error"] for _, r in observations if not r["ok"]]})
    return records
