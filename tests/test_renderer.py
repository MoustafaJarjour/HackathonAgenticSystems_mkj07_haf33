"""Presentation-boundary checks for escaped prose, script data, and evidence navigation."""
import unittest
from html.parser import HTMLParser

from src.renderer import render
from src.validator import validate_html
from tests.fixtures import lesson


class RendererTests(unittest.TestCase):
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
