"""The versioned A/B contract. Change this together; pipeline and renderer use dicts."""
import json
from pathlib import Path
from urllib.parse import urlparse

from jsonschema import Draft202012Validator


class SpecError(ValueError):
    pass


TEXT = {"type": "string", "minLength": 1, "maxLength": 5000}
ID = {"type": "string", "pattern": "^[a-z][a-z0-9_]{0,39}$"}
NUMBER = {"type": "number", "minimum": -1e6, "maximum": 1e6}
FINITE = {"type": "number"}
ARRAY = {"type": "array", "minItems": 1, "maxItems": 64, "items": {
    "anyOf": [NUMBER, {"type": "array", "minItems": 1, "maxItems": 64, "items": NUMBER}]}}


def obj(properties, required=None):
    return {"type": "object", "additionalProperties": False, "properties": properties,
            "required": list(properties) if required is None else required}


def items(schema, minimum=1, maximum=16):
    return {"type": "array", "minItems": minimum, "maxItems": maximum, "items": schema}


PROVENANCE = {
    "provenance": {"enum": ["source_supported", "teaching_simplification"]},
    "evidence_ids": items(ID, minimum=0),
}

LESSON_SCHEMA = obj({
    "schema_version": {"const": 2},
    "title": TEXT,
    "concept_summary": TEXT,
    "why_it_matters": TEXT,
    "explanation_steps": items(obj({"heading": TEXT, "body": TEXT, **PROVENANCE}), maximum=8),
    "terms": items(obj({"symbol": TEXT, "meaning": TEXT})),
    "equations": items(obj({"expression": TEXT, "explanation": TEXT, **PROVENANCE})),
    "controls": items(obj({
        "id": ID, "label": TEXT, "meaning": TEXT,
        "kind": {"enum": ["range", "number", "array", "toggle"]},
        "default": {"anyOf": [NUMBER, ARRAY]},
        "min": NUMBER, "max": NUMBER,
        "step": {"type": "number", "exclusiveMinimum": 0, "maximum": 1e6},
        "min_items": {"type": "integer", "minimum": 1, "maximum": 64},
        "max_items": {"type": "integer", "minimum": 1, "maximum": 64},
    }, ["id", "label", "meaning", "kind", "default"]), minimum=1, maximum=24),
    "computations": items(obj({
        "id": ID, "label": TEXT, "expression": TEXT,
        "unit": {"type": "string", "maxLength": 100}, "show": {"type": "boolean"},
        **PROVENANCE,
    }), maximum=24),
    "visualizations": items(obj({
        "id": ID, "kind": {"enum": ["line", "bars", "heatmap"]},
        "title": TEXT, "source": ID, "x_label": TEXT, "y_label": TEXT,
        "sweep_control": ID,
        "labels": items(TEXT, maximum=64), "value_label": TEXT,
        "row_labels": items(TEXT, maximum=64), "column_labels": items(TEXT, maximum=64),
    }, ["id", "kind", "title", "source", "x_label", "y_label"]), maximum=3),
    "explorations": items(obj({"change": TEXT, "observe": TEXT, "why": TEXT}), minimum=2, maximum=3),
    "limitations": items(TEXT, maximum=8),
    "grounding": obj({
        "paper_title": TEXT, "source_url": TEXT,
        "source_claims": items(obj({"id": ID, "claim": TEXT, "locator": TEXT, "quote": TEXT,
                                  "source_start": {"type": "integer", "minimum": 0},
                                  "source_end": {"type": "integer", "minimum": 1}},
                                 ["id", "claim", "locator", "quote"])),
        "teaching_simplifications": items(TEXT, maximum=8),
    }),
    "checks": items(obj({
        "id": ID, "name": TEXT,
        "state": {"type": "object", "minProperties": 1,
                  "additionalProperties": {"anyOf": [FINITE, ARRAY]}},
        "expected": {"type": "object", "minProperties": 1,
                     "additionalProperties": {"anyOf": [FINITE, ARRAY]}},
        "atol": {"type": "number", "minimum": 0, "maximum": 1e-3},
        "rtol": {"type": "number", "minimum": 0, "maximum": 1e-3},
    }, ["id", "name", "state", "expected"]), minimum=2, maximum=8),
})


def load_case(path: Path) -> dict:
    try:
        case = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as exc:
        raise SpecError("Input must be a readable UTF-8 JSON file.") from exc
    if not isinstance(case, dict):
        raise SpecError("Input must be a JSON object.")
    for key in ("source_url", "focus", "audience"):
        if not isinstance(case.get(key), str) or not case[key].strip():
            raise SpecError(f"Missing nonempty string: {key}")
    url = urlparse(case["source_url"])
    if url.scheme not in ("http", "https") or not url.netloc or url.username or url.password:
        raise SpecError("source_url must be an HTTP(S) paper URL without credentials.")
    # PDF says five fields but names only three. Extra fields are allowed, not required.
    return case


def validate_schema(spec: dict) -> None:
    errors = sorted(Draft202012Validator(LESSON_SCHEMA).iter_errors(spec), key=lambda e: str(e.path))
    if errors:
        # Paths/keywords suffice for repair. Do not echo arbitrary model-generated text.
        details = [f"{'/'.join(map(str, e.path)) or '$'}: {e.validator}" for e in errors[:12]]
        raise SpecError("LessonSpec schema: " + "; ".join(details))
