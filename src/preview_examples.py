"""Refresh AhaLab presentation copies without changing historical review packages."""
from pathlib import Path
import json

from .expressions import compile_computations
from .renderer import render
from .models import validate_schema
from .validator import validate_html


def main():
    root = Path(__file__).resolve().parent.parent
    presentation = json.loads((root / "examples" / "ahalab" / "plot_text.json").read_text(encoding="utf-8"))
    for saved in sorted((root / "examples" / "generated").glob("*/lesson.json")):
        spec = json.loads(saved.read_text(encoding="utf-8"))
        # Exact authored typography substitutions only; computations, checks,
        # source quotations, and historical specifications remain unchanged.
        for vis in spec["visualizations"]:
            for key in ("title", "x_label", "y_label", "value_label", "labels", "row_labels", "column_labels"):
                if isinstance(vis.get(key), str):
                    vis[key] = presentation.get(vis[key], vis[key])
                elif isinstance(vis.get(key), list):
                    vis[key] = [presentation.get(value, value) for value in vis[key]]
        validate_schema(spec)
        compiled, _ = compile_computations(spec)
        page = render(spec, compiled)
        validate_html(page, spec)
        output = root / "examples" / "ahalab" / saved.parent.name / "index.html"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(page, encoding="utf-8")
        print(f"Wrote {output.relative_to(root)}")


if __name__ == "__main__":
    main()
