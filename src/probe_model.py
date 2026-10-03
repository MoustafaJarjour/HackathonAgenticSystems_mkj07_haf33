"""Small live feasibility probe. Reads the key only from the local environment."""
import argparse
import json
import os
import sys
import time
from pathlib import Path

from .models import obj
from .openrouter_client import Budget, OpenRouterClient, OpenRouterError, BudgetError
from .trace import Trace


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", type=Path, default=Path("probe-out"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    trace = Trace(args.output / "model-probe.jsonl")
    budget = Budget(time.monotonic(), max_seconds=130)
    client = None
    try:
        client = OpenRouterClient(args.model, trace, budget)
        content = client.complete([
            {"role": "system", "content": "Return only the requested JSON object. No explanatory text."},
            {"role": "user", "content": "Calculate 2+2 and return {\"value\":4}."}],
            max_tokens=512, schema=obj({"value": {"type": "integer", "const": 4}}))
        if json.loads(content) != {"value": 4}:
            raise OpenRouterError("Live model probe returned the wrong JSON result.")
        trace.event("probe", "finish", "passed", requested_model=args.model, **budget.summary())
        print("Live model probe passed; inspect model-probe.jsonl for model, format, finish status, usage and latency.")
        return 0
    except (OpenRouterError, BudgetError, ValueError) as exc:
        trace.event("probe", "finish", "failed", error=str(exc), **budget.summary())
        print(f"Live model probe failed: {exc}", file=sys.stderr)
        return 1
    finally:
        if client:
            client.close()


if __name__ == "__main__":
    raise SystemExit(main())
