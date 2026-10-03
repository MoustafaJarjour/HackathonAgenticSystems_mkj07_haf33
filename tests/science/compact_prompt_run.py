"""Developer experiment: unchanged agent with compact prompt JSON serialization.

Only the planner module's JSON facade changes; production files are untouched.
"""
import agent
import hashlib
import json as original_json
from pathlib import Path
from src import planner


class CompactJSON:
    def __getattr__(self, name):
        return getattr(original_json, name)

    def dumps(self, value, *args, **kwargs):
        kwargs.setdefault("separators", (",", ":"))
        return original_json.dumps(value, *args, **kwargs)


OriginalTrace = agent.Trace


class ExperimentalTrace(OriginalTrace):
    def event(self, stage, action, result, **metadata):
        if stage == "run" and action == "start":
            metadata.update(variant="compact-json", production_files_modified=False,
                            entrypoint_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
        return super().event(stage, action, result, **metadata)


def main(argv=None):
    planner.json = CompactJSON()
    agent.Trace = ExperimentalTrace
    return agent.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
