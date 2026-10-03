"""Assessment entry point. One planner, one deterministic renderer, one optional repair."""
import time

PROCESS_STARTED = time.monotonic()

import argparse
import json
import os
import sys
import threading
from pathlib import Path

from src.models import SpecError, load_case
from src.openrouter_client import Budget, BudgetError, OpenRouterClient, OpenRouterError
from src.planner import generate, select_context
from src.renderer import render
from src.source import SourceError, obtain_source
from src.trace import Trace
from src.validator import validate_html, validate_spec


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
        for filename in ("index.html", "lesson.json", "index.tmp"):
            (args.output / filename).unlink(missing_ok=True)
        trace = Trace(args.output / "trace.jsonl", secret=os.environ.get("OPENROUTER_API_KEY", ""))
        trace.event("run", "start", "ok", model=args.model, schema_version=1,
                    limits={"requests": 10, "completion_tokens": 30000, "seconds": 570})

        def deadline():
            try:
                trace.event("run", "deadline", "failed", elapsed_seconds=round(time.monotonic() - PROCESS_STARTED, 3))
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
        spec, errors = None, None
        for attempt in range(2):
            budget.check()
            trace.event("planning", "generate" if attempt == 0 else "revise", "started", attempt=attempt + 1)
            try:
                spec = generate(client, case, context, spec if attempt else None, errors)
                compiled, spec_checks = validate_spec(spec, source.text, case["source_url"])
                html = render(spec, compiled)
                html_checks = validate_html(html, spec)
                trace.event("validation", "deterministic_checks", "passed", checks=spec_checks + html_checks,
                            browser_executed=False, scientific_fidelity_verified=False)
                break
            except SpecError as exc:
                errors = [str(exc)]
                trace.event("validation", "deterministic_checks", "failed", failures=errors, attempt=attempt + 1)
                if attempt == 1:
                    raise
                # Invalid JSON has no prior object; still send check errors on next attempt.
                if spec is None:
                    spec = {}
        budget.check()
        temp = args.output / "index.tmp"
        temp.write_text(html, encoding="utf-8")
        temp.replace(args.output / "index.html")
        (args.output / "lesson.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
        trace.event("output", "write", "ok", files=["index.html", "trace.jsonl", "lesson.json"],
                    html_bytes=(args.output / "index.html").stat().st_size)
        if not (args.output / "trace.jsonl").stat().st_size:
            raise OSError("Empty trace.")
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
