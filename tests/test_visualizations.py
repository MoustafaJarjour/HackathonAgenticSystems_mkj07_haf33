"""Budget, immutable mathematics and diagram validation through the real pipeline."""
import copy
import json
import tempfile
import time
import unittest
from pathlib import Path

from src.models import SpecError, normalize_optional, provider_schema, VISUALIZATION_DESIGN_SCHEMA
from src.openrouter_client import Budget, BudgetError
from src.renderer import render
from src.runtime_checker import check_runtime
from src.validator import validate_html, validate_spec
from tests.fixtures import SOURCE, SOURCE_URL, completion, diagram, lesson, run_fixture


class VisualizationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.output = Path(temporary.name) / "out"

    def test_dedicated_default_budget_and_temperature_preserve_science_and_audit_new_views(self):
        views = [diagram(), *lesson()["visualizations"]]
        code, events, requests = run_fixture(self.output, visualization_responses=[completion({"visualizations": views})])
        self.assertEqual(code, 0)
        self.assertEqual([r["max_tokens"] for r in requests], [8000, 4000, 3500])
        self.assertEqual([r["temperature"] for r in requests], [0.2, 0.5, 0.2])
        self.assertTrue(all(r["reasoning"]["enabled"] is False for r in requests))
        saved = json.loads((self.output / "lesson.json").read_text())
        self.assertEqual(saved["visualizations"], views)
        self.assertEqual({key: value for key, value in saved.items() if key != "visualizations"},
                         {key: value for key, value in lesson().items() if key != "visualizations"})
        self.assertIn('"id": "mechanism"', requests[2]["messages"][1]["content"])
        self.assertTrue(any(e["metadata"].get("after_visualization_design") for e in events))
        self.assertEqual(events[-1]["metadata"]["reserved_completion_tokens"], 15500)
        self.assertEqual(events[-1]["metadata"]["held_completion_tokens"], 0)
        validate_html((self.output / "index.html").read_text(), saved)

    def test_custom_budget_and_explicit_disabled_pass(self):
        code, _, requests = run_fixture(self.output, visualization_tokens=6000)
        self.assertEqual(code, 0)
        self.assertEqual([r["max_tokens"] for r in requests], [8000, 6000, 3500])
        code, events, requests = run_fixture(self.output, visualization_tokens=0, visualization_responses=[])
        self.assertEqual(code, 0)
        self.assertEqual([r["max_tokens"] for r in requests], [8000, 3500])
        self.assertTrue(any(e["action"] == "visualization_design" and e["result"] == "skipped" for e in events))

    def test_earlier_attempts_cannot_spend_held_design_and_review_capacity(self):
        budget = Budget(time.monotonic(), held_completion_tokens=7500)
        budget.begin_attempt(8000)
        budget.begin_attempt(8000)
        with self.assertRaises(BudgetError):
            budget.begin_attempt(8000)
        self.assertEqual(budget.requests, 2)
        budget.held_completion_tokens -= 4000
        budget.begin_attempt(4000)
        budget.held_completion_tokens -= 3500
        budget.begin_attempt(3500)
        self.assertEqual(budget.reserved_completion_tokens, 23500)

    def test_design_cannot_change_expressions_or_numerical_expectations(self):
        for extra in ("computations", "checks"):
            with self.subTest(extra=extra):
                body = {"visualizations": [diagram()], extra: []}
                code, events, requests = run_fixture(self.output, visualization_responses=[completion(body)])
                self.assertEqual(code, 1)
                self.assertEqual(len(requests), 2)
                self.assertEqual(events[-1]["metadata"]["error_type"], "VisualizationDesignError")
                self.assertFalse((self.output / "index.html").exists())

    def test_bad_chart_shape_is_repaired_without_repeating_design_or_changing_cases(self):
        wrong = copy.deepcopy(lesson()["visualizations"][0])
        wrong["kind"] = "bars"  # The bound output is scalar, so executed view checks must fail.
        wrong.pop("sweep_control")
        replacement = {"controls": [], "computations": [], "visualizations": lesson()["visualizations"],
                       "teaching": {}}
        code, events, requests = run_fixture(self.output,
            [completion(lesson()), completion(replacement)],
            visualization_responses=[completion({"visualizations": [wrong]})])
        self.assertEqual(code, 0)
        self.assertEqual([r["max_tokens"] for r in requests], [8000, 4000, 3500, 3500])
        self.assertEqual(sum("VISUALIZATION DESIGN CONTRACT" in r["messages"][1]["content"] for r in requests), 1)
        self.assertTrue(any(e["metadata"].get("after_visualization_design") and e["result"] == "failed"
                            for e in events))
        saved = json.loads((self.output / "lesson.json").read_text())
        self.assertEqual(saved["checks"], lesson()["checks"])
        self.assertEqual(saved["visualizations"], lesson()["visualizations"])

    def test_truncated_design_is_terminal_without_repeating_or_skipping_review(self):
        truncated = completion({"visualizations": [diagram()]})
        truncated["choices"][0]["finish_reason"] = "length"
        code, events, requests = run_fixture(self.output, visualization_responses=[truncated])
        self.assertEqual(code, 1)
        self.assertEqual(len(requests), 2)
        self.assertEqual(events[-1]["metadata"]["reserved_completion_tokens"], 12000)
        self.assertFalse((self.output / "lesson.json").exists())
        self.assertTrue(any(e["action"] == "visualization_design" and e["result"] == "failed" for e in events))

    def test_invalid_graph_bindings_layout_and_provenance_cannot_be_promoted(self):
        changes = [
            lambda v: v["diagram"]["edges"][0].update(to="missing"),
            lambda v: v["diagram"]["nodes"][2].update(source="missing"),
            lambda v: v["diagram"]["nodes"][1].update(column=0),
            lambda v: v["diagram"].update(provenance="source_supported", evidence_ids=[]),
            lambda v: v["diagram"].update(evidence_ids=["missing"]),
            lambda v: v["diagram"]["nodes"][1].update(id="scale"),
        ]
        for mutate in changes:
            with self.subTest(mutate=mutate):
                view = diagram()
                mutate(view)
                spec = lesson()
                spec["visualizations"] = [view]
                with self.assertRaises(SpecError):
                    validate_spec(spec, SOURCE, SOURCE_URL)
        invalid = diagram()
        invalid["diagram"]["edges"][0]["to"] = "missing"
        empty = {"controls": [], "computations": [], "visualizations": [], "teaching": {}}
        code, events, _ = run_fixture(self.output, [completion(lesson()), completion(empty), completion(empty)],
                                     visualization_responses=[completion({"visualizations": [invalid]})])
        self.assertEqual(code, 1)
        self.assertEqual(events[-1]["metadata"]["error_type"], "SpecError")

    def test_node_bound_hidden_computation_is_a_visible_control_effect(self):
        spec = lesson()
        spec["visualizations"] = [diagram()]
        spec["computations"][0]["show"] = False
        spec["computations"].append({**copy.deepcopy(spec["computations"][0]), "id": "constant",
                                     "expression": "1", "show": True})
        compiled, _ = validate_spec(spec, SOURCE, SOURCE_URL)
        records = check_runtime(spec, compiled)
        self.assertTrue(all(r["status"] == "passed" for r in records), records)

    def test_diagram_labels_are_sanitized_mathml_and_provider_nulls_are_accepted(self):
        spec = lesson()
        view = diagram()
        view["diagram"]["nodes"][0]["label"] = '**Scale** $a$ <img src=x onerror=alert(1)>'
        spec["visualizations"] = [view]
        page = render(spec, {})
        validate_html(page, spec)
        self.assertIn('<strong>Scale</strong>', page)
        self.assertIn('id="diagram-node-mechanism-scale"', page)
        self.assertIn('id="plot-label-mechanism-edges-0"', page)
        self.assertIn('<math', page)
        self.assertIn('&lt;img', page)
        view.update(source=None, x_label=None, y_label=None)
        view["diagram"]["nodes"][0]["source"] = None
        normalized = normalize_optional(spec)
        validate_spec(normalized, SOURCE, SOURCE_URL)
        schema = provider_schema(VISUALIZATION_DESIGN_SCHEMA)
        self.assertIn("diagram", schema["properties"]["visualizations"]["items"]["required"])


if __name__ == "__main__":
    unittest.main()
