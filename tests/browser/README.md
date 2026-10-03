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

The first fresh package, `examples/generated/entropy-v1/`, was reviewed unchanged at commit **`d944f28c8f76422f76a6e92e940883fb4847274f`** on 3 October 2026. Its trace reports CLI success using `deepseek/deepseek-v4.1-flash`: one request, 3,674 prompt tokens, 2,727 completion tokens, zero reasoning tokens, and 14.327 seconds. The embedded UTF-8 spec equals `lesson.json`, compiled expressions match, and the embedded math core matches the reviewed core. Its UI matches the earlier `3bcb827` runtime, rather than the new numeric-editor integration in `6512a95`.

Independent core comparisons passed for seven valid three-outcome states. Four invalid/out-of-size core states failed as expected. Chromium passed 17 recorded observations at the six-digit display tolerance: the initial uniform distribution, certain/two-positive/uneven distributions, editing all three weight positions, both scale endpoints, maximum legal weights, eight invalid edits, and recovery without reload. All five calculation disclosures opened and closed. Invalid inputs cleared all five readouts and removed the plot; correction restored them. No warning/error console logs were observed. Controls and results were inspected at desktop and narrow viewports without horizontal overflow; the temporary viewport override was reset.

| Fresh entropy action | Independent expected H | Chromium observed H |
|---|---|---|
| weights=[1,1,1], scale=1 | log2(3)=1.584962500721156 | 1.58496 |
| weights=[1,0,0], scale=1 | 0 | 0 |
| weights=[1,1,0], scale=1 | 1 | 1 |
| weights=[1,3,0] or [0,1,3], scale=1 | 0.8112781244591328 | 0.811278 |
| weights=[1,3,0], scale=0.1 then 10 | 0.8112781244591328 at both endpoints | 0.811278 at both endpoints |
| weights=[100,100,100], scale=1 | log2(3)=1.584962500721156 | 1.58496 |
| Zero total, negative/over-limit entry, wrong length/shape, malformed/empty JSON | Error, cleared values and plot | Visible error; five cleared readouts; zero SVGs |
| Correct to weights=[1,3,0], scale=10 | 0.8112781244591328 and restored plot | 0.811278 and one restored SVG |

P2 manually opened this **fresh** `entropy-v1/index.html` through `file://` with the network disconnected, kept scale=1, changed weights from [1,1,1] to [1,3,0], and confirmed H changed from 1.58496 to 0.811278 bits. This is user-reported offline evidence; Chromium version was not supplied. The reviewed Windows HTML SHA-256 is `b545b7460ab7e300746cddc088b6ed21b78cae719cfed8d6cc311071c10cf14f`. Git's LF blob and Windows CRLF checkout hashes are both recorded in [the full review](reviews/entropy-v1.json).

**Acceptance remains needs revision.** Fixed min_items=max_items=3 prevents outcome-count changes; the scale control preserves entropy and does not replace resizing. Generated evidence presents authored equation-transcription text as source quotation and mislocates the zero-limit claim under entropy property 2. Weight normalization needs teaching provenance, while Hmax has genuine support in [Shannon's section 6, property 2](https://people.math.harvard.edu/~ctm/home/text/others/shannon/entropy/entropy.pdf). The embedded older page uses a JSON textarea, ignores the supplied outcome labels, and cannot verify new numeric cells, resizing, or checkbox controls. The compression statement also needs lossless/memoryless qualifications or removal. The other three fresh packages have not been reviewed. An updated release page needs its own unchanged-artifact and offline checks.

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
