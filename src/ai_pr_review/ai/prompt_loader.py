from pathlib import Path


def load_prompt(name: str) -> str:
    prompts_dir = Path(__file__).resolve().parent / "prompts"
    prompt_path = prompts_dir / name
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {name}")
    return prompt_path.read_text(encoding="utf-8")
