"""Upgrade legacy scientific notation for display, without editing lesson data."""
import ast
import copy
import re


SYMBOLS = {
    "vmax": r"V_{\max}", "Vmax": r"V_{\max}", "km": "K_m", "Km": "K_m",
    "dk": "d_k", "Phi": r"\Phi", "phi": r"\phi", "nu": r"\nu",
    "x_next": "x_{t+1}", "Q·Kᵀ": r"QK^{\top}",
}
FUNCTIONS = {"sum", "log", "log2", "sqrt", "exp", "softmax", "normalize",
             "length", "ncols", "matmul", "transpose", "dot", "mean", "norm"}
LEGACY_PHRASES = {
    "H = -sum(p_i log2 p_i)": r"H = -\sum_i p_i\log_2 p_i",
    "p_i log2 p_i": r"p_i\log_2 p_i",
    "log2 p_i": r"\log_2 p_i",
    "log2 n": r"\log_2 n",
    "0 log2 0": r"0\log_2 0",
}


def symbols_for(spec):
    symbols = dict(SYMBOLS)
    control_ids = {item["id"] for item in spec["controls"]}
    if {"q", "k", "v"} <= control_ids:
        symbols.update(q="Q", k="K", v="V")
    if {"s", "km", "vmax"} <= control_ids:
        symbols["s"] = "S"
    return symbols


def latex_expression(source, symbols):
    """Parse notation into typesetting only. This never evaluates an expression."""
    if source.strip() in LEGACY_PHRASES:
        return LEGACY_PHRASES[source.strip()]

    def visit(node):
        if isinstance(node, ast.Name):
            if node.id in symbols:
                return symbols[node.id]
            if len(node.id) == 1:
                return node.id
            match = re.fullmatch(r"([A-Za-z])(?:_([A-Za-z0-9]+)|(\d+))", node.id)
            if match:
                return f"{match[1]}_{{{match[2] or match[3]}}}"
            return r"\mathrm{" + node.id.replace("_", r"\_") + "}"
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return str(node.value)
        if isinstance(node, (ast.List, ast.Tuple)):
            rows = node.elts
            if rows and all(isinstance(row, ast.List) for row in rows):
                body = r" \\ ".join(" & ".join(visit(cell) for cell in row.elts) for row in rows)
            else:
                body = " & ".join(visit(item) for item in rows)
            return r"\begin{bmatrix}" + body + r"\end{bmatrix}"
        if isinstance(node, ast.Subscript):
            sub = node.slice.elts if isinstance(node.slice, ast.Tuple) else [node.slice]
            return visit(node.value) + "_{" + ",".join(visit(item) for item in sub) + "}"
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            return ("-" if isinstance(node.op, ast.USub) else "+") + visit(node.operand)
        if isinstance(node, ast.BinOp):
            left, right = visit(node.left), visit(node.right)
            if isinstance(node.op, ast.Div):
                return r"\frac{" + left + "}{" + right + "}"
            if isinstance(node.op, (ast.Pow, ast.BitXor)):
                if isinstance(node.left, (ast.BinOp, ast.UnaryOp)):
                    left = r"\left(" + left + r"\right)"
                if isinstance(node.right, ast.Name) and node.right.id == "T":
                    right = r"\top"
                return "{" + left + "}^{" + right + "}"
            if isinstance(node.op, ast.Mult):
                if isinstance(node.left, ast.BinOp) and isinstance(node.left.op, (ast.Add, ast.Sub)):
                    left = r"\left(" + left + r"\right)"
                if isinstance(node.right, ast.UnaryOp) or (isinstance(node.right, ast.BinOp) and isinstance(node.right.op, (ast.Add, ast.Sub))):
                    right = r"\left(" + right + r"\right)"
                return left + r"\," + right
            if isinstance(node.op, (ast.Add, ast.Sub)):
                if isinstance(node.op, ast.Sub) and isinstance(node.right, ast.BinOp) and isinstance(node.right.op, (ast.Add, ast.Sub)):
                    right = r"\left(" + right + r"\right)"
                return left + (" + " if isinstance(node.op, ast.Add) else " - ") + right
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and not node.keywords:
            name, args = node.func.id, [visit(arg) for arg in node.args]
            if name == "sqrt" and len(args) == 1:
                return r"\sqrt{" + args[0] + "}"
            if name == "transpose" and len(args) == 1:
                if isinstance(node.args[0], (ast.BinOp, ast.UnaryOp)):
                    args[0] = r"\left(" + args[0] + r"\right)"
                return "{" + args[0] + r"}^{\top}"
            if name == "matmul" and len(args) == 2:
                for index, arg in enumerate(node.args):
                    if isinstance(arg, ast.BinOp) and isinstance(arg.op, (ast.Add, ast.Sub)):
                        args[index] = r"\left(" + args[index] + r"\right)"
                return args[0] + r"\," + args[1]
            operator = {"log2": r"\log_2", "log": r"\ln", "exp": r"\exp"}.get(name, r"\operatorname{" + name + "}")
            return operator + r"\left(" + ", ".join(args) + r"\right)"
        raise ValueError("Unsupported display notation")

    if source.strip() == "Q·Kᵀ":
        return r"QK^{\top}"
    if source.strip() == "output[i] = sum_j attn_weights[i,j] * V[j]":
        return r"\mathrm{output}_i = \sum_j \mathrm{attn\_weights}_{i,j} V_j"
    # Equality is display notation, not executable Python assignment.
    parts = re.split(r"\s*(:=|=|≈|<=|>=|<|>)\s*", source.strip())
    rendered = []
    for index, part in enumerate(parts):
        if index % 2:
            rendered.append({"≈": r"\approx", "<=": r"\le", ">=": r"\ge"}.get(part, part))
        else:
            rendered.append(visit(ast.parse(part.replace("·", "*").replace("^", "**"), mode="eval").body))
    return " ".join(rendered)


def presentation_spec(spec):
    """Return a display copy. Original specs, computations and quotes stay intact."""
    result = copy.deepcopy(spec)
    symbols = symbols_for(spec)
    control_ids = {item["id"] for item in spec["controls"]}
    known = {item["symbol"].strip("$ ") for item in spec["terms"]}
    known |= {match[1] for token in tuple(known)
              if (match := re.match(r"^([A-Za-z])_", token))}
    known |= {"p_i", "w_i", "x_next", "d_k", "x0", "x1", "x2", "x3", "x4"}
    known |= set(re.findall(r"\b[A-Za-z]_[A-Za-z0-9]+\b", str(spec)))
    known |= {key for key in symbols if key in control_ids or key in known}
    for item in spec["equations"]:
        known |= {token for token in re.findall(r"[A-Za-z]\w*", item["expression"])
                  if len(token) == 1 or "_" in token or re.fullmatch(r"x\d+", token)}
    known -= {"a", "A", "I", "i", "softmax", "scaled"}
    phrases = {
        **LEGACY_PHRASES,
        "X_(t+1) = a*X_t*(1-X_t)": r"X_{t+1} = aX_t\left(1-X_t\right)",
        "[S]/([S]+k)": r"\frac{[S]}{[S]+k}",
        "v (nu)": r"v\;(\nu)",
        "Q·Kᵀ": r"QK^{\top}",
        "Attention(Q,K,V) = softmax(Q*K^T/sqrt(d_k))*V": r"\operatorname{Attention}(Q,K,V) = \operatorname{softmax}\left(\frac{QK^{\top}}{\sqrt{d_k}}\right)V",
    }
    for item in spec["equations"] + spec["computations"]:
        source = item["expression"]
        if "$" in source or "\\" in source:
            continue
        try:
            value = latex_expression(source, symbols)
        except (ValueError, SyntaxError, RecursionError):
            continue
        phrases[source] = value
        phrases[re.sub(r"\s+", "", source)] = value
    for token in known:
        try:
            phrases[token] = latex_expression(token, symbols)
        except (ValueError, SyntaxError):
            pass
    # Function notation and small parenthesized formulas appearing in prose.
    call = r"\b(?:" + "|".join(sorted(FUNCTIONS)) + r")\([^()\n]*(?:\([^()\n]*\)[^()\n]*)*\)"
    formula = r"(?:[A-Za-z]\w*|\d+(?:\.\d+)?|" + call + r"|\([^()\n]+\))(?:\s*(?:\*\*|<=|>=|[*/+^=<>]|-(?![A-Za-z])|:=|≈)\s*-?(?:" + call + r"|[A-Za-z]\w*|\d+(?:\.\d+)?|\([^()\n]+\)))+"
    array = r"\[\s*(?:\[[\d.,\s+eE-]+\]|[-+\d.eE]+)(?:\s*,\s*(?:\[[\d.,\s+eE-]+\]|[-+\d.eE]+))+\s*\]"
    exact = "|".join(re.escape(key) for key in sorted(phrases, key=len, reverse=True))
    compound = "|".join(re.escape(key) for key in sorted(phrases, key=len, reverse=True)
                        if re.search(r"[^A-Za-z0-9_]", key))
    pattern = re.compile(r"(?<![\w\\])(?:" + compound + "|" + formula + "|" + call + "|" + array + "|" + exact + r")(?!\w)")
    simple = re.compile(r"(?<![\w\\])(?:" + exact + r")(?!\w)")
    protected = re.compile(r"(\$\$[\s\S]*?\$\$|\$[^$\n]+\$|`+[^`]*`+|\[[^\]]*\]\([^)]*\)|<[^>]*>)")

    def text(value):
        def replace(match):
            raw = match[0]
            if raw in phrases:
                return "$" + phrases[raw] + "$"
            tokens = set(re.findall(r"[A-Za-z]\w*", raw))
            names = set(symbols) | known | FUNCTIONS | control_ids | {item["id"] for item in spec["computations"]}
            if not raw.startswith("[") and (not tokens & (known | FUNCTIONS | control_ids) or tokens - names):
                return simple.sub(lambda part: "$" + phrases[part[0]] + "$", raw)
            try:
                return "$" + latex_expression(raw, symbols) + "$"
            except (ValueError, SyntaxError):
                return raw
        return "".join(part if index % 2 else pattern.sub(replace, part)
                       for index, part in enumerate(protected.split(str(value))))

    for key in ("title", "concept_summary", "why_it_matters"):
        result[key] = text(result[key])
    for group, fields in (("terms", ("symbol", "meaning")),
                          ("explanation_steps", ("heading", "body")),
                          ("controls", ("label", "meaning")),
                          ("computations", ("label", "unit")),
                          ("equations", ("explanation",)),
                          ("explorations", ("change", "observe", "why")),
                          ("visualizations", ("title", "caption", "x_label", "y_label", "value_label"))):
        for item in result.get(group, []):
            for field in fields:
                if field in item:
                    item[field] = text(item[field])
    for item in result["equations"]:
        if "$" not in item["expression"] and "\\" not in item["expression"]:
            try:
                item["expression"] = "$$" + latex_expression(item["expression"], symbols) + "$$"
            except (ValueError, SyntaxError):
                pass
    for item in result["visualizations"]:
        for field in ("labels", "row_labels", "column_labels"):
            if field in item:
                item[field] = [text(value) for value in item[field]]
        for node in item.get("diagram", {}).get("nodes", []):
            node["label"] = text(node["label"])
            if "detail" in node:
                node["detail"] = text(node["detail"])
        for edge in item.get("diagram", {}).get("edges", []):
            if "label" in edge:
                edge["label"] = text(edge["label"])
    result["limitations"] = [text(value) for value in result["limitations"]]
    for item in result["grounding"]["source_claims"]:
        item["claim"] = text(item["claim"])
    result["grounding"]["teaching_simplifications"] = [text(value) for value in result["grounding"]["teaching_simplifications"]]
    return result
