from pathlib import Path

def load_prompt(filename: str) -> str:
    path = Path(__file__).parent.parent / "prompts" / filename
    with open(path, "r", encoding="utf-8") as f:
        return f.read() 