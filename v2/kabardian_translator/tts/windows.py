"""Windows voices — for the languages our models do not voice, and as an alternative where they do.

Two system interfaces, both used: SAPI 5 (the desktop voices, `comtypes`) and OneCore (`Windows.Media.SpeechSynthesis`,
`winrt`), which also sees the voices of installed language packs that SAPI often does not. The list is their union,
OneCore first, a voice present in both listed once. More voices: Settings → Time & language → Speech → Add voices.
Synthesis returns 16-bit PCM; nothing is written to disk except SAPI's temporary WAV, removed at once.
"""
from __future__ import annotations

import io
import locale
import os
import tempfile
import threading
from functools import lru_cache

import numpy as np

SAMPLE_RATE = 22050          # SAPI is asked for 22 kHz 16-bit mono; OneCore's own rate is read from its WAV
_lock = threading.Lock()


def _lang_of(tag: str) -> str:
    """'en-US' / 'en_US' → 'en'; Norwegian Bokmål → 'no'."""
    code = tag.replace("_", "-").split("-")[0].lower()
    return {"nb": "no", "nn": "no"}.get(code, code)


# ---------------------------------------------------------------------------------------------- OneCore
def _onecore_voices() -> list:
    try:
        from winrt.windows.media.speechsynthesis import SpeechSynthesizer
    except Exception:
        return []
    out = []
    for v in SpeechSynthesizer.all_voices:
        out.append({"name": v.display_name, "lang": _lang_of(v.language), "locale": v.language,
                    "id": "onecore:" + v.id, "api": "onecore"})
    return out


def _onecore_wav(text: str, voice_id: str, speed: float) -> bytes:
    import asyncio
    from winrt.windows.media.speechsynthesis import SpeechSynthesizer
    from winrt.windows.storage.streams import DataReader

    async def run():
        s = SpeechSynthesizer()
        for v in SpeechSynthesizer.all_voices:
            if v.id == voice_id:
                s.voice = v
                break
        s.options.speaking_rate = max(0.5, min(3.0, speed))
        stream = await s.synthesize_text_to_stream_async(text)
        size = stream.size
        reader = DataReader(stream.get_input_stream_at(0))
        await reader.load_async(size)
        buf = bytearray(size)
        reader.read_bytes(buf)
        return bytes(buf)
    return asyncio.run(run())


# ---------------------------------------------------------------------------------------------- SAPI 5
def _sapi_voices() -> list:
    try:
        import comtypes.client
        voice = comtypes.client.CreateObject("SAPI.SpVoice")
    except Exception:
        return []
    out = []
    tokens = voice.GetVoices()
    for i in range(tokens.Count):
        t = tokens.Item(i)
        try:
            lcid = int(t.GetAttribute("Language").split(";")[0], 16)
        except Exception:
            continue
        tag = locale.windows_locale.get(lcid, "")
        if tag:
            out.append({"name": t.GetDescription(), "lang": _lang_of(tag), "locale": tag, "id": "sapi:" + t.Id,
                        "api": "sapi"})
    return out


def _sapi_wav(text: str, token_id: str, speed: float) -> bytes:
    import comtypes.client
    voice = comtypes.client.CreateObject("SAPI.SpVoice")
    tokens = voice.GetVoices()
    for i in range(tokens.Count):
        if tokens.Item(i).Id == token_id:
            voice.Voice = tokens.Item(i)
            break
    voice.Rate = int(max(-10, min(10, round((speed - 1.0) * 10))))
    fd, path = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    try:
        stream = comtypes.client.CreateObject("SAPI.SpFileStream")
        stream.Format.Type = 22                      # SAFT22kHz16BitMono
        stream.Open(path, 3)                         # SSFMCreateForWrite
        voice.AudioOutputStream = stream
        voice.Speak(text)
        stream.Close()
        with open(path, "rb") as f:
            return f.read()
    finally:
        os.remove(path)


# ---------------------------------------------------------------------------------------------- the list
@lru_cache(maxsize=1)
def voices() -> list:
    out, seen = [], set()
    for v in _onecore_voices() + _sapi_voices():
        key = (v["name"].replace("Microsoft ", "").split(" - ")[0], v["lang"])
        if key not in seen:
            seen.add(key)
            out.append(v)
    return out


def for_language(lang: str) -> list:
    """Voices for a language code, the default locale of the language first."""
    from ..languages import APPLE_LOCALES          # the same main locale per language as on macOS
    main = APPLE_LOCALES.get(lang, "").replace("_", "-").lower()
    return sorted((v for v in voices() if v["lang"] == lang),
                  key=lambda v: (v["locale"].replace("_", "-").lower() != main, v["api"] != "onecore", v["name"]))


def synthesize(text: str, lang: str, voice: str | None = None, speed: float = 1.0):
    """→ (samples float32, sample rate)."""
    import soundfile as sf
    options = for_language(lang)
    if voice is None:
        if not options:
            raise RuntimeError(f"no Windows voice installed for {lang!r}")
        voice = options[0]["id"]
    with _lock:
        wav = _onecore_wav(text, voice[len("onecore:"):], speed) if voice.startswith("onecore:") \
            else _sapi_wav(text, voice[len("sapi:"):], speed)
    y, rate = sf.read(io.BytesIO(wav), dtype="float32", always_2d=False)
    if y.ndim > 1:
        y = y.mean(axis=1)
    return y.astype(np.float32), rate
