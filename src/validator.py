"""Cheap structural checks. These do not establish scientific truth or JS execution."""
import math
import re
from html.parser import HTMLParser

from .expressions import ARITY, compile_computations
from .models import SpecError, validate_schema


def require(condition, message):
    if not condition:
        raise SpecError(message)


def validate_spec(spec: dict, source_text: str, source_url: str) -> tuple[dict, list[str]]:
    validate_schema(spec)
    controls = {c["id"]: c for c in spec["controls"]}
    ids = [item["id"] for group in ("controls", "computations", "visualizations") for item in spec[group]]
    require(len(ids) == len(set(ids)), "All control/computation/visualization ids must be unique.")
    require(not set(ids) & ARITY.keys(), "Identifiers cannot use reserved function names.")
    require(any(c["show"] for c in spec["computations"]), "Show at least one computed result.")
    for c in controls.values():
        if c["kind"] != "array":
            require(type(c["default"]) in (int, float), "Scalar controls need numeric defaults.")
            require(all(k in c for k in ("min", "max", "step")), "Scalar controls need min/max/step.")
            require(c["min"] < c["max"] and c["min"] <= c["default"] <= c["max"], "Invalid control bounds.")
            require(c["step"] <= c["max"] - c["min"], "Control step must fit within its bounds.")
            if c["kind"] == "toggle":
                require(c["default"] in (0, 1) and (c["min"], c["max"], c["step"]) == (0, 1, 1),
                        "Toggle metadata must be min=0, max=1, step=1 and default 0/1.")
        else:
            a = c["default"]
            require(isinstance(a, list), "Array controls need array defaults.")
            matrix = any(isinstance(v, list) for v in a)
            require(not matrix or all(isinstance(v, list) and len(v) == len(a[0]) for v in a),
                    "Matrix control must have equal row lengths.")
            count = sum(len(v) for v in a) if matrix else len(a)
            require(count <= 64, "Array control exceeds 64 numeric cells.")
            if "min_items" in c or "max_items" in c:
                require(not matrix and "min_items" in c and "max_items" in c,
                        "Vector resizing needs both min_items and max_items; matrices stay fixed.")
                require(c["min_items"] <= len(a) <= c["max_items"], "Default vector length is outside resize bounds.")
            if "min" in c or "max" in c:
                if "min" in c and "max" in c:
                    require(c["min"] < c["max"], "Array bounds need min < max.")
                values = [v for row in a for v in row] if matrix else a
                require(all(c.get("min", -math.inf) <= v <= c.get("max", math.inf) for v in values),
                        "Array default is outside bounds.")
    if len(controls) == 1:
        c = next(iter(controls.values()))
        require(c["kind"] == "array" and c.get("min_items", 1) < c.get("max_items", 1),
                "One control is sufficient only for an explicitly resizable vector with value editing.")
    # JSON Schema's numeric validation is not a guarantee against nonstandard NaN.
    def finite(value):
        if isinstance(value, dict):
            return all(finite(v) for v in value.values())
        if isinstance(value, list):
            return all(finite(v) for v in value)
        return math.isfinite(value) if type(value) in (int, float) else True
    require(finite(spec), "LessonSpec contains a nonfinite number.")
    compiled, dependencies = compile_computations(spec)
    check_ids = [case["id"] for case in spec["checks"]]
    require(len(check_ids) == len(set(check_ids)), "Numerical case ids must be unique.")
    for case in spec["checks"]:
        require(set(case["state"]) == set(controls), "Numerical cases need complete control state with no unknown keys.")
        require(set(case["expected"]) <= set(compiled), "Numerical expectations must reference computations.")
        from .runtime_checker import shape
        for value in case["expected"].values():
            require(len(shape(value)) <= 2, "Expectations must be scalars, vectors or matrices.")
    visible = {c["id"] for c in spec["computations"] if c["show"]}
    for v in spec["visualizations"]:
        require(v["source"] in compiled, "Visualization source must reference a computation.")
        visible.add(v["source"])
        if v["kind"] == "line":
            control = controls.get(v.get("sweep_control"))
            require(control is not None and control["kind"] != "array",
                    f"{v['id']}: line plot needs an existing scalar sweep_control.")
            require(control["id"] in dependencies[v["source"]],
                    f"{v['id']}: line source '{v['source']}' must be a scalar computation depending on "
                    f"swept control '{control['id']}'. Bind the current-value formula; the renderer samples it.")
    used = set().union(*(dependencies[name] for name in visible))
    require(set(controls) <= used, "Every control must affect a visual or shown calculation.")
    grounding = spec["grounding"]
    require(grounding["source_url"] == source_url, "Grounding source_url must equal the input URL.")
    evidence = {claim["id"] for claim in grounding["source_claims"]}
    require(len(evidence) == len(grounding["source_claims"]), "Evidence ids must be unique.")
    normalized_source = " ".join(source_text.split())
    for claim in grounding["source_claims"]:
        quote = " ".join(claim["quote"].split())
        require(bool(quote) and quote in normalized_source, "Evidence quote must occur in supplied source text.")
        if "source_start" in claim or "source_end" in claim:
            require("source_start" in claim and "source_end" in claim, "Evidence offsets need both endpoints.")
            start, end = claim["source_start"], claim["source_end"]
            require(0 <= start < end <= len(source_text), "Evidence offsets are outside full source bounds.")
            require(" ".join(source_text[start:end].split()) == quote, "Evidence offsets do not match the quoted span.")
    for item in spec["equations"] + spec["computations"] + spec["explanation_steps"]:
        require(set(item["evidence_ids"]) <= evidence, "Unknown evidence reference.")
        if item["provenance"] == "source_supported":
            require(bool(item["evidence_ids"]), "Source-supported items need evidence references.")
    return compiled, ["schema", "unique_ids", "expression_whitelist", "dependency_order",
                      "control_reachability", "source_quote_presence", "provenance_references"]


class PageInspector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids, self.controls, self.resources = [], [], []
        self.tags, self.errors = [], []

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if "data-control-id" in attrs:
            self.controls.append(attrs["data-control-id"])
        if tag in ("iframe", "object", "embed", "base", "link"):
            self.resources.append(tag)
        if any(k in attrs for k in ("src", "srcset", "poster")):
            self.resources.append(tag)
        if any(k.startswith("on") for k in attrs):
            self.resources.append("inline event handler")
        if tag not in {"meta", "input", "br", "hr", "img", "link", "source", "wbr", "area", "base", "col", "param", "embed", "track"}:
            self.tags.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if self.tags and self.tags[-1] == tag:
            self.tags.pop()

    def handle_endtag(self, tag):
        if self.tags and self.tags[-1] == tag:
            self.tags.pop()
        else:
            self.errors.append(f"Unmatched closing tag: {tag}")


def validate_html(html: str, spec: dict) -> list[str]:
    require(len(html.encode("utf-8")) > 1000, "HTML is missing or empty.")
    require(html.lstrip().lower().startswith("<!doctype html>"), "HTML needs a doctype.")
    page = PageInspector()
    page.feed(html)
    page.close()
    require(not page.errors and not page.tags, "HTML has unmatched tags.")
    require(not page.resources, "HTML contains runtime resources or event handlers.")
    require(len(page.ids) == len(set(page.ids)), "Duplicate HTML ids.")
    sections = {"concept", "why", "terms", "equations", "controls", "calculations",
                "visualizations", "explorations", "limitations", "grounding"}
    require(sections <= set(page.ids), "Required HTML sections are missing.")
    expected = {c["id"] for c in spec["controls"]}
    require(expected == set(page.controls) and len(page.controls) == len(expected), "Rendered controls do not match LessonSpec.")
    require({"control-" + c for c in expected} <= set(page.ids), "Control identifiers are missing.")
    require("<style" in html and "<script" in html and "connect-src 'none'" in html,
            "Missing embedded assets or offline content policy.")
    # Static checks only; a browser test is the extension point for runtime/calculation checking.
    require(not re.search(r"@import\s|url\s*\(|\bfetch\s*\(|XMLHttpRequest|WebSocket|\bimport\s*\(|\beval\s*\(|new\s+Function", html),
            "External resources or dynamic code execution detected.")
    return ["nonempty_html", "required_sections", "control_ids", "balanced_tags", "offline_resources"]


# Model source critique is orchestrated separately with the same budgeted client.
# Exact quotations and executed model cases do not prove scientific interpretation.
