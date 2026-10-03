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

**Acceptance remains needs revision.** Fixed min_items=max_items=3 prevents outcome-count changes; the scale control preserves entropy and does not replace resizing. Generated evidence presents authored equation-transcription text as source quotation and mislocates the zero-limit claim under entropy property 2. Weight normalization needs teaching provenance, while Hmax has genuine support in [Shannon's section 6, property 2](https://people.math.harvard.edu/~ctm/home/text/others/shannon/entropy/entropy.pdf). The embedded older page uses a JSON textarea, ignores the supplied outcome labels, and cannot verify new numeric cells, resizing, or checkbox controls. The compression statement also needs lossless/memoryless qualifications or removal. An updated release page needs its own unchanged-artifact and offline checks; subsequent packages are reviewed below.

The fresh `examples/generated/logistic-map/` package was reviewed unchanged at commit **`ab9d72967e4a0a8d435cb6a641923b94e39d4da1`**. Its input uses the corrected [May section 2, equation (3)](https://ned.ipac.caltech.edu/level5/Sept01/May/May2.html). The recurrence and parameter renaming are faithful; computations feed each preceding result into the next update. Saved/embedded specs and compiled expressions agree, and both embedded math and UI match the integrated checkout. Its trace reports three requests, 3,137 completion tokens, zero reasoning tokens, and 54.24 seconds. Repairs changed an invalid line view to bars and corrected a quote-occurrence failure, preserving the declared numerical expectations.

Seven valid states passed independent core comparison at 1e-12 absolute/relative tolerance, including the nonconstant r=3,x0=0.2 trajectory; two invalid domain states failed correctly. Fifteen recorded Chromium observations passed the display tolerance, exercising both sliders, endpoints, all-zero bars, legal interior recovery, and the light/dark theme button. Five calculation disclosures opened and closed; x0 through x4 labels appeared. Range widgets held r at 4 after an upward step and x0 at 0 after a downward step. They expose no blank-text edit, so invalid calculation errors were checked in the core rather than claimed as browser observations. No warning/error console logs were observed, and desktop/narrow control layouts had no horizontal overflow. Direct-file offline interaction has not been reported for this logistic package.

| Fresh logistic state | Independent trajectory, initial state plus four updates | Chromium trajectory |
|---|---|---|
| r=4,x0=0.5 | [0.5,1,0,0,0] | [0.5,1,0,0,0] |
| r=4,x0=0.25 | [0.25,0.75,0.75,0.75,0.75] | [0.25,0.75,0.75,0.75,0.75] |
| r=4,x0=0 | [0,0,0,0,0] | [0,0,0,0,0] |
| r=4,x0=1 | [1,0,0,0,0] | [1,0,0,0,0] |
| r=2,x0=0.5 | [0.5,0.5,0.5,0.5,0.5] | [0.5,0.5,0.5,0.5,0.5] |
| r=0,x0=0.5 | [0.5,0,0,0,0] | [0.5,0,0,0,0] |
| r=3,x0=0.2 | [0.2,0.48,0.7488,0.56429568,0.7375981966000128] | [0.2,0.48,0.7488,0.564296,0.737598] |

**Logistic acceptance remains needs revision.** The first exploration incorrectly describes the r=4,x0=0.5 transient to the fixed point zero as a longer cycle; r=2,x0=0.5 is already a fixed point. A teaching paragraph still describes a line plot after repair changed the view to bars. The equation evidence displays an authored ASCII transcription as a paper quotation without preserving its transcription label. These findings do not change the passing numerical expectations. Exact hashes, inputs, expected/observed values, and findings are in [the logistic review](reviews/logistic-map.json).

Fresh `examples/generated/attention/` was reviewed unchanged at **`9b6609be7c5414ffd0b16624283e7c1a1e750541`**. Its mechanism matches [Vaswani et al., section 3.2.1, equation (1)](https://arxiv.org/html/1706.03762v7): Q times K transpose, division by the actual feature count's square root, row softmax, then multiplication by V. Saved and embedded specs/expressions agree; both embedded math and UI match the reviewed checkout. The trace reports two requests, 3,390 completion tokens, zero reasoning tokens, and 56.74 seconds. The first candidate used a vector-only row-sum operator on a matrix; component repair replaced it with matrix multiplication, preserving declared expectations.

Seven valid states passed independent core comparisons, and a third K column was correctly rejected by the fixed-shape control domain. All 24 recorded Chromium observations passed: all 12 Q/K/V cells were edited independently, distinct values produced the expected weighted outputs, zero queries and identical keys produced uniform weights, negative entries remained legal, and large finite scores saturated softmax stably. Blank/nonfinite edits cleared all six readouts and both heatmaps; correction restored them without reload. All six calculation disclosures opened and closed. Theme changes preserved calculations, and the initial dark theme was restored. Query/key labels appeared in both heatmaps; desktop/narrow layouts had no horizontal overflow. No warning/error console logs were observed.

| Fresh attention state | Independent expectation | Chromium observation |
|---|---|---|
| Q=K=identity, V=[[10,0],[0,20]] | First weights [0.6697615493,0.3302384507]; first output [6.6976154933,6.6047690135] | [0.669762,0.330238]; [6.69762,6.60477] |
| Q all zeros, K=identity, same V | Both weight rows [0.5,0.5]; both output rows [5,10] | Exact displayed agreement |
| K=[[1,0],[1,0]], Q=identity, same V | Both weight rows [0.5,0.5]; both output rows [5,10] | Exact displayed agreement |
| Q=diag(1000), K=identity, same V | Diagonal weights round to 1; off-diagonal weights about 8.0802875164e-308 | 1 and 8.08029e-308; finite outputs and both heatmaps |
| Blank/nonfinite Q cell, then correct to 1 | Clear six results/two views, then recover scaled identity case | Visible finite-number error, six em dashes/zero SVGs, then six results/two SVGs |

**Attention acceptance remains needs revision.** Exploration 3 requests three feature columns despite the fixed 2×2 inputs; no resize or advanced editor exists. The stated limitation wrongly attributes weak softmax saturation to the small matrix size; the diag(1000) observation directly contradicts it. The equation-transcription evidence also loses its supplied label. No scientific checkbox or unscaled mode is generated, so this package cannot establish fresh scaling-checkbox interaction; its input focus requested raw/scaled scores rather than a toggle. Full states, hashes, errors and findings are in [the attention review](reviews/attention.json). Direct-file offline interaction was not checked for this package. Entropy resizing and a revised showcase's offline check remain outstanding.

Fresh `examples/generated/enzyme-kinetics/` was reviewed unchanged at **`9b6609be7c5414ffd0b16624283e7c1a1e750541`**. The source locator is [the Johnson/Goody translation of Michaelis and Menten, equations (3)–(4), PDF page 11](https://www.chem.uwec.edu/Chem352_F18/pages/readings/media/Michaelis_%26_Menton_1913.pdf). The modern Vmax=C*Phi and Km=k renaming is explicitly presented as teaching notation. Equation (4)'s V is the fractional rate rather than Vmax. The generated initial-rate equation is faithful, without claiming a full reaction simulation or reproduction of the invertase experiments. Saved/embedded spec and expressions agree, and both embedded math/UI match the reviewed checkout. The trace reports one request, 2,005 completion tokens, zero reasoning tokens and 44.123 seconds, with no repair.

Seven legal core states passed independent comparisons; Km=0 and negative substrate were rejected. All 19 Chromium observations passed at the display tolerance, covering all three sliders, legal minima/maxima, proportional concentration changes, endpoint clamping, theme changes and return to an interior state. All four disclosures opened/closed. The Vmax domain is 0.1–10, excluding the independent Vmax=0/20 fixture states; generated bounds were kept unchanged. Sliders expose no blank editor, so invalid core errors are not claimed as browser observations. No warning/error console logs were observed. Desktop and narrow controls/curve were visually inspected, with no horizontal overflow; the viewport override was reset.

| Fresh enzyme state | Independent expected rate/fraction | Chromium observed |
|---|---|---|
| S=2,Km=2,Vmax=10 | 5 / 0.5 | 5 / 0.5 |
| S=6,Km=2,Vmax=10 | 7.5 / 0.75 | 7.5 / 0.75 |
| S=2,Km=6,Vmax=10 | 2.5 / 0.25 | 2.5 / 0.25 |
| S=2,Km=2,Vmax=0.1 | 0.05 / 0.5 | 0.05 / 0.5 |
| S=0,Km=2,Vmax=10 | 0 / 0 | 0 / 0 |
| S=20,Km=2,Vmax=10 | 100/11 / 10/11 | 9.09091 / 0.909091 |
| S=2,Km=0.1,Vmax=10 | 200/21 / 20/21 | 9.52381 / 0.952381 |
| S=2,Km=10,Vmax=10 | 5/3 / 1/6 | 1.66667 / 0.166667 |
| S=4,Km=4,Vmax=10 | 5 / 0.5 | 5 / 0.5 |

The actual SVG's 48 polyline samples and current marker were independently checked at every recorded state. Substrate was recovered from each observed x position on the 0–20 concentration axis; the independent rate oracle supplied the expected velocity and corresponding y position on the observed axis rectangle. All samples/markers agreed within 1e-9 SVG coordinate units; five x/y axis ticks agreed at the display tolerance. The curve begins at rate zero and its S=20 endpoint remains below Vmax. Full raw points, inputs, expectations, observed values and comparison errors are retained in [the enzyme review](reviews/enzyme-kinetics.json).

**Enzyme acceptance remains needs revision.** The evidence block loses the equation-transcription label from the supplied input. The Km/Vmax readout headings imply reference lines that the SVG does not contain: only the curve, marker, axes and grid are drawn. Rename those readouts as parameter/reference values, or generate supported reference views. Direct-file offline interaction has not been checked for this package. All four supplied packages have now received independent source/math and available-control review, totaling 75 recorded Chromium observations. No package is accepted yet; the documented findings and fresh resizing/checkbox/revised-offline checks remain outstanding.

For each supplied package, record the publishing commit/model, exact input case and source selection, `lesson.json`, `index.html`, and `trace.jsonl` paths and SHA-256 hashes. Keep those files unchanged. Verify the HTML's embedded spec equals the saved JSON and its compiled computations correspond to that spec; identify the embedded math/UI versions rather than assuming the current checkout matches. Review the trace's final outcome, requests, usage, repairs, failed/skipped checks, and output promotion. A leftover HTML page from another run is not a successful generation.

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
