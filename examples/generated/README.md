# AhaLab — historical generated lessons and review evidence

For the current branding and renderer, open the [AhaLab presentation copies](../ahalab/README.md).
This directory preserves the original reviewed artifacts; their recorded hashes
and browser observations apply to those historical files, not the new copies.

These packages preserve fresh CLI output and separately identified model repairs. Keep each package's `input.json`, `lesson.json`, `index.html`, and `trace.jsonl` unchanged during review; publish revisions as distinct packages. Authored development fixtures live separately under `tests/science/` and ignored `review-out/`.

## Current showcase packages

The three original showcases were published at `17c2dbd` and remain unchanged. The final entropy page is a separate title-only revision, preserving every other field. P2 subsequently passed 89 final Chromium observations and 116 numerical checks on these three exact packages, including domain failures. Every folder contains `input.json`, `lesson.json`, `index.html`, and `trace.jsonl`. Attention/enzyme include their preceding fresh CLI output and traces; attention also retains the first teaching-repair stage. The final HTML was produced by the renderer from model output, with no manual edits.

| Package | Generation mode | Independent science | Browser evidence |
|---|---|---|---|
| [entropy-polished](entropy-polished/index.html) | Fresh CLI parent [entropy-showcase](entropy-showcase/index.html) plus one title-only model repair | 132 legal states and 8 invalid rejections pass; resizing, scale invariance and provenance accepted | Parent: 32 P2 and nine P1 Chromium observations, plus five user offline steps. Final page changes only one chart title; no new browser review claimed |
| [attention-showcase](attention-showcase/index.html) | Fresh CLI plus two separately traced teaching repairs | 63 legal states and 11 invalid rejections pass; frozen computations/controls/checks preserved | User verified checkbox on the preceding fresh page offline; final teaching-only revision preserves numerical/UI definitions. P2 exact final-page recheck passed (34 observations) |
| [enzyme-showcase](enzyme-showcase/index.html) | Fresh CLI plus one separately traced teaching repair | 412 legal states and 6 invalid rejections pass; absolute scan labels and Km caveat accepted | User verified three final slider states offline; P2 exact final-page recheck passed (23 observations) |
| [logistic-reviewed](logistic-reviewed/index.html) | Saved fresh candidate plus traced model teaching repair | Accepted four-update recurrence and source/teaching scope | P2 science/browser review and user-reported direct-file offline check passed |

| Current case | Fresh CLI: input / completion / total | Complete showcase history: input / completion / total | Attempts across history |
|---|---|---|---|
| Entropy | 11,864 / 2,989 / 14,853 | 18,525 / 3,195 / 21,720 | 3 |
| Attention | 21,761 / 6,002 / 27,763 | 37,604 / 7,841 / 45,445 | 5 |
| Enzyme | 13,934 / 2,416 / 16,350 | 19,913 / 2,890 / 22,803 | 3 |
| Logistic | 17,415 / 3,137 / 20,552 | 23,103 / 3,855 / 26,958 | 4 |

Costs include all recorded attempts in each chain, including failed numerical candidates. Final teaching-repair traces are separate development runs, explicitly marked `fresh_cli_generation=false`; they are not claimed as fresh assessment-CLI acceptance. The per-run 30,000 limit applies to completion tokens, while total tokens include input. Immutable-case repair behavior and honest failure were also proved by injecting a known wrong logistic equation into a separate copy, then executing and repairing it; [the live repair trace and both candidate JSON files](../../tests/science/live_repair_evidence/) preserve that evidence. Original showcase files were unchanged.

Detailed independent states are in [science reports](../../tests/science/reviews/), replayable with `python -m tests.science.check_generated`. Direct-file reports and served-browser observations are recorded separately in [browser evidence](../../tests/browser/reviews/entropy-showcase.json) and [attention checkbox evidence](../../tests/browser/reviews/attention-showcase.json).

## Earlier unchanged candidates

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

Each repair uses one model request, with completion tokens of 718 (logistic), 538 (attention), 1,259 (entropy) and 529 (enzyme). Exact traces, hashes, inputs and findings are in the corresponding [logistic](../../tests/browser/reviews/logistic-reviewed.json), [attention](../../tests/browser/reviews/attention-reviewed.json), [entropy](../../tests/browser/reviews/entropy-reviewed.json) and [enzyme](../../tests/browser/reviews/enzyme-reviewed.json) review records. Logistic is an independently reviewed offline example; fresh CLI acceptance and the later resizing/scaling/final-page checks are recorded separately above.

The entropy-polished revision replaces “larger total” with “total multiplied by c”, valid for the full positive scale range including values below 1. The exact model patch cost 206 completion tokens; `tests.science.check_generated` verifies that this is the only lesson change and that the compiled math, controls and rendered assets agree with the reviewed parent. The original reviewed entropy page and evidence remain unchanged.
