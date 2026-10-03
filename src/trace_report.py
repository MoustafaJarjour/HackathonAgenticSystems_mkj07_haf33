"""Human-readable reports derived from the redacted JSONL audit log."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import json
import re
from pathlib import Path


def _cell(value: object) -> str:
    return str(value).replace("&", "&amp;").replace("<", "&lt;").replace(
        ">", "&gt;"
    ).replace("|", "&#124;").replace("\n", " ").replace("\r", " ").replace("`", "&#96;")


def _time(value: object) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


def _elapsed(start: datetime | None, end: datetime | None) -> str:
    if start is None or end is None:
        return "unknown"
    try:
        return f"{(end - start).total_seconds():.2f}s"
    except TypeError:
        return "unknown"


def _description(event: dict) -> str:
    metadata = event.get("metadata", {})
    check = metadata.get("check", {})
    if isinstance(check, dict) and check:
        return f"{check.get('name', 'check')}: {check.get('details', '')}"
    if metadata.get("error") or metadata.get("reason"):
        return str(metadata.get("error") or metadata["reason"])
    if "checks" in metadata and isinstance(metadata["checks"], list):
        return ", ".join(str(item.get("name", "check")) if isinstance(item, dict)
                         else str(item) for item in metadata["checks"])
    parts = []
    for key in ("attempt", "request_number", "model", "method", "status_code", "finish_reason", "files"):
        if key in metadata:
            parts.append(f"{key.replace('_', ' ')}: {metadata[key]}")
    return "; ".join(parts)


def render_report(events: list[dict], issues: list[str] | None = None) -> str:
    issues = issues or []
    first = events[0] if events else {}
    last = events[-1] if events else {}
    terminal = last if (last.get("action") == "finish" or
                        last.get("stage") == "run" and last.get("action") == "deadline") else {}
    outcome = terminal.get("result", "incomplete") if not issues else "incomplete"
    summary = terminal.get("metadata", {})
    start = _time(first.get("timestamp"))
    counts = Counter(str(e.get("result", "unknown")) for e in events)
    lines = ["# Run trace", "", f"**Outcome: {_cell(outcome).upper()}**", "",
             "| Summary | Value |", "| --- | --- |",
             f"| Model | {_cell(first.get('metadata', {}).get('model', 'unknown'))} |",
             f"| Started (timestamp includes timezone) | {_cell(first.get('timestamp', 'unknown'))} |",
             f"| Elapsed | {_cell(str(summary['elapsed_seconds']) + 's') if 'elapsed_seconds' in summary else _elapsed(start, _time(last.get('timestamp')))} |",
             f"| API attempts | {_cell(summary.get('requests', 'unknown'))} |"]
    for label, key in (("Prompt tokens (observed)", "observed_prompt_tokens"),
                       ("Completion tokens (observed)", "observed_completion_tokens"),
                       ("Total tokens (observed)", "observed_total_tokens"),
                       ("Reasoning tokens (observed)", "observed_reasoning_tokens")):
        lines.append(f"| {label} | {_cell(summary.get(key, 'unknown'))} |")
    lines.extend([f"| Usage accounting complete | {_cell(summary.get('usage_is_complete', 'unknown'))} |",
                  f"| Events | {len(events)} |", "",
                  "Event results across the entire run (including earlier attempts): " +
                  (", ".join(f"{_cell(key)}: {value}" for key, value in sorted(counts.items())) or "none") + ".", "",
                  "Earlier failed checks may have been repaired. The outcome above comes from the final event; "
                  "a trace without a final event is incomplete. Token values are observed usage, not reserved budgets. "
                  "Skipped browser or independent science checks do not count as verification.", ""])
    if issues:
        lines.extend(["## Trace read warnings", ""] + [f"- {_cell(issue)}" for issue in issues] + [""])
    lines.extend(["## Timeline", "", "Times below are seconds since the first event. Details refer to numbered events below.", "",
                  "| Event | Time | Stage / action | Result | What happened |",
                  "| --- | --- | --- | --- | --- |"])
    for number, event in enumerate(events, 1):
        lines.append(f"| {number} | {_elapsed(start, _time(event.get('timestamp')))} | "
                     f"{_cell(event.get('stage', '?'))} / {_cell(event.get('action', '?').replace('_', ' '))} | "
                     f"{_cell(event.get('result', '?'))} | {_cell(_description(event))} |")
    lines.extend(["", "## Event details", "", "Full recorded evidence, formatted for reading. Credentials and private reasoning "
                  "are redacted by the trace writer; this report does not fetch additional data.", ""])
    for number, event in enumerate(events, 1):
        pretty = json.dumps(event, ensure_ascii=False, indent=2)
        # A payload containing Markdown fences must not terminate the code block.
        fence = "`" * max(3, max((len(part) for part in re.findall(r'`+', pretty)), default=0) + 1)
        lines.extend([f"### Event {number}: {_cell(event.get('stage', '?'))} / {_cell(event.get('action', '?'))}",
                      "", fence + "json", pretty, fence, ""])
    return "\n".join(lines)


def write_report(trace_path: Path, output: Path | None = None) -> Path:
    trace_path = Path(trace_path)
    output = Path(output) if output is not None else trace_path.with_suffix(".md")
    if output.resolve() == trace_path.resolve():
        raise ValueError("Report output must differ from the JSONL trace.")
    events, issues = [], []
    for number, line in enumerate(trace_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
            if not isinstance(event, dict) or not all(isinstance(event.get(key), str)
                                                     for key in ("stage", "action", "result")):
                raise ValueError("Invalid event")
            if not isinstance(event.get("metadata", {}), dict):
                raise ValueError("Invalid metadata")
            events.append(event)
        except (ValueError, json.JSONDecodeError):
            issues.append(f"Line {number} is invalid or truncated; omitted from this report.")
    output.write_text(render_report(events, issues), encoding="utf-8")
    return output


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Convert a JSONL trace to a readable Markdown report, without API calls.")
    parser.add_argument("trace", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        output = write_report(args.trace, args.output)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Could not write trace report: {exc}\n")
    print(f"Created {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
