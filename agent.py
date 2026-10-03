"""Assessment CLI: source-grounded data, executed math, bounded targeted repair."""
import time

PROCESS_STARTED = time.monotonic()

import argparse
import json
import os
import sys
import threading
from pathlib import Path

from src.models import SpecError, load_case
from src.openrouter_client import Budget, BudgetError, OpenRouterClient, OpenRouterError, TruncatedCompletion
from src.planner import generate, repair, select_context, can_repair
from src.renderer import render
from src.source import SourceError, obtain_source
from src.trace import Trace
from src.validator import validate_html, validate_spec
from src.runtime_checker import check_runtime


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Turn a supplied paper concept into an offline interactive lesson.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--model", required=True)
    args = parser.parse_args(argv)
    trace, client, timer = None, None, None
    budget = Budget(PROCESS_STARTED)
    try:
        args.output.mkdir(parents=True, exist_ok=True)
        # Do not let a failed rerun look successful by retaining previous artifacts.
        for filename in ("index.html", "lesson.json", "index.tmp", "lesson.tmp", "partial.lesson.json"):
            (args.output / filename).unlink(missing_ok=True)
        trace = Trace(args.output / "trace.jsonl", secret=os.environ.get("OPENROUTER_API_KEY", ""))
        trace.event("run", "start", "ok", model=args.model, schema_version=2,
                    limits={"requests": 10, "completion_tokens": 30000, "soft_seconds": 540, "seconds": 570},
                    success_criteria="schema/source structure, exact JS numerical cases, control probes, offline HTML structure",
                    browser_executed=False, independent_science_verified=False)

        def deadline():
            try:
                trace.event("run", "deadline", "failed", **budget.summary())
            finally:
                os._exit(4)  # Bounds even slow DNS, PDF extraction or a trickling response.

        timer = threading.Timer(max(0.001, budget.remaining()), deadline)
        timer.daemon = True
        timer.start()
        case = load_case(args.input)
        trace.event("input", "load", "ok", extra_fields=sorted(set(case) - {"source_url", "focus", "audience"}))
        source = obtain_source(case, args.input, trace, budget)
        context = select_context(source.text, case["focus"])
        trace.event("source", "select_context", "ok", source_characters=len(source.text),
                    context_characters=len(context), method="lexical_windows" if context != source.text else "complete_excerpt")
        client = OpenRouterClient(args.model, trace, budget)
        spec, errors, compact = None, None, False
        for attempt in range(3):
            budget.check()
            trace.event("planning", "generate" if attempt == 0 else "revise", "started", attempt=attempt + 1)
            try:
                stage = "generation"
                repairable = can_repair(spec)
                targeted_repair = bool(attempt and repairable)
                if targeted_repair:
                    spec = repair(client, case, context, spec, errors, compact=compact)
                    trace.event("planning", "component_replacements", "applied", attempt=attempt + 1,
                                preserved_numerical_cases=True)
                else:
                    if attempt:
                        trace.event("planning", "full_regeneration", "started",
                                    reason="Prior package is unusable or incomplete; retain any supplied numerical cases.",
                                    compact=compact)
                    spec = generate(client, case, context, spec if attempt else None, errors, compact=compact)
                stage = "spec"
                compiled, spec_checks = validate_spec(spec, source.text, case["source_url"])
                trace.event("validation", "spec_checks", "passed", checks=[
                    {"name": name, "stage": "spec", "status": "passed", "details": "Structural validation passed."}
                    for name in spec_checks], scientific_fidelity_verified=False)
                stage = "runtime"
                errors = None
                runtime_checks = check_runtime(spec, compiled, timeout=min(5.0, budget.remaining()))
                for record in runtime_checks:
                    trace.event("validation", "runtime_case", record["status"], check=record)
                errors = [record for record in runtime_checks if record["status"] != "passed"]
                if errors:
                    raise SpecError("Executed numerical/control checks failed; see expected/actual evidence.")
                stage = "html"
                html = render(spec, compiled)
                html_checks = validate_html(html, spec)
                trace.event("validation", "html_checks", "passed", checks=[
                    {"name": name, "stage": "html", "status": "passed", "details": "Offline HTML structure passed."}
                    for name in html_checks],
                            browser_executed=False, scientific_fidelity_verified=False)
                break
            except TruncatedCompletion as exc:
                errors = [{"name": "completion_length", "stage": "generation", "status": "failed", "details": str(exc)}]
                # A compact full generation already changed the output strategy.
                # Repeating it would spend another cap without a new recovery.
                recover_length = attempt < 2 and (targeted_repair or not compact)
                compact = True
                trace.event("planning", "length_recovery", "scheduled" if recover_length else "failed",
                            strategy="Reduce package/replacement size, preserve mechanism and existing cases.",
                            reason="A smaller changed request remains available." if recover_length else
                                   "Compact full generation was already tried or no repair attempts remain.")
                if not recover_length:
                    raise
            except SpecError as exc:
                if stage != "runtime" or not errors:
                    errors = [{"name": "candidate_validation", "stage": stage,
                               "status": "failed", "details": str(exc)}]
                trace.event("validation", "candidate", "failed", failures=errors, attempt=attempt + 1)
                if isinstance(spec, dict):
                    (args.output / "partial.lesson.json").write_text(
                        json.dumps(spec, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
                if attempt == 2:
                    raise
            finally:
                budget.check()
        budget.check()
        temp = args.output / "index.tmp"
        temp.write_text(html, encoding="utf-8")
        lesson_temp = args.output / "lesson.tmp"
        lesson_temp.write_text(json.dumps(spec, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
        # HTML is promoted last, after both accepted files have been fully written.
        lesson_temp.replace(args.output / "lesson.json")
        temp.replace(args.output / "index.html")
        (args.output / "partial.lesson.json").unlink(missing_ok=True)
        trace.event("output", "write", "ok", files=["index.html", "trace.jsonl", "lesson.json"],
                    html_bytes=(args.output / "index.html").stat().st_size)
        if not (args.output / "trace.jsonl").stat().st_size:
            raise OSError("Empty trace.")
        trace.event("validation", "independent_review", "skipped", checks=[
            {"name": "real_browser", "stage": "browser", "status": "skipped", "details": "Not executed by the assessment CLI."},
            {"name": "independent_science", "stage": "science", "status": "skipped", "details": "Model expectations are not independent scientific validation."}])
        trace.event("run", "finish", "success", **budget.summary())
        print(f"Created {args.output / 'index.html'} and {args.output / 'trace.jsonl'}")
        return 0
    except (SpecError, SourceError, OpenRouterError, BudgetError, OSError, ValueError) as exc:
        message = str(exc) if isinstance(exc, (SpecError, SourceError, OpenRouterError, BudgetError)) else "File or data operation failed."
        if trace:
            trace.event("run", "finish", "failed", error=message, error_type=type(exc).__name__,
                        **budget.summary())
        print(f"Generation failed: {message}", file=sys.stderr)
        return 3 if isinstance(exc, BudgetError) else 1
    except Exception as exc:
        # No raw traceback: third-party errors can contain credentials or response payloads.
        if trace:
            trace.event("run", "finish", "failed", error_type=type(exc).__name__,
                        error="Unexpected internal error; inspect the pipeline locally.", **budget.summary())
        print(f"Generation failed: unexpected {type(exc).__name__}.", file=sys.stderr)
        return 1
    finally:
        if timer:
            timer.cancel()
        if client:
            client.close()


if __name__ == "__main__":
    raise SystemExit(main())
