# Generated review candidates

These packages contain complete model output from the actual CLI. Keep each package's `input.json`, `lesson.json`, `index.html`, and `trace.jsonl` unchanged during review; publish revisions as distinct packages. Authored development fixtures live separately under `tests/science/` and ignored `review-out/`.

| Package | Published commit | Independent result |
|---|---|---|
| [entropy-v1](entropy-v1/index.html) | `d944f28c8f76422f76a6e92e940883fb4847274f` | Numerical values, available Chromium controls, invalid-input recovery, and user-reported offline recalculation passed. Needs revision for outcome resizing, source provenance, and a freshly generated page embedding the integrated UI. |
| [logistic-map](logistic-map/index.html) | `ab9d72967e4a0a8d435cb6a641923b94e39d4da1` | All four updates passed independent comparisons; both sliders, endpoints, labels, theme button, and 15 Chromium observations passed. Needs correction of the longer-cycle claim, stale line-plot description, and equation-transcription provenance. |

The entropy trace reports one `deepseek/deepseek-v4.1-flash` request with 2,727 completion tokens; logistic reports three requests with 3,137 completion tokens, including two component repairs. Both report CLI success. CLI success does not establish scientific or browser acceptance. See [verification notes](../../tests/browser/README.md) and the [entropy](../../tests/browser/reviews/entropy-v1.json) / [logistic](../../tests/browser/reviews/logistic-map.json) records for exact hashes, states, observations, and findings. No package is yet designated as the accepted showcase.
