"""Normalize case-only wire references before numerical cases are frozen.

Declarations, scientific text, operators, literals and numerical values stay exact.
The compiler and runtime still enforce the case-sensitive internal contract.
"""
import copy
import io
import re
import tokenize

from .expressions import ARITY
from .models import ID, SpecError

_ALIAS = re.compile(r"[A-Za-z][A-Za-z0-9_]{0,39}")


def normalize_references(spec):
    result = copy.deepcopy(spec)
    records = []
    groups = ("controls", "computations", "visualizations")
    if not isinstance(result, dict) or not all(isinstance(result.get(key), list) for key in groups):
        return result, records
    declared = []
    for group in groups:
        for item in result[group]:
            if not isinstance(item, dict) or not isinstance(item.get("id"), str):
                return result, records
            name = item["id"]
            if not re.fullmatch(ID["pattern"], name) or name in ARITY:
                return result, records  # The schema/identifier gate rejects declarations.
            declared.append(name)
    if len(declared) != len(set(declared)):
        raise SpecError("Duplicate declarations cannot be normalized.")
    controls = {item["id"] for item in result["controls"]}
    computations = {item["id"] for item in result["computations"]}

    def reference(value, names, path):
        if isinstance(value, str) and _ALIAS.fullmatch(value) and value.lower() in names:
            canonical = value.lower()
            if canonical != value:
                records.append({"path": path, "from": value, "to": canonical})
            return canonical
        return value

    def keys(mapping, names, path):
        normalized = {}
        for key, value in mapping.items():
            canonical = reference(key, names, path + "/" + key)
            if canonical in normalized:
                raise SpecError("Case-only references collide; refusing to discard a value.")
            normalized[canonical] = value
        return normalized

    names = set(controls)
    for index, computation in enumerate(result["computations"]):
        expression = computation.get("expression")
        if isinstance(expression, str) and len(expression) <= 1500:
            try:
                tokens = list(tokenize.generate_tokens(io.StringIO(expression).readline))
                lines = expression.splitlines(keepends=True)
                offsets, position = [], 0
                for line in lines:
                    offsets.append(position)
                    position += len(line)
                replacements = []
                for at, token in enumerate(tokens):
                    if token.type != tokenize.NAME:
                        continue
                    following = next((item for item in tokens[at + 1:]
                                      if item.type not in (tokenize.NL, tokenize.NEWLINE, tokenize.COMMENT)), None)
                    if following is not None and following.string == "(":
                        continue  # Function names are never aliases.
                    canonical = reference(token.string, names, f"computations/{index}/expression")
                    if canonical != token.string:
                        start = offsets[token.start[0] - 1] + token.start[1]
                        end = offsets[token.end[0] - 1] + token.end[1]
                        replacements.append((start, end, canonical))
                for start, end, canonical in reversed(replacements):
                    expression = expression[:start] + canonical + expression[end:]
                computation["expression"] = expression
            except (tokenize.TokenError, IndentationError, IndexError):
                pass  # Unsupported syntax remains subject to the compiler.
        names.add(computation["id"])
    cases = result.get("checks")
    for index, case in enumerate(cases if isinstance(cases, list) else []):
        if not isinstance(case, dict):
            continue
        for field, namespace in (("state", controls), ("expected", computations)):
            if isinstance(case.get(field), dict):
                case[field] = keys(case[field], namespace, f"checks/{index}/{field}")
    for index, view in enumerate(result["visualizations"]):
        for field, namespace in (("source", computations), ("sweep_control", controls)):
            if field in view:
                view[field] = reference(view[field], namespace, f"visualizations/{index}/{field}")
    return result, records
