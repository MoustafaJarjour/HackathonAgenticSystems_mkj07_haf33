"""Developer-only sequential CLI measurements; independent quality review is separate.

Run with ``python -m tests.science.benchmark_papers --inputs ... --model MODEL``.
This harness does not change prompts, generated artifacts, or the production CLI.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone


REPO = Path(__file__).resolve().parents[2]
QUALITY_CRITERIA = {
    "scientific_accuracy": 25, "teaching": 20, "visuals": 15,
    "meaningful_controls": 15, "autonomous_operation": 10,
}


def hashes(path: Path) -> dict:
    raw = path.read_bytes()
    return {"raw_sha256": hashlib.sha256(raw).hexdigest(),
            "canonical_lf_sha256": hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest(),
            "bytes": len(raw)}


def safe_text(value: str, secret: str) -> str:
    if secret:
        value = value.replace(secret, "[REDACTED]")
    return re.sub(r"(?i)\bbearer\s+\S+", "Bearer [REDACTED]", value)


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
                    encoding="utf-8")


def trace_measurements(path: Path) -> dict:
    records, errors = [], []
    if path.exists():
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            try:
                record = json.loads(line)
                if not isinstance(record, dict):
                    raise ValueError("Object required")
                records.append(record)
            except (ValueError, TypeError):
                errors.append(f"Invalid JSONL record {number}")
    responses = [r.get("metadata", {}) for r in records
                 if r.get("stage") == "openrouter" and r.get("action") == "response"]
    requests = [r for r in records if r.get("stage") == "openrouter"
                and r.get("action") == "request"]
    finished = [r for r in records if r.get("stage") == "run" and r.get("action") == "finish"]
    fields = ("prompt_tokens", "completion_tokens", "total_tokens")
    observed = dict.fromkeys(fields, 0)
    missing = dict.fromkeys(fields, max(0, len(requests) - len(responses)))
    attempts = []
    for response in responses:
        usage = response.get("usage") or {}
        clean = {}
        for field in fields:
            value = usage.get(field)
            valid = type(value) is int and value >= 0
            clean[field] = value if valid else None
            if valid:
                observed[field] += value
            else:
                missing[field] += 1
        details = usage.get("prompt_tokens_details") or {}
        cached = details.get("cached_tokens", usage.get("cached_tokens"))
        reasoning = usage.get("reasoning_tokens")
        if reasoning is None:
            reasoning = (usage.get("completion_tokens_details") or {}).get("reasoning_tokens")
        clean.update({"cached_tokens": cached if type(cached) is int and cached >= 0 else None,
                      "reasoning_tokens": reasoning if type(reasoning) is int and reasoning >= 0 else None})
        complete = all(clean[field] is not None for field in fields)
        attempts.append({"request_number": response.get("request_number"),
                         "response_id": response.get("response_id"), "usage": clean,
                         "total_equals_prompt_plus_completion":
                             clean["total_tokens"] == clean["prompt_tokens"] + clean["completion_tokens"]
                             if complete else None})
    finish = finished[-1] if finished else None
    finish_meta = finish.get("metadata", {}) if finish else {}
    complete = bool(requests and responses and finish) and not any(missing.values()) and len(requests) == len(responses) and not errors
    response_ids = [attempt["response_id"] for attempt in attempts]
    ids_valid = bool(response_ids) and all(isinstance(value, str) and value for value in response_ids)
    ids_unique = ids_valid and len(set(response_ids)) == len(response_ids)
    counters_match = all(finish_meta.get("observed_" + field) == observed[field] for field in fields) if finish else None
    attempt_consistency = all(attempt["total_equals_prompt_plus_completion"] is True for attempt in attempts)
    return {"requests": len(requests), "responses": attempts,
            "observed_usage": observed, "missing_usage_attempts": missing,
            "usage_complete": complete,
            "T_prompt_plus_completion": observed["prompt_tokens"] + observed["completion_tokens"]
                if complete else None,
            "T_observed_lower_bound": observed["prompt_tokens"] + observed["completion_tokens"],
            "accounting_note": "T includes all attempts and cached input; reasoning is already included in completion and is not added again. Missing cache/usage fields are unknown.",
            "trace_finish_result": finish.get("result") if finish else None,
            "trace_finish_elapsed_seconds": finish_meta.get("elapsed_seconds"),
            "trace_finish_usage_matches_attempts": counters_match,
            "api_response_ids_present_and_unique": ids_unique,
            "token_usage_matches_finish_and_perattempt": counters_match and attempt_consistency if complete else None,
            "provider_record_verification": "Response IDs retained; API-account records not independently queried.",
            "parse_errors": errors}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", nargs="+", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=Path("review-out/new-papers"))
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--model", required=True)
    parser.add_argument("--variant", choices=("baseline", "compact-json"), default="baseline")
    args = parser.parse_args(argv)
    if args.repeats < 1 or not args.model.strip():
        parser.error("Use positive repeats and a nonempty explicit model.")
    inputs = [p.resolve() for p in args.inputs]
    if any(not p.is_file() for p in inputs):
        parser.error("Every input must be an existing file.")
    output = args.output.resolve()
    planned = []
    for source in inputs:
        stem = re.sub(r"[^a-zA-Z0-9_-]+", "-", source.stem).strip("-") or "case"
        case_name = stem + "-" + hashes(source)["raw_sha256"][:8]
        for repeat in range(1, args.repeats + 1):
            planned.append((source, output / f"{case_name}-run{repeat:02d}"))
    if len({p for _, p in planned}) != len(planned) or any(p.exists() for _, p in planned):
        parser.error("Run folders must be distinct and fresh; choose another output directory.")
    output.mkdir(parents=True, exist_ok=True)
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True,
                            text=True, check=False).stdout.strip() or None
    secret = os.environ.get("OPENROUTER_API_KEY", "")
    if not secret.strip():
        write_json(output / "benchmark-summary.json", {
            "status": "not_run", "reason": "OPENROUTER_API_KEY is not configured.",
            "commit": commit, "api_requests": 0, "model": args.model,
            "planned_runs": len(planned), "variant": args.variant, "quality_status": "unreviewed"})
        print("No runs started: OPENROUTER_API_KEY is not configured.")
        return 1
    reports = []
    for source, folder in planned:
        folder.mkdir()
        shutil.copyfile(source, folder / "input.json")
        entrypoint = REPO / ("agent.py" if args.variant == "baseline" else "tests/science/compact_prompt_run.py")
        invocation = [str(entrypoint)] if args.variant == "baseline" else ["-m", "tests.science.compact_prompt_run"]
        command = [sys.executable, *invocation, "--input", str(source),
                   "--output", str(folder), "--model", args.model]
        started_utc = datetime.now(timezone.utc).isoformat()
        started = time.perf_counter()
        timed_out, launch_error = False, None
        try:
            process = subprocess.Popen(command, cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            try:
                stdout, stderr = process.communicate(timeout=600)
            except subprocess.TimeoutExpired:
                timed_out = True
                process.kill()
                stdout, stderr = process.communicate()
            exit_code = process.returncode
        except OSError:
            stdout, stderr, exit_code = b"", b"", None
            launch_error = "Could not start the generation process."
        elapsed = time.perf_counter() - started
        log = "STDOUT\n" + stdout.decode("utf-8", errors="replace") + "\nSTDERR\n" + stderr.decode("utf-8", errors="replace")
        (folder / "process-output.log").write_text(safe_text(log, secret), encoding="utf-8")
        trace = trace_measurements(folder / "trace.jsonl")
        html = folder / "index.html"
        report = {"commit": commit, "model": args.model, "variant": args.variant,
                  "entrypoint_hashes": hashes(entrypoint), "input_path": str(source),
                  "command": command, "process_started_utc": started_utc,
                  "process_exit_code": exit_code, "external_process_elapsed_seconds": elapsed,
                  "timing_scope": "Before subprocess launch through child wait/exit; includes child startup, imports, checks, retries and cleanup; excludes harness setup and later report writing.",
                  "external_timeout": timed_out, "launch_error": launch_error,
                  "hashes": {name: hashes(folder / name) for name in
                             ("input.json", "lesson.json", "index.html", "trace.jsonl")
                             if (folder / name).is_file()},
                  "trace": trace,
                  "usable_html": exit_code == 0 and trace["trace_finish_result"] == "success"
                      and html.is_file() and html.stat().st_size > 0,
                  "quality_status": "unreviewed",
                  "quality_qualification": "Usable HTML only establishes successful CLI output, not scientific, teaching, visual, control or autonomous quality; no official score is promised.",
                  "manual_quality_review": {"criteria_maxima": QUALITY_CRITERIA,
                                            "scores": None, "sources": [], "states": [],
                                            "findings": [], "reviewer": None}}
        write_json(folder / "measured-run.json", report)
        reports.append({"folder": str(folder), "exit_code": exit_code,
                        "external_process_elapsed_seconds": elapsed,
                        "T": trace["T_prompt_plus_completion"], "usable_html": report["usable_html"]})
        print(f"Measured {folder.name}: exit={exit_code}, seconds={elapsed:.3f}, T={trace['T_prompt_plus_completion']}")
    write_json(output / "benchmark-summary.json", {"commit": commit, "model": args.model, "variant": args.variant,
               "sequential": True, "runs": reports, "quality_status": "unreviewed"})
    return 0 if all(r["usable_html"] for r in reports) else 1


if __name__ == "__main__":
    raise SystemExit(main())
