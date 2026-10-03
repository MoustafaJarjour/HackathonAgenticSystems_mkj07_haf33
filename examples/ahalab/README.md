# AhaLab example lessons

![AhaLab](../../assets/brand/ahalab-logo.png)

**Turn papers into playgrounds.**

Open any lesson locally; its logo, styles, calculations, and visualizations are
embedded in one offline HTML file.

| Lesson | Open |
| --- | --- |
| Entropy | [Explore](entropy-polished/index.html) |
| Attention | [Explore](attention-showcase/index.html) |
| Enzyme kinetics | [Explore](enzyme-showcase/index.html) |
| Logistic map | [Explore](logistic-reviewed/index.html) |

These are presentation copies of saved lesson specifications rendered with the
current AhaLab renderer, not new model generations. Source specifications,
traces, historical HTML, and exact-artifact review records remain in
[the original packages](../generated/README.md). Their historical browser reviews
do not establish acceptance of these newly rendered pages.

Plot text receives exact typography substitutions from `plot_text.json` so legacy
formulas also display as math in titles, axes, and categorical labels. Calculation
expressions, numerical checks, and source quotations are preserved.

Rebuild all twelve saved examples without API calls:

```bash
python -m src.preview_examples
```

The remaining copies retain their historical package names: attention,
attention-reviewed, entropy-v1, entropy-reviewed, entropy-showcase,
enzyme-kinetics, enzyme-reviewed, and logistic-map.
