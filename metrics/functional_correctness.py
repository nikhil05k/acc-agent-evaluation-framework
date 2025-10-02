from common.evaluators.python_code_eval import evaluate_code_output

def score(output_text: str, expected_sequence: list[int]) -> dict:
    ev = evaluate_code_output(output_text, expected_sequence)
    return {
        "functional_correctness": 1.0 if ev["ok"] else 0.0,
        "functional_correctness_details": ev,
    }
