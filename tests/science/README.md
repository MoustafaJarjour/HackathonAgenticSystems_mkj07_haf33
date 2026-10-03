# Independent scientific acceptance fixtures

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
- **Logistic map:** May, *Simple mathematical models with very complicated dynamics* (1976), equation (3); [original-paper transcription](https://www.esalq.usp.br/departamentos/leb/aulas/lce164/simple.pdf), [publisher record](https://www.nature.com/articles/261459a0). We rename a to r: x_next = r*x*(1-x). At r = 4, x0 = 1/4 gives 3/4, which stays at 3/4 in exact arithmetic. At x0 = 1/2 it gives 1, then 0. A one-step curve alone is insufficient to teach iteration or chaos. The trajectory fixture deliberately tests the expression backend's iteration/indexing gap; a failure must be reported as a coverage limitation.

Control-effect acceptance: change entropy weights and outcome count; edit Q/K/V and compare attention scaling; vary S and Km in enzyme kinetics; vary both growth r and initial x0 while preserving actual recurrence in the logistic map. Entropy also displays log2(n), the maximum for the selected outcome count, so appending a zero-weight outcome changes that meaningful readout while correctly preserving the distribution's entropy. Legal boundary cases and invalid domains are listed separately.
