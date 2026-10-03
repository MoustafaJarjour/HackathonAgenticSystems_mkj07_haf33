"""Generate an offline preview through the real pipeline with a mocked model response."""
import argparse
import sys
from pathlib import Path

# Support the convenient direct command: python tests/create_demo.py --output smoke-out
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests.fixtures import completion, diagram, lesson, run_fixture


def main():
    parser = argparse.ArgumentParser(description="Create synthetic mock-generated preview; no API/network.")
    parser.add_argument("--output", type=Path, default=Path("smoke-out"))
    parser.add_argument("--diagrams", action="store_true", help="Include a synthetic mechanism diagram in the design pass.")
    args = parser.parse_args()
    visuals = [completion({"visualizations": [diagram(), *lesson()["visualizations"]]})] if args.diagrams else None
    code, _, _ = run_fixture(args.output, visualization_responses=visuals)
    if code == 0:
        print("SYNTHETIC MOCK DEMO: tests the real pipeline, not real model quality or paper fidelity.")
        print(f"Open {args.output / 'index.html'} in Chromium.")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
