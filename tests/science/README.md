# AhaLab independent scientific acceptance fixtures

These development fixtures are independent of model responses and production prompts. They are **not** a paper-answer lookup table. The numeric examples are small teaching examples chosen by P2; the underlying relationships come from the cited original papers. Source quotations are short; equation transcriptions use plain-text notation and are identified explicitly.

Run the reference checks without an API key:

```text
python -m unittest discover -s tests/science -p "test_*.py" -v
python -m tests.science.create_previews
```

`fixtures.json` holds complete states and independent expectations. `test_shared_core.py` compiles developer expressions and compares execution in the exact browser math core against those values. `create_previews.py` writes lessons to JSON, reads the saved JSON back, executes cases, and renders HTML; open the resulting pages under `review-out/science/` in Chromium. These are authored fixtures, not fresh model outputs. Map generated control/output names explicitly when they differ. Never change expectations to accommodate an incorrect generated lesson.

- **Entropy:** Shannon, *A Mathematical Theory of Communication*, section 6, Theorem 2 and properties 1–2; [original reprint](https://people.math.harvard.edu/~ctm/home/text/others/shannon/entropy/entropy.pdf). Logarithms are base 2. Uniform distributions have H = log2(n); certain outcomes have H = 0. The zero contribution is the continuous limit of p log2(p), not an epsilon approximation. Weights divided by their sum produce probabilities; L2 normalization does not.
- **Attention:** Vaswani et al., *Attention Is All You Need*, section 3.2.1, equation (1); [original paper](https://arxiv.org/html/1706.03762v7). For identity Q and K with two columns, the score advantage is 1/sqrt(2). The first weight is 1/(1+exp(-1/sqrt(2))). Each row sums to one. Multiplying those weights by V gives the output. The optional unscaled mode is a teaching comparison, not the paper's scaled mechanism.
- **Enzyme kinetics:** Michaelis and Menten, *The Kinetics of Invertase Action* (1913), equations (3)–(4), translated PDF page 11 (zero-based PDF page 10); [translation by Kenneth A. Johnson and Roger S. Goody](https://www.chem.uwec.edu/Chem352_F18/pages/readings/media/Michaelis_%26_Menton_1913.pdf). Use modern names Vmax and Km with v = Vmax*S/(Km+S). Here S and Km use the same concentration unit. At S = Km, v = Vmax/2; at S = 3*Km, v = 3*Vmax/4. This illustrates initial-rate saturation, without fitting original experiments or asserting a universal kinetic law.
- **Logistic map:** May, *Simple mathematical models with very complicated dynamics* (1976), section 2, equation (3); [Caltech/NED transcription](https://ned.ipac.caltech.edu/level5/Sept01/May/May2.html), [publisher record](https://www.nature.com/articles/261459a0). We rename a to r: x_next = r*x*(1-x). At r = 4, x0 = 1/4 gives 3/4, which stays at 3/4 in exact arithmetic. At x0 = 1/2 it gives 1, then 0. Four updates are explicitly unrolled using each preceding result; arbitrary iteration is not supported. A one-step curve cannot demonstrate the requested repeated updates, and four updates cannot establish long-run chaos. May's practical population discussion uses 1 < a < 4 and 0 < X < 1; our endpoint cases are mathematical boundary tests.

Control-effect acceptance: change entropy weights and outcome count; edit Q/K/V and compare attention scaling; vary S and Km in enzyme kinetics; vary both growth r and initial x0 while preserving actual recurrence in the logistic map. Entropy also displays log2(n), the maximum for the selected outcome count, so appending a zero-weight outcome changes that meaningful readout while correctly preserving the distribution's entropy. Legal boundary cases and invalid domains are listed separately.

## Independent control checks

The 27 complete states in `fixtures.json` are expected values, not browser observations. The Python oracle independently derives them; the shared-core tests compare the implementation at 1e-12 absolute plus 1e-12 relative tolerance. Reset to the named baseline before each control check. Generated names may differ: record the explicit control/output mapping and retain any extra controls at their declared defaults. Test only states legal for the actual lesson; report excluded states and missing capabilities rather than changing its bounds or matrix dimensions.

On 3 October 2026, the four science test methods passed for all 27 states and seven invalid states on Windows with Python 3.12. Saved authored lessons rendered separately under `review-out/science-expanded/` passed all 40 runtime records: nine entropy, ten attention, twelve enzyme, and nine logistic checks. This includes declared cases, control-effect probes, and the enzyme line sweep. It establishes authored-fixture math/render validation; fresh-generation source fidelity and Chromium controls remain separate checks.

| Mechanism | Baseline and action | Independent expectation |
|---|---|---|
| Attention | `identity_scaled`; change Q to all zeros (`equal_two_queries`) | Both weight rows become [0.5,0.5]; both output rows become [5,10]. |
| Attention | `identity_scaled`; uncheck scaling (`identity_unscaled`) | First weight rises from 0.6697615493 to 0.7310585786; d_k is 2. |
| Attention | `identity_unscaled`; change K[0][0] from 1 to 2 (`edited_key_unscaled`) | First weight becomes 0.8807970780; first output becomes [8.8079707798,2.3840584404]. Second query's row stays unchanged. |
| Attention | `identity_unscaled`; change V[0][0] from 10 to 20 (`edited_value_unscaled`) | Weights stay unchanged; first output becomes [14.6211715726,5.3788284274]. |
| Entropy | `fair_pair`; change the second weight from 1 to 3 (`uneven`) | Probabilities become [0.25,0.75], H=0.8112781245 bits. |
| Entropy | `fair_pair`; append a zero-weight outcome (`zero_outcome`) | H stays 1 bit; Hmax rises from 1 to log2(3)=1.5849625007 bits; retained entries stay [1,1]. Remove it to recover the original state. |
| Entropy | Set four equal weights (`fair_four`), then `certain` | H changes from 2 to exactly 0 bits; zero-probability contributions remain finite. |
| Entropy | Compare `uneven` with `proportional_weights` | Doubling every weight preserves probabilities and H. |
| Enzyme kinetics | `half_maximum`; change S from 2 to 6 (`three_quarters`) | Rate rises from 5 to 7.5; fraction rises from 0.5 to 0.75. |
| Enzyme kinetics | `half_maximum`; change Km from 2 to 6 (`higher_km`) | Rate falls to 2.5; fraction becomes 0.25. |
| Enzyme kinetics | `half_maximum`; change Vmax from 10 to 20 (`double_vmax`), then 0 (`zero_enzyme`) | Rate becomes 10, then 0; fraction stays 0.5. The zero-rate curve remains visible. |
| Enzyme kinetics | Set S=0 (`zero_substrate`) and S=20 (`upper_substrate`) with Km=2,Vmax=10 | Rate is 0 and 100/11=9.0909090909 respectively; the sweep includes legal endpoints. |
| Logistic map | r=4; change x0 from 0.25 to 0.5 | Initial state plus four updates changes from [0.25,0.75,0.75,0.75,0.75] to [0.5,1,0,0,0]. |
| Logistic map | x0=0.5; change r from 4 to 2 (`different_growth`) | All five displayed states become 0.5. |
| Logistic map | r=3,x0=0.2 (`interior_four_updates`) | [0.2,0.48,0.7488,0.56429568,0.7375981966000128]. Each update uses its predecessor; these expectations were also derived with exact rational arithmetic. |
| All four | Blank an editable numeric cell/field, then restore it | Visible input error; stale values and plots cleared; correct values and plots return without a reload. |

Also exercise every declared cell, slider endpoint, checkbox, outcome-count boundary, and advanced editor if exposed. For legal negative attention entries, verify against the oracle rather than imposing probability bounds on Q/K/V. Invalid science domains include all-zero/negative entropy weights, incompatible attention dimensions, Km<=0, negative substrate/Vmax, and logistic states outside 0<=r<=4 or 0<=x0<=1. Browser widgets may prevent these values; record prevention as such, without claiming an evaluation error was observed.

Source fidelity is a separate review: inspect the actual generated equations, computations, quotations, locators, teaching steps, and limitations. Attention must use row softmax and the actual feature dimension; entropy must use probability normalization and the exact zero limit. In the enzyme translation, C*Phi becomes modern Vmax and equation (4)'s V is a fractional rate, not Vmax. Logistic bars must represent successive states rather than repeated independent one-step evaluations. The optional unscaled attention mode and chosen parameter values must be described as teaching choices. Quote occurrence alone does not establish this fidelity.

Independent reviews of all four unchanged fresh CLI packages are recorded in [browser verification notes](../browser/README.md) and `tests/browser/reviews/`. Their available numerical calculations pass, while each package has open source/teaching or presentation findings. The fresh attention package fixes Q/K/V at 2×2 and has no unscaled toggle; its scaled calculations, every numeric cell, zero/equal-score cases, legal negative entries and strong score saturation were checked independently. Fresh enzyme Vmax is bounded to 0.1–10, so Vmax=0 and 20 authored fixtures were excluded; all legal control endpoints, concentration-ratio invariance, curve samples and current markers passed. Fresh entropy fixes the outcome count at three, so resizing still requires a new generated package. These limits do not change the authored fixture expectations.

Separate saved-candidate live model repairs were subsequently reviewed at commit `781b369186afe61362dcefc84924c3944f2ceb92`. Their original computations and numerical cases remained intact; all 37 core observations were rerun against the exact repaired embedded configurations. Repaired logistic and attention resolve their recorded source/teaching findings and pass the stated mechanism/browser scope. Revised logistic also has user-reported direct-file, network-disconnected interaction evidence for both complete trajectories. Entropy outcome resizing and enzyme's unplotted reference-line labels remain open. These repair traces explicitly say they are not fresh CLI generations; source-backed fixture math, repaired-page review and new-generation acceptance remain distinct evidence.

## Final generated-package checks

`python -m tests.science.check_generated` replays the recorded independent expected values in `reviews/*-showcase.json` against unchanged saved final lessons. It checks source structure, offline HTML structure, exact lesson SHA-256, 607 legal numerical states and 25 invalid-state rejections. Expectations use the separate Shannon, scaled-attention and Michaelis-Menten development references and analytically constructed states. These references are not used in production generation. Browser behavior and human offline reports remain separate evidence.

P2 also independently reviewed the exact three showcase outputs at `17c2dbd`: 116 numerical checks including invalid states passed. These are separate review samples and are not added to the 607 legal-state count as if all states were unique. The P2 run used Python 3.12; the submitted suite and recorded-state replay also passed on P1's clean Python 3.11.15 installation.
