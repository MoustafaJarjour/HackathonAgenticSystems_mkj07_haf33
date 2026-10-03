"""Parse a small math DSL into JSON nodes. Never execute model text as Python/JS."""
import ast
import math

from .models import SpecError

ARITY = {name: 1 for name in (
    "sin", "cos", "exp", "log", "log2", "sqrt", "abs", "sum", "mean", "norm",
    "transpose", "softmax", "normalize", "xlogx", "length", "ncols")}
ARITY.update({"minimum": 2, "maximum": 2, "dot": 2, "matmul": 2,
              "linspace": 3, "clip": 3})
BINARY = {ast.Add: "add", ast.Sub: "sub", ast.Mult: "mul", ast.Div: "div", ast.Pow: "pow"}


def compile_expression(expression: str, names: set[str]) -> tuple[list, set[str]]:
    if len(expression) > 1500:
        raise SpecError("Expression exceeds 1500 characters.")
    try:
        tree = ast.parse(expression, mode="eval")
    except (SyntaxError, RecursionError) as exc:
        raise SpecError("Expression is not valid math DSL syntax.") from exc
    if sum(1 for _ in ast.walk(tree)) > 256:
        raise SpecError("Expression exceeds 256 syntax nodes.")
    references = set()

    def visit(node, depth=0):
        if depth > 32:
            raise SpecError("Expression nesting exceeds 32.")
        child = lambda value: visit(value, depth + 1)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            if abs(node.value) > 1e6 or not math.isfinite(node.value):
                raise SpecError("Expression constant is out of bounds.")
            return ["num", node.value]
        if isinstance(node, ast.Name) and node.id in names:
            references.add(node.id)
            return ["var", node.id]
        if isinstance(node, ast.List) and 1 <= len(node.elts) <= 64:
            return ["list", [child(value) for value in node.elts]]
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.USub, ast.UAdd)):
            return ["neg" if isinstance(node.op, ast.USub) else "pos", child(node.operand)]
        if isinstance(node, ast.BinOp) and type(node.op) in BINARY:
            return [BINARY[type(node.op)], child(node.left), child(node.right)]
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id in ARITY and not node.keywords
                and len(node.args) == ARITY[node.func.id]):
            return ["call", node.func.id, [child(arg) for arg in node.args]]
        raise SpecError("Unsupported expression node or unknown variable. Use only the documented DSL.")

    return visit(tree.body), references


def compile_computations(spec: dict) -> tuple[dict, dict]:
    names = {control["id"] for control in spec["controls"]}
    compiled, dependencies = {}, {}
    for computation in spec["computations"]:
        name = computation["id"]
        if name in names:
            raise SpecError("Control/computation identifiers must be unique.")
        node, refs = compile_expression(computation["expression"], names)
        compiled[name] = node
        dependencies[name] = set().union(*(dependencies.get(ref, {ref}) for ref in refs))
        names.add(name)
    return compiled, dependencies
