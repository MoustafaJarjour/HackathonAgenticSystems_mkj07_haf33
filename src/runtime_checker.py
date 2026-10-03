"""Execute the exact browser math core; numerical cases are separate evidence."""
import copy
import json
import math
import os
import subprocess
import sys
from pathlib import Path

from .models import SpecError, visualization_sources


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
        if view["kind"] == "diagram":
            for source in visualization_sources(view):
                shape(outputs[source])  # Scalars, vectors and matrices all have live representations.
            continue
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
            end = control["min"] + math.floor((control["max"] - control["min"]) / control["step"] + 1e-9) * control["step"]
            middle = control["min"] + math.floor((end - control["min"]) / (2 * control["step"])) * control["step"]
            values = [control["min"], min(end, control["max"]), middle]
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
    # Try backgrounds from the declared cases as well: multiplicative controls
    # can correctly be flat at zero, and equal attention scores can hide effects.
    probes = []
    for background in [default] + [case["state"] for case in cases[:2]]:
        for key, candidate in perturbations(spec, background):
            if (key, candidate, background) not in probes:
                probes.append((key, candidate, background))
    backgrounds = [background for _, _, background in probes]
    sweeps = []
    for view in spec["visualizations"]:
        if view["kind"] != "line":
            continue
        control = next(c for c in spec["controls"] if c["id"] == view["sweep_control"])
        end = math.floor((control["max"] - control["min"]) / control["step"])
        samples = sorted({math.floor(i * end / 47 + .5) for i in range(48)})
        if len(samples) < 2:
            raise SpecError("Line sweep needs at least two distinct legal settings.")
        for sample in samples:
            value = control["min"] + sample * control["step"]
            if value > control["max"]:
                value = control["min"] + max(0, sample - 1) * control["step"]
            state = copy.deepcopy(default)
            state[control["id"]] = value
            sweeps.append((view["id"], state))
    states = [default] + [case["state"] for case in cases] + [state for _, state, _ in probes] + backgrounds + [s for _, s in sweeps]
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
    for view in spec["visualizations"]:
        visible.update(visualization_sources(view))
    baseline = results[0].get("outputs")
    probe_results = results[1 + len(cases):1 + len(cases) + len(probes)]
    background_results = results[1 + len(cases) + len(probes):1 + len(cases) + 2 * len(probes)]
    for control in spec["controls"]:
        observations = [(state, result, background, background_result)
                        for (key, state, background), result, background_result in zip(probes, probe_results, background_results)
                        if key == control["id"]]
        changed = [(state, result["outputs"]) for state, result, _, original in observations if result["ok"] and original["ok"]
                   and any(not close(result["outputs"][key], original["outputs"][key], 1e-10, 1e-10) for key in visible)]
        records.append({"name": "control_effect:" + control["id"], "stage": "runtime",
                        "status": "passed" if changed else "failed",
                        "details": "Legal perturbation changed a visible output." if changed else
                                   "No visible effect found in bounded legal probes; review the control/domain.",
                        "actual": changed[:1], "probe_failures": [r["error"] for _, r, _, _ in observations if not r["ok"]]})
        if len(spec["controls"]) == 1 and control["kind"] == "array":
            resized = [(state, result["outputs"]) for state, result, background, original in observations
                       if len(state[control["id"]]) != len(background[control["id"]]) and result["ok"] and original["ok"]
                       and any(not close(result["outputs"][key], original["outputs"][key], 1e-10, 1e-10) for key in visible)]
            records.append({"name": "resize_effect:" + control["id"], "stage": "runtime",
                            "status": "passed" if resized else "failed",
                            "details": "Resizing changed a visible output." if resized else "Resizing had no measured visible effect.",
                            "actual": resized[:1]})
    sweep_results = results[1 + len(cases) + 2 * len(probes):]
    for view in spec["visualizations"]:
        if view["kind"] != "line":
            continue
        samples = [(state, result) for (key, state), result in zip(sweeps, sweep_results) if key == view["id"]]
        failures = [{"state": state, "exception": result["error"]} for state, result in samples if not result["ok"]]
        for state, result in samples:
            if result["ok"] and len(shape(result["outputs"][view["source"]])) != 0:
                failures.append({"state": state, "details": "Line source is not scalar."})
        records.append({"name": "line_sweep:" + view["id"], "stage": "runtime",
                        "status": "failed" if failures else "passed", "sample_count": len(samples),
                        "details": "Legal step-grid samples executed." if not failures else "Line sweep contains invalid calculations.",
                        "actual": failures[:4]})
    return records
