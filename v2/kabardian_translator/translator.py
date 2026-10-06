"""Any-to-any translation over the two engines, with no length limit.

A text is split into paragraphs (line structure is kept) and every paragraph goes through the route of the pair
(`languages.route`): Russian ↔ Kabardian on our model, Kabardian with anything else through Russian, the rest on
MADLAD (Macs with Apple Silicon) or SMaLL-100 (elsewhere), each with its measured pivots. Both work sentence by
sentence; the Kabardian engine makes its own units.
Long texts run as background jobs that report progress and hand out the translation as it grows.
"""
from __future__ import annotations

import re
import threading
import time
import uuid

from . import languages, models

_SENT = re.compile(r'[.!?…]+["»”\')\]]*\s+')
_OPENERS = '"«“„([—–- '


def split_sentences(text: str) -> list:
    """Sentence ends: . ! ? … (closing quotes allowed) followed by a space and a capital letter of any script, a
    digit, or a quote/dash opening the next sentence. A lowercase continuation («т. е. так») is not a break."""
    out, pos = [], 0
    for m in _SENT.finditer(text):
        nxt = text[m.end():m.end() + 4].lstrip(_OPENERS)
        if not nxt:
            continue
        # Georgian (Mkhedruli) has no capitals at a sentence start, so any Georgian letter opens a sentence
        # Kabardian may open a sentence with a lowercase palochka («ӏушэ»)
        if nxt[0].isupper() or nxt[0].isdigit() or (nxt[0].isalpha() and not nxt[0].islower()) \
                or "ა" <= nxt[0] <= "ჿ" or nxt[0] in "ӏӀ":
            out.append(text[pos:m.end()].strip())
            pos = m.end()
    out.append(text[pos:].strip())
    return [s for s in out if s]


_OPEN_CLOSE = (("«", "»"), ("(", ")"), ("[", "]"))


def _closed(text: str) -> bool:
    """No quotation or bracket is left open (a stray closer does not hold the segment open)."""
    if any(text.count(a) > text.count(b) for a, b in _OPEN_CLOSE):
        return False
    return text.count('"') % 2 == 0 and (text.count("„") + text.count("“") + text.count("”")) % 2 == 0


def segments(text: str, limit: int = 1500) -> list:
    """The units a paragraph is translated in, and paired in a bilingual file: sentences, except that a quotation or
    a bracket running over several sentences stays one segment — the Kabardian engine treats direct speech and notes
    as a whole. A segment that never closes (a stray quote) is cut at `limit` characters."""
    out, buf = [], ""
    for s in split_sentences(text):
        buf = f"{buf} {s}" if buf else s
        if _closed(buf) or len(buf) >= limit:
            out.append(buf)
            buf = ""
    if buf:
        out.append(buf)
    return out


def align(original: str, translation: str) -> list:
    """Sentence pairs of a paragraph translated as a whole: segments, else plain sentences, matched one to one when
    both sides have as many; otherwise the paragraph is one pair."""
    for split in (segments, split_sentences):
        a, b = split(original), split(translation)
        if len(a) == len(b):
            return list(zip(a, b))
    return [(original.strip(), translation.strip())]


class Translator:
    def __init__(self):
        self._madlad = None
        self._small = None
        self._kbd = None
        self._load_lock = threading.Lock()

    # -- engines, loaded on first use
    @property
    def madlad(self):
        with self._load_lock:
            if self._madlad is None:
                if not models.installed("madlad"):
                    raise RuntimeError("model 'madlad' is not installed: run kabardian-download-models madlad")
                from .engines.madlad import Madlad
                self._madlad = Madlad()
            return self._madlad

    @property
    def small(self):
        with self._load_lock:
            if self._small is None:
                if not models.installed("small100"):
                    raise RuntimeError("model 'small100' is not installed: run kabardian-download-models small100")
                from .engines.small100 import Small100
                self._small = Small100()
            return self._small

    @property
    def kbd(self):
        with self._load_lock:
            if self._kbd is None:
                if not models.installed("kbd"):
                    raise RuntimeError("model 'kbd' is not installed: run kabardian-download-models kbd")
                from .engines.kbd import KbdTranslator
                self._kbd = KbdTranslator()
            return self._kbd

    def unload(self) -> None:
        """Drops the loaded translators (the engine was switched and one of them is gone)."""
        with self._load_lock:
            self._madlad = self._small = None

    def loaded(self) -> dict:
        return {"madlad": self._madlad is not None, "small100": self._small is not None, "kbd": self._kbd is not None}

    # -- one segment through the route of the pair
    def _route(self, text: str, src: str, tgt: str, beams: int) -> str:
        for engine, a, b in languages.route(src, tgt):
            if engine == "kbd":
                text = self.kbd.translate(text, a, b, beams=beams)
            elif engine == "small100":
                text = self.small.translate(text, a, b)
            else:
                text = " ".join(self.madlad.translate_sentence(s, b) for s in split_sentences(text))
        return text

    # -- one paragraph: [(original, translation)] for the bilingual file
    def paragraph_pairs(self, text: str, src: str, tgt: str, beams: int = 4) -> list:
        """MADLAD routes are translated segment by segment, so their pairs are exact (MADLAD works by sentence anyway,
        the text is the same). A route through the Kabardian engine translates the whole paragraph, as before: the
        engine splits a dialogue line into replicas and author's words itself, and cutting the line earlier changes
        the translation (10 of 60 paragraphs of Chekhov's «Тоска»); its pairs are aligned afterwards."""
        if not text.strip() or not re.search(r"\w", text):
            return [(text, text)]
        if all(engine != "kbd" for engine, _, _ in languages.route(src, tgt)):
            return [(seg, self._route(seg, src, tgt, beams)) for seg in segments(text)]
        return align(text, self._route(text, src, tgt, beams))

    def paragraph(self, text: str, src: str, tgt: str, beams: int = 4) -> str:
        return " ".join(t for _, t in self.paragraph_pairs(text, src, tgt, beams))

    # -- any text: paragraphs, line structure kept; `pairs` (a list) receives the segment pairs of every paragraph
    def text(self, text: str, src: str, tgt: str, beams: int = 4, progress=None, pairs: list | None = None) -> str:
        blocks = re.split(r"(\n+)", text.replace("\r\n", "\n"))
        paras = [i for i, b in enumerate(blocks) if b.strip() and not b.startswith("\n")]
        out = list(blocks)
        for n, i in enumerate(paras):
            lead = blocks[i][: len(blocks[i]) - len(blocks[i].lstrip())]
            pp = self.paragraph_pairs(blocks[i].strip(), src, tgt, beams)
            out[i] = lead + " ".join(t for _, t in pp)
            if pairs is not None:
                pairs.append(pp)
            if progress:
                progress(n + 1, len(paras), "".join(out[: i + 1]))
        return "".join(out)


class Jobs:
    """Background translations with progress; one job runs at a time (the engines are single-stream)."""

    def __init__(self, translator: Translator):
        self.tr = translator
        self.jobs = {}
        self.run_lock = threading.Lock()

    def start(self, text: str, src: str, tgt: str, beams: int = 4, name: str | None = None) -> str:
        jid = uuid.uuid4().hex[:12]
        paras = sum(1 for b in re.split(r"\n+", text) if b.strip())
        job = {"id": jid, "state": "queued", "done": 0, "total": paras, "partial": "", "result": None,
               "error": None, "src": src, "tgt": tgt, "name": name, "started": time.time(), "seconds": None,
               "original": text, "pairs": []}
        self.jobs[jid] = job

        def progress(done, total, partial):
            job.update(done=done, total=total, partial=partial)

        def run():
            with self.run_lock:
                job["state"] = "running"
                try:
                    job["result"] = self.tr.text(text, src, tgt, beams, progress, pairs=job["pairs"])
                    job["state"] = "done"
                except Exception as e:  # reported to the page, the server keeps running
                    job["state"], job["error"] = "error", str(e)
                job["seconds"] = round(time.time() - job["started"], 1)
        threading.Thread(target=run, daemon=True).start()
        return jid

    def get(self, jid: str):
        return self.jobs.get(jid)
