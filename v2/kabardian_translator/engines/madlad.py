"""MADLAD-400 3B MT on the Apple Neural Engine (package madlad-sayfable-v1, the same files as the SayFable app).

Decoding is the one measured for the app (prompt 405): embeddings looked up outside the graph, 4 encoder and
4 decoder Core ML chunks, greedy, a fixed length of 64 tokens, the full prefix recomputed every step (no KV cache —
the step is weight-bandwidth bound); input over 50 tokens is split at clause punctuation, and a piece whose output
reaches 64 tokens without EOS is split again; a 1..8-token piece repeated 4 times stops generation.
"""
from __future__ import annotations

import re
import threading
import time
from pathlib import Path

import numpy as np

from .. import models

L = 64                 # fixed sequence length of every chunk
MAX_IN = 50            # input tokens before splitting (prompt 405)
PAD, EOS, START = 1, 2, 0

UZ = {'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo', 'ж': 'j', 'з': 'z', 'и': 'i', 'й': 'y',
      'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f',
      'х': 'x', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sh', 'ъ': "'", 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
      'ў': "o'", 'қ': 'q', 'ғ': "g'", 'ҳ': 'h'}


def uz_latin(s: str) -> str:
    """MADLAD writes Uzbek in Cyrillic; modern Uzbek uses the Latin alphabet."""
    out = []
    for i, ch in enumerate(s):
        lo = ch.lower()
        r = UZ.get(lo, ch)
        if lo == 'е' and (i == 0 or not s[i - 1].isalpha()):
            r = 'ye'
        if ch != lo and r:
            r = r[0].upper() + r[1:]
        out.append(r)
    return ''.join(out)


def cycling_tail(out, maxlen=8, reps=4) -> int:
    """A 1..8-token piece repeated 4x in a row: how many trailing tokens to drop (0 = no loop)."""
    n = len(out)
    for k in range(1, maxlen + 1):
        if n < k * reps:
            break
        piece = out[n - k:]
        if all(out[n - k * (r + 1): n - k * r] == piece for r in range(reps)):
            return k * (reps - 1)
    return 0


class Madlad:
    def __init__(self, folder: Path | None = None, compute: str = "ane"):
        import coremltools as ct
        import sentencepiece as spm
        folder = Path(folder or models.folder("madlad"))
        cu = {"ane": ct.ComputeUnit.CPU_AND_NE, "cpu": ct.ComputeUnit.CPU_ONLY}[compute]
        t = time.time()
        self.enc = [self._load(ct, folder, f"encoder_{a}_{a + 8}", cu) for a in (0, 8, 16, 24)]
        self.dec = [self._load(ct, folder, f"decoder_{a}_{a + 8}", cu) for a in (0, 8, 16, 24)]
        rows = np.fromfile(folder / "embed_int8.bin", dtype=np.int8).reshape(-1, 1024)
        scale = np.fromfile(folder / "embed_scale_fp16.bin", dtype=np.float16).astype(np.float32)
        self.E = (rows.astype(np.float32) * scale[:, None]).astype(np.float16)
        self.V = self.E.shape[0]
        self.sp = spm.SentencePieceProcessor(model_file=str(folder / "spiece.model"))
        self.load_s = time.time() - t
        self.lock = threading.Lock()     # Core ML models are not shared between threads
        self.stat = {"sentences": 0, "steps": 0, "split": 0, "guard": 0, "truncated": 0}

    @staticmethod
    def _load(ct, folder: Path, name: str, cu):
        """An .mlpackage is compiled into a temporary .mlmodelc on every load, and the Neural Engine then compiles
        that path again (≈ 70 s for the eight chunks). The compiled model is kept in `compiled/` under a fixed path,
        so the Neural Engine's own cache is hit from the second start on (measured: 0.5 s). The package is removed
        after compiling — the compiled model is all that runs, and keeping both would cost another 1.2 GB."""
        import shutil
        pkg = folder / f"{name}.mlpackage"
        compiled = folder / "compiled" / f"{name}.mlmodelc"
        if compiled.exists():
            try:
                return ct.models.CompiledMLModel(str(compiled), compute_units=cu)
            except Exception:
                if not pkg.exists():
                    raise RuntimeError("the compiled MADLAD model does not load; reinstall it: "
                                       "kabardian-download-models madlad --force")
                shutil.rmtree(compiled, ignore_errors=True)
        model = ct.models.MLModel(str(pkg), compute_units=cu)
        try:
            compiled.parent.mkdir(exist_ok=True)
            shutil.copytree(model.get_compiled_model_path(), compiled)
            model = ct.models.CompiledMLModel(str(compiled), compute_units=cu)
            shutil.rmtree(pkg, ignore_errors=True)
        except OSError:
            pass                                                   # read-only folder: works, just slower to start
        return model

    # ------------------------------------------------------------------ one piece
    def _encode(self, ids):
        n = len(ids)
        x = np.array(ids + [PAD] * (L - n))
        m = np.array([[1.0] * n + [0.0] * (L - n)], np.float16)
        h = self.E[x][None].astype(np.float16)
        for c in self.enc:
            h = c.predict({"h": h, "mask": m})["out"]
        return h, m

    def _translate_piece(self, text: str, tgt: str):
        ids = self.sp.encode(f"<2{tgt}> " + text) + [EOS]
        if len(ids) > L:
            ids = ids[:L - 1] + [EOS]
        e, m = self._encode(ids)
        out, done = [START], False
        while len(out) < L:
            d = np.array(out + [PAD] * (L - len(out)))
            h = self.E[d][None].astype(np.float16)
            st = np.zeros((1, L), np.float16)
            st[0, len(out) - 1] = 1
            for c in self.dec:
                h = c.predict({"h": h, "enc": e, "enc_mask": m, "step": st})["out"]
            self.stat["steps"] += 1
            nxt = int(np.argmax(h[..., :self.V]))
            if nxt == EOS:
                done = True
                break
            out.append(nxt)
            cut = cycling_tail(out[1:])
            if cut:
                del out[len(out) - cut:]
                done = True
                self.stat["guard"] += 1
                break
        if not done:
            self.stat["truncated"] += 1
        self.stat["sentences"] += 1
        return self.sp.decode(out[1:]), done

    def _split_translate(self, text: str, tgt: str, depth: int = 0) -> str:
        n = len(self.sp.encode(text))
        if n <= MAX_IN or depth > 3:
            y, done = self._translate_piece(text, tgt)
            if done or depth > 3:
                return y
        parts = [p for p in re.split(r'(?<=[,;:—–])\s+', text) if p]
        if len(parts) < 2:
            w = text.split()
            h = len(w) // 2
            if h == 0:
                return self._translate_piece(text, tgt)[0]
            parts = [' '.join(w[:h]), ' '.join(w[h:])]
        lim = max(8, min(MAX_IN, n // 2 + 1)) if n <= MAX_IN else MAX_IN
        chunks, cur = [], ''
        for p in parts:
            cand = (cur + ' ' + p).strip()
            if cur and len(self.sp.encode(cand)) > lim:
                chunks.append(cur)
                cur = p
            else:
                cur = cand
        if cur:
            chunks.append(cur)
        if len(chunks) < 2:
            w = text.split()
            h = max(1, len(w) // 2)
            chunks = [' '.join(w[:h]), ' '.join(w[h:])]
        self.stat["split"] += 1
        return ' '.join(self._split_translate(c, tgt, depth + 1) for c in chunks if c.strip())

    # ------------------------------------------------------------------ public
    def translate_sentence(self, sentence: str, tgt: str) -> str:
        """One sentence into `tgt` (MADLAD needs no source tag)."""
        if not sentence.strip():
            return sentence
        with self.lock:
            y = self._split_translate(sentence.strip(), tgt)
        return uz_latin(y) if tgt == "uz" else y
