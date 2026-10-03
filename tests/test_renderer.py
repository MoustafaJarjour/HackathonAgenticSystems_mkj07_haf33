"""Presentation-boundary checks for escaped prose, script data, and evidence navigation."""
import unittest

from src.renderer import render
from src.validator import validate_html
from tests.fixtures import lesson


class RendererTests(unittest.TestCase):
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
