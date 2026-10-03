"""Render saved source-backed developer lessons; no model, key, or network.

These deliberately authored fixtures prove the renderer/core boundary. They do
not establish model-generation quality. All pages are rendered from saved JSON.
"""
import argparse
import copy
import json
from pathlib import Path

from src.renderer import render
from src.runtime_checker import check_runtime
from src.validator import validate_html, validate_spec
from tests.science.test_shared_core import FIXTURES, mechanism_spec


TEACHING = {
    "entropy": (
        "Entropy: uncertainty in a distribution",
        "Divide nonnegative weights by their sum to obtain probabilities. Entropy measures the uncertainty of that distribution in bits.",
        "A uniform distribution over more possible outcomes is less predictable; a certain outcome has zero uncertainty.",
        [("Normalize weights", "Divide each weight by their positive total; this is probability normalization."),
         ("Add uncertainty contributions", "Calculate -p*log2(p) for each outcome and add them. A zero-probability outcome contributes exactly zero.")],
        [("Set one weight to 1 and the others to 0.", "Entropy becomes 0 bits.", "There is only one possible outcome."),
         ("Compare two equal weights with four equal weights.", "Entropy rises from 1 to 2 bits.", "The number of equally likely outcomes doubles.")],
        ["Weights must be nonnegative and have a positive sum.", "This is discrete entropy, not thermodynamic or differential entropy."]),
    "attention": (
        "Attention: score, normalize, combine",
        "Queries score keys using dot products. Divide the scores by the square root of the key dimension, apply softmax to each row, then combine values using those weights.",
        "Each query can combine information from several values according to its compatibility with their keys.",
        [("Compute compatibility", "Multiply Q by the transpose of K. The key dimension is the actual number of columns, not the number of tokens."),
         ("Scale and normalize", "Scaled mode divides scores by sqrt(d_k). Softmax makes each row nonnegative with sum one."),
         ("Combine values", "Multiply the weight matrix by V. The output can have a different feature dimension from Q and K.")],
        [("Uncheck the scaling comparison.", "The identity example gives a larger leading weight.", "Larger score differences make softmax more concentrated."),
         ("Change one entry of V.", "Outputs change while the attention weights remain fixed.", "Q and K determine weights; V determines the values being combined.")],
        ["This is a single-head teaching example without learned projections, masking, dropout, or training.", "Unscaled mode is a teaching comparison; the paper uses scaled scores.", "Matrix dimensions stay fixed in this lesson."]),
    "enzyme_kinetics": (
        "Enzyme kinetics: initial-rate saturation",
        "For this initial-rate model, v = Vmax*S/(Km+S). The substrate concentration S and Km use the same concentration unit.",
        "The relationship explains why adding substrate has a diminishing effect as the rate approaches Vmax.",
        [("Find the fractional rate", "Compute S/(Km+S), which lies between zero and one for S>=0 and Km>0."),
         ("Convert to the reaction rate", "Multiply the fraction by Vmax. At S=Km the rate is half Vmax.")],
        [("Set S equal to Km.", "The rate is half Vmax.", "The numerator is half the denominator."),
         ("Increase Km while keeping S and Vmax fixed.", "The predicted rate falls.", "A larger denominator lowers S/(Km+S).")],
        ["Teaching parameter values do not fit the original invertase measurements.", "This initial-rate saturation model omits product inhibition and substrate depletion.", "Km is positive; this model alone does not make Km a universal measure of binding affinity."]),
    "logistic_map": (
        "Logistic map: four repeated updates",
        "Apply x_next = r*x*(1-x) repeatedly, using each output as the next input. This lesson displays the initial state and four updates.",
        "A simple nonlinear recurrence can produce different behavior as the growth parameter changes.",
        [("Choose a starting state", "x0 is a dimensionless state between zero and one; r is between zero and four."),
         ("Repeat the update", "Each step uses the preceding value. The bars are successive states, not independent samples."),
         ("Interpret a short trajectory", "Four updates illustrate recurrence but cannot establish long-run chaos or stability.")],
        [("Set r=4 and x0=0.5.", "The sequence starts 0.5, 1, 0, 0, 0.", "The first update reaches one and the next reaches zero."),
         ("Set r=2 and x0=0.5.", "All shown values remain 0.5.", "The initial state is a fixed point for this parameter.")],
        ["Only four updates are displayed; this is not a bifurcation diagram or evidence of chaos.", "Finite precision can alter long trajectories near unstable states.", "The mathematical boundary states 0 and 1 are included for testing."]),
}


def saved_lesson(name):
    fixture = FIXTURES[name]
    default_case = {"entropy": 2, "attention": 1, "enzyme_kinetics": 1, "logistic_map": 0}[name]
    state = fixture["cases"][default_case]["state"]
    spec = mechanism_spec(name, state)
    title, concept, why, steps, explorations, limitations = TEACHING[name]
    spec.update(schema_version=2, title=title, concept_summary=concept, why_it_matters=why,
                explanation_steps=[{"heading": h, "body": b, "provenance": "teaching_simplification", "evidence_ids": []} for h, b in steps],
                terms=[{"symbol": c["id"], "meaning": c["label"]} for c in spec["controls"]],
                equations=[{"expression": fixture["relationship"], "explanation": "Plain-text transcription of the cited relationship; parameter names and numeric values are chosen for teaching.", "provenance": "source_supported", "evidence_ids": ["mechanism"]}],
                explorations=[dict(zip(("change", "observe", "why"), x)) for x in explorations],
                limitations=limitations,
                grounding={"paper_title": fixture["source_title"], "source_url": fixture["source_url"],
                           "source_claims": [{"id": "mechanism", "claim": fixture["relationship"], "locator": fixture["locator"], "quote": fixture["quote"]}],
                           "teaching_simplifications": ["Small parameter examples are authored development fixtures, not model output or original experimental measurements."]})
    labels = {"weights": "Outcome weights", "q": "Queries Q", "k": "Keys K", "v": "Values V", "scaled": "Use scaled scores", "substrate": "Substrate concentration S", "km": "Michaelis constant Km", "vmax": "Maximum rate Vmax", "growth": "Growth parameter r", "initial": "Initial state x0"}
    for control in spec["controls"]:
        control.update(label=labels[control["id"]], meaning={
            "weights": "Edit nonnegative weights; changing outcome count preserves retained values and appends zeros.",
            "q": "Rows are queries; columns are key features.", "k": "Rows are keys; columns match query features.",
            "v": "Rows match keys; columns are output features.", "scaled": "Compare the paper's scaled scores with an unscaled teaching variant.",
            "substrate": "Substrate concentration in teaching concentration units.", "km": "Positive concentration parameter in the same units as S.",
            "vmax": "Maximum reaction rate in teaching rate units.", "growth": "Dimensionless growth parameter between zero and four.",
            "initial": "Starting population fraction between zero and one."}[control["id"]])
        if control["id"] == "weights":
            control.update(min_items=2, max_items=8, max=100)
        elif control["id"] in ("substrate", "growth", "initial"):
            control["kind"] = "range"
            if control["id"] == "substrate":
                control["max"] = 20
    for c in spec["computations"]:
        c.update(show=c["id"] not in ("step_two", "step_three", "step_four"), unit="", provenance="teaching_simplification", evidence_ids=[])
        c["label"] = {"probabilities": "Outcome probabilities", "entropy_bits": "Entropy H", "max_entropy_bits": "Maximum entropy for this outcome count",
                      "scores": "Scaled compatibility scores", "weights": "Attention weights",
                      "attention_output": "Weighted values", "fraction": "Fraction of maximum rate",
                      "rate": "Reaction rate v", "next_value": "First update x1",
                      "trajectory": "Initial state and successive updates"}.get(c["id"], c["id"])
        c["unit"] = {"entropy_bits": "bits", "max_entropy_bits": "bits", "rate": "teaching rate units",
                     "fraction": "dimensionless", "next_value": "dimensionless",
                     "trajectory": "dimensionless"}.get(c["id"], "")
    spec["terms"] = [{"symbol": c["id"], "meaning": c["meaning"]} for c in spec["controls"]]
    views = {
        "entropy": [{"id": "distribution", "kind": "bars", "title": "Outcome probabilities", "source": "probabilities", "x_label": "Outcome", "y_label": "Probability", "value_label": "Probability"}],
        "attention": [{"id": "attention_weights", "kind": "heatmap", "title": "Attention weights", "source": "weights", "x_label": "Key token", "y_label": "Query token", "row_labels": ["Query A", "Query B"], "column_labels": ["Key A", "Key B"]},
                      {"id": "output_matrix", "kind": "heatmap", "title": "Weighted output", "source": "attention_output", "x_label": "Output feature", "y_label": "Query token", "row_labels": ["Query A", "Query B"], "column_labels": ["Feature 1", "Feature 2"]}],
        "enzyme_kinetics": [{"id": "saturation", "kind": "line", "title": "Rate as substrate changes", "source": "rate", "sweep_control": "substrate", "x_label": "Substrate concentration S", "y_label": "Reaction rate v"}],
        "logistic_map": [{"id": "successive_states", "kind": "bars", "title": "Initial state and four updates", "source": "trajectory", "x_label": "Update number", "y_label": "State x", "labels": ["x0", "x1", "x2", "x3", "x4"], "value_label": "State"}],
    }
    spec["visualizations"] = views[name]
    accepted_cases = fixture["cases"] if name != "attention" else fixture["cases"][1:3]
    spec["checks"] = [{"id": c["id"], "name": c["id"].replace("_", " "), "state": copy.deepcopy(c["state"]), "expected": copy.deepcopy(c["expected"]), "atol": 1e-10, "rtol": 1e-10} for c in accepted_cases]
    return spec


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("review-out/science"))
    parser.add_argument("--cases-output", type=Path, help="Optionally export source-backed inputs for fresh model runs.")
    args = parser.parse_args()
    for name, fixture in FIXTURES.items():
        output = args.output / name
        output.mkdir(parents=True, exist_ok=True)
        spec = saved_lesson(name)
        source = f'{fixture["source_title"]}. {fixture["locator"]}.\n{fixture["quote"]}\nEquation transcription: {fixture["relationship"]}'
        case = {"source_url": fixture["source_url"], "focus": TEACHING[name][1], "audience": "Undergraduate learner", "excerpt": source}
        (output / "case.json").write_text(json.dumps(case, indent=2, ensure_ascii=False), encoding="utf-8")
        if args.cases_output:
            args.cases_output.mkdir(parents=True, exist_ok=True)
            (args.cases_output / f"{name}.json").write_text(json.dumps(case, indent=2, ensure_ascii=False), encoding="utf-8")
        lesson_path = output / "lesson.json"
        lesson_path.write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")
        # Read the saved artifact back; never alter the generated HTML by hand.
        saved = json.loads(lesson_path.read_text(encoding="utf-8"))
        compiled, _ = validate_spec(saved, source, fixture["source_url"])
        checks = check_runtime(saved, compiled)
        (output / "checks.json").write_text(json.dumps(checks, indent=2), encoding="utf-8")
        failures = [c for c in checks if c["status"] != "passed"]
        if failures:
            raise RuntimeError(f"{name}: runtime checks failed: {failures}")
        page = render(saved, compiled)
        validate_html(page, saved)
        (output / "index.html").write_text(page, encoding="utf-8")
        print(f"{name}: saved developer fixture -> exact shared-core checks -> {output / 'index.html'}")


if __name__ == "__main__":
    main()
