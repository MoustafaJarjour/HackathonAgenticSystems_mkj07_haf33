# New-paper and efficiency measurements

On 3 October 2026, P2 tested the production generator at `61ddce2bac24eb705d7a26a0ec541b09689b506f` on Einstein's 1905 Brownian diffusion and Hubble's 1929 velocity-distance relation. The supplied excerpts contain short primary quotations, explicitly transcribed equations and authored explanatory summaries. Focus fields specify teaching units and controls. This tests unfamiliar mechanisms with supplied evidence; it does not establish discovery from arbitrary full papers or performance on the hidden assessment inputs.

Independent expectations were prepared before generation in [generalization_inputs.json](generalization_inputs.json), separately from production. Brownian expectations derive diffusivity in SI and convert to micrometre units; Hubble expectations derive the historical corrected-velocity teaching relation. Fixture expectations were not supplied as an answer lookup table to the generator.

## Six real measured runs

All runs used `deepseek/deepseek-v4.1-flash`, fresh output folders and the same input bytes. Each made three API attempts. The baseline invoked the production CLI twice per paper. The compact-JSON experiment invokes the same pipeline through an explicitly marked developer entrypoint that removes JSON serialization whitespace. Production files, checks, source, caps and review requirements were unchanged. It was run once per paper and was not adopted.

| Paper / variant / run | Total API tokens T | External process seconds L | Result |
|---|---:|---:|---|
| Brownian / baseline / 1 | 30,500 | 92.294 | Failed numerical gate; no HTML |
| Brownian / baseline / 2 | 29,050 | 68.503 | Failed numerical gate; no HTML |
| Hubble / baseline / 1 | 21,783 | 43.017 | Usable page; independent findings remain |
| Hubble / baseline / 2 | 22,653 | 25.398 | Usable page; independent findings remain |
| Brownian / compact / 1 | 24,378 | 26.408 | Failed numerical gate; no HTML |
| Hubble / compact / 1 | 19,221 | 38.258 | Failed numerical gate; no HTML |

T includes prompt and completion usage across every attempt, including failed candidates; reasoning is counted once within completion. Cached input remains included. Eighteen API response IDs are present and unique, and usage sums agree with trace totals. Account-side API records were not independently queried; cache breakdown is unknown. L is measured externally before subprocess creation through wait/exit, including interpreter startup, imports, API waits, checks, retries and cleanup. Trace finish occurs roughly 0.29-0.36 seconds earlier and is not the exact scoring latency. Installation and independent reviews are outside each generation run.

The rubric requires at least 50/85 quality points before efficiency points apply. These reviews do not assign an official quality score, establish that threshold, or know competitors' Tmin/Lmin. No efficiency points are claimed. Lower token totals with no usable page are not a demonstrated improvement. The compact variant produced 0/2 pages versus baseline's 2/4; retain the baseline. Small stochastic samples do not isolate a causal effect of whitespace on quality or timing.

## Independent findings

Both Brownian baseline candidates calculate primary diffusivity, mean-square displacement and one-axis RMS correctly, but their own proposed expectations omit the temperature factor. At T=300, eta=1, radius=1, independent diffusivity is 0.21973711302488222, not 0.000732. Preserved incorrect expectations prevent successful repair. The compact Brownian candidate instead guesses nearby decimal values outside its declared tolerance. Auxiliary unit/scaling descriptions also have findings. Each partial candidate passed 60 independent primary-value states and three invalid rejections; this does not make a failed generation usable.

Both Hubble baseline pages compute physical velocities correctly, but display a ratio of 2 at d=0, where v(2d)/v(d)=0/0 is undefined. Their “steeper line” exploration is misleading because the view rescales its vertical axis: K=500 to 600 changes the maximum tick from 5000 to 6000 while keeping line geometry identical. Authored summaries are promoted to source quotations without clear summary labeling; the second page also mislocates the residuals discussion. Each page passed 56 independent primary-value states and two invalid rejections. Chromium operated both sliders, endpoints, theme and all six disclosures: 14/16 complete readout observations passed on each page; two legal-zero observations fail the ratio. Each actual SVG's 768 recorded samples, 16 markers and 160 ticks matched independent expectations. Console warning/error logs were empty and desktop/narrow layouts had no horizontal overflow. Direct-file offline checks were not performed for these new pages.

The compact Hubble run preserves an expected ratio of zero at d=0 while a repair substitutes constant 2. Both interpretations of the literal ratio are incorrect; the numerical gate rejects the run. Lower-cost experimentation did not resolve reliability findings. Across all six candidates, 348 primary-value/line states and 15 invalid rejections passed; no new page received full independent acceptance.

Priority proposals for P1: distinguish supplied independent cases from model-proposed expectations; allow only explicitly recorded source-grounded corrections of erroneous self-proposed expectations; detect repeated unchanged failures before spending another repair; handle optional ratio diagnostics honestly at zero. Never accept a check merely by copying actual output into expected output. Successful autonomous generation and fidelity take priority over serialization savings. P2 made no such production change.

## Reproduction and evidence

With the key configured locally, use another fresh output root:

```text
python -m tests.science.benchmark_papers --inputs examples/science_cases/brownian_diffusion.json examples/science_cases/hubble_relation.json --output review-out/new-papers-rerun --repeats 2 --model deepseek/deepseek-v4.1-flash
```

The optional experiment adds `--variant compact-json`. The harness records external timing, token usage, API IDs, exit status and hashes; science/browser review remains separate. Inputs are [Brownian](../../examples/science_cases/brownian_diffusion.json) and [Hubble](../../examples/science_cases/hubble_relation.json). Exact outputs are byte-preserving copies under `examples/generated/generalization-baseline/` and `examples/generated/generalization-compact/`. Failed packages contain no HTML. Original absolute commands remain in measurement files for provenance and require local path adjustment elsewhere.

See [measurements](reviews/efficiency-measurements.json), [science findings](reviews/new-paper-benchmark.json), and the [first](../browser/reviews/hubble-generalization-run01.json) / [second](../browser/reviews/hubble-generalization-run02.json) Chromium reports. Generated outputs stayed unchanged during review.
