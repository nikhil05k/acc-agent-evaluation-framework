def score(output_text: str, required_keywords: list[str]) -> dict:
    ok = all(k in (output_text or "") for k in (required_keywords or []))
    return {"success_keywords": 1.0 if ok else 0.0}
