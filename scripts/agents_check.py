from __future__ import annotations

import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENTS = ROOT / "ai" / "agents"
SKILLS = ROOT / "ai" / "skills"
REQUIRED = [
    ROOT / "AGENTS.md",
    ROOT / "CLAUDE.md",
    ROOT / "PROJECT.md",
    ROOT / "README.md",
    ROOT / "Makefile",
    ROOT / "project.sh",
    AGENTS / "architect.md",
    AGENTS / "developer.md",
    AGENTS / "reviewer.md",
    AGENTS / "documentation.md",
    AGENTS / "environment.md",
    SKILLS / "environment-observability" / "SKILL.md",
    SKILLS / "makefile-workflow" / "SKILL.md",
    SKILLS / "testing-quality" / "SKILL.md",
    SKILLS / "documentation" / "SKILL.md",
]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def list_agents() -> None:
    for path in sorted(AGENTS.glob("*.md")):
        print(rel(path))


def list_skills() -> None:
    for path in sorted(SKILLS.glob("*/SKILL.md")):
        print(rel(path))


def check() -> int:
    missing = [path for path in REQUIRED if not path.is_file()]
    if missing:
        for path in missing:
            print(f"MISSING: {rel(path)}")
        return 2
    print(f"Agent/skill scaffold: OK ({len(REQUIRED)} required files present)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list-agents", action="store_true")
    parser.add_argument("--list-skills", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.list_agents:
        list_agents()
    if args.list_skills:
        list_skills()
    if args.check:
        return check()
    if not (args.list_agents or args.list_skills or args.check):
        parser.error("choose an action")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
