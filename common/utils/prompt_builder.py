from __future__ import annotations
from pathlib import Path
import yaml

CASES_DIR = Path(__file__).parent.parent / "cases"

def load_case(case_name: str) -> dict:
    path = CASES_DIR / f"{case_name}.yaml"
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def get_prompts(case_cfg: dict) -> tuple[str, str]:
    sys = (case_cfg.get("prompts", {}) or {}).get("system", "").strip()
    usr = (case_cfg.get("prompts", {}) or {}).get("user", "").strip()
    return sys, usr

def get_llm_config(case_cfg: dict) -> dict:
    temperature = case_cfg.get("llm", {}).get("temperature")
    if temperature is None:
        temperature = 0
    model_name = (case_cfg.get("llm", {}) or {}).get("model")
    if model_name is None:
        raise Exception("No model name defined")
    return temperature, model_name
