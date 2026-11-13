"""Says which .env keys are filled, WITHOUT printing any value.

Run from the repo root:  python scripts/check_env.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ["TELEGRAM_BOT_TOKEN", "GEMINI_API_KEY", "GROQ_API_KEY"]


def read_env(path: Path) -> dict[str, str]:
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            values[key.strip()] = value.strip()
    return values


def main() -> int:
    env_path = ROOT / ".env"
    if not env_path.exists():
        print("No .env file. Copy .env.example to .env and fill in your own keys.")
        return 1
    env = read_env(env_path)
    example = read_env(ROOT / ".env.example")
    missing = 0
    for key in example:
        filled = bool(env.get(key))
        must = key in REQUIRED
        if not filled and must:
            missing += 1
        mark = "set" if filled else ("EMPTY  <- fill this in" if must else "empty (default is used)")
        print(f"  {key:<22} {mark}")
    print("All required keys are set." if not missing else f"{missing} required key(s) are empty.")
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
