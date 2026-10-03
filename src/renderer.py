"""Deterministic LessonSpec -> one offline HTML file.

The teammate owning presentation can change this module, style.css and runtime.js
without touching retrieval, prompts or the OpenRouter client. The runtime is fixed:
model output is data and checked expression trees, never executable JavaScript.
"""

import html
import json
from pathlib import Path


ASSETS = Path(__file__).parent


def _text(value: object) -> str:
    return html.escape(str(value), quote=True)


def _json(value: object) -> str:
    # JSON in a script element must not contain an HTML closing-tag sequence.
    return (json.dumps(value, ensure_ascii=False, allow_nan=False)
            .replace("&", "\\u0026").replace("<", "\\u003c")
            .replace(">", "\\u003e").replace("\u2028", "\\u2028")
            .replace("\u2029", "\\u2029"))


def _provenance(item: dict) -> str:
    kind = item["provenance"]
    label = "Source-supported relationship" if kind == "source_supported" else "Teaching simplification"
    evidence = ", ".join(item.get("evidence_ids", []))
    return (f'<span class="badge">{label}</span>'
            + (f'<span class="evidence"> Evidence: {_text(evidence)}</span>' if evidence else ""))


def _control(control: dict) -> str:
    identifier = _text(control["id"])
    kind = control["kind"]
    attrs = " ".join(f'{name}="{_text(control[name])}"' for name in ("min", "max", "step") if name in control)
    if kind == "array":
        field = (f'<textarea id="control-{identifier}" data-control-id="{identifier}" '
                 f'rows="4" spellcheck="false" aria-describedby="meaning-{identifier}">'
                 f'{_text(json.dumps(control["default"], allow_nan=False))}</textarea>')
    else:
        if "step" not in control:
            attrs += ' step="any"'
        field = (f'<input type="{kind}" id="control-{identifier}" data-control-id="{identifier}" '
                 f'value="{_text(control["default"])}" {attrs} aria-describedby="meaning-{identifier}">')
    return (f'<div class="control"><label for="control-{identifier}">{_text(control["label"])} '
            f'<output id="value-{identifier}" for="control-{identifier}"></output></label>{field}'
            f'<p class="muted" id="meaning-{identifier}">{_text(control["meaning"])}</p></div>')


def render(spec: dict, compiled: dict) -> str:
    """Render an already validated spec and computation-id -> checked AST mapping."""
    style = (ASSETS / "style.css").read_text(encoding="utf-8")
    runtime = (ASSETS / "math_runtime.js").read_text(encoding="utf-8") + "\n" + (ASSETS / "runtime.js").read_text(encoding="utf-8")
    terms = "".join(f'<dt>{_text(item["symbol"])}</dt><dd>{_text(item["meaning"])}</dd>' for item in spec["terms"])
    equations = "".join(
        f'<article><p class="formula">{_text(item["expression"])}</p><p>{_text(item["explanation"])}</p>'
        f'<p>{_provenance(item)}</p></article>' for item in spec["equations"])
    controls = "".join(_control(item) for item in spec["controls"])
    calculations = "".join(
        f'<article class="calculation"><h3>{_text(item["label"])}</h3>'
        f'<code>{_text(item["expression"])}</code>'
        f'<pre id="calculation-{_text(item["id"])}" aria-live="polite">—</pre>'
        f'<p class="muted">{_text(item["unit"])}</p><p>{_provenance(item)}</p></article>'
        for item in spec["computations"] if item["show"])
    visuals = "".join(
        f'<figure><h3>{_text(item["title"])}</h3>'
        f'<div id="visualization-{_text(item["id"])}" class="visual" aria-label="{_text(item["title"])}"></div>'
        f'<figcaption>{_text(item["x_label"])} · {_text(item["y_label"])}'
        + (' · The marker shows the current setting; the curve sweeps the selected control.' if item["kind"] == "line" else '')
        + '</figcaption></figure>' for item in spec["visualizations"])
    explorations = "".join(
        f'<li><p><strong>Change:</strong> {_text(item["change"])}</p>'
        f'<p><strong>Observe:</strong> {_text(item["observe"])}</p>'
        f'<p><strong>Why:</strong> {_text(item["why"])}</p></li>' for item in spec["explorations"])
    limitations = "".join(f'<li>{_text(item)}</li>' for item in spec["limitations"])
    grounding = spec["grounding"]
    claims = "".join(
        f'<li id="evidence-{_text(item["id"])}"><strong>{_text(item["id"])}</strong>: {_text(item["claim"])}'
        f'<p class="muted">Source location: {_text(item["locator"])}</p>'
        + (f'<blockquote>{_text(item["quote"])}</blockquote>' if item.get("quote") else '')
        + '</li>' for item in grounding["source_claims"])
    simplifications = "".join(f'<li>{_text(item)}</li>' for item in grounding["teaching_simplifications"])
    config = _json({"spec": spec, "compiled": compiled})
    title = _text(spec["title"])
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src 'none'; connect-src 'none'; font-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'">
<title>{title}</title><style>{style}</style></head>
<body><main><header><p class="eyebrow">Paper to Playground · interactive lesson</p><h1>{title}</h1></header>
<section id="concept"><h2>The concept</h2><p>{_text(spec["concept_summary"])}</p></section>
<section id="why"><h2>Why it matters</h2><p>{_text(spec["why_it_matters"])}</p></section>
<section id="terms"><h2>Symbols and terms</h2><dl>{terms}</dl></section>
<section id="equations"><h2>Relationships</h2>{equations}</section>
<section id="controls"><h2>Explore the mechanism</h2><p class="muted">Changing a value recomputes the displayed results and plots. Arrays use JSON notation.</p><div class="control-grid">{controls}</div>
<p id="runtime-status" role="status" aria-live="polite">Initializing calculations…</p></section>
<section id="calculations"><h2>Executable calculations</h2><p class="muted">Displayed numbers are rounded to six significant digits. Calculations use full floating-point precision.</p><div class="calculation-grid">{calculations}</div></section>
<section id="visualizations"><h2>See what changes</h2>{visuals}</section>
<section id="explorations"><h2>Two guided explorations</h2><ol>{explorations}</ol></section>
<section id="limitations"><h2>Assumptions and limitations</h2><ul>{limitations}</ul></section>
<section id="grounding"><h2>Grounding in the source</h2><p><strong>{_text(grounding["paper_title"])}</strong></p><p class="source-url">{_text(grounding["source_url"])}</p><h3>Source-supported claims</h3><ul>{claims}</ul><h3>Our teaching simplifications</h3><ul>{simplifications}</ul><p class="muted">This lesson illustrates a mechanism. A toy calculation does not reproduce the paper’s experimental results.</p></section>
<footer>All calculations and visualizations run locally in this file.</footer></main>
<script id="lesson-data" type="application/json">{config}</script><script>{runtime}</script></body></html>'''


def main() -> int:
    """Preview a saved spec independently of the source/model pipeline."""
    import argparse
    import sys
    from .expressions import compile_computations
    from .models import SpecError, validate_schema

    parser = argparse.ArgumentParser(description="Render a saved LessonSpec without an API call.")
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path, help="Path to the standalone HTML file.")
    args = parser.parse_args()
    try:
        spec = json.loads(args.spec.read_text(encoding="utf-8-sig"))
        validate_schema(spec)
        compiled, _ = compile_computations(spec)
        page = render(spec, compiled)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(page, encoding="utf-8")
    except (OSError, ValueError, SpecError) as exc:
        print(f"Render failed: {exc}", file=sys.stderr)
        return 2
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
