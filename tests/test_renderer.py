"""Presentation-boundary checks for escaped prose, script data, and evidence navigation."""
import unittest
from html.parser import HTMLParser

from src.renderer import render
from src.rich_text import equation, inline, math, prose
from src.branding import logo_data_uri
from src.models import SpecError
from src.validator import validate_html
from tests.fixtures import lesson


class RendererTests(unittest.TestCase):
    def test_plot_titles_captions_and_all_label_types_support_math(self):
        spec = lesson()
        vis = spec["visualizations"][0]
        vis.update(title="**Probability** $p_i$", x_label="$i$", y_label="$p_i$",
                   labels=["$x_0$"], row_labels=["$q_1$"], column_labels=["$k_1$"])
        page = render(spec, {})
        validate_html(page, spec)
        self.assertIn(f'<h3 id="plot-heading-{vis["id"]}"><strong>Probability</strong> <span class="math inline">', page)
        self.assertNotIn('aria-label="**Probability**', page)
        for key in ("x_label", "y_label", "labels-0", "row_labels-0", "column_labels-0"):
            self.assertIn(f'id="plot-label-{vis["id"]}-{key}"', page)
        self.assertIn('<figcaption><span class="math inline">', page)
        vis["x_label"] = '<img src=x onerror=alert(1)>'
        validate_html(render(spec, {}), spec)

    def test_brand_logo_is_embedded_and_only_trusted_image_is_allowed(self):
        spec = lesson()
        page = render(spec, {})
        validate_html(page, spec)
        self.assertIn('alt="AhaLab"', page)
        self.assertIn('Turn papers into playgrounds.', page)
        self.assertIn(' | AhaLab</title>', page)
        self.assertNotIn('Paper to Playground', page)
        for replacement in ('https://example.com/logo.png', 'data:image/svg+xml;base64,PHN2Zz4='):
            with self.assertRaises(SpecError):
                validate_html(page.replace(logo_data_uri(), replacement), spec)

    def test_rich_lesson_has_native_math_and_balanced_blocks(self):
        spec = lesson()
        spec["concept_summary"] = "**Probability** uses $p_i$.\n\n- First outcome\n- Second outcome\n\n$$\\sum_i p_i = 1$$"
        spec["equations"][0]["expression"] = r"$$H = -\sum_{i=1}^{n} p_i \log_2 p_i$$"
        spec["explanation_steps"][0]["body"] = "Use `weights` and *normalize*.\n\nA second paragraph."
        spec["terms"][0]["symbol"] = "$p_i$"
        spec["grounding"]["source_claims"][0]["quote"] = "**exact source** $p_i$"
        page = render(spec, {})
        validate_html(page, spec)
        self.assertIn("<strong>Probability</strong>", page)
        self.assertIn("<li>First outcome</li>", page)
        self.assertIn("<msub>", page)
        self.assertIn("<munderover>", page)
        self.assertIn('<math display="block"', page)
        self.assertIn("<em>normalize</em>", page)
        self.assertIn('<blockquote>**exact source** $p_i$</blockquote>', page)

    def test_untrusted_markdown_and_math_cannot_add_resources(self):
        spec = lesson()
        spec["concept_summary"] = '<img src=x onerror=alert(1)>\n\n![remote](https://example.com/x.png)\n\n[bad](javascript:alert(1))\n\n[good](https://example.com)'
        spec["equations"][0]["expression"] = r'$$\text{<script>alert(1)</script>}$$'
        page = render(spec, {})
        validate_html(page, spec)
        self.assertEqual(page.count('<img '), 1)  # Only the trusted brand asset.
        self.assertNotIn('href="javascript:', page)
        self.assertIn('href="https://example.com"', page)
        self.assertIn('&lt;script&gt;', page)
        unsafe = math(r'\href{javascript:alert(1)}{x}')
        self.assertNotIn('href=', unsafe)
        self.assertNotIn('style=', math(r'\style{background:url(x)}{x}'))

    def test_code_currency_and_legacy_equations_are_preserved(self):
        self.assertIn('<code>$p_i$</code>', inline('`$p_i$`'))
        self.assertNotIn('<math', prose('Costs $5 and $10.'))
        self.assertEqual(equation('p_i = w_i / sum(w)'), '<code>p_i = w_i / sum(w)</code>')
        self.assertIn('math-fallback', math(r'\frac{'))

    def test_numeric_array_editors_and_single_control_markers(self):
        spec = lesson()
        spec["controls"] = [
            {"id": "weights", "kind": "array", "label": "Weights", "meaning": "Outcome weights", "default": [1, 2], "min_items": 1, "max_items": 4},
            {"id": "matrix", "kind": "array", "label": "Matrix", "meaning": "Fixed entries", "default": [[1, 2], [3, 4]]},
            {"id": "scaled", "kind": "toggle", "label": "Scaling", "meaning": "Apply scaling", "default": 1, "min": 0, "max": 1, "step": 1},
        ]
        page = render(spec, {})
        validate_html(page, spec)
        class Fields(HTMLParser):
            def __init__(self):
                super().__init__()
                self.fields = []
            def handle_starttag(self, tag, attrs):
                self.fields.append((tag, dict(attrs)))
        inspector = Fields()
        inspector.feed(page)
        cells = [attrs for tag, attrs in inspector.fields if tag == "input" and "data-array-cell" in attrs]
        self.assertEqual(len(cells), 6)
        self.assertTrue(all(item["type"] == "number" and item["step"] == "any" for item in cells))
        self.assertIn("Matrix, row 2, column 2", {item["aria-label"] for item in cells})
        markers = [(tag, attrs["data-control-id"]) for tag, attrs in inspector.fields if "data-control-id" in attrs]
        self.assertEqual(markers, [("div", "weights"), ("div", "matrix"), ("div", "scaled")])
        toggle = next(attrs for tag, attrs in inspector.fields if attrs.get("id") == "control-scaled")
        self.assertEqual(toggle["type"], "checkbox")
        self.assertIn("checked", toggle)
        self.assertIn('id="add-weights"', page)
        self.assertNotIn('id="add-matrix"', page)
        self.assertIn("fixed shape", page)
        self.assertNotIn("<textarea", page)

    def test_fixed_vector_has_no_resize_buttons(self):
        spec = lesson()
        spec["controls"][0] = {"id": "weights", "kind": "array", "label": "Weights", "meaning": "Fixed", "default": [1, 2]}
        page = render(spec, {})
        validate_html(page, spec)
        self.assertNotIn('id="add-weights"', page)
        self.assertNotIn('id="remove-weights"', page)

    def test_ordered_teaching_and_evidence_links(self):
        spec = lesson()
        page = render(spec, {})
        validate_html(page, spec)
        self.assertIn('id="explanation"', page)
        self.assertIn(spec["explanation_steps"][0]["heading"], page)
        self.assertIn('href="#evidence-relation"', page)
        self.assertIn('rel="noopener noreferrer"', page)
        self.assertIn("globalThis.PTPMath", page)

    def test_model_text_cannot_close_script_or_inject_html(self):
        spec = lesson()
        spec["title"] = '</script><img src=x onerror="alert(1)">'
        spec["explanation_steps"][0]["body"] = '<script>alert("bad")</script>'
        page = render(spec, {})
        self.assertNotIn('<img src=x', page)
        self.assertNotIn('<script>alert("bad")', page)
        self.assertIn('\\u003c/script\\u003e', page)
        self.assertIn('&lt;script&gt;', page)
        validate_html(page, spec)

    def test_non_web_source_url_is_not_linked(self):
        spec = lesson()
        spec["grounding"]["source_url"] = 'javascript:alert(1)'
        page = render(spec, {})
        self.assertNotIn('href="javascript:', page)


if __name__ == "__main__":
    unittest.main()
