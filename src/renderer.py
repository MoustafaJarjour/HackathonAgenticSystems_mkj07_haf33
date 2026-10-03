"""Deterministic LessonSpec -> one offline HTML file.

The teammate owning presentation can change this module, style.css and runtime.js
without touching retrieval, prompts or the OpenRouter client. The runtime is fixed:
model output is data and checked expression trees, never executable JavaScript.
"""

import html
import json
from pathlib import Path
from urllib.parse import urlparse


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
    evidence = ", ".join(f'<a href="#evidence-{_text(identifier)}">{_text(identifier)}</a>'
                         for identifier in item.get("evidence_ids", []))
    return (f'<span class="badge badge-{kind}">{label}</span>'
            + (f'<span class="evidence"> Evidence: {evidence}</span>' if evidence else ""))


def _control(control: dict) -> str:
    identifier = _text(control["id"])
    kind = control["kind"]
    attrs = " ".join(f'{name}="{_text(control[name])}"' for name in ("min", "max", "step") if name in control)
    if kind == "array":
        value = control["default"]
        is_matrix = isinstance(value[0], list)
        rows = value if is_matrix else [value]
        cells = "".join(
            f'<label class="array-cell"><span>{("r" + str(r + 1) + " · c" + str(c + 1)) if is_matrix else str(c + 1)}</span>'
            f'<input type="number" step="any" data-array-cell="" value="{_text(number)}" '
            f'aria-label="{_text(control["label"])}{(", row " + str(r + 1) + ", column " + str(c + 1)) if is_matrix else (", entry " + str(c + 1))}" '
            f'aria-describedby="meaning-{identifier}"></label>'
            for r, row in enumerate(rows) for c, number in enumerate(row))
        field = (f'<div id="control-{identifier}" class="array-editor" role="group" '
                 f'aria-labelledby="label-{identifier}" aria-describedby="meaning-{identifier}">'
                 f'<p class="array-shape" id="shape-{identifier}">'
                 + (f'{len(rows)} rows × {len(rows[0])} columns · fixed shape' if is_matrix else f'{len(value)} entries')
                 + f'</p><div class="array-cells {"matrix-cells" if is_matrix else "vector-cells"}"'
                 + (f' style="grid-template-columns:repeat({len(rows[0])},minmax(4.5rem,1fr))"' if is_matrix else '')
                 + f' id="cells-{identifier}">{cells}</div></div>')
        if not is_matrix:
            minimum = control.get("min_items", len(value))
            maximum = control.get("max_items", len(value))
            if minimum < maximum:
                field += (f'<div class="array-actions"><button type="button" id="remove-{identifier}"'
                          f' aria-label="Remove the last entry from {_text(control["label"])}"'
                          + (' disabled' if len(value) <= minimum else '') + '>Remove last</button>'
                          f'<button type="button" id="add-{identifier}"'
                          f' aria-label="Append zero to {_text(control["label"])}"'
                          + (' disabled' if len(value) >= maximum else '') + '>Add entry</button>'
                          f'<span class="muted">{minimum}–{maximum} entries · new entries start at 0</span></div>')
        label = f'<div class="control-label" id="label-{identifier}">{_text(control["label"])}<output id="value-{identifier}"></output></div>'
    elif kind == "toggle":
        field = (f'<div class="toggle-field"><input type="checkbox" id="control-{identifier}"'
                 + (' checked' if control["default"] == 1 else '')
                 + f' aria-label="{_text(control["label"])}" aria-describedby="meaning-{identifier}"><label for="control-{identifier}">Enabled</label></div>')
        label = f'<div class="control-label">{_text(control["label"])}<output id="value-{identifier}" for="control-{identifier}"></output></div>'
    else:
        if "step" not in control:
            attrs += ' step="any"'
        field = (f'<input type="{kind}" id="control-{identifier}" '
                 f'value="{_text(control["default"])}" {attrs} aria-describedby="meaning-{identifier}">')
        label = (f'<label class="control-label" for="control-{identifier}">{_text(control["label"])} '
                 f'<output id="value-{identifier}" for="control-{identifier}"></output></label>')
    return (f'<div class="control" data-control-id="{identifier}">{label}{field}'
            f'<p class="muted" id="meaning-{identifier}">{_text(control["meaning"])}</p></div>')


def render(spec: dict, compiled: dict) -> str:
    """Render an already validated spec and computation-id -> checked AST mapping."""
    style = (ASSETS / "style.css").read_text(encoding="utf-8")
    runtime = (ASSETS / "math_runtime.js").read_text(encoding="utf-8") + "\n" + (ASSETS / "runtime.js").read_text(encoding="utf-8")
    terms = "".join(f'<div class="term-pill"><dt>{_text(item["symbol"])}</dt><dd>{_text(item["meaning"])}</dd></div>' for item in spec["terms"])
    equations = "".join(
        f'<article class="equation-hud"><p class="formula">{_text(item["expression"])}</p><p>{_text(item["explanation"])}</p>'
        f'<p>{_provenance(item)}</p></article>' for item in spec["equations"])
    steps = "".join(
        f'<li><h3>{_text(item["heading"])}</h3><p>{_text(item["body"])}</p>'
        f'<p>{_provenance(item)}</p></li>' for item in spec.get("explanation_steps", []))
    controls = "".join(_control(item) for item in spec["controls"])
    calculations = "".join(
        f'<article class="calculation"><h3>{_text(item["label"])}</h3>'
        f'<pre id="calculation-{_text(item["id"])}" aria-live="polite">—</pre>'
        f'<p class="unit">{_text(item["unit"])}</p>'
        f'<details><summary>Calculation and evidence</summary><code>{_text(item["expression"])}</code>'
        f'<p>{_provenance(item)}</p></details></article>'
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
    source_url = grounding["source_url"]
    parsed = urlparse(source_url)
    source_link = (f'<a href="{_text(source_url)}" target="_blank" rel="noopener noreferrer">Read the source</a>'
                   if parsed.scheme in ("http", "https") and parsed.netloc
                   else _text(source_url))
    return f'''<!doctype html>
<html lang="en" data-theme="dark"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src 'none'; connect-src 'none'; font-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'">
<title>{title}</title><style>{style}</style></head>
<body><a class="skip-link" href="#controls">Skip to the interactive controls</a><main><header class="command-bar"><p class="brand-title">Paper to Playground<span class="brand-badge">Interactive lesson</span></p><button type="button" class="theme-toggle" id="theme-toggle" aria-pressed="false">Light theme</button></header>
<div class="hero-statement"><p class="eyebrow">From a relationship to a working model</p><h1>{title}</h1><nav aria-label="Lesson navigation"><a href="#concept">Understand</a><a href="#controls">Explore</a><a href="#grounding">Check the source</a></nav></div>
<div class="brief-cards">
<section id="concept"><h2>The concept</h2><p>{_text(spec["concept_summary"])}</p></section>
<section id="why"><h2>Why it matters</h2><p>{_text(spec["why_it_matters"])}</p></section>
</div>
<section id="terms"><h2>Symbols and terms</h2><dl>{terms}</dl></section>
{('<section id="explanation"><h2>How the mechanism works</h2><ol class="explanation-steps">' + steps + '</ol></section>') if steps else ''}
<div class="lab-grid"><div class="control-deck">
<section id="controls"><h2>Explore the mechanism</h2><p class="muted">Edit a value to update the results and plots. Array entries are numbered from 1.</p><div class="control-grid">{controls}</div>
<p id="runtime-status" role="status" aria-live="polite">Initializing calculations…</p></section>
<section id="equations"><h2>Relationships</h2>{equations}</section>
</div><div class="apparatus-deck">
<section id="visualizations"><h2>See what changes</h2>{visuals}</section>
<section id="calculations"><h2>Calculated results</h2><p class="muted">Displayed numbers are rounded to six significant digits. Calculations use full floating-point precision.</p><div class="calculation-grid">{calculations}</div></section>
</div></div>
<section id="explorations"><h2>Try these explorations</h2><ol>{explorations}</ol></section>
<section id="limitations"><h2>Assumptions and limitations</h2><ul>{limitations}</ul></section>
<section id="grounding"><h2>Grounding in the source</h2><p><strong>{_text(grounding["paper_title"])}</strong></p><p class="source-url">{source_link}</p><h3>Source-supported claims</h3><ul>{claims}</ul><h3>Our teaching simplifications</h3><ul>{simplifications}</ul><p class="muted">This lesson illustrates a mechanism. A toy calculation does not reproduce the paper’s experimental results.</p></section>
<footer>All calculations and visualizations run locally in this file.</footer></main>
<script id="lesson-data" type="application/json">{config}</script><script>{runtime}</script></body></html>'''


def main() -> int:
    """Preview a saved spec independently of the source/model pipeline."""
    import argparse
    import sys
    from .expressions import compile_computations
    from .models import SpecError, validate_schema
    from .validator import validate_html

    parser = argparse.ArgumentParser(description="Render a saved LessonSpec without an API call.")
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path, help="Path to the standalone HTML file.")
    args = parser.parse_args()
    try:
        spec = json.loads(args.spec.read_text(encoding="utf-8-sig"))
        validate_schema(spec)
        compiled, _ = compile_computations(spec)
        page = render(spec, compiled)
        validate_html(page, spec)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(page, encoding="utf-8")
    except (OSError, ValueError, SpecError) as exc:
        print(f"Render failed: {exc}", file=sys.stderr)
        return 2
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
