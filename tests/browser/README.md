# Browser checks

Use the **exact renderer output**. Do not edit HTML to obtain a passing result. Serve the ignored preview directory, then open its pages in Chromium:

```text
python -m tests.create_demo --output review-out/generic-v2
python -m src.renderer --spec review-out/generic-v2/lesson.json --output review-out/saved-generic/index.html
python -m tests.science.create_previews
python -m http.server 8082 --bind 127.0.0.1 --directory review-out
```

The page math is separately compared to independent expectations in `tests/science/test_shared_core.py` at 1e-12 absolute/relative tolerances. Browser readouts use six significant digits; compare displayed values at 5e-6 absolute plus 5e-6 relative tolerance.

Observed in Codex's in-app Chromium on 3 October 2026, using renderer output from the version-2 developer fixtures:

| Page | Input/action | Expected and observed |
|---|---|---|
| Saved generic | a=-4, b=1 | y=-7 |
| Saved generic | Empty b | Result cleared; curve removed; visible error |
| Saved generic | a=4, b=2 after correction | y=10; curve restored |
| Entropy | Four equal weights | 2 bits |
| Entropy | [1,0,0,0] | 0 bits, without epsilon clipping |
| Entropy | [1,1] | 1 bit |
| Entropy | [0,0] | Visible error; bars removed |
| Entropy | [1,1,0] after correction | 1 bit; bars restored |
| Attention | Identity Q/K, scaled, V=[[10,0],[0,20]] | First weight 0.669762; first output [6.69762,6.60477] |
| Attention | Q=[[0,0],[0,0]] | Both weight rows [0.5,0.5]; both output rows [5,10] |
| Attention | Identity Q/K, unscaled comparison | First weight 0.731059 |
| Attention | Edit V to [[20,0],[0,20]] | Weights unchanged; first output [14.6212,5.37883] |
| Attention | Ragged K, then correction | Stale outputs/heatmaps cleared, then restored |
| Enzyme kinetics | S=Km=2, Vmax=10 | v=5 |
| Enzyme kinetics | S=2, Km=6, Vmax=10 | v=2.5 |
| Enzyme kinetics | Vmax=0 | v=0 with a visible constant curve |
| Enzyme kinetics | S=0 after an empty-Km edit/correction | v=0; calculation and curve recover |
| Enzyme kinetics | S=20, Km=2, Vmax=10 | v=9.09091 |
| Logistic map | r=4, x0=0.25 | [0.25,0.75,0.75,0.75,0.75] |
| Logistic map | r=4, x0=0.5 | [0.5,1,0,0,0] |
| Logistic map | r=0, x0=0.5 | [0.5,0,0,0,0] |

The observed pages produced no warning/error console logs. The generic layout was visually inspected in a narrow viewport. Numeric cell editors, a true toggle checkbox, explicit vector resizing, category/row/column role labels, and desktop/mobile review must be repeated after the UI-runtime handoff. The current baseline uses JSON text areas and a text field for the toggle.

These are authored source-backed development fixtures, **not fresh model-generated outputs**. Repeat the science/interaction checks on unmodified fresh `lesson.json` / `index.html` / trace outputs before treating the submission as ready. A generation that omits the required mechanism fails the science gate even if the page runs.

Direct `file://` navigation was blocked by the browser tool's URL policy. Served-page interaction and embedded/offline-resource checks passed; direct-file behavior with networking disconnected remains a manual Chromium check. A DOM shim or the QuickJS engine cannot prove that browser check.
