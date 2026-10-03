/* Pure bounded mathematics shared verbatim by the browser and Python checker. */
(() => {
  "use strict";
  const MAX_LEAVES = 64, MAX_DEPTH = 32, MAX_OPERATIONS = 100000;
  const fail = message => { throw new Error(message); };
  const budget = limits => ({remaining: Math.min(MAX_OPERATIONS, limits.maxOperations ?? MAX_OPERATIONS)});
  function tick(b) { if (--b.remaining < 0) fail("Calculation operation budget exceeded."); }
  function number(x) { if (typeof x !== "number" || !Number.isFinite(x)) fail("A calculation produced a non-finite number or invalid value."); return x; }
  function checkValue(value, depth = 0, count = {leaves: 0}) {
    if (depth > MAX_DEPTH) fail("Array nesting is too deep.");
    if (Array.isArray(value)) {
      if (value.length < 1 || value.length > MAX_LEAVES) fail("Arrays must contain between 1 and 64 elements.");
      const children = value.map(item => checkValue(item, depth + 1, count));
      if (children.some(shape => JSON.stringify(shape) !== JSON.stringify(children[0]))) fail("Arrays must have a rectangular shape.");
      return [value.length, ...children[0]];
    }
    number(value);
    if (++count.leaves > MAX_LEAVES) fail("Each array is limited to 64 numeric values.");
    return [];
  }
  function vector(value) {
    if (!Array.isArray(value) || !value.length || value.some(x => typeof x !== "number")) fail("This operation requires a numeric vector.");
    return value;
  }
  function matrix(value) {
    if (!Array.isArray(value) || !value.length || !Array.isArray(value[0])) fail("This operation requires a numeric matrix.");
    value.forEach(vector);
    if (value.some(row => row.length !== value[0].length)) fail("Matrix rows must have equal lengths.");
    return value;
  }
  function unary(value, fn, b) {
    tick(b);
    return Array.isArray(value) ? value.map(x => unary(x, fn, b)) : number(fn(number(value)));
  }
  function binary(a, c, fn, b) {
    tick(b);
    if (Array.isArray(a) && Array.isArray(c)) {
      if (a.length !== c.length) fail("Array operations require equal shapes, or a scalar to broadcast.");
      // Reject differently nested shapes rather than broadcasting each subarray.
      if (a.some((x, i) => Array.isArray(x) !== Array.isArray(c[i]))) fail("Array operations require equal shapes.");
      return a.map((x, i) => binary(x, c[i], fn, b));
    }
    if (Array.isArray(a)) return a.map(x => binary(x, c, fn, b));
    if (Array.isArray(c)) return c.map(x => binary(a, x, fn, b));
    return number(fn(number(a), number(c)));
  }
  const arithmetic = {add: (a,b) => a+b, sub: (a,b) => a-b, mul: (a,b) => a*b, div: (a,b) => a/b, pow: (a,b) => a**b};
  const elementwise = {sin: Math.sin, cos: Math.cos, exp: Math.exp, log: Math.log, log2: Math.log2, sqrt: Math.sqrt, abs: Math.abs, xlogx: x => { if (x < 0) fail("xlogx requires nonnegative values."); return x === 0 ? 0 : x * Math.log2(x); }};
  function softmax(xs, b) {
    vector(xs);
    const largest = Math.max(...xs);
    const weights = xs.map(x => {tick(b); return Math.exp(x - largest);});
    const total = weights.reduce((a,c) => a+c, 0);
    return weights.map(x => {tick(b); return x / total;});
  }
  function call(name, args, b) {
    const arity = expected => { if (args.length !== expected) fail(`${name} requires ${expected} argument(s).`); };
    if (Object.hasOwn(elementwise, name)) {arity(1); return unary(args[0], elementwise[name], b);}
    switch (name) {
      case "minimum": case "maximum":
        arity(2); return binary(args[0], args[1], name === "minimum" ? Math.min : Math.max, b);
      case "length": arity(1); return vector(args[0]).length;
      case "ncols": arity(1); return matrix(args[0])[0].length;
      case "sum": case "mean": {
        arity(1); const xs = vector(args[0]);
        const total = xs.reduce((a,c) => {tick(b); return a+c;}, 0);
        return number(name === "mean" ? total / xs.length : total);
      }
      case "norm": case "normalize": {
        arity(1); const xs = vector(args[0]); xs.forEach(() => tick(b));
        const magnitude = number(Math.hypot(...xs));
        if (name === "norm") return magnitude;
        if (magnitude === 0) fail("Cannot normalize a zero vector.");
        return unary(xs, x => x / magnitude, b);
      }
      case "dot": {
        arity(2); const a = vector(args[0]), c = vector(args[1]);
        if (a.length !== c.length) fail("dot requires vectors of equal length.");
        return number(a.reduce((total, x, i) => {tick(b); return total + x * c[i];}, 0));
      }
      case "matmul": {
        arity(2); const a = matrix(args[0]), c = matrix(args[1]);
        if (a[0].length !== c.length) fail("Matrix dimensions do not match for matmul.");
        if (a.length * c[0].length > MAX_LEAVES) fail("Matrix product exceeds 64 numeric values.");
        return a.map(row => c[0].map((_, j) => number(row.reduce((total, x, k) => {tick(b); return total + x * c[k][j];}, 0))));
      }
      case "transpose": {
        arity(1); const a = matrix(args[0]);
        return a[0].map((_, j) => a.map(row => {tick(b); return row[j];}));
      }
      case "softmax": {
        arity(1);
        if (Array.isArray(args[0]) && Array.isArray(args[0][0])) return matrix(args[0]).map(row => softmax(row, b));
        return softmax(args[0], b);
      }
      case "linspace": {
        arity(3); const start = number(args[0]), end = number(args[1]), n = number(args[2]);
        if (!Number.isInteger(n) || n < 2 || n > MAX_LEAVES) fail("linspace count must be an integer between 2 and 64.");
        return Array.from({length:n}, (_, i) => {tick(b); const t = i / (n - 1); return number((1-t)*start + t*end);});
      }
      case "clip": {
        arity(3); const lo = number(args[1]), hi = number(args[2]);
        if (lo > hi) fail("clip lower bound exceeds its upper bound.");
        return unary(args[0], x => Math.min(hi, Math.max(lo, x)), b);
      }
      default: fail(`Unsupported operation: ${name}`);
    }
  }
  function evaluate(node, env, b, depth = 0) {
    tick(b);
    if (depth > MAX_DEPTH) fail("Expression nesting is too deep.");
    if (!Array.isArray(node)) fail("Invalid expression tree.");
    const next = n => evaluate(n, env, b, depth + 1);
    switch (node[0]) {
      case "num": return number(node[1]);
      case "var": if (!Object.hasOwn(env, node[1])) fail(`Unknown variable: ${node[1]}`); return env[node[1]];
      case "list": return node[1].map(next);
      case "neg": return unary(next(node[1]), x => -x, b);
      case "pos": return next(node[1]);
      case "call": return call(node[1], node[2].map(next), b);
      default:
        if (Object.hasOwn(arithmetic, node[0])) return binary(next(node[1]), next(node[2]), arithmetic[node[0]], b);
        fail(`Unsupported expression node: ${node[0]}`);
    }
  }
  function controlValues(spec, state) {
    if (!state || typeof state !== "object" || Array.isArray(state)) fail("A complete control state is required.");
    const ids = spec.controls.map(c => c.id);
    if (Object.keys(state).length !== ids.length || Object.keys(state).some(id => !ids.includes(id))) fail("Control state has missing or unknown keys.");
    const values = Object.create(null);
    for (const control of spec.controls) {
      if (!Object.hasOwn(state, control.id)) fail("Control state has missing keys.");
      const value = state[control.id];
      if (control.kind === "array") {
        if (!Array.isArray(value)) fail(`${control.label}: enter a JSON array.`);
        const shape = checkValue(value), declared = checkValue(control.default);
        if (shape.length > 2) fail("Controls support vectors or matrices only.");
        if (declared.length === 2 && JSON.stringify(shape) !== JSON.stringify(declared)) fail(`${control.label}: matrix dimensions must stay fixed.`);
        if (declared.length === 1 && (shape.length !== 1 || shape[0] < (control.min_items ?? declared[0]) || shape[0] > (control.max_items ?? declared[0]))) fail(`${control.label}: vector length is outside the allowed bounds.`);
        if (control.min != null || control.max != null) value.flat().forEach(x => {if (control.min != null && x < control.min || control.max != null && x > control.max) fail(`${control.label}: array value is outside the allowed bounds.`);});
      } else {
        number(value);
        if (control.kind === "toggle" && value !== 0 && value !== 1) fail(`${control.label}: toggle must be 0 or 1.`);
        if (control.min !== undefined && value < control.min || control.max !== undefined && value > control.max) fail(`${control.label}: value is outside the allowed bounds.`);
      }
      values[control.id] = value;
    }
    return values;
  }
  function compute(spec, compiled, state, limits = {}) {
    if (limits.maxOperations !== undefined && (!Number.isInteger(limits.maxOperations) || limits.maxOperations < 1)) fail("Invalid operation limit.");
    const b = budget(limits);
    const env = controlValues(spec, state), outputs = Object.create(null);
    for (const computation of spec.computations) {
      try {
        const value = evaluate(compiled[computation.id], env, b);
        checkValue(value);
        env[computation.id] = value; outputs[computation.id] = value;
      } catch (error) { fail(`${computation.label}: ${error.message}`); }
    }
    return outputs;
  }
  globalThis.PTPMath = Object.freeze({compute, validateState: controlValues});
})();
