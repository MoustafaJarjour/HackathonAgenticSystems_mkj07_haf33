# Generated review candidates

These packages contain complete model output from the actual CLI. Keep each package's `input.json`, `lesson.json`, `index.html`, and `trace.jsonl` unchanged during review; publish revisions as distinct packages. Authored development fixtures live separately under `tests/science/` and ignored `review-out/`.

| Package | Published commit | Independent result |
|---|---|---|
| [entropy-v1](entropy-v1/index.html) | `d944f28c8f76422f76a6e92e940883fb4847274f` | Numerical values, available Chromium controls, invalid-input recovery, and user-reported offline recalculation passed. Needs revision for outcome resizing, source provenance, and a freshly generated page embedding the integrated UI. |

The entropy trace reports one `deepseek/deepseek-v4.1-flash` request with 2,727 completion tokens and a successful CLI run. CLI success does not establish scientific or browser acceptance. See [verification notes](../../tests/browser/README.md) and [exact hashes, states, observations, and findings](../../tests/browser/reviews/entropy-v1.json). No package is yet designated as the accepted showcase.
