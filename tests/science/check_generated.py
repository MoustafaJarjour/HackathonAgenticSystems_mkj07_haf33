"""Replay independent review states against unchanged generated showcase files."""
import hashlib
import json
import copy
from pathlib import Path

from src.renderer import render
from src.runtime_checker import close, execute_states
from src.validator import validate_html, validate_spec


def matches_reviewed_hash(raw, expected):
    """Allow Git's LF-to-CRLF checkout conversion without masking content edits."""
    return (hashlib.sha256(raw).hexdigest() == expected or
            hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest() == expected)


def check_report(path):
    report = json.loads(path.read_text(encoding="utf-8"))
    lesson_path = Path(report["lesson"])
    raw = lesson_path.read_bytes()
    if not matches_reviewed_hash(raw, report["sha256_after"]):
        raise ValueError(f"Reviewed lesson hash changed: {lesson_path}")
    spec = json.loads(raw)
    case = json.loads((lesson_path.parent / "input.json").read_text(encoding="utf-8"))
    compiled, _ = validate_spec(spec, case["excerpt"], case["source_url"])
    html = (lesson_path.parent / "index.html").read_text(encoding="utf-8")
    validate_html(html, spec)
    # Archived browser evidence covers the saved page; numerical replay uses the
    # unchanged reviewed lesson with the current shared core. Presentation updates
    # are verified separately and do not retroactively change browser evidence.
    validate_html(render(spec, compiled), spec)
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
    revision = report.get("title_only_revision")
    if revision:
        revised_path = Path(revision["lesson"])
        revised_raw = revised_path.read_bytes()
        if not matches_reviewed_hash(revised_raw, revision["sha256"]):
            raise ValueError("Title revision hash changed.")
        revised = json.loads(revised_raw)
        expected_revision = copy.deepcopy(spec)
        next(view for view in expected_revision["visualizations"]
             if view["id"] == revision["view_id"])["title"] = revision["title"]
        if revised != expected_revision:
            raise ValueError("Title revision changed other reviewed fields.")
        revised_compiled, _ = validate_spec(revised, case["excerpt"], case["source_url"])
        if revised_compiled != compiled:
            raise ValueError("Title revision changed compiled math.")
        validate_html((revised_path.parent / "index.html").read_text(encoding="utf-8"), revised)
        validate_html(render(revised, compiled), revised)
        print(f"{revised_path.parent.name}: exact title-only change verified; reviewed math/controls preserved")


def main():
    paths = sorted(Path("tests/science/reviews").glob("*-showcase.json"))
    if not paths:
        raise ValueError("Run from the repository root with the submitted review reports.")
    for path in paths:
        check_report(path)


if __name__ == "__main__":
    main()
