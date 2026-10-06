"""Apple voices installed on this Mac (the system `say` command) — for the languages our models do not voice,
and as an alternative where they do. More voices: System Settings → Accessibility → Spoken Content → System voice
→ Manage Voices (Premium and Enhanced voices sound best and are picked first).
"""
from __future__ import annotations

import re
import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path

import numpy as np

SAMPLE_RATE = 22050
NOVELTY = {"Albert", "Bad News", "Bahh", "Bells", "Boing", "Bubbles", "Cellos", "Good News", "Jester", "Organ",
           "Superstar", "Trinoids", "Whisper", "Wobble", "Zarvox", "Fred", "Junior", "Ralph", "Kathy"}
LINE = re.compile(r"^(?P<name>.+?)\s+(?P<locale>[a-z]{2,3}_[A-Z0-9]{2,3})\s+#")


@lru_cache(maxsize=1)
def voices() -> list:
    try:
        out = subprocess.run(["say", "-v", "?"], capture_output=True, text=True, timeout=20).stdout
    except (OSError, subprocess.TimeoutExpired):
        return []
    res = []
    for line in out.splitlines():
        m = LINE.match(line)
        if not m:
            continue
        name = m.group("name").strip()
        if name.split(" (")[0] in NOVELTY:
            continue
        rank = 2 if "Premium" in name else 1 if "Enhanced" in name else 0
        res.append({"name": name, "locale": m.group("locale"), "lang": m.group("locale").split("_")[0], "rank": rank})
    return res


def for_language(lang: str) -> list:
    """Voices for a language code (no → nb), best first."""
    from ..languages import APPLE_LOCALES
    code = {"no": "nb"}.get(lang, lang)
    main = APPLE_LOCALES.get(lang, "")
    seen, out = set(), []
    for v in sorted((v for v in voices() if v["lang"] == code),
                    key=lambda v: (-v["rank"], v["locale"] != main, v["name"])):
        if v["name"] not in seen:
            seen.add(v["name"])
            out.append(v)
    return out


def synthesize(text: str, lang: str, voice: str | None = None, speed: float = 1.0) -> np.ndarray:
    import soundfile as sf
    options = for_language(lang)
    if voice is None:
        if not options:
            raise RuntimeError(f"no Apple voice installed for {lang!r}")
        voice = options[0]["name"]
    rate = int(180 * max(0.5, min(2.0, speed)))
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "say.wav"
        txt = Path(d) / "in.txt"
        txt.write_text(text, encoding="utf-8")
        subprocess.run(["say", "-v", voice, "-r", str(rate), "--file-format=WAVE",
                        f"--data-format=LEI16@{SAMPLE_RATE}", "-o", str(out), "-f", str(txt)],
                       check=True, capture_output=True, timeout=600)
        y, _ = sf.read(str(out), dtype="float32")
    return y.reshape(-1)
