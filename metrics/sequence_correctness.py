from common.evaluators.sequence_match import evaluate

def score(output_text: str, expected_sequence: list[int]) -> dict:
    ev = evaluate(output_text, expected_sequence)
    return {
        "sequence_correctness": 1.0 if ev["ok"] else 0.0,
        "sequence_correctness_details": ev,
    }
