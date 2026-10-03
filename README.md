# Paper to Playground

Turn a supplied research-paper excerpt into one offline interactive lesson. The model proposes explanations, controls, mathematical expressions, and views. Trusted Python validates the lesson and compiles a bounded expression tree; fixed JavaScript computes values and draws the page.

Team: **mkj07 / haf33**. P1 owns generation, source handling, mathematical compilation, checking, budgets, and integration. P2 owns presentation, browser controls, independent scientific examples, and browser review.

## Setup and generation

Use **Python 3.11** and the pinned dependencies. Node and a browser are development tools; generation does not require them.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Windows, use `py -3.11 -m venv .venv`, then `.venv\Scripts\python.exe` in place of `python`; activation is optional.

Set `OPENROUTER_API_KEY` in the environment. Keep the key out of input files, source control, and chat. The selected model is **`deepseek/deepseek-v4.1-flash`**; the CLI always takes the model explicitly.

```bash
python agent.py --input examples/science_cases/attention.json --output out --model deepseek/deepseek-v4.1-flash
```

Open `out/index.html` locally. It contains its styles, lesson data, math core, controls, and SVG views. Interactions require no API calls or downloaded resources. `out/lesson.json` contains the saved lesson; `out/trace.jsonl` records stages, attempts, reported usage, and outcomes. Read the final trace status and exit code; a partial file is not evidence of success.

Input JSON requires nonempty `source_url`, `focus`, and `audience` strings. Supply the actual source text through `excerpt`, `source_text`, or `paper_excerpt`; alternatively set `PTP_SOURCE_FILE` to a local text/PDF file or `PTP_SOURCE_DIR` to a source cache. The assignment names three required fields while referring to five strings, so additional source aliases are accepted without guessing the unnamed fields. A URL without supplied/local text fails by default. Development-only retrieval can be enabled with `PTP_ALLOW_SOURCE_FETCH=1`; leave it disabled for assessment, where network requests are restricted to OpenRouter.

## Offline verification

```bash
python -m unittest discover -s tests -v
python -m tests.create_demo --output smoke-out
python -m tests.science.create_previews
python -m src.renderer --spec smoke-out/lesson.json --output review-out/saved/index.html
```

The generic demo intercepts the model request and uses synthetic data. The source-backed developer previews are authored fixtures, rendered from saved JSON and checked against independent expectations. Neither proves fresh model-generation quality. See [scientific acceptance fixtures](tests/science/README.md) for sources, assumptions, numerical derivations, and invalid domains. Optional `node tests/runtime_smoke.cjs` checks a simulated DOM; it does not establish Chromium rendering.

Current evidence covers authored attention, entropy, enzyme-kinetics, and logistic-map fixtures, including 27 independent numeric states and seven invalid states. [Four fresh generated packages](examples/generated/README.md) passed independent numerical comparisons and 75 recorded Chromium observations on their available controls. Attention's 12 matrix cells, both heatmaps and invalid-edit recovery passed. Enzyme's three sliders, all 48 curve samples and the current marker passed independent comparison at each recorded state. Fresh entropy also passed invalid-edit recovery and a user-reported `file://` recalculation with the network disconnected. See [browser verification notes](tests/browser/README.md) for exact inputs, expected/observed values, file hashes and findings.

All four remain review candidates. Entropy lacks resizing and embeds the older interface; logistic needs corrections to its cycle/plot descriptions; attention contains an unreachable dimension-changing exploration and an incorrect saturation limitation; enzyme labels reference lines that are not plotted. All four need clearer transcription provenance. No fresh showcase is accepted yet. A scientific scaling checkbox, entropy resizing, and revised-showcase offline interaction still need independent review. The integrated 38-test suite passed on P2's Python 3.12, followed by 19 transport/generation/repair tests after P1's latest changes; this does not establish the required Python 3.11 environment.

The shared `src/math_runtime.js` is used by the page and the pip-installed QuickJS checker. Generation executes default states, numerical cases, control-effect probes, and legal line-sweep samples before promoting output. Numerical cases compare finite values and exact shapes with absolute/relative tolerances. Failed cases feed targeted component replacement; their expectations are preserved during repair. Source-quote occurrence and valid evidence references are structural checks; scientific interpretation also needs independent review. The CLI records browser and independent-science review as skipped because it does not perform those reviews itself.

## Scope and limits

- Views are scalar line sweeps, vector bars, and rectangular heatmaps. Controls support bounded scalar values, numeric vectors/matrices, and numeric 0/1 toggles. Every meaningful control should change a relevant visible calculation in its valid domain.
- Computations use whitelisted arithmetic and functions, with at most 64 numeric cells per value, expression depth 32, 256 syntax nodes, and 1,500 expression characters. No expression-string evaluation, arbitrary generated HTML, or generated JavaScript is used.
- `normalize` is **L2 normalization**. Probability weights use `weights/sum(weights)` with a positive total. `xlogx(0)` is exactly zero; negative inputs are rejected. Attention scaling uses actual query/key column count.
- The expression language has no arbitrary indexing, conditionals, or loops. A short recurrence can be explicitly unrolled; a short trajectory does not establish chaos or reproduce a full numerical algorithm. Unsupported mechanisms must fail honestly rather than be replaced by unrelated calculations.
- API attempts, including retries, are capped at 10; completion-token reservations are capped at 30,000. New optional API work stops at 540 seconds; a 570-second watchdog leaves room under the assignment's 600-second cap. Missing API usage remains unknown in the trace.
- Tiny teaching examples do not reproduce original experimental results. Four authored mechanisms do not establish fresh generation quality or coverage of every paper or hidden assessment case.

## Reuse and sources

The implementation was selectively adapted from the team's [bounded-expression starter](https://github.com/MoustafaJarjour/AgenticHackathon_mkj07_haf33) at commit `cd82d4af11fdd93ebffadbbd9a8f665b1c0550b9`. Reused components include the source adapter, HTTP client and trace scaffold, expression compiler, and offline rendering foundation. The submission repository has its own history and contains implementation, tests, examples, and public documentation.

Scientific fixtures cite Shannon (1948), Vaswani et al. (2017), Michaelis and Menten (1913, translated by Johnson and Goody), and May (1976), with the relevant equation/section locators. Their example states and independent expected values were chosen for teaching and testing.
