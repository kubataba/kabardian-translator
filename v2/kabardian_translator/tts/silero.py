"""Silero v5 (v5_cis_base, no-stress model) on ONNX Runtime — the SayFable app's export, five graphs, no PyTorch. Ported from `SileroTokenizer.swift`, `SileroTTSEngine.swift` and `SileroISTFT.swift`:

  text → stress marks (tts/stress.py: silero-stress logic over our exported networks) → tokens (language alphabet filter)
  → dur_predictor → durations round(exp(x) − 1), first ≤ 5 → pitch_predictor → mel_encoder
  → length regulation (rows repeated by duration, the two streams summed) → mel_decoder → vocoder
  → spectrum mag·(x + iy) → inverse STFT (n_fft 2400, hop 600, Hann, centered) → 48 kHz.

Every language offers all the speakers the model has for it (names and sex from the app's markup,
data/silero-voices.json); the first is the default. Georgian and Armenian are read by default by the Kabardian voice
after the v1 transliteration (as in v1); Georgian also by Vika and Armenian by Zara, through the app's own tables
(`SileroTransliterator`: Georgian → Russian Cyrillic, Armenian → Cyrillic with the ու digraph).
"""
from __future__ import annotations

import json
import re
import threading
from importlib import resources
from pathlib import Path

import numpy as np

from .. import models

SAMPLE_RATE = 48000
N_FFT, HOP, BINS = 2400, 600, 1201
MAX_CHARS = 600            # the mel decoder holds 5000 frames ≈ 62 s; longer text is split (app, prompt 200)

SOS, EOS = 2, 1
SYMBOLS = "!'+,-.:;?hабвгдежзийклмнопрстуфхцчшщъыьэюяёєіїјўґғҕҗҙқҝҡңҥҫүұҳҷҹһӑӗәӝӟӣӥӧөӯӱӳӵӏ—… "
SYMBOL_ID = {c: i + 3 for i, c in enumerate(SYMBOLS)}
ALPHABETS = {
    "kaz": "абвгдежзийклмнопрстуфхцчшщыьэюяіғқңүұһәө", "ru": "абвгдеёжзийклмнопрстуфхцчшщъыьэюя",
    "uzb": "абвгдежзийклмнопрстуфхцчшъьэюяёўғқҳ", "aze": "абвгғдеәжзиыјкҝлмноөпрстуүфхһчҹш",
    "ukr": "абвгґдеєжзиіїйклмнопрстуфхцчшщьюя", "bak": "абвгдежзийклмнопрстуфхцчшщъыьэюяёғҙҡңҫүһәө",
    "tat": "абвгдежзийклмнопрстуфхцчшъыьэюяҗңүһәө", "bel": "абвгдежзйклмнопрстуфхцчшыьэюяёіў",
    "tgk": "абвгдежзийклмнопрстуфхчшъэюяёғқҳҷӣӯ", "kir": "абвгдежзийклмнопрстуфхцчшыьэюяёңүө",
    "kbd": "абвгдежзийклмнопрстуфхцчшщъыьэюяӏ", "hye": "абвгдежзийклмнопрстуфхцчшщъыьэюя",
    "kat": "абвгдежзийклмнопрстуфхцчшщъыьэюя",
}
EXTRA = set("!'+,-.:;?h —…")
AZE_LATIN = [("ch", "ч"), ("sh", "ш"), ("zh", "ж"), ("a", "а"), ("b", "б"), ("c", "ҹ"), ("ç", "ч"), ("d", "д"),
             ("e", "е"), ("ə", "ә"), ("f", "ф"), ("g", "ҝ"), ("ğ", "ғ"), ("h", "һ"), ("x", "х"), ("i", "ы"),
             ("ı", "ы"), ("j", "ж"), ("k", "к"), ("q", "г"), ("l", "л"), ("m", "м"), ("n", "н"), ("o", "о"),
             ("ö", "ө"), ("p", "п"), ("r", "р"), ("s", "с"), ("ş", "ш"), ("t", "т"), ("u", "у"), ("ü", "ү"),
             ("v", "в"), ("y", "ј"), ("z", "з")]
UZB_LATIN = [("o'", "ў"), ("g'", "ғ"), ("sh", "ш"), ("ch", "ч"), ("ng", "нг"), ("a", "а"), ("b", "б"), ("d", "д"),
             ("e", "э"), ("f", "ф"), ("g", "г"), ("h", "ҳ"), ("i", "и"), ("j", "ж"), ("k", "к"), ("l", "л"),
             ("m", "м"), ("n", "н"), ("o", "о"), ("p", "п"), ("q", "қ"), ("r", "р"), ("s", "с"), ("t", "т"),
             ("u", "у"), ("v", "в"), ("x", "х"), ("y", "й"), ("z", "з"), ("'", "ъ")]
SPEAKERS = {
    "aze_gamat": 0, "bak_aigul": 1, "bak_alfia": 2, "bak_alfia2": 3, "bak_miyau": 4, "bak_ramilia": 5,
    "bel_anatoliy": 6, "bel_dmitriy": 7, "bel_larisa": 8, "chv_ekaterina": 9, "erz_alexandr": 10, "hye_zara": 11,
    "kat_vika": 12, "kaz_zhadyra": 13, "kaz_zhazira": 14, "kbd_eduard": 15, "kir_nurgul": 16, "kjh_karina": 17,
    "kjh_sibday": 18, "mdf_oksana": 19, "ru_aigul": 20, "ru_albina": 21, "ru_alexandr": 22, "ru_alfia": 23,
    "ru_alfia2": 24, "ru_bogdan": 25, "ru_dmitriy": 26, "ru_eduard": 27, "ru_ekaterina": 28, "ru_gamat": 29,
    "ru_igor": 30, "ru_karina": 31, "ru_kejilgan": 32, "ru_kermen": 33, "ru_marat": 34, "ru_miyau": 35,
    "ru_nurgul": 36, "ru_oksana": 37, "ru_onaoy": 38, "ru_ramilia": 39, "ru_roman": 40, "ru_safarhuja": 41,
    "ru_saida": 42, "ru_sibday": 43, "ru_vika": 44, "ru_zara": 45, "ru_zhadyra": 46, "ru_zhazira": 47,
    "ru_zinaida": 48, "sah_zinaida": 49, "tat_albina": 50, "tat_marat": 51, "tgk_onaoy": 52, "tgk_safarhuja": 53,
    "udm_bogdan": 54, "ukr_igor": 55, "ukr_roman": 56, "uzb_saida": 57, "xal_kejilgan": 58, "xal_kermen": 59,
}
# our language code → (speaker, stress accentor). Voices are the app's catalogue defaults.
VOICES = {
    "ru": ("ru_eduard", "ru"), "kbd": ("kbd_eduard", None), "uk": ("ukr_igor", "ukr"), "be": ("bel_anatoliy", "bel"),
    "kk": ("kaz_zhadyra", None), "ky": ("kir_nurgul", None), "tt": ("tat_albina", None),
    "ba": ("bak_aigul", None), "uz": ("uzb_saida", None), "az": ("aze_gamat", None),
    "tg": ("tgk_onaoy", None), "hy": ("kbd_eduard", None), "ka": ("kbd_eduard", None),
}
# The model is the no-stress v5: «+» marks are needed only for Russian, Ukrainian and Belarusian (curator, 06.10).

# The speakers of a language: the default above first, then every speaker the model has for that language.
_PREFIX = {"ru": "ru", "uk": "ukr", "be": "bel", "kk": "kaz", "ky": "kir", "tt": "tat", "ba": "bak", "uz": "uzb",
           "az": "aze", "tg": "tgk", "kbd": "kbd"}
_EXTRA = {"hy": ["hye_zara"], "ka": ["kat_vika"]}
VOICE_NAMES = json.loads(resources.files("kabardian_translator").joinpath("data/silero-voices.json").read_text("utf-8"))


def speakers(lang: str) -> list:
    """All speakers for a language, the default first, then by name."""
    if lang not in VOICES:
        return []
    default = VOICES[lang][0]
    pre = _PREFIX.get(lang)
    rest = [s for s in SPEAKERS if pre and s.split("_")[0] == pre and s != default] + _EXTRA.get(lang, [])
    return [default] + sorted(rest, key=lambda s: VOICE_NAMES.get(s, {}).get("name", s))


# The app's tables for the Georgian and Armenian speakers (SileroTransliterator.swift: katMap, hyeMap).
KAT_MAP = {"ა": "а", "ბ": "б", "გ": "г", "დ": "д", "ე": "э", "ვ": "в", "ზ": "з", "თ": "т", "ი": "и", "კ": "к",
           "ლ": "л", "მ": "м", "ნ": "н", "ო": "о", "პ": "п", "ჟ": "ж", "რ": "р", "ს": "с", "ტ": "т", "უ": "у",
           "ფ": "п", "ქ": "к", "ღ": "г", "ყ": "к", "შ": "ш", "ჩ": "ч", "ც": "ц", "ძ": "дз", "წ": "ц", "ჭ": "ч",
           "ხ": "х", "ჯ": "дж", "ჰ": "х", "ჱ": "э", "ჲ": "й", "ჳ": "уи", "ჴ": "х", "ჵ": "о", "ჶ": "ф", "ჷ": "ы",
           "ჸ": "", "ჹ": "г", "ჺ": "л"}
HYE_MAP = {"ա": "а", "բ": "б", "գ": "г", "դ": "д", "ե": "е", "զ": "з", "է": "э", "ը": "ы", "թ": "т", "ժ": "ж",
           "ի": "и", "լ": "л", "խ": "х", "ծ": "ц", "կ": "к", "հ": "х", "ձ": "дз", "ղ": "г", "ճ": "ч", "մ": "м",
           "յ": "й", "ն": "н", "շ": "ш", "ո": "во", "չ": "ч", "պ": "п", "ջ": "дж", "ռ": "р", "ս": "с", "վ": "в",
           "տ": "т", "ր": "р", "ց": "ц", "ւ": "у", "փ": "п", "ք": "к", "օ": "о", "ֆ": "ф", "և": "эв"}


def _script_text(text: str, lang: str, speaker: str) -> str:
    """Georgian or Armenian text for a Cyrillic speaker."""
    if lang not in ("ka", "hy"):
        return text
    pre = speaker.split("_")[0]
    if pre == "kat":
        return "".join(KAT_MAP.get(c, c) for c in text.lower())
    if pre == "hye":
        t = text.lower().replace("ու", "у")
        return "".join(HYE_MAP.get(c, c) for c in t)
    from .transliterator import transliterator
    return transliterator.transliterate_for_tts(text, {"ka": "kat_Geor", "hy": "hye_Armn"}[lang])


def _replace_all(text, rules):
    out, i = [], 0
    while i < len(text):
        for a, b in rules:
            if text.startswith(a, i):
                out.append(b)
                i += len(a)
                break
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def tokenize(text: str, speaker: str) -> list:
    lang = speaker.split("_")[0]
    t = text.strip().replace("–", "—").replace("―", "—").replace("‑", "-")
    if lang == "kbd":
        t = "".join({"I": "ӏ", "l": "ӏ", "1": "ӏ", "|": "ӏ", "Ӏ": "ӏ"}.get(c, c) for c in t)
    t = t.replace("\n", ". ")
    latin = sum(1 for c in t.lower() if c.isascii() and c.isalpha())
    cyr = sum(1 for c in t.lower() if "Ѐ" <= c <= "ԯ")
    if lang == "aze" and latin > cyr:
        t = _replace_all(t.lower(), AZE_LATIN)
    elif lang == "uzb" and latin > cyr:
        t = _replace_all(t.lower(), UZB_LATIN)
    else:
        t = t.lower()
    allowed = EXTRA | set(ALPHABETS.get(lang, ""))
    return [SOS] + [SYMBOL_ID[c] for c in t if c in allowed and c in SYMBOL_ID] + [EOS]


def split_for_decoder(text: str, max_chars: int = MAX_CHARS) -> list:
    pieces, rest = [], text.strip()
    while len(rest) > max_chars:
        head = rest[:max_chars]
        cut = max((head.rfind(c) for c in ".!?…"), default=-1)
        if cut < max_chars // 3:
            cut = max(head.rfind(","), head.rfind(";"), head.rfind(":"))
        if cut < max_chars // 3:
            cut = head.rfind(" ")
        if cut <= 0:
            cut = max_chars - 1
        pieces.append(rest[:cut + 1].strip())
        rest = rest[cut + 1:].strip()
    if rest:
        pieces.append(rest)
    return pieces


def istft(spec: np.ndarray) -> np.ndarray:
    """spec [1201, T] complex → samples; torch.istft(center=True, hann, n_fft 2400, hop 600) semantics."""
    frames = np.fft.irfft(spec, n=N_FFT, axis=0)                     # [2400, T]
    win = 0.5 - 0.5 * np.cos(2 * np.pi * np.arange(N_FFT) / N_FFT)
    T = spec.shape[1]
    size = (T - 1) * HOP + N_FFT
    y = np.zeros(size)
    env = np.zeros(size)
    w2 = win * win
    for t in range(T):
        s = t * HOP
        y[s:s + N_FFT] += frames[:, t] * win
        env[s:s + N_FFT] += w2
    pad = (N_FFT - HOP) // 2
    return (y[pad:size - pad] / np.maximum(env[pad:size - pad], 1e-11)).astype(np.float32)


class Silero:
    def __init__(self, folder: Path | None = None, threads: int = 0):
        import onnxruntime as ort
        f = Path(folder or models.folder("silero"))
        self.folder = f
        o = ort.SessionOptions()
        o.log_severity_level = 3
        if threads:
            o.intra_op_num_threads = threads
        self.s = {n: ort.InferenceSession(str(f / f"{n}.onnx"), o, providers=["CPUExecutionProvider"])
                  for n in ("dur_predictor", "pitch_predictor", "mel_encoder", "mel_decoder", "vocoder")}
        self.accentors = {}
        self.lock = threading.Lock()

    def _run(self, name, *inputs):
        sess = self.s[name]
        return sess.run(None, {i.name: x for i, x in zip(sess.get_inputs(), inputs)})

    def _accent(self, text, code):
        if code is None:
            return text
        if code not in self.accentors:
            try:
                from .stress import load_accentor
                self.accentors[code] = load_accentor(code, self.folder)
            except Exception:
                self.accentors[code] = None       # no stress marks: the voice still reads, flatter
        acc = self.accentors[code]
        if acc is None or "+" in text:
            return text
        try:
            return acc(text)
        except Exception:
            return text

    def _synth_tokens(self, tokens, speaker_id, speed=1.0):
        L = len(tokens)
        seq = np.array([tokens], dtype=np.int64)
        spk = np.array([speaker_id], dtype=np.int64)
        log_dur = self._run("dur_predictor", seq, spk)[0].reshape(-1)
        k = max(0.5, min(2.0, 1.0 / speed))
        dur = np.round((np.exp(log_dur.astype(np.float64)) - 1.0) * k).astype(np.int64)
        dur[0] = min(dur[0], 5)
        dur = np.maximum(dur, 0)
        if dur.sum() <= 0:
            return np.zeros(0, np.float32), dur
        pitch = self._run("pitch_predictor", seq, spk)[0].reshape(1, 1, L).astype(np.float32)
        enc, pitch_emb = self._run("mel_encoder", seq, spk, pitch)[:2]
        rows = (enc.reshape(L, -1) + pitch_emb.reshape(L, -1)).astype(np.float32)
        reg = np.repeat(rows, dur, axis=0)[None]
        mel = self._run("mel_decoder", reg)[0]
        mel = mel.reshape(1, 192, -1).astype(np.float32)
        mag, xr, yi = self._run("vocoder", mel)[:3]
        mag, xr, yi = (a.reshape(BINS, -1) for a in (mag, xr, yi))
        return istft(mag * (xr + 1j * yi)), dur

    def synthesize(self, text: str, lang: str, speed: float = 1.0, speaker: str | None = None) -> np.ndarray:
        default, accent = VOICES[lang]
        speaker = speaker if speaker in speakers(lang) else default
        text = _script_text(text, lang, speaker)
        out = []
        with self.lock:
            for piece in split_for_decoder(text, int(MAX_CHARS / max(1.0, 1.0 / speed))):
                if not re.search(r"\w", piece):
                    continue
                tokens = tokenize(self._accent(piece, accent), speaker)
                if len(tokens) > 2:
                    out.append(self._synth_tokens(tokens, SPEAKERS[speaker], speed)[0])
                    out.append(np.zeros(int(0.15 * SAMPLE_RATE), np.float32))
        return np.concatenate(out) if out else np.zeros(int(0.35 * SAMPLE_RATE), np.float32)

    def synthesize_marked(self, sentence: str, lang: str, speed: float = 1.0, speaker: str | None = None):
        """One sentence → (samples, words), words = [(char_start, char_end, t0, t1)] relative to the sentence.

        Word times come from the model's own durations: every token (a letter, a space, a mark) has a number of mel
        frames, so a word lasts from its first letter's frame to its last. Words are matched to the sentence in
        order; a word that has no letters for the voice (digits, Latin for a Cyrillic voice) gets no time of its own.
        """
        default, accent = VOICES[lang]
        speaker = speaker if speaker in speakers(lang) else default
        if lang in ("ka", "hy"):                       # transliterated: the sentence is still timed, words are not
            return self.synthesize(sentence, lang, speed, speaker), []
        lang_code = speaker.split("_")[0]
        letters = set(ALPHABETS.get(lang_code, ""))
        space_id = SYMBOL_ID[" "]
        letter_ids = {SYMBOL_ID[c] for c in letters if c in SYMBOL_ID}
        samples, words, offset = [], [], 0
        with self.lock:
            pos = 0
            for piece in split_for_decoder(sentence, int(MAX_CHARS / max(1.0, 1.0 / speed))):
                start = sentence.find(piece, pos)
                start = pos if start < 0 else start
                pos = start + len(piece)
                if not re.search(r"\w", piece):
                    continue
                tokens = tokenize(self._accent(piece, accent), speaker)
                if len(tokens) <= 2:
                    continue
                y, dur = self._synth_tokens(tokens, SPEAKERS[speaker], speed)
                if not len(y):
                    continue
                sec_per_frame = len(y) / SAMPLE_RATE / max(1, int(dur.sum()))
                cum = np.concatenate([[0], np.cumsum(dur)])
                groups, cur = [], None                 # (first token, last token) of every word with letters
                for i, tok in enumerate(tokens):
                    if tok in letter_ids:
                        cur = [i, i] if cur is None else [cur[0], i]
                    elif tok == space_id or tok in (SOS, EOS):
                        if cur:
                            groups.append(cur)
                        cur = None
                if cur:
                    groups.append(cur)
                spoken = [m for m in re.finditer(r"[\w'’+-]+", piece)
                          if letter_ids & set(tokenize(m.group(0), speaker))]
                t_off = offset / SAMPLE_RATE
                for m, (a, b) in zip(spoken, groups):
                    words.append((start + m.start(), start + m.end(),
                                  t_off + cum[a] * sec_per_frame, t_off + cum[b + 1] * sec_per_frame))
                samples.append(y)
                offset += len(y)
        return (np.concatenate(samples) if samples else np.zeros(int(0.35 * SAMPLE_RATE), np.float32)), words
