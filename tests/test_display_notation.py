import copy
import json
from pathlib import Path
import unittest

from src.display_notation import latex_expression, presentation_spec
from src.renderer import render
from src.validator import validate_html


ROOT = Path(__file__).resolve().parent.parent


class DisplayNotationTests(unittest.TestCase):
    def test_every_lesson_surface_upgrades_legacy_notation_without_changing_data(self):
        spec = json.loads((ROOT / "examples/generated/entropy-polished/lesson.json").read_text())
        original = copy.deepcopy(spec)
        display = presentation_spec(spec)
        self.assertEqual(spec, original)
        self.assertEqual(display["computations"][0]["expression"], spec["computations"][0]["expression"])
        self.assertEqual(display["checks"], spec["checks"])
        self.assertEqual(display["grounding"]["source_claims"][0]["quote"], spec["grounding"]["source_claims"][0]["quote"])
        for value in (display["concept_summary"], display["terms"][0]["symbol"],
                      display["terms"][1]["meaning"], display["explanation_steps"][0]["body"],
                      display["controls"][0]["meaning"], display["computations"][1]["label"],
                      display["equations"][0]["expression"], display["explorations"][0]["why"],
                      display["grounding"]["teaching_simplifications"][0]):
            self.assertIn("$", value)
        page = render(spec, {})
        validate_html(page, spec)
        payload = page.split('<script id="lesson-data" type="application/json">')[1].split('</script>')[0]
        self.assertEqual(json.loads(payload)["spec"], original)
        self.assertIn('<summary>Calculation code</summary>', page)

    def test_explicit_markdown_math_code_and_links_are_not_rewritten(self):
        spec = json.loads((ROOT / "examples/generated/entropy-polished/lesson.json").read_text())
        spec["concept_summary"] = '**Entropy** uses $p_i$ and `p_i`. [source](https://example.com/p_i) Costs $5 and $10.'
        result = presentation_spec(spec)
        self.assertEqual(result["concept_summary"], spec["concept_summary"])
        spec["computations"][0]["label"] = 'p_i = feature columns'
        self.assertNotIn(r'\mathrm{feature}', presentation_spec(spec)["computations"][0]["label"])
        spec["terms"][0]["symbol"] = "$w_i$"
        spec["controls"][0]["meaning"] = 'Use w_i/sum(w) and c*sum(w).'
        meaning = presentation_spec(spec)["controls"][0]["meaning"]
        self.assertNotIn('/sum(w)', meaning)
        self.assertNotIn('c*sum(w)', meaning)

    def test_algebraic_structure_and_transpose_are_preserved(self):
        self.assertEqual(latex_expression('Q*K^T', {}), r'Q\,{K}^{\top}')
        self.assertIn(r'\left(b + c\right)', latex_expression('a-(b+c)', {}))
        self.assertEqual(latex_expression('a/(b/c)', {}), r'\frac{a}{\frac{b}{c}}')
        self.assertIn(r'\left(a + b\right)', latex_expression('(a+b)**2', {}))
        self.assertIn(r'\left(a + b\right)', latex_expression('matmul(a+b,c)', {}))
        with self.assertRaises(ValueError):
            latex_expression('object.attribute', {})


if __name__ == '__main__':
    unittest.main()
