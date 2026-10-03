# Generated review candidates

These packages contain saved model output from CLI generation or explicitly traced live model repairs. Keep each package's input, lesson, HTML and traces unchanged during review; publish revisions as distinct packages. Authored development fixtures live separately under `tests/science/` and ignored `review-out/`.

## Final showcase review

The three exact showcase folders at **`17c2dbded568be3ccc0feba4bdbd52a0135843b5`** passed 116 independent numerical checks (including expected failures) and 89 Chromium observations. All 18 package files, including ancestor lessons/traces, stayed unchanged. Source equations, teaching adaptations and corrected explanations were reviewed independently.

| Showcase | Exact-output review | Generation lineage |
|---|---|---|
| [entropy-showcase](entropy-showcase/index.html) | [32 browser observations / 22 core checks](../../tests/browser/reviews/entropy-showcase.json): 2–6 entries, zero append/removal, scale invariance, invalid edits and recovery passed. One minor title issue: “larger total” also appears when scale<1. | Fresh CLI generation, two model requests. |
| [attention-showcase](attention-showcase/index.html) | [34 browser observations / 27 core checks](../../tests/browser/reviews/attention-showcase.json): scaling checkbox, all 12 cells, both heatmaps, legal saturation/negative states and recovery passed. Corrected fixed-shape/scaling explanations accepted. | Original CLI generation plus two separately traced live model repairs; original/intermediate lessons and traces retained. |
| [enzyme-showcase](enzyme-showcase/index.html) | [23 browser observations / 67 core checks](../../tests/browser/reviews/enzyme-showcase.json): all sliders, bounds, 48 curve samples/current marker and six fixed absolute-concentration scan bars passed. Misleading reference-line headings resolved. | Original CLI generation plus a separately traced live model repair; original lesson/trace retained. |

The final attention/enzyme repair traces say `fresh_cli_generation=false`; they do not claim a new full CLI run. Their numerical expressions/cases are preserved from the saved candidates (enzyme's scan computation label was clarified). Stage request counts, reported usage and elapsed times are recorded separately in the reviews; inspection delays are not pipeline execution time.

The user reports network-disconnected `file://` recalculation passed on the final entropy and attention pages, without supplying exact states or browser versions. Enzyme direct-file interaction is unestablished. P1 reports Python 3.11 with 51 passing tests; this was not independently rerun by P2. [Logistic-reviewed](logistic-reviewed/index.html) remains accepted for its four-update source/math/browser and user-reported offline scope.

## Earlier CLI packages

| Package | Published commit | Independent result |
|---|---|---|
| [entropy-v1](entropy-v1/index.html) | `d944f28c8f76422f76a6e92e940883fb4847274f` | Numerical values, available Chromium controls, invalid-input recovery, and user-reported offline recalculation passed. Needs revision for outcome resizing, source provenance, and a freshly generated page embedding the integrated UI. |
| [logistic-map](logistic-map/index.html) | `ab9d72967e4a0a8d435cb6a641923b94e39d4da1` | All four updates passed independent comparisons; both sliders, endpoints, labels, theme button, and 15 Chromium observations passed. Needs correction of the longer-cycle claim, stale line-plot description, and equation-transcription provenance. |
| [attention](attention/index.html) | `9b6609be7c5414ffd0b16624283e7c1a1e750541` | Scaled attention, all 12 numeric cells, validation/recovery, both heatmaps, and 24 Chromium observations passed. Needs correction of the unreachable third-column exploration, false small-matrix saturation limitation, and equation-transcription provenance. No scientific scaling checkbox is generated. |
| [enzyme-kinetics](enzyme-kinetics/index.html) | `9b6609be7c5414ffd0b16624283e7c1a1e750541` | Initial-rate values, all three sliders, endpoints, 48 curve samples/current marker per state, and 19 Chromium observations passed. Needs equation-transcription labeling and correction of readouts that imply reference lines absent from the plot. |

The entropy trace reports one `deepseek/deepseek-v4.1-flash` request with 2,727 completion tokens; logistic reports three requests with 3,137 completion tokens, including two component repairs; attention reports two requests with 3,390 completion tokens, including repair of its row-sum computation; enzyme reports one request with 2,005 completion tokens. All report CLI success. CLI success does not establish scientific or browser acceptance. See [verification notes](../../tests/browser/README.md) and the [entropy](../../tests/browser/reviews/entropy-v1.json), [logistic](../../tests/browser/reviews/logistic-map.json), [attention](../../tests/browser/reviews/attention.json), and [enzyme](../../tests/browser/reviews/enzyme-kinetics.json) records for exact hashes, states, observations, and findings.

## Separate live model repairs

These packages at **`781b369186afe61362dcefc84924c3944f2ceb92`** preserve the earlier saved model candidate's calculations/checks and apply a traced live model component repair before rendering. The traces explicitly set `fresh_cli_generation=false` and `mode=saved_model_candidate_live_repair`. They establish review of the exact repaired renderer outputs, rather than a new end-to-end CLI generation. Both original and repaired packages were kept unchanged during P2 review.

| Repaired package | Independent review |
|---|---|
| [logistic-reviewed](logistic-reviewed/index.html) | Source/teaching findings resolved; four-update numerical checks, 14 Chromium observations and user-reported `file://` interaction with network disconnected passed. Accepted for the stated science/browser/offline page scope. |
| [attention-reviewed](attention-reviewed/index.html) | All three recorded findings resolved; 12 cells, heatmaps, saturation, recovery and 24 Chromium observations passed. Accepted for the stated fixed-matrix science/browser scope; no scientific scaling checkbox exists. |
| [entropy-reviewed](entropy-reviewed/index.html) | Provenance/coding claims and old UI findings resolved; numeric cells, outcome labels, recovery and 18 Chromium observations passed. Still lacks outcome resizing. |
| [enzyme-reviewed](enzyme-reviewed/index.html) | Transcription labeling and historical-Km scope clarified; rates, slider bounds, all 48 curve samples/current marker per state and 23 Chromium observations passed. Reference-line readout labels remain misleading. |

Each repair uses one model request, with completion tokens of 718 (logistic), 538 (attention), 1,259 (entropy) and 529 (enzyme). Exact traces, hashes, inputs and findings are in the corresponding [logistic](../../tests/browser/reviews/logistic-reviewed.json), [attention](../../tests/browser/reviews/attention-reviewed.json), [entropy](../../tests/browser/reviews/entropy-reviewed.json) and [enzyme](../../tests/browser/reviews/enzyme-reviewed.json) review records. Logistic is an independently reviewed offline example; fresh CLI acceptance after generator changes and the outstanding control/presentation checks remain separate work.
