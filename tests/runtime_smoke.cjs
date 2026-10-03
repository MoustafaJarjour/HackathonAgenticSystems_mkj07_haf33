/* Optional developer check: node tests/runtime_smoke.cjs
 * Uses only Node built-ins and a tiny DOM shim. This checks execution and SVG
 * structure, not actual browser rendering, accessibility or Chromium behavior.
 */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const runtime = fs.readFileSync(path.join(__dirname, "../src/math_runtime.js"), "utf8") + "\n" + fs.readFileSync(path.join(__dirname, "../src/runtime.js"), "utf8");
const num = x => ["num", x], variable = x => ["var", x];
const call = (name, ...args) => ["call", name, args];
const jsonEqual = (actual, expected) => assert.equal(JSON.stringify(actual), JSON.stringify(expected));

function boot(controls, compiled, visualizations = []) {
  const nodes = new Map();
  const create = () => ({
    value: "", checked: false, disabled: false, textContent: "", className: "", attrs: {}, children: [], listeners: {},
    setAttribute(key, value) { this.attrs[key] = String(value); },
    removeAttribute(key) { delete this.attrs[key]; },
    append(...children) { children.forEach(child => { child.parent = this; this.children.push(child); }); },
    replaceChildren(...children) { this.children = children; },
    addEventListener(name, callback) { (this.listeners[name] ??= []).push(callback); },
    fire(name) { (this.listeners[name] ?? []).forEach(callback => callback()); },
    querySelectorAll() { return this.children.flatMap(child => Object.hasOwn(child.attrs, "data-array-cell") ? [child] : child.querySelectorAll()); },
    get lastElementChild() { return this.children[this.children.length - 1]; },
    remove() { this.parent.children.splice(this.parent.children.indexOf(this), 1); },
  });
  const element = id => {
    if (!nodes.has(id)) nodes.set(id, create());
    return nodes.get(id);
  };
  const spec = {controls, visualizations, computations: Object.keys(compiled).map(id => ({id, label: id, show: true}))};
  element("lesson-data").textContent = JSON.stringify({spec, compiled});
  controls.forEach(c => {
    element(`control-${c.id}`).value = String(c.default);
    element(`control-${c.id}`).checked = c.default === 1;
    if(c.kind === "array") c.default.flat().forEach(value => {
      const label=create(), input=create();input.value=String(value);input.setAttribute("data-array-cell", "");
      label.append(input);element(`cells-${c.id}`).append(label);
    });
  });
  const context = {window: {}, document: {
    getElementById: element, createElementNS: create, createElement: create,
    documentElement: {dataset: {theme: "dark"}},
  }};
  vm.createContext(context);
  vm.runInContext(runtime, context, {timeout: 2000});
  return {api: context.window.PTP, element, state: context.document.documentElement.dataset};
}

const controls = [
  {id: "a", label: "A", kind: "range", min: 0, max: 5, step: .1, default: 2},
  {id: "b", label: "B", kind: "number", min: 0, max: 5, step: .1, default: 3},
  {id: "u", label: "Vector", kind: "array", default: [1, 2, 3]},
  {id: "m", label: "Matrix", kind: "array", default: [[1, 2], [3, 4]]},
];
const compiled = {
  product: ["mul", variable("a"), variable("b")],
  ratio: ["div", variable("a"), variable("b")],
  dot_result: call("dot", variable("u"), variable("u")),
  matrix_result: call("matmul", variable("m"), variable("m")),
  transposed: call("transpose", variable("m")),
  normalized: call("normalize", variable("u")),
  norm_result: call("norm", variable("u")),
  probabilities: call("softmax", ["list", [num(1000), num(1001)]]),
  samples: call("linspace", variable("a"), variable("b"), num(3)),
  clipped: call("clip", variable("u"), num(1.5), num(2.5)),
  square_roots: call("sqrt", variable("u")),
  average: call("mean", variable("u")),
  scaled: ["mul", variable("m"), variable("a")],
};
const run = boot(controls, compiled);
assert.equal(run.state.runtimeState, "ok");
const values = run.api.compute();
assert.equal(values.product, 6);
assert.equal(values.dot_result, 14);
assert.equal(values.average, 2);
jsonEqual(values.matrix_result, [[7, 10], [15, 22]]);
jsonEqual(values.transposed, [[1, 3], [2, 4]]);
jsonEqual(values.scaled, [[2, 4], [6, 8]]);
jsonEqual(values.samples, [2, 2.5, 3]);
jsonEqual(values.clipped, [1.5, 2, 2.5]);
assert.ok(Math.abs(values.probabilities.reduce((a, b) => a + b) - 1) < 1e-12);
assert.ok(Math.abs(values.probabilities[0] - 1 / (1 + Math.exp(1))) < 1e-12);
assert.ok(Math.abs(values.norm_result - Math.sqrt(14)) < 1e-12);
assert.ok(Math.abs(values.normalized[2] - 3 / Math.sqrt(14)) < 1e-12);
assert.throws(() => run.api.compute({b: 0}), /non-finite/);
assert.throws(() => run.api.compute({u: [0, 0, 0]}), /zero vector/);
assert.throws(() => run.api.compute({u: Array(65).fill(1)}), /64/);
assert.throws(() => run.api.compute({m: [[1, 2], [3]]}), /rectangular/);
assert.throws(() => run.api.compute({a: Infinity}), /non-finite/);
run.element("control-b").value = "";
assert.equal(run.api.update().ok, false);
assert.equal(run.state.runtimeState, "error");
assert.equal(run.element("calculation-product").textContent, "—");
run.element("control-b").value = "4";
assert.equal(run.api.update().ok, true);
assert.equal(run.element("calculation-product").textContent, "8");

// Integer-valued counts stay valid when a line sweep recomputes linspace.
const stepped = boot([
  {id: "n", label: "Count", kind: "range", default: 3, min: 2, max: 6, step: 1},
  {id: "end", label: "End", kind: "number", default: 2, min: 1, max: 4, step: 1},
], {total: call("sum", call("linspace", num(0), variable("end"), variable("n")))}, [
  {id: "curve", kind: "line", title: "Count sweep", source: "total", sweep_control: "n", x_label: "Count", y_label: "Sum"},
]);
assert.equal(stepped.state.runtimeState, "ok");
assert.equal(stepped.api.compute().total, 3);
const svg = stepped.element("visualization-curve").children[0];
const polyline = svg.children.find(node => node.attrs.points);
assert.equal(polyline.attrs.points.split(" ").length, 5);

// Numeric cells, bounded resizing, toggle conversion and clearing stale views.
const editing = boot([
  {id:"weights", label:"Weights", kind:"array", default:[1,2], min:0, min_items:1, max_items:3},
  {id:"enabled", label:"Enabled", kind:"toggle", default:1, min:0, max:1, step:1},
  {id:"matrix", label:"Matrix", kind:"array", default:[[1,2],[3,4]]},
], {
  total: ["mul", call("sum",variable("weights")),variable("enabled")],
  count: call("length",variable("weights")),
  cells: variable("matrix"),
  weights_copy: variable("weights"),
}, [{id:"bars",kind:"bars",title:"Weights",source:"weights_copy",x_label:"Entry",y_label:"Value"}]);
const inputs = id => editing.element(`cells-${id}`).querySelectorAll("[data-array-cell]");
assert.equal(editing.state.runtimeState,"ok");
editing.element("add-weights").fire("click");
assert.equal(inputs("weights").length,3);
assert.equal(inputs("weights")[2].value,"0");
assert.equal(editing.element("calculation-count").textContent,"3");
assert.equal(editing.element("add-weights").disabled,true);
editing.element("add-weights").fire("click");
assert.equal(inputs("weights").length,3);
inputs("weights")[0].value="4";
editing.element("control-weights").fire("input");
assert.equal(editing.element("calculation-total").textContent,"6");
inputs("weights")[2].value="";
editing.element("control-weights").fire("input");
assert.equal(editing.state.runtimeState,"error");
assert.equal(editing.element("calculation-total").textContent,"—");
assert.equal(editing.element("visualization-bars").children[0].className,"plot-error");
assert.equal(inputs("weights")[2].attrs["aria-invalid"],"true");
editing.element("remove-weights").fire("click");
assert.equal(editing.state.runtimeState,"ok");
assert.equal(editing.element("calculation-total").textContent,"6");
editing.element("remove-weights").fire("click");
assert.equal(editing.element("remove-weights").disabled,true);
editing.element("remove-weights").fire("click");
assert.equal(inputs("weights").length,1);
assert.equal(inputs("weights")[0].value,"4");
editing.element("control-enabled").checked=false;
editing.element("control-enabled").fire("input");
assert.equal(editing.element("calculation-total").textContent,"0");
assert.equal(editing.element("value-enabled").textContent,"Off · 0");
editing.element("control-enabled").checked=true;
editing.element("control-enabled").fire("input");
assert.equal(editing.element("calculation-total").textContent,"4");
inputs("matrix")[3].value="9";
editing.element("control-matrix").fire("input");
assert.equal(editing.element("calculation-cells").textContent,"[[1, 2],\n [3, 9]]");
inputs("matrix")[1].value="";
assert.equal(editing.api.update().ok,false);
inputs("matrix")[1].value="2";
assert.equal(editing.api.update().ok,true);
assert.equal(inputs("matrix")[1].attrs["aria-invalid"],undefined);
editing.element("cells-matrix").lastElementChild.remove();
assert.equal(editing.api.update().ok,false);
editing.element("theme-toggle").fire("click");
assert.equal(editing.state.theme,"light");
assert.equal(editing.element("theme-toggle").attrs["aria-pressed"],"true");
console.log("Runtime smoke passed: shared math, numeric matrix/vector edits, bounded zero-append/trailing-remove, numeric toggles, error recovery, stale plot clearing, theme and stepped SVG sweep (simulated DOM).");
