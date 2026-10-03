"""Replay independent review states against unchanged generated showcase files."""
import hashlib
import json
from pathlib import Path

from src.renderer import render
from src.runtime_checker import close, execute_states
from src.validator import validate_html, validate_spec


def check_report(path):
    report = json.loads(path.read_text())
    lesson_path = Path(report["lesson"])
    raw = lesson_path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != report["sha256_after"]:
        raise ValueError(f"Reviewed lesson hash changed: {lesson_path}")
    spec = json.loads(raw)
    case = json.loads((lesson_path.parent / "input.json").read_text())
    compiled, _ = validate_spec(spec, case["excerpt"], case["source_url"])
    html = (lesson_path.parent / "index.html").read_text()
    validate_html(html, spec)
    if render(spec, compiled) != html:
        raise ValueError("Saved HTML differs from the exact reviewed spec and current renderer/runtime.")
    records = report["records"]
    actual = execute_states(spec, compiled, [record["state"] for record in records])
    valid = invalid = 0
    for record, result in zip(records, actual):
        expected = record["expected"]
        if expected is None:
            if result["ok"]:
                raise ValueError(f"Invalid state accepted: {record['id']}")
            invalid += 1
        else:
            if not result["ok"] or any(
                    key not in result["outputs"] or not close(result["outputs"][key], value,
                                                             report["atol"], report["rtol"])
                    for key, value in expected.items()):
                raise ValueError(f"Independent comparison failed: {record['id']}")
            valid += 1
    if valid != report["valid_total"] or invalid != report["invalid_total"]:
        raise ValueError("Review case counts disagree.")
    print(f"{lesson_path.parent.name}: {valid} independent states, {invalid} invalid rejections passed")


def main():
    paths = sorted(Path("tests/science/reviews").glob("*-showcase.json"))
    if not paths:
        raise ValueError("Run from the repository root with the submitted review reports.")
    for path in paths:
        check_report(path)


if __name__ == "__main__":
    main()
