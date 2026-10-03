"""Child-process QuickJS boundary; no Python callbacks or credential environment."""
import json
import sys
from pathlib import Path

import quickjs


def execute(payload):
    context = quickjs.Context()
    context.set_memory_limit(32 * 1024 * 1024)
    context.set_max_stack_size(512 * 1024)
    context.set_time_limit(2.0)
    # JSON parsing, computation and result serialization all occur within limits.
    context.eval((Path(__file__).with_name("math_runtime.js")).read_text(encoding="utf-8"))
    encoded = json.dumps(payload, allow_nan=False, separators=(",", ":"))
    context.eval("globalThis.payload = JSON.parse(" + json.dumps(encoded) + ");")
    result = context.eval("""JSON.stringify(payload.states.map(state => {
      try { return {ok:true, outputs:PTPMath.compute(payload.spec, payload.compiled, state)}; }
      catch(error) { return {ok:false, error:String(error.message)}; }
    }))""")
    return json.loads(result)


if __name__ == "__main__":
    try:
        payload = json.loads(sys.stdin.read(1024 * 1024))
        print(json.dumps({"results": execute(payload)}, allow_nan=False))
    except Exception as exc:
        # Fixed code is run; do not echo arbitrary input or native diagnostics.
        print(json.dumps({"error": "JS worker failed: " + type(exc).__name__}))
        raise SystemExit(1)
