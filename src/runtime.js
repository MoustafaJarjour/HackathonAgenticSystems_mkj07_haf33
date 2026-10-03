/* Browser controls and SVG views. Mathematics lives in math_runtime.js. */
(() => {
  "use strict";
  const {spec, compiled} = JSON.parse(document.getElementById("lesson-data").textContent);
  const MAX_OPERATIONS = 100000;
  const SVG_NS = "http://www.w3.org/2000/svg";
  const accent = "var(--accent)", muted = "var(--muted)";
  const fail = message => { throw new Error(message); };
  const budget = () => ({remaining: MAX_OPERATIONS});
  function number(x) { if (typeof x !== "number" || !Number.isFinite(x)) fail("A calculation produced a non-finite number or invalid value."); return x; }
  function vector(value) { if (!Array.isArray(value) || !value.length || value.some(x => typeof x !== "number")) fail("This view requires a numeric vector."); return value; }
  function matrix(value) { if (!Array.isArray(value) || !value.length || !Array.isArray(value[0]) || value.some(row => !Array.isArray(row) || row.length !== value[0].length)) fail("This view requires a rectangular numeric matrix."); value.forEach(vector); return value; }
  function controlValues(overrides = {}) {
    const state = Object.fromEntries(spec.controls.map(c => [c.id, c.default]));
    Object.assign(state, overrides);
    return globalThis.PTPMath.validateState(spec, state);
  }
  function compute(overrides = {}, b = budget()) {
    return globalThis.PTPMath.compute(spec, compiled, controlValues(overrides), {maxOperations:b.remaining});
  }
  function formatted(value) {
    if (Array.isArray(value)) return "[" + value.map(formatted).join(Array.isArray(value[0]) ? ",\n " : ", ") + "]";
    const n = number(value);
    return String(Number(n.toPrecision(6)));
  }
  function svgElement(name, attrs = {}, text) {
    const node = document.createElementNS(SVG_NS, name);
    for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, String(value));
    if (text !== undefined) node.textContent = String(text);
    return node;
  }
  function plotRoot(vis) {
    const svg = svgElement("svg", {viewBox:"0 0 800 340", role:"img", "aria-label":vis.title});
    svg.append(svgElement("title", {}, vis.title));
    return svg;
  }
  function domain(values, includeZero = false) {
    let lo = Math.min(...values), hi = Math.max(...values);
    if (includeZero) {lo = Math.min(0, lo); hi = Math.max(0, hi);}
    if (lo === hi) {const padding = Math.max(1, Math.abs(lo) * .1); lo -= padding; hi += padding;}
    number(lo); number(hi); number(hi - lo);
    return [lo, hi];
  }
  function axes(svg, vis, xDomain, yDomain, categorical = false) {
    const left=70, top=25, width=700, height=230;
    const x = n => left + (n - xDomain[0]) / (xDomain[1] - xDomain[0]) * width;
    const y = n => top + height - (n - yDomain[0]) / (yDomain[1] - yDomain[0]) * height;
    svg.append(svgElement("path", {d:`M${left},${top}V${top+height}H${left+width}`, fill:"none", stroke:muted}));
    for (let i=0; i<=4; i++) {
      const t=i/4, value=(1-t)*yDomain[0]+t*yDomain[1];
      svg.append(svgElement("line", {x1:left,y1:y(value),x2:left+width,y2:y(value),stroke:"var(--line)"}));
      svg.append(svgElement("text", {x:left-9,y:y(value)+4,"text-anchor":"end","font-size":11,fill:muted}, formatted(value)));
      if (!categorical) {
        const xv=(1-t)*xDomain[0]+t*xDomain[1];
        svg.append(svgElement("text", {x:x(xv),y:top+height+22,"text-anchor":"middle","font-size":11,fill:muted}, formatted(xv)));
      }
    }
    svg.append(svgElement("text", {x:left+width/2,y:325,"text-anchor":"middle","font-size":13,fill:muted}, vis.x_label));
    svg.append(svgElement("text", {x:17,y:top+height/2,transform:`rotate(-90 17 ${top+height/2})`, "text-anchor":"middle","font-size":13,fill:muted}, vis.y_label));
    return {x,y,left,top,width,height};
  }
  function linePlot(vis, values, outputs, b) {
    const control = spec.controls.find(item => item.id === vis.sweep_control);
    if (!control || control.kind === "array" || control.min === undefined || control.max === undefined || control.min >= control.max) fail("Line plots need a scalar sweep control with distinct min/max bounds.");
    const xs=[], ys=[];
    // Respect a finite step grid, including integer-valued algorithm parameters.
    const intervals=(control.max-control.min)/control.step;
    const onGrid=Number.isFinite(intervals)&&intervals>=1;
    const gridEnd=onGrid?Math.floor(intervals):0;
    for (let i=0; i<48; i++) {
      const t=i/47;
      let k=onGrid?Math.round(t*gridEnd):0;
      let value=onGrid?control.min+k*control.step:(1-t)*control.min+t*control.max;
      // Rounding can put a grid point just beyond max; use the prior valid point.
      if(onGrid&&value>control.max) {k=Math.max(0,k-1);value=control.min+k*control.step;}
      if(value<control.min||value>control.max) fail("Sweep sample lies outside the control bounds.");
      if(xs.length&&value===xs[xs.length-1]) continue;
      xs.push(value); ys.push(number(compute({...values,[control.id]:value}, b)[vis.source]));
    }
    if(xs.length<2) fail("Line plots need at least two distinct valid sweep settings.");
    const current = number(outputs[vis.source]);
    const svg=plotRoot(vis), a=axes(svg,vis,[control.min,control.max],domain([...ys,current]));
    const points=xs.map((value,i) => `${number(a.x(value))},${number(a.y(ys[i]))}`).join(" ");
    svg.append(svgElement("polyline", {points,fill:"none",stroke:accent,"stroke-width":2.5}));
    const marker=svgElement("circle", {cx:number(a.x(values[control.id])),cy:number(a.y(current)),r:5,fill:accent,stroke:"white","stroke-width":2});
    marker.append(svgElement("title", {}, `${control.label}: ${formatted(values[control.id])}; result: ${formatted(current)}`));
    svg.append(marker); return svg;
  }
  function barsPlot(vis, outputs) {
    const values=vector(outputs[vis.source]), svg=plotRoot(vis), a=axes(svg,vis,[0,values.length],domain(values,true),true);
    const cell=a.width/values.length, base=a.y(0);
    values.forEach((value,i) => {
      const top=Math.min(base,a.y(value)), height=Math.abs(base-a.y(value));
      const rect=svgElement("rect",{x:a.left+i*cell+cell*.1,y:top,width:cell*.8,height,fill:accent});
      const label=vis.labels?.[i]??String(i+1);
      rect.append(svgElement("title",{},`${label}: ${formatted(value)}`)); svg.append(rect);
      svg.append(svgElement("text",{x:a.left+(i+.5)*cell,y:a.top+a.height+22,"text-anchor":"middle","font-size":11,fill:muted},label));
      if(values.length<=12) svg.append(svgElement("text",{x:a.left+(i+.5)*cell,y:value>=0?top-5:top+height+14,"text-anchor":"middle","font-size":11,fill:accent},formatted(value)));
    });
    return svg;
  }
  function heatmapPlot(vis, outputs) {
    const values=matrix(outputs[vis.source]), flat=values.flat(), [lo,hi]=domain(flat), svg=plotRoot(vis);
    const left=85, top=25, width=625, height=245, cellWidth=width/values[0].length, cellHeight=height/values.length;
    values.forEach((row,i) => {
      const rowLabel=vis.row_labels?.[i]??String(i+1);
      svg.append(svgElement("text",{x:left-12,y:top+(i+.5)*cellHeight+4,"text-anchor":"end","font-size":11,fill:muted},rowLabel));
      row.forEach((value,j) => {
        const t=(value-lo)/(hi-lo), fill=`hsl(192 66% ${94-t*61}%)`;
        const rect=svgElement("rect",{x:left+j*cellWidth,y:top+i*cellHeight,width:cellWidth,height:cellHeight,fill,stroke:"white","stroke-width":1});
        rect.append(svgElement("title",{},`Row ${rowLabel}, column ${vis.column_labels?.[j]??j+1}: ${formatted(value)}`));svg.append(rect);
        if(values.length<=8&&row.length<=8) svg.append(svgElement("text",{x:left+(j+.5)*cellWidth,y:top+(i+.5)*cellHeight+4,"text-anchor":"middle","font-size":12,fill:t>.65?"white":"#203046"},formatted(value)));
      });
    });
    values[0].forEach((_,j) => svg.append(svgElement("text",{x:left+(j+.5)*cellWidth,y:top+height+18,"text-anchor":"middle","font-size":11,fill:muted},vis.column_labels?.[j]??j+1)));
    svg.append(svgElement("text",{x:left+width/2,y:320,"text-anchor":"middle","font-size":13,fill:muted},vis.x_label));
    svg.append(svgElement("text",{x:20,y:top+height/2,transform:`rotate(-90 20 ${top+height/2})`,"text-anchor":"middle","font-size":13,fill:muted},vis.y_label));
    svg.append(svgElement("text",{x:785,y:30,"text-anchor":"end","font-size":10,fill:muted},`High ${formatted(hi)}`));
    svg.append(svgElement("text",{x:785,y:48,"text-anchor":"end","font-size":10,fill:muted},`Low ${formatted(lo)}`));
    return svg;
  }
  function readNumber(input, label) {
    input.removeAttribute("aria-invalid");
    if(input.value.trim()==="" || !Number.isFinite(Number(input.value))) {
      input.setAttribute("aria-invalid", "true");
      fail(`${label}: enter a finite number in every field.`);
    }
    return Number(input.value);
  }
  function arrayInputs(control) {
    return [...document.getElementById(`cells-${control.id}`).querySelectorAll("[data-array-cell]")];
  }
  function resizeVector(control, delta) {
    const cells=document.getElementById(`cells-${control.id}`), inputs=arrayInputs(control);
    const minimum=control.min_items??control.default.length, maximum=control.max_items??control.default.length;
    const length=inputs.length+delta;
    if(length<minimum || length>maximum) return;
    if(delta<0) cells.lastElementChild.remove();
    else {
      const label=document.createElement("label"), index=document.createElement("span"), input=document.createElement("input");
      label.className="array-cell";index.textContent=String(length);
      input.type="number";input.step="any";input.value="0";
      input.setAttribute("data-array-cell", "");
      input.setAttribute("aria-label", `${control.label}, entry ${length}`);
      input.setAttribute("aria-describedby", `meaning-${control.id}`);
      label.append(index,input);cells.append(label);
    }
    document.getElementById(`shape-${control.id}`).textContent=`${length} entries`;
    document.getElementById(`remove-${control.id}`).disabled=length<=minimum;
    document.getElementById(`add-${control.id}`).disabled=length>=maximum;
    update();
  }
  function readControls() {
    const values=Object.create(null);
    for(const control of spec.controls) {
      const input=document.getElementById(`control-${control.id}`);
      if(control.kind==="array") {
        const entries=arrayInputs(control).map(cell=>readNumber(cell,control.label));
        if(Array.isArray(control.default[0])) {
          const columns=control.default[0].length;
          if(entries.length!==control.default.length*columns) fail(`${control.label}: matrix shape must remain fixed.`);
          values[control.id]=Array.from({length:control.default.length},(_,row)=>entries.slice(row*columns,(row+1)*columns));
        } else values[control.id]=entries;
      } else if(control.kind==="toggle") {
        values[control.id]=input.checked?1:0;
      } else {
        values[control.id]=readNumber(input,control.label);
      }
    }
    return controlValues(values);
  }
  function update() {
    const status=document.getElementById("runtime-status");
    try {
      const values=readControls(), b=budget(), outputs=compute(values,b);
      const plots=spec.visualizations.map(vis => {
        try {
          switch(vis.kind) {
            case "line": return linePlot(vis,values,outputs,b);
            case "bars": return barsPlot(vis,outputs);
            case "heatmap": return heatmapPlot(vis,outputs);
            default: fail(`Unsupported visualization: ${vis.kind}`);
          }
        } catch(error) {fail(`${vis.title}: ${error.message}`);}
      });
      for(const control of spec.controls) document.getElementById(`value-${control.id}`).textContent=control.kind==="array"?"":control.kind==="toggle"?(values[control.id]===1?"On · 1":"Off · 0"):formatted(values[control.id]);
      for(const item of spec.computations) if(item.show) document.getElementById(`calculation-${item.id}`).textContent=formatted(outputs[item.id]);
      spec.visualizations.forEach((vis,i) => document.getElementById(`visualization-${vis.id}`).replaceChildren(plots[i]));
      status.textContent="Calculations and visualizations updated.";status.className="";
      document.documentElement.dataset.runtimeState="ok";
      return {ok:true,outputs};
    } catch(error) {
      status.textContent=`Cannot calculate: ${error.message}`;status.className="error";
      for(const control of spec.controls) document.getElementById(`value-${control.id}`).textContent="";
      for(const item of spec.computations) if(item.show) document.getElementById(`calculation-${item.id}`).textContent="—";
      for(const vis of spec.visualizations) {
        const target=document.getElementById(`visualization-${vis.id}`);
        target.replaceChildren();const p=document.createElement("p");p.className="plot-error";p.textContent="Plot unavailable until the calculation error is corrected.";target.append(p);
      }
      document.documentElement.dataset.runtimeState="error";
      return {ok:false,error:error.message};
    }
  }
  // Pure compute and update hooks support lightweight Chromium smoke tests.
  window.PTP=Object.freeze({compute:overrides=>compute(overrides),update});
  for(const control of spec.controls) {
    document.getElementById(`control-${control.id}`).addEventListener("input",update);
    if(control.kind==="array"&&!Array.isArray(control.default[0])&&(control.min_items??control.default.length)<(control.max_items??control.default.length)) {
      document.getElementById(`add-${control.id}`).addEventListener("click",()=>resizeVector(control,1));
      document.getElementById(`remove-${control.id}`).addEventListener("click",()=>resizeVector(control,-1));
    }
  }
  const themeToggle=document.getElementById("theme-toggle");
  if(themeToggle) themeToggle.addEventListener("click",()=>{
    const light=document.documentElement.dataset.theme!=="light";
    document.documentElement.dataset.theme=light?"light":"dark";
    themeToggle.textContent=light?"Dark theme":"Light theme";
    themeToggle.setAttribute("aria-pressed", String(light));
  });
  update();
})();
