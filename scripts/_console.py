from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PALETTE_PATH = ROOT / "config" / "console-colors.json"
THEME_PATH = ROOT / "config" / "doctor-theme.json"


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


PALETTE = _load_json(PALETTE_PATH)
THEME = _load_json(THEME_PATH)


def color_enabled(force: bool = False, disable: bool = False) -> bool:
    if disable or os.environ.get("NO_COLOR") is not None:
        return False
    if force:
        return True
    if os.environ.get("FORCE_COLOR") not in (None, "", "0"):
        return True
    return bool(sys.stdout.isatty())


def style(text: object, role: str, *, enabled: bool) -> str:
    raw = str(text)
    if not enabled:
        return raw
    names = THEME.get(role, [])
    codes = [PALETTE[name] for name in names if name in PALETTE]
    if not codes:
        return raw
    return f"\033[{';'.join(codes)}m{raw}\033[0m"


def section(title: str, *, enabled: bool) -> None:
    print()
    print(style(f"[{title}]", "section", enabled=enabled))


def kv(key: str, value: object, *, enabled: bool, role: str = "value") -> None:
    print(
        f"{style(key, 'key', enabled=enabled)}="
        f"{style(value, role, enabled=enabled)}"
    )
