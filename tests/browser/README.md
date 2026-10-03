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

Direct `file://` navigation was blocked by the browser tool's URL policy. Served-page interaction and embedded/offline-resource checks passed. P2 manually opened `review-out/science/entropy/index.html` via `file://` with the network disconnected, changed **Outcome weights**, and confirmed that the result recalculated correctly while offline (3 October 2026). This is user-reported direct-file, network-disconnected interaction evidence for the authored entropy fixture; the exact edited values and browser version were not reported. The offline check passes for this fixture and still needs repetition on the fresh model-generated release page. A DOM shim or the QuickJS engine cannot prove that browser check.

## Fresh generated artifact review

As of 3 October 2026, no accepted fresh lesson package has been supplied to P2. Complete live model responses alone do not establish an accepted lesson. The observations above apply to authored fixtures; the expanded independent states in `tests/science/fixtures.json` have not yet been operated in a fresh page.

For each supplied package, record the generation commit/model, exact input case and source selection, `lesson.json`, `index.html`, and `trace.jsonl` paths and SHA-256 hashes. Keep those files unchanged. Verify the HTML's embedded spec equals the saved JSON and its compiled computations correspond to that spec; identify the embedded math/UI versions rather than assuming the current checkout matches. Review the trace's final outcome, requests, usage, repairs, failed/skipped checks, and output promotion. A leftover HTML page from another run is not a successful generation.

Map generated IDs to the [independent control checks](../science/README.md#independent-control-checks), then inspect the source fidelity and operate every exposed control in Chromium. Record complete inputs, precise expected values, displayed observed values, comparison tolerance, the specific action, error text, removal of stale results/views, recovery, and warning/error console logs. Include default state, legal endpoints, array-cell edits, resize preservation/zero append/removal, checkbox changes, degenerate plots, relevant labels, and desktop/narrow layout. Missing controls or a missing requested mechanism are failures, even if the available page runs.

Each review record should include:

```json
{
  "artifact_sha256": {"case.json": "...", "lesson.json": "...", "index.html": "...", "trace.jsonl": "..."},
  "generation_commit": "...",
  "browser": "Chromium version and review timestamp",
  "mechanism": "...",
  "id_mapping": {"controls": {}, "outputs": {}},
  "observations": [{"action": "...", "state": {}, "expected": {}, "observed": {}, "error": null, "recovery": null, "status": "passed/failed/not tested"}],
  "console": [],
  "offline": {"status": "not tested", "reviewer": null, "state": null, "expected": null, "observed": null},
  "limitations": []
}
```

Repeat direct-file offline interaction on the exact fresh showcase HTML: disconnect the network, open it through `file://`, record at least one complete before/after state and expected/observed recalculation, then verify the HTML hash is unchanged. Because this browser tool cannot navigate to `file://`, that part needs a user-reported Chromium check, clearly attributed with the file hash and values. The authored entropy check does not transfer to a newly generated page. Store screenshots and raw review records outside submission unless selected as necessary public showcase evidence.
