"""Print the current status and the newest progress entries (D43).

Each progress entry is its own file in docs/progress/, named YYYY-MM-DD_HHMM_<task>_<person>.md,
so two pull requests never edit the same lines. File names sort by time.

Run:  python scripts/show_progress.py        (newest 5)
      python scripts/show_progress.py 15     (newest 15)
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    try:
        count = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    except ValueError:
        count = 5
    progress = (ROOT / "docs" / "PROGRESS.md").read_text(encoding="utf-8")
    start = progress.find("## Current status")
    end = progress.find("\n## ", start + 1)
    if start != -1:
        print(progress[start:end if end != -1 else None].strip(), "\n")
    entries = sorted((ROOT / "docs" / "progress").glob("20*.md"), reverse=True)[:count]
    print(f"Newest {len(entries)} progress entries (docs/progress/):\n")
    for path in entries:
        print("=" * 72)
        print(path.name)
        print(path.read_text(encoding="utf-8").strip(), "\n")
    if not entries:
        print("(none yet; older history is in docs/PROGRESS.md under 'Log')")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
