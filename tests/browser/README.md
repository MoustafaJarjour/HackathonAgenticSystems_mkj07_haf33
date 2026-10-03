# Browser checks

Entropy-polished at `61ddce2` passed [16 exact-output observations](reviews/entropy-polished.json) and 140 independent numerical checks; only corrected scale-title text differs from its reviewed parent. Two new Hubble pages received [16 observations each](reviews/hubble-generalization-run01.json), with the [second report](reviews/hubble-generalization-run02.json) retaining the same zero-distance ratio and auto-scaled-line findings. Costs and source limitations are in [the new-paper experiment](../science/GENERALIZATION.md). These new pages are not accepted showcases and have no direct-file offline confirmation.

Current showcase evidence is indexed in [the generated lesson table](../../examples/generated/README.md). The records below identify earlier original/revised packages by exact hashes. The final resizable entropy review adds nine served-Chromium observations and five user-reported direct-file offline steps; the fresh attention checkbox and three final enzyme slider states have separate user-reported offline checks. P2 completed the final three-page recheck: 89 observations passed. These evidence scopes are kept separate.


Use the **exact renderer output**. Do not edit HTML to obtain a passing result. Serve the ignored preview directory, then open its pages in Chromium:

```text
python -m tests.create_demo --output review-out/generic-v2
python -m src.renderer --spec review-out/generic-v2/lesson.json --output review-out/saved-generic/index.html
python -m tests.science.create_previews
python -m http.server 8082 --bind 127.0.0.1 --directory review-out
```

The page math is separately compared to independent expectations in `tests/science/test_shared_core.py` at 1e-12 absolute/relative tolerances. Browser readouts use six significant digits; compare displayed values at 5e-6 absolute plus 5e-6 relative tolerance.

## Final showcase recheck at 17c2dbd

On 3 October 2026, P2 reviewed the exact unchanged packages at **`17c2dbded568be3ccc0feba4bdbd52a0135843b5`** in Codex's in-app Chromium, served from localhost. All **89 browser observations** passed independent readout/error comparisons: 32 entropy, 34 attention and 23 enzyme. The exact embedded configurations also passed **116 independent core checks**, including expected domain failures, at 1e-12 absolute/relative tolerance. All 18 package files, including ancestor lessons and traces, still match that commit after normalizing Windows checkout line endings. P2 made no model calls and changed no generated files.

| Exact package/action | Independent expected | Chromium observed |
|---|---|---|
| Entropy: four equal weights, append zero | H=2 unchanged; Hmax=log2(5) | H=2; Hmax=2.32193; retained [1,1,1,1,0] |
| Entropy: remove to two, append zeros through six | H=1 throughout; Hmax=log2(n) | H=1 for n=2–6; Hmax ends at 2.58496; removal/add disabled at respective bounds |
| Entropy: six equal weights | H=Hmax=log2(6) | Both 2.58496; each of six cells independently edited and checked |
| Entropy: [1,3,0,0,0,0], scale=0.1 then 10 | H=0.8112781244591328 at both; scaled totals 0.4 then 40 | H=0.811278 at both; totals 0.4 and 40 |
| Entropy: zero total, negative/over-limit, blank/nonfinite edit; correct to uneven weights | Visible error, six cleared readouts and zero SVGs; valid results/two plots recover | All error/recovery pairs passed without reload |
| Attention: identity Q/K, checkbox on then off | First weight 0.6697615493 then 0.7310585786; d_k=2 | 0.669762 then 0.731059; d_k=2; checking restores scaled state |
| Attention: V=[[10,0],[0,5]], scaled then unscaled | First output [6.6976154933,1.6511922534] then [7.3105857863,1.3447071068] | [6.69762,1.65119] then [7.31059,1.34471] |
| Attention: all 12 matrix cells, zero queries, identical keys, legal negatives and Q=K=diag(10,10) | Independent matrix product/row softmax; uniform weights for equal scores; stable saturation at legal bounds | All calculations and both heatmaps passed |
| Attention: blank/nonfinite query, Q=11 or V=-11; correct to legal state | Six cleared readouts and zero SVGs; calculation and both heatmaps recover | All error/recovery pairs passed |
| Enzyme: S=Km=2,Vmax=10; S=6; Km=6 with S=2 | Rate/fraction 5/0.5; 7.5/0.75; 2.5/0.25 | Exact displayed values agree |
| Enzyme: S=2,Km=2,Vmax=10, double both S and Km | Current rate/fraction stay 5/0.5; fixed absolute scan changes | Current 5/0.5 preserved; scan changes from [1.11111,2,3.33333,5,6.66667,8] to [0.588235,1.11111,2,3.33333,5,6.66667] |
| Enzyme: every slider minimum/maximum and attempted outward keyboard step | Range widgets hold declared bounds; legal interior recalculates | All six endpoint clamp attempts and return to S=Km=2,Vmax=10 passed |

Each enzyme observation retains the actual 48 polyline samples, current marker and six scan bars. Coordinates were compared independently to v=Vmax*S/(Km+S) at 1e-9 SVG units; labels/readouts use the display tolerance. Scan x labels are the fixed absolute concentrations **0.25,0.5,1,2,4,8**, with the axis “Substrate concentration S”. No readout implies an absent Km/Vmax reference line. The hidden `s_scan` computation is not a missing visible readout. Sliders expose no blank numeric editor, so enzyme invalid-domain failures are core evidence; browser evidence records prevention at widget bounds.

Every theme button and every calculation disclosure was operated. All disclosure open/close states matched; no warning/error console messages were observed. Desktop and narrow screenshots were inspected, with no horizontal overflow at actual viewport widths 1164 and 355 pixels. Narrow SVG text is smaller; numerical readouts remain separately available. Temporary viewport overrides were reset.

Source fidelity and corrected explanations pass for the stated teaching mechanisms. Attention uses its actual two-feature dimension, identifies the unscaled mode as a teaching comparison, and removes the unreachable third-column/false saturation statements. Entropy marks weight normalization as a teaching construction and handles zero probabilities exactly. Enzyme distinguishes the historical notation from general modern Km. **One minor entropy wording finding remains:** its chart title says “larger total” when c<1 makes the total smaller. Prefer “changed total”; calculations are correct and the generated page was left unchanged.

| HTML | Git LF SHA-256 | Reviewed Windows CRLF SHA-256 |
|---|---|---|
| entropy-showcase/index.html | `735096b0db42773c0d979c05f47e5b7a110606919bf7a2e8357826e31d3eb487` | `cabf213eee302dcaf498f52a3184d75f2919c272c1269a57b46e2585410ba4b2` |
| attention-showcase/index.html | `c491117d7551700d055614f6ecdc0c6c3369432d8f2030be806a80542085fc0c` | `e25e85741c3702dc1597b54d64248b9838cbefb8a3fcf2d98a4993cf581804f5` |
| enzyme-showcase/index.html | `62db1e7fa59b04060c16297a1e86292304a930d9dff3187819bcd97c5c1432d3` | `ba19478b449f0be510c9f358c5d16d8b951d10b4be9a7473f2effb29bfc02c21` |

Complete inputs, expectations, observations, errors, recovery, control metadata, source findings and all file hashes are in the [entropy](reviews/entropy-showcase.json), [attention](reviews/attention-showcase.json) and [enzyme](reviews/enzyme-showcase.json) records. Entropy is a fresh CLI generation: two requests, 31.632 seconds. Attention retains its original CLI trace (three requests, 26.25 seconds), first live-repair trace (one request, 5.266 seconds), and final live-repair trace (one request, 2.593 seconds). Enzyme retains its original CLI trace (two requests, 39.587 seconds) and final live-repair trace (one request, 2.05 seconds). All six traces finish successfully; recorded response usage matches their finish totals. Final attention/enzyme traces set `fresh_cli_generation=false`. These separate stages do not establish one new CLI execution within a cumulative budget; attention's wall-clock lineage includes inspection delays.

Updated user reports are retained in [entropy offline evidence](reviews/entropy-showcase-user.json), [attention offline evidence](reviews/attention-showcase-user.json), and [enzyme offline evidence](reviews/enzyme-showcase-user.json). The exact entropy-showcase file passed direct-file, network-disconnected interaction. Attention's offline check covered its earlier auto-reviewed page; the final teaching repairs preserved math and controls, but this does not establish an exact-final-file offline check. The exact final enzyme-showcase file passed three offline states: S=Km=2,Vmax=1 gives v=0.5, Vmax=2 gives v=1, and S=0 gives v=0. The browser tool blocks `file://`, so these checks are attributed to the user. P1 reports Python 3.11 with 51 passing tests and fresh CLI traces; P2's additional suite run used Python 3.12. Logistic-reviewed is already accepted and was not changed or rechecked in this pass. The separate entropy-polished title repair has no direct-file offline confirmation.

## Historical authored-fixture review

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

**Original enzyme acceptance remains needs revision.** The evidence block loses the equation-transcription label from the supplied input. The Km/Vmax readout headings imply reference lines that the SVG does not contain: only the curve, marker, axes and grid are drawn. Rename those readouts as parameter/reference values, or generate supported reference views. Direct-file offline interaction has not been checked for this package. All four original CLI packages received independent source/math and available-control review, totaling 75 recorded Chromium observations. Their original files and recorded findings remain unchanged; separate repairs are reviewed below.

## Live model repair follow-up

P1 published four separate `*-reviewed` packages at **`781b369186afe61362dcefc84924c3944f2ceb92`**. Each trace identifies `mode=saved_model_candidate_live_repair` and `fresh_cli_generation=false`: an earlier saved model candidate was repaired through one live model request and rendered again. This is exact-output review of a traced model repair, not proof of a new full CLI generation. The repair reports do not overwrite the original packages/reviews. Embedded specs, compiled expressions, math and UI agree with each saved package/current checkout; original expressions and numerical cases are preserved. P2 reran all 37 original independent core observations against these exact embedded configurations, including expected domain/shape failures.

P2 then operated every exposed scientific input and the theme button in each repaired page. All 79 further observations passed at the six-digit display tolerance: 18 entropy, 24 attention, 23 enzyme and 14 logistic. Blank/illegal entropy weights and blank/nonfinite query cells cleared stale readouts/SVGs; correction restored them. Range widgets clamped the tested bounds, and legal interior recovery recalculated normally. All calculation disclosures opened/closed. Temporary desktop/narrow viewport checks had no horizontal overflow and were reset; no warning/error console logs were observed. Enzyme's actual 48 polyline samples, current marker and axis ticks were compared independently again at every recorded state. Narrow SVG text is smaller than desktop text; numerical readouts remain available separately.

| Repaired package | Resolved findings | Remaining scope/findings |
|---|---|---|
| [logistic-reviewed](reviews/logistic-reviewed.json) | Fixed-point/transient exploration, bar-chart description and transcription labeling | Accepted for stated source/math/browser scope and user-reported offline page interaction. Four updates only; no chaos/long-run claim. Not a new CLI run. |
| [attention-reviewed](reviews/attention-reviewed.json) | Reachable fixed-shape exploration, correct two-key saturation limitation and transcription labeling | Accepted for stated fixed-matrix science/browser scope. No learned projections/masking/multi-head model, scientific checkbox or unscaled mode. |
| [entropy-reviewed](reviews/entropy-reviewed.json) | Weight normalization marked as teaching construction; transcription/zero locator corrected; compression claim qualified; new numeric cells and Outcome 1/2/3 labels | Outcome count remains fixed at three; no resizing. Offline evidence for entropy-v1 does not transfer to this changed HTML. |
| [enzyme-reviewed](reviews/enzyme-reviewed.json) | Supplied-transcription label and distinction between historical k and general modern Km | Readout headings still imply reference lines absent from the SVG. Vmax=0/20 remain outside the unchanged range. No direct-file interaction claimed. |

The human P2 reviewer opened **`examples/generated/logistic-reviewed/index.html` via `file://` with the network disconnected**, kept r=4 and changed x0 from 0.5 to 0.25. They confirmed the displayed trajectory changed from [0.5,1,0,0,0] to [0.25,0.75,0.75,0.75,0.75], matching the independent four-update expectations. This is explicitly user-reported offline interaction; Chromium version was not supplied. The reviewed Windows HTML SHA-256 is **`282bc607ca14445f8cb43e37bed6000098c93f737dec2df239117b960f2695ce`**. The browser tool still blocks direct-file navigation, and served-page testing does not replace this reported check. Both Git LF and reviewed CRLF hashes are in the repaired logistic record; the package stayed unchanged.

The earlier integrated 38-test run on Python 3.12 was followed by 19 transport/generation/repair tests, then 21 affected runtime/generation/repair tests after P1's optional array-bound and exploration-prompt updates. These are overlapping historical test groups, not additive full-suite counts. The final showcase section above records the later resizing/checkbox/label checks, new entropy CLI lineage and attributed P1 Python 3.11 result.

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

The `*-showcase-user.json` records supplement P2's final reviews with the guided user offline confirmations and P1's earlier entropy observations. In particular, the enzyme direct-file check now has three confirmed states; attention's user check applies to the preceding fresh page with unchanged numerical/UI definitions. The user reported pass/fail, not browser version or raw full-precision output.

The separately traced `entropy-polished` page corrects only the scaled-bar title. Its controls, mathematics, other teaching and view bindings are exactly equal to the independently reviewed `entropy-showcase` parent. No new browser observations are attributed to the revised HTML.
