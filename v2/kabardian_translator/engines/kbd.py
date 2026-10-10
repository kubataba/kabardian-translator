"""Our Russian ↔ Kabardian translator (package kbd-translate-v2, int8 ONNX — the SayFable app's model; the desktop build with 7-bit weights).

The pipeline is the app's (prompts 408, 410, 414), ported from its Python reference:
  * one model for both directions; the target tag `>>kbd<<` / `>>ru<<` is the first source token;
  * beam 4 (HF semantics: length_penalty 1, early_stopping False) or greedy; a 1…8-token loop repeated 4× is cut;
  * the unit is a SENTENCE; a sentence over 60 tokens is cut into clauses; speech in quotes of ≥ 4 words is its
    own unit, a short quoted title is translated inside its sentence; a sentence's own terminal mark stays in it;
  * the guard ladder (ru→kbd and kbd→ru): a press name without support in the source, an enumeration of quoted
    chunks, a lost or extra number, a phrase repeated three times, a Russian run left untranslated → retry with the
    other decoder, then clauses of 25 and 12 tokens; the first clean try wins, else the least bad;
  * ru→kbd only: compound colours are resolved («тёмно-синим» → «тёмным синим», «чёрно-белых» → «чёрных и белых»);
    notes «[Примечание: X]» and dash dialogue are cut apart before the model; calques with a common
    native word are replaced in the same form («самолётым» → «кхъухьлъатэм», 26 lemmas approved by a native speaker);
  * the palochka normalizer on the input (kbd) and on the output (kbd).
"""
from __future__ import annotations

import json
import re
import threading
from importlib import resources
from pathlib import Path

import numpy as np

from .. import models
from .kbd_normalizer import palochka

H, D = 8, 64                 # decoder heads and head size
START, EOS, UNK = 32000, 0, 1
MAX_SRC = 128

# ---------------------------------------------------------------------------------------------- text units
SENT_END = re.compile(r'(?<=[.!?…])["»”)]?\s+(?=["«“(—–-]?\s*[A-ZА-ЯЁӀ0-9])')
QUOTE_SPAN = re.compile(r'(["«„“])([^"»”]+)(["»”])')
QUOTES = re.compile(r'["«»„“”]')
WORDS = re.compile(r"[A-Za-zА-Яа-яЁёӀӏ]+(?:-[A-Za-zА-Яа-яЁёӀӏ]+)*")
DIGITS = re.compile(r"\d+")
NOTE = re.compile(r"\[\s*Примечание\s*:\s*([^\]]*)(\]?)")
NOTE_LABEL = "Гу зылъытапхъэ"
DIALOGUE_START = re.compile(r"^\s*[—–]\s+")
DIALOGUE_SPLIT = re.compile(r"([,.!?…]+)\s*[—–]\s+")
LEAKS = {"спартак": ("спартак",), "налшык": ("нальчик", "налшык"), "къэбэрдей-балъкъэр": ("кабардин",),
         "адыгэ псалъэ": ("адыгэ псалъэ", "адыге псалэ")}
DIALOGUE = re.compile(r'^\s*[—–-]\s|[.!?,…]\s*[—–]\s')
SPAN = re.compile(r'["«„“][^"»”]{1,60}["»”]')


def split_sentences(text):
    parts = [p.strip() for p in SENT_END.split(text) if p.strip()]
    return parts or [text]


def cycling_trim(ids):
    for end in range(1, len(ids) + 1):
        out = ids[:end]
        for n in range(1, 9):
            if len(out) >= 4 * n and out[-4 * n:] == out[-n:] * 4:
                return out[: len(out) - 3 * n]
    return ids


def quote_units(text, min_speech_words=4):
    parts, pos = [], 0
    for m in QUOTE_SPAN.finditer(text):
        if len(m.group(2).split()) >= min_speech_words:
            parts.append(("ctx", text[pos:m.start()], "", ""))
            parts.append(("q", m.group(2), m.group(1), m.group(3)))
            pos = m.end()
    parts.append(("ctx", text[pos:], "", ""))
    return [(k, t if k == "q" else QUOTES.sub("", t), o, c) for k, t, o, c in parts]


def translate_text(unit, text):
    def sentences(t):
        return " ".join(unit(u) for u in split_sentences(t) if re.search(r"\w", u))
    out = []
    for kind, t, o, c in quote_units(text):
        if kind == "q":
            inner = sentences(t).rstrip()
            if c and inner.endswith(".") and not inner.endswith(".."):
                inner = inner[:-1]
            out.append(o + inner + c)
            continue
        lead = re.match(r"^[\s,.:;!?—–-]*", t).group(0)
        rest = t[len(lead):]
        trail = re.search(r"[\s,:;—–-]*$", rest).group(0)
        core = rest[: len(rest) - len(trail)]
        out.append(lead + (sentences(core) if core else "") + trail)
    return re.sub(r"\s+", " ", "".join(out)).strip()


def note_parts(line):
    out, pos = [], 0
    for m in NOTE.finditer(line):
        if m.start() > pos:
            out.append(("text", line[pos:m.start()]))
        out.append(("note", m.group(1), m.group(2)))
        pos = m.end()
    if pos < len(line):
        out.append(("text", line[pos:]))
    return out


def dialogue_parts(text):
    m = DIALOGUE_START.match(text)
    if not m:
        return None
    out, pos = [("sep", text[:m.end()])], m.end()
    for d in DIALOGUE_SPLIT.finditer(text, pos):
        out.append(("unit", text[pos:d.start()]))
        out.append(("sep", d.group(1) + " — "))
        pos = d.end()
    out.append(("unit", text[pos:]))
    return out


# ---------------------------------------------------------------------------------------------- guard signals
def _triple(tokens):
    for n in range(1, 6):
        for j in range(len(tokens) - 3 * n + 1):
            if tokens[j:j + n] == tokens[j + n:j + 2 * n] == tokens[j + 2 * n:j + 3 * n]:
                return " ".join(tokens[j:j + n])
    return None


def copy_flags(src, out):
    s, o = src.lower(), out.lower()
    leak = [k for k, ok in LEAKS.items() if k in o and not any(x in s for x in ok)]
    quotes = len(SPAN.findall(out)) if not (QUOTES.search(src) or DIALOGUE.search(src)) else 0
    return leak, quotes


def number_flag(src, out):
    s = [d for d in DIGITS.findall(src) if len(d) >= 2]
    o = [d for d in DIGITS.findall(out) if len(d) >= 2]
    return sorted(set(s) ^ set(o))


def repeat_flag(src, out):
    t = _triple([w.lower() for w in WORDS.findall(out)])
    return t if t and not _triple([w.lower() for w in WORDS.findall(src)]) else None


def copied_run(src, out):
    """3+ words in a row copied from the source, ≥ 2 of them lowercase Cyrillic: the piece was not translated."""
    s = [w.lower() for w in WORDS.findall(src)]
    o = WORDS.findall(out)
    ol = [w.lower() for w in o]
    run = [[0] * (len(s) + 1) for _ in range(len(ol) + 1)]
    for j in range(1, len(ol) + 1):
        for i in range(1, len(s) + 1):
            if ol[j - 1] == s[i - 1]:
                run[j][i] = run[j - 1][i - 1] + 1
    for j in range(1, len(ol) + 1):
        for i in range(1, len(s) + 1):
            n = run[j][i]
            if n >= 3 and not (j < len(ol) and i < len(s) and ol[j] == s[i]):
                words = o[j - n:j]
                if sum(1 for w in words if re.match(r"[а-яё]", w)) >= 2:
                    return " ".join(words)
    return None


def score(src, out, to_kbd):
    leak, quotes = copy_flags(src, out)
    s = (len(leak), quotes if quotes >= 2 else 0, len(number_flag(src, out)), 1 if repeat_flag(src, out) else 0)
    if to_kbd:
        s += (1 if copied_run(src, out) else 0,)
    return s


# ---------------------------------------------------------------------------------------------- calques
V_KBD = "эеяаыиоуюё"
KBD_END = re.compile(r"(м|р|хэр|хэм|мрэ|хэмрэ|кӏэ|мкӏэ|хэмкӏэ|рщ|щ|ри|ми|хэри|хэми)$")
RU_END = re.compile(r"(ыми|ими|ами|ями|ого|его|ому|ему|ую|юю|ые|ие|ых|их|ов|ев|ах|ях|ою|ею)$")
NOUN_SUFFIX = re.compile(r"^(хэ)?(р|м|мрэ|рэ|мкӏэ|кӏэ|щ|рщ|у|ри|ми|кӏи|мкӏи)?$")
SENTENCE_START = re.compile(r"(^|[.!?…:])['\"«»„“”()\[\]\s—–-]*$")


def _plain(k):
    return k.lower().replace("ӏ", "").replace("ё", "е")


def _split_calque(w, st):
    for i in range(1, len(w) + 1):
        pl = _plain(w[:i])
        if pl == st:
            return w[i:]
        if len(pl) > len(st):
            return None
    return None


def _native_forms(rest, nat, lemma=""):
    if rest[:1] == "ь":
        rest = rest[1:]
    rs = {rest}
    own = ("ы",) if lemma and lemma[-1] not in "аяеёиоуыэюйь" else (
        "ие", "иэ", "ой", "ей", "нэ", "э", "е", "я", "а", "ы", "и")
    for pre in own:
        if rest.startswith(pre):
            rs.add(rest[len(pre):])
    out = []
    for r in rs:
        core = r[1:] if r.startswith("ы") else r
        if not NOUN_SUFFIX.match(core):
            continue
        if nat[-1] in V_KBD or core[:1] not in ("р", "м"):
            out.append(nat + core)
        else:
            out += [nat + core, nat + "ы" + core]
    return sorted(set(out))


def _replace_word(lw, e):
    nat, att = e["native"], e["attested"]
    rest = _split_calque(lw, e["stem"])
    if rest is None or "-" in lw:
        return None
    ru = lw.replace("ӏ", "").replace("ё", "е") in e["ruForms_set"]
    if ru and (not KBD_END.search(lw) or RU_END.search(lw)) and lw.replace("ё", "е") != e["stem"]:
        return None
    forms = _native_forms(rest, nat, e["lemma"])
    if not forms:
        return None
    best = max(forms, key=lambda x: (att.get(x, 0), -len(x)))
    if att.get(best, 0) < 3:
        regular = [f for f in forms if f == nat or (f[len(nat):] and f[len(nat)] != "ы") or nat[-1] not in V_KBD]
        if not (e["baseOK"] and regular):
            return ""
        best = min(regular, key=len) if rest in ("", "э", "е", "я", "а", "ие") else max(
            regular, key=lambda x: (att.get(x, 0), x.startswith(nat + "ы") == (nat[-1] not in V_KBD and rest[:1] in "ыэ")))
    return best


def load_calques():
    data = json.loads(resources.files("kabardian_translator").joinpath("data/kbd-calques.json").read_text("utf-8"))
    table = data["lemmas"]
    for e in table:
        e["ruForms_set"] = set(e["ruForms"])
    return table


def apply_calques(source, text, table):
    seq = [w.lower().replace("ё", "е") for w in WORDS.findall(source)]
    src = set(seq)
    count = 0
    for e in table:
        if not (src & e["ruForms_set"]):
            continue
        if e["blockedAfter"] and any(w in e["ruForms_set"] and any(seq[j] in e["blockedAfter"] for j in (i - 1, i - 2) if j >= 0)
                                     for i, w in enumerate(seq)):
            continue

        def repl(m):
            nonlocal count
            w = m.group(0)
            r = _replace_word(w.lower().replace("Ӏ", "ӏ"), e)
            if not r:
                return w
            if w[0].isupper() and not SENTENCE_START.search(m.string[:m.start()]):
                return w
            count += 1
            return r[0].upper() + r[1:] if w[0].isupper() else r
        text = WORDS.sub(repl, text)
    return text, count


def _top(scores: np.ndarray, n: int) -> np.ndarray:
    """Indices of the n largest scores, best first — argpartition instead of sorting the whole vocabulary
    (32 045 × 4 rows) at every beam step."""
    part = np.argpartition(-scores, n)[:n]
    return part[np.argsort(-scores[part], kind="stable")]


# ---------------------------------------------------------------------------------------------- the engine
class KbdTranslator:
    def __init__(self, folder: Path | None = None, threads: int = 2):
        import onnxruntime as ort
        import sentencepiece as spm
        f = Path(folder or models.folder("kbd"))
        o = ort.SessionOptions()
        o.intra_op_num_threads = threads
        o.log_severity_level = 3
        self.enc = ort.InferenceSession(str(f / "encoder_model.int8.onnx"), o, providers=["CPUExecutionProvider"])
        self.dec = ort.InferenceSession(str(f / "decoder_merged.int8.int32flag.onnx"), o, providers=["CPUExecutionProvider"])
        self.past = [i.name for i in self.dec.get_inputs() if i.name.startswith("past_key_values")]
        self.outs = [x.name for x in self.dec.get_outputs()]
        self.sp = spm.SentencePieceProcessor(model_file=str(f / "source.spm"))
        self.vocab = json.loads((f / "vocab.json").read_text("utf-8"))
        self.inv = {v: k for k, v in self.vocab.items()}
        self.calques = load_calques()
        from .colours import Colours
        self.colours = Colours(f / "ru-morph.txt")
        self.lock = threading.Lock()
        self.stat = {"units": 0, "guard": 0, "calques": 0}

    # -- tokens
    def encode(self, text):
        """MarianTokenizer semantics: a leading `>>xx<<` is its own token, the rest goes through SentencePiece."""
        ids = []
        m = re.match(r"\s*(>>\w+<<)\s*", text)
        if m:
            ids.append(self.vocab.get(m.group(1), UNK))
            text = text[m.end():]
        ids += [self.vocab.get(p, UNK) for p in self.sp.encode(text, out_type=str)]
        return ids[:MAX_SRC - 1] + [EOS]

    def decode(self, ids):
        pieces = [self.inv[i] for i in ids if i not in (EOS, UNK, START) and i in self.inv]
        return self.sp.decode_pieces(pieces).strip()

    # -- model
    def _step(self, ids, mask, hid, past, flag):
        feed = {"input_ids": ids, "encoder_attention_mask": mask, "encoder_hidden_states": hid,
                "use_cache_branch_i32": np.array([flag], dtype=np.int32)}
        feed.update(past)
        r = dict(zip(self.outs, self.dec.run(self.outs, feed)))
        new = {n.replace("present", "past_key_values"): v for n, v in r.items() if n.startswith("present")}
        return r["logits"][:, -1], new

    def _generate(self, src_ids, beams, max_new):
        ids = np.array([src_ids], dtype=np.int64)
        mask = np.ones_like(ids)
        hid = self.enc.run(["last_hidden_state"], {"input_ids": ids, "attention_mask": mask})[0]
        empty = {n: np.zeros((1, H, 0, D), np.float32) for n in self.past}
        logits, past = self._step(np.array([[START]], np.int64), mask, hid, empty, 0)
        if beams == 1:
            out = []
            nxt = int(logits[0].argmax())
            while nxt != EOS and len(out) < max_new:
                out.append(nxt)
                logits, past = self._step(np.array([[nxt]], np.int64), mask, hid, past, 1)
                nxt = int(logits[0].argmax())
            return out
        return self._beam(logits, past, mask, hid, beams, max_new)

    def _beam(self, logits, past, mask, hid, k, max_new):
        mx = logits.max(-1, keepdims=True)
        lp = logits - mx - np.log(np.exp(logits - mx).sum(-1, keepdims=True))
        order = _top(lp[0], 2 * k)
        live, done = [], []
        for t in order:
            (done if t == EOS else live).append(([] if t == EOS else [int(t)], float(lp[0, t]), 0))
        live = live[:k]
        past = {n: np.repeat(v, len(live), 0) for n, v in past.items()}
        mask_k, hid_k = np.repeat(mask, len(live), 0), np.repeat(hid, len(live), 0)
        done = [(h, s) for h, s, _ in done]
        for _ in range(1, max_new):
            ids = np.array([[h[-1]] for h, _, _ in live], np.int64)
            logits, past = self._step(ids, mask_k[: len(live)], hid_k[: len(live)], past, 1)
            mx = logits.max(-1, keepdims=True)
            lp = logits - mx - np.log(np.exp(logits - mx).sum(-1, keepdims=True))
            tot = lp + np.array([s for _, s, _ in live])[:, None]
            flat = _top(tot.reshape(-1), 2 * k)
            nxt = []
            for f in flat:
                b, t = divmod(int(f), tot.shape[1])
                h, s = live[b][0], float(tot[b, t])
                if t == EOS:
                    done.append((h, s / (len(h) + 1)))
                else:
                    nxt.append((h + [t], s, b))
                if len(nxt) == k:
                    break
            done = sorted(done, key=lambda x: -x[1])[:k]
            best_live = max(s for _, s, _ in nxt) / (len(nxt[0][0]) + 1)
            if len(done) >= k and done[-1][1] >= best_live:
                break
            idx = np.array([b for _, _, b in nxt])
            past = {n: v[idx] for n, v in past.items()}
            live = nxt
        if not done:
            done = [(h, s / len(h)) for h, s, _ in live]
        return max(done, key=lambda x: x[1])[0]

    # -- one piece / one sentence
    def _raw(self, text, tgt, beams):
        ids = self.encode(f">>{tgt}<< {text}")
        out = cycling_trim(self._generate(ids, beams, min(160, 3 * len(ids))))
        y = self.decode(out)
        return palochka(y) if tgt == "kbd" else y

    def _clauses(self, s, tgt, limit):
        def n(x):
            return len(self.encode(f">>{tgt}<< {x}"))
        if n(s) <= limit:
            return [s]
        pieces, buf = [], ""
        for w in s.split():
            buf += (" " if buf else "") + w
            if w[-1] in ";:,—–":
                pieces.append(buf)
                buf = ""
        if buf:
            pieces.append(buf)
        out, cur = [], ""
        for p in pieces:
            c = f"{cur} {p}" if cur else p
            if cur and n(c) > limit:
                out.append(cur)
                cur = p
            else:
                cur = c
        if cur:
            out.append(cur)
        return out or [s]

    def _unit(self, s, tgt, beams):
        to_kbd = tgt == "kbd"

        def attempt(limit, b):
            return " ".join(self._raw(c, tgt, b) for c in self._clauses(s, tgt, limit))
        other = 1 if beams > 1 else 4
        main = attempt(60, beams)
        self.stat["units"] += 1
        if not any(score(s, main, to_kbd)):
            out = main
        else:
            self.stat["guard"] += 1
            tries = [main, attempt(60, other)]
            for limit, b in ((25, beams), (12, beams), (12, other)):
                if not any(score(s, tries[-1], to_kbd)):
                    break
                tries.append(attempt(limit, b))
            clean = [t for t in tries[1:] if not any(score(s, t, to_kbd))]
            out = clean[0] if clean else min(tries, key=lambda t: score(s, t, to_kbd))
        if to_kbd:
            out, n = apply_calques(s, out, self.calques)
            self.stat["calques"] += n
        # a terminal mark the model dropped comes back from the source
        m = re.search(r"[.!?…]+$", s.strip())
        if m and out and not re.search(r"[.!?…]$", out.strip()):
            out = out.rstrip() + m.group(0)
        return out

    def _plain(self, t, tgt, beams):
        if not t.strip():
            return t
        lead, trail = t[: len(t) - len(t.lstrip())], t[len(t.rstrip()):]
        core = t.strip()
        if not re.search(r"\w", core):
            return t
        parts = dialogue_parts(core) if tgt == "kbd" else None
        unit = lambda u: self._unit(u, tgt, beams)  # noqa: E731
        if not parts:
            return lead + translate_text(unit, core) + trail
        res = [x if kind == "sep" or not x.strip() else translate_text(unit, x) for kind, x in parts]
        return lead + "".join(res) + trail

    def translate(self, text: str, src: str, tgt: str, beams: int = 4) -> str:
        """One paragraph (any length): kbd input is normalized, ru→kbd gets the notes, dialogue and calque rules."""
        if src == "kbd":
            text = palochka(text)
        if src == "ru" and tgt == "kbd":
            text = self.colours.rewrite(text)         # «тёмно-синим» → «тёмным синим» before the model
        with self.lock:
            if tgt != "kbd":
                return self._plain(text, tgt, beams)
            out = []
            for part in note_parts(text):
                if part[0] == "note":
                    out.append(f"[{NOTE_LABEL}: {self._plain(part[1], tgt, beams).strip()}{part[2]}")
                else:
                    out.append(self._plain(part[1], tgt, beams))
            return "".join(out)
