"""Any-to-any translation over the two engines, with no length limit.

A text is split into paragraphs (line structure is kept) and every paragraph goes through the route of the pair
(`languages.route`): Russian ↔ Kabardian on our model, Kabardian with anything else through Russian, the rest on
MADLAD (with its measured pivots). MADLAD works sentence by sentence; the Kabardian engine makes its own units.
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
        if nxt[0].isupper() or nxt[0].isdigit() or (nxt[0].isalpha() and not nxt[0].islower()) \
                or "ა" <= nxt[0] <= "ჿ":
            out.append(text[pos:m.end()].strip())
            pos = m.end()
    out.append(text[pos:].strip())
    return [s for s in out if s]


class Translator:
    def __init__(self):
        self._madlad = None
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
    def kbd(self):
        with self._load_lock:
            if self._kbd is None:
                if not models.installed("kbd"):
                    raise RuntimeError("model 'kbd' is not installed: run kabardian-download-models kbd")
                from .engines.kbd import KbdTranslator
                self._kbd = KbdTranslator()
            return self._kbd

    def loaded(self) -> dict:
        return {"madlad": self._madlad is not None, "kbd": self._kbd is not None}

    # -- one paragraph
    def paragraph(self, text: str, src: str, tgt: str, beams: int = 4) -> str:
        if not text.strip() or not re.search(r"\w", text):
            return text
        for engine, a, b in languages.route(src, tgt):
            if engine == "kbd":
                text = self.kbd.translate(text, a, b, beams=beams)
            else:
                text = " ".join(self.madlad.translate_sentence(s, b) for s in split_sentences(text))
        return text

    # -- any text: paragraphs, line structure kept
    def text(self, text: str, src: str, tgt: str, beams: int = 4, progress=None) -> str:
        blocks = re.split(r"(\n+)", text.replace("\r\n", "\n"))
        paras = [i for i, b in enumerate(blocks) if b.strip() and not b.startswith("\n")]
        out = list(blocks)
        for n, i in enumerate(paras):
            lead = blocks[i][: len(blocks[i]) - len(blocks[i].lstrip())]
            out[i] = lead + self.paragraph(blocks[i].strip(), src, tgt, beams)
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
               "error": None, "src": src, "tgt": tgt, "name": name, "started": time.time(), "seconds": None}
        self.jobs[jid] = job

        def progress(done, total, partial):
            job.update(done=done, total=total, partial=partial)

        def run():
            with self.run_lock:
                job["state"] = "running"
                try:
                    job["result"] = self.tr.text(text, src, tgt, beams, progress)
                    job["state"] = "done"
                except Exception as e:  # reported to the page, the server keeps running
                    job["state"], job["error"] = "error", str(e)
                job["seconds"] = round(time.time() - job["started"], 1)
        threading.Thread(target=run, daemon=True).start()
        return jid

    def get(self, jid: str):
        return self.jobs.get(jid)
