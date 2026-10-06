"""Speech: which engine reads which language, and one entry point that returns a WAV file.

Silero v5 (Russian, Kabardian, Ukrainian, Belarusian, Kazakh, Kyrgyz, Tatar, Bashkir, Uzbek, Azerbaijani, Tajik;
Georgian and Armenian through the Kabardian voice) and the Baltic Piper model (Latvian, Lithuanian, Estonian) on every
system; the system's own voices for everything else — and as an alternative wherever one is installed: Apple voices
on macOS, Windows voices (OneCore and SAPI) on Windows. Linux has no system voices worth using.
"""
from __future__ import annotations

import io
import threading

import numpy as np

from .. import languages, models
from ..system import SYSTEM_VOICES


def _system():
    """The module of this system's voices, or None."""
    if SYSTEM_VOICES == "apple":
        from . import apple
        return apple
    if SYSTEM_VOICES == "windows":
        from . import windows
        return windows
    return None


class Speech:
    def __init__(self):
        self._silero = None
        self._baltic = None
        self._lock = threading.Lock()

    @property
    def silero(self):
        with self._lock:
            if self._silero is None:
                if not models.installed("silero"):
                    raise RuntimeError("model 'silero' is not installed: run kabardian-download-models silero")
                from .silero import Silero
                self._silero = Silero()
            return self._silero

    @property
    def baltic(self):
        with self._lock:
            if self._baltic is None:
                if not models.installed("baltic"):
                    raise RuntimeError("model 'baltic' is not installed: run kabardian-download-models baltic")
                from .piper_baltic import BalticPiper
                self._baltic = BalticPiper()
            return self._baltic

    def options(self, lang: str) -> list:
        """Voices for the language page and the voice menu: [{'id', 'label', 'engine'}], the default first."""
        out = []
        engine, voice = languages.SPEECH.get(lang, (None, None))
        if engine == "silero" and models.installed("silero"):
            out.append({"id": "silero", "label": f"Silero · {languages.name(lang)}", "engine": "silero"})
        if engine == "baltic" and models.installed("baltic"):
            try:
                for v in self.baltic.voice_list(lang):
                    out.append({"id": f"baltic:{v['speaker']}", "label": f"{v['name']} ({v['sex']})", "engine": "baltic"})
            except Exception:
                pass
        sysv = _system()
        if sysv is not None:
            try:
                for v in sysv.for_language(lang)[:8]:
                    if SYSTEM_VOICES == "apple":
                        out.append({"id": f"apple:{v['name']}", "label": f"Apple · {v['name']}", "engine": "apple"})
                    else:
                        out.append({"id": f"win:{v['id']}", "label": f"Windows · {v['name']}", "engine": "windows"})
            except Exception:
                pass
        return out

    def synthesize(self, text: str, lang: str, voice: str | None = None, speed: float = 1.0):
        """→ (samples float32, sample_rate)."""
        opts = self.options(lang)
        if not opts:
            raise RuntimeError(f"no voice for {lang!r}")
        voice = voice or opts[0]["id"]
        if voice == "silero":
            return self.silero.synthesize(text, lang, speed), 48000
        if voice.startswith("baltic:"):
            return self.baltic.synthesize(text, lang, voice.split(":", 1)[1], speed), 22050
        if voice.startswith("apple:"):
            from . import apple
            return apple.synthesize(text, lang, voice.split(":", 1)[1], speed), apple.SAMPLE_RATE
        if voice.startswith("win:"):
            from . import windows
            return windows.synthesize(text, lang, voice.split(":", 1)[1], speed)
        raise RuntimeError(f"unknown voice {voice!r}")

    def synthesize_marked(self, text: str, lang: str, voice: str | None = None, speed: float = 1.0):
        """Sentence by sentence, with timings for highlighting:
        → (samples, rate, sentences [{start, end, t0, t1}], words [{start, end, t0, t1}]); start/end are character
        offsets in `text`, t0/t1 seconds in the audio. Words are timed for Silero voices (the model's durations);
        the Baltic model and Apple voices are timed by sentence."""
        from ..translator import split_sentences
        opts = self.options(lang)
        if not opts:
            raise RuntimeError(f"no voice for {lang!r}")
        voice = voice or opts[0]["id"]
        rate = 48000 if voice == "silero" else 22050 if voice.startswith(("baltic:", "apple:")) else None
        chunks, sentences, words, t, pos = [], [], [], 0.0, 0
        for sent in split_sentences(text):
            start = text.find(sent, pos)
            start = pos if start < 0 else start
            pos = start + len(sent)
            if voice == "silero":
                y, w = self.silero.synthesize_marked(sent, lang, speed)
                words += [{"start": start + a, "end": start + b, "t0": round(float(t + t0), 3), "t1": round(float(t + t1), 3)}
                          for a, b, t0, t1 in w]
            else:
                y, got = self.synthesize(sent, lang, voice, speed)
                rate = rate or got                       # a Windows voice reports its own rate
            dur = len(y) / rate
            sentences.append({"start": start, "end": start + len(sent), "t0": round(float(t), 3), "t1": round(float(t + dur), 3)})
            pause = np.zeros(int(0.18 * rate), np.float32)
            chunks += [y, pause]
            t += dur + len(pause) / rate
        rate = rate or 22050
        samples = np.concatenate(chunks) if chunks else np.zeros(int(0.35 * rate), np.float32)
        return samples, rate, sentences, words

    @staticmethod
    def wav_bytes(samples: np.ndarray, rate: int) -> bytes:
        import soundfile as sf
        buf = io.BytesIO()
        sf.write(buf, np.clip(samples, -1, 1), rate, format="WAV", subtype="PCM_16")
        return buf.getvalue()
