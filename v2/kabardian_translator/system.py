"""What this computer can run, and which translator it uses for the pairs without Kabardian.

MADLAD is a Core ML model for the Apple Neural Engine, so it exists on Macs with Apple Silicon only. There it is the
default, and the user may switch to SMaLL-100 instead (lighter and about ten times faster: 289 MB instead of 1.3 GB,
but 30 languages instead of 37 and chrF 47.9 instead of 55.5 on average); only the chosen model stays on disk, and the
choice is kept in settings.json. Everywhere else SMaLL-100 translates and there is nothing to choose. Apple voices
exist on macOS only, Windows voices on Windows only; Silero and the Baltic model run everywhere.

MADLAD also needs coremltools with its native part, which exists for Python 3.11–3.13 only (coremltools 9.0 has no
build for 3.14; found 06.10). Without it a Mac uses SMaLL-100 like any other system — checked by the file, not by the
Python version, so a future coremltools for 3.14 brings MADLAD back by itself.
"""
from __future__ import annotations

import importlib.util
import json
import os
import platform
import sys
from functools import lru_cache
from pathlib import Path

IS_MAC = sys.platform == "darwin"
IS_MAC_ARM = IS_MAC and platform.machine() == "arm64"
IS_WINDOWS = sys.platform == "win32"
SYSTEM_VOICES = "apple" if IS_MAC else "windows" if IS_WINDOWS else None
ENGINES = ("madlad", "small100")
SETTINGS = Path(os.environ.get("KT_HOME", Path.home() / ".kabardian-translator")) / "settings.json"


@lru_cache(maxsize=1)
def madlad_runs() -> bool:
    """A Mac with Apple Silicon whose coremltools has its native part (it is looked for, not imported: fast)."""
    if not IS_MAC_ARM:
        return False
    spec = importlib.util.find_spec("coremltools")
    if spec is None or not spec.origin:
        return False
    return any(Path(spec.origin).parent.glob("libcoremlpython*.so"))


def madlad_blocked_by_python() -> bool:
    """Apple Silicon, but MADLAD cannot run under this Python (no native coremltools for it)."""
    return IS_MAC_ARM and not madlad_runs()


def _forced():
    """KT_TRANSLATOR=small100 forces SMaLL-100 (a test of the Linux/Windows path on a Mac); madlad only where it runs."""
    v = os.environ.get("KT_TRANSLATOR")
    return v if v == "small100" or (v == "madlad" and madlad_runs()) else None


def can_choose() -> bool:
    return madlad_runs() and _forced() is None


def _settings() -> dict:
    try:
        return json.loads(SETTINGS.read_text("utf-8"))
    except (OSError, ValueError):
        return {}


def translator() -> str:
    """The engine for every pair without Kabardian: the user's choice on a Mac with Apple Silicon (MADLAD by
    default), SMaLL-100 everywhere else."""
    forced = _forced()
    if forced:
        return forced
    if not madlad_runs():
        return "small100"
    choice = _settings().get("translator")
    return choice if choice in ENGINES else "madlad"


def set_translator(engine: str) -> None:
    if engine not in ENGINES:
        raise ValueError(f"unknown translator {engine!r}")
    s = _settings()
    s["translator"] = engine
    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS.write_text(json.dumps(s, indent=1), "utf-8")
