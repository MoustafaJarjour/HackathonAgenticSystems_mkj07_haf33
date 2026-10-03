# AhaLab

![AhaLab logo](assets/brand/ahalab-logo.png)

**Turn papers into playgrounds.**

Explore the [AhaLab example lessons](examples/ahalab/README.md).

Turn a supplied research-paper excerpt into one offline interactive lesson. The model proposes explanations, controls, mathematical expressions, and views. Trusted Python validates the lesson and compiles a bounded expression tree; fixed JavaScript computes values and draws the page.

Lessons explain the intuition, causal steps, and effects of changing inputs, using small worked examples where helpful. Source quotations and attribution belong in the grounding section; each explanation's provenance is available under “Source and teaching notes.” Saved lesson prose needs regeneration or editing to adopt updated teaching prompts; rendering alone only updates its presentation.

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
python agent.py --input examples/generated/entropy-showcase/input.json --output out --model deepseek/deepseek-v4.1-flash
```

Generation now includes a separate visualization design pass with a **4,000-output-token ceiling**
and temperature **0.5**. It can design up to three complementary views, including mechanism diagrams
with directed connections, annotations, and live computed values. Set `--visualization-tokens 6000`
to give this pass more room (allowed: 1,000–8,000), or `--visualization-tokens 0` to disable it.
The ceiling is an allowance, not a requirement to spend tokens. Saved lessons need regeneration to
receive new designs; rendering an existing lesson retains its declared views.

Open `out/index.html` locally. It contains its styles, lesson data, math core, controls, and SVG views. Interactions require no API calls or downloaded resources. `out/lesson.json` contains the saved lesson; `out/trace.jsonl` records stages, attempts, reported usage, and outcomes. Read the final trace status and exit code; a partial file is not evidence of success.

Open `out/trace.md` for a readable run report, automatically written on success or failure. It includes the final outcome, elapsed time, observed token usage, a timeline, and formatted numerical evidence. Earlier failed checks remain visible even when a repair succeeds; missing usage is shown as unknown. The JSONL file remains the original audit log.

To convert an existing trace without rerunning the model:

```bash
python -m src.trace_report out/my-test/trace.jsonl
```

This writes `out/my-test/trace.md`. Use `--output path/to/report.md` to choose a different report path. Incomplete or malformed traces are marked incomplete, with line warnings.

Input JSON requires nonempty `source_url`, `focus`, and `audience` strings. Supply the actual source text through `excerpt`, `source_text`, or `paper_excerpt`; alternatively set `PTP_SOURCE_FILE` to a local text/PDF file or `PTP_SOURCE_DIR` to a source cache. The assignment names three required fields while referring to five strings, so additional source aliases are accepted without guessing the unnamed fields. A URL without supplied/local text fails by default. Development-only retrieval can be enabled with `PTP_ALLOW_SOURCE_FETCH=1`; leave it disabled for assessment, where network requests are restricted to OpenRouter.

## Offline verification

Lesson prose supports paragraphs, emphasis, lists, links, and code through restricted
Markdown. Use `$p_i$` for inline LaTeX and `$$...$$` on separate lines for display
math. `equations.expression` accepts display LaTeX wrapped in `$$...$$`;
`terms.symbol` accepts inline math. LaTeX backslashes must be escaped in JSON.
Lesson and plot titles, calculation labels/units, captions, axes, and category,
row, and column labels, section headings, and control labels support inline Markdown
and math too. Source quotes stay verbatim. `computations.expression`
always uses the validated calculation language, independent of display notation.
Markdown is rendered with raw HTML and images disabled, and equations become
native MathML during generation, so no browser libraries, fonts, or network access
are required. Legacy plain-text equations remain readable; malformed math falls
back to escaped text. Typesetting requires a browser with native MathML support.

The renderer also upgrades recognized legacy scientific notation throughout the
displayed lesson, including prose, symbols, labels, explorations, and limitations.
This operates on a presentation copy; the embedded specification, executable
expressions, numerical checks, and original source quotations are unchanged.
Calculation disclosures show a typeset formula, with literal code in its own disclosure.

Numeric inputs use themed increase/decrease buttons, with keyboard editing and
control bounds preserved. The provenance badge “Teaching simplification” identifies
a teaching relationship rather than a claim directly supported by the source.

```bash
python -m unittest discover -s tests -v
python -m tests.create_demo --output smoke-out
python -m tests.create_demo --diagrams --output diagram-smoke-out
python -m tests.science.create_previews
python -m tests.science.check_generated
python -m src.renderer --spec smoke-out/lesson.json --output review-out/saved/index.html
```

The generic demo intercepts the model request and uses synthetic data. The source-backed developer previews are authored fixtures, rendered from saved JSON and checked against independent expectations. Neither proves fresh model-generation quality. See [scientific acceptance fixtures](tests/science/README.md) for sources, assumptions, numerical derivations, and invalid domains. Optional `node tests/runtime_smoke.cjs` checks a simulated DOM; it does not establish Chromium rendering.

The submitted dependencies were installed with standard pip in a clean **Python 3.11.15** environment. The current suite passes **74 tests** on Python 3.11; Node smoke checks also pass, including diagram updates and recovery. Recorded independent checks of the final entropy, attention and enzyme packages cover **607 legal states and 25 invalid-state rejections**, at absolute/relative tolerance 1e-12. The independent review states can be replayed with `python -m tests.science.check_generated`; their expectations come from separate mathematical reference calculations, not the model's own cases.

[Reviewed examples](examples/generated/README.md) include resizable entropy, attention with a scaling checkbox, enzyme kinetics and four explicitly unrolled logistic-map updates. P2's final exact-output review adds **89 Chromium observations and 116 numerical checks**, including invalid states, on the three showcases at `17c2dbd`. Scaling, all matrix cells, bounded resizing, slider updates, curves/bars, invalid edits and recovery passed. Earlier original/revised packages retain 154 separately scoped observations. Entropy-showcase has nine additional P1 Chromium states and five user-reported direct-file offline steps. The user also verified the preceding attention page's checkbox and three exact-final enzyme slider states offline. [Browser notes](tests/browser/README.md) identify exact files and evidence scopes. A separately traced [entropy title correction](examples/generated/entropy-polished/index.html) resolves the wording for scale below 1; every other lesson field and compiled computation matches its parent. That exact polished page passed 16 served-Chromium observations and 140 independent numerical checks; its direct-file offline interaction remains unconfirmed.

Numerical test expectations can be literal values or independent DSL arithmetic strings referencing only controls and constants. The latter are evaluated in the bounded shared runtime before the numerical expectations are frozen; saved `expected_expressions` retain their derivation. Repairs preserve the frozen values and derivations. This avoids guessed physical-constant decimals without copying tested outputs into expectations, and still establishes consistency rather than independent scientific truth.

The shared `src/math_runtime.js` is used by the page and the pip-installed QuickJS checker. Generation executes defaults, immutable numerical cases, control-effect probes and legal line-sweep samples. A dedicated visualization pass then replaces only the views; its output reruns structural and numerical gates. A bounded model source critique checks interpretations, units, diagram relationships, labels and explorations; any replacements rerun those gates. An unresolved critique, truncated design/review, or correction conflicting with preserved expectations fails without promoting a page. Model critique is not independent scientific verification: it caught an entropy interpretation error, but independent review still found teaching-label/prose errors in two other cases. Those showcase corrections have separately traced model repairs.

Generation has an 8,000-token ceiling; visualization design defaults to 4,000; source critique and targeted repairs each have a 3,500-token ceiling. The normal three-call path reserves 15,500 completion tokens. One visualization call and one source-review call have their capacity held aside so earlier generation/repair attempts cannot consume it. All retries still count against the shared 30,000-token and 10-request limits; no capacity is reclaimed merely because a response is short. Design uses temperature 0.5; generation, critique and repairs use 0.2. Optional reasoning stays disabled, so the design allowance is available for its JSON output. Budget allocation, each attempt's ceiling, temperature and observed usage are recorded in the trace.

Historical runs before the dedicated visualization pass used 2,989 completion tokens for entropy, 2,416 for enzyme and 6,002 for attention (including a numerical repair), with 2/2/3 API attempts respectively. These are CLI costs, excluding subsequent independent-review teaching repairs; [the example table](examples/generated/README.md) accounts for the complete showcase histories. Those saved examples do not establish live quality of the new design pass. Reported reasoning tokens remain part of completion accounting when present. Prompt tokens are separate from the 30,000 completion limit but count toward efficiency.

Source selection preserves supplied locators and page markers, using complete short excerpts or lexical windows bounded to 24,000 characters. This is a character bound, not a firm token budget or a section-aware retrieval system. Source-quote occurrence and valid evidence references are structural checks. The CLI records external browser and independent-science reviews as skipped because it does not perform those reviews itself.

## Scope and limits

Additional [new-paper measurements](tests/science/GENERALIZATION.md) test Einstein's Brownian diffusion and Hubble's historical relation with supplied excerpts. Of four production CLI runs, two Hubble pages were usable with independent findings; both Brownian runs failed on incorrect model-proposed expectations. A separate compact-JSON experiment produced no usable pages and was not adopted. Records report all prompt/completion tokens, API IDs and external process time; they do not claim the rubric's 50/85 qualification or official efficiency points.

- Views are scalar line sweeps, vector bars, rectangular heatmaps, and mechanism diagrams. Diagrams have 2–8 nodes on a bounded three-column/four-row grid and 1–12 directed connections. Nodes can bind existing scalar/vector/matrix computations; vectors and matrices show short entry previews (plus matrix shape), with full values in tooltips and the accessible description. Labels support sanitized Markdown/MathML. Connections, placement, computation references and diagram provenance are validated. Controls support bounded scalar values, numeric vectors/matrices, and numeric 0/1 toggles. Every meaningful control should change a relevant visible calculation in its valid domain.
- Computations use whitelisted arithmetic and functions, with at most 64 numeric cells per value, expression depth 32, 256 syntax nodes, and 1,500 expression characters. No expression-string evaluation, arbitrary generated HTML, or generated JavaScript is used.
- `normalize` is **L2 normalization**. Probability weights use `weights/sum(weights)` with a positive total. `xlogx(0)` is exactly zero; negative inputs are rejected. Attention scaling uses actual query/key column count.
- The expression language has no arbitrary indexing, conditionals, or loops. A short recurrence can be explicitly unrolled; a short trajectory does not establish chaos or reproduce a full numerical algorithm. Unsupported mechanisms must fail honestly rather than be replaced by unrelated calculations.
- API attempts, including retries, are capped at 10; completion-token reservations are capped at 30,000. New optional API work stops at 540 seconds; a 570-second watchdog leaves room under the assignment's 600-second cap. Missing API usage remains unknown in the trace.
- Tiny teaching examples do not reproduce original experimental results. Reviewed examples do not establish coverage of every paper or hidden assessment case.

## Reuse and sources

The implementation was selectively adapted from the team's [bounded-expression starter](https://github.com/MoustafaJarjour/AgenticHackathon_mkj07_haf33) at commit `cd82d4af11fdd93ebffadbbd9a8f665b1c0550b9`. Reused components include the source adapter, HTTP client and trace scaffold, expression compiler, and offline rendering foundation. The submission repository has its own history and contains implementation, tests, examples, and public documentation.

UI layout and theme styling were adapted from the team's PRISMA `playground_design_lab` prototype (`master_style.css`, `master_renderer.py`, and `enhanced_runtime.js`). Integration retains the bounded lesson contract and adds tested numeric cells, vector resizing, numeric checkbox mapping, stale-result clearing and recovery.

Scientific fixtures cite Shannon (1948), Vaswani et al. (2017), Michaelis and Menten (1913, translated by Johnson and Goody), and May (1976), with the relevant equation/section locators. Their example states and independent expected values were chosen for teaching and testing.
