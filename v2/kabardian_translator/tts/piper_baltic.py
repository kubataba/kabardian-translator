"""baltic-sayfable — our Piper (VITS) model for Latvian, Lithuanian and Estonian, 18 voices, on ONNX Runtime.

The text layer and the phonemizers are the SayFable app's own Swift code, compiled into the small helper
`bin/baltic-phonemes` (tools/baltic-phonemes/build.sh): the model gets exactly the input it was trained on
(parity with the training set — 599 of 600 lines; the one difference is the app's Roman-numeral rule, «II» → «teine»).
The helper reads lt.dict / et.dict from its own folder, so it is copied next to the model on first use.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import threading
import unicodedata
from importlib import resources
from pathlib import Path

import numpy as np

from .. import models

SAMPLE_RATE = 22050
MAX_IDS = 600            # VITS loses half of a longer chain (measured in the app, prompt 347)
SCALES = (0.667, 1.0, 0.8)
DEFAULT_VOICE = {"lv": "Kristine", "lt": "Regina", "et": "Mari"}


class BalticPiper:
    def __init__(self, folder: Path | None = None):
        import onnxruntime as ort
        f = Path(folder or models.folder("baltic"))
        cfg = json.loads((f / "baltic-sayfable.onnx.json").read_text("utf-8"))
        self.id_map = cfg["phoneme_id_map"]
        self.speakers = cfg["speaker_id_map"]
        self.voices = {v["speaker"]: v for v in cfg["sayfable"]["voices"]}
        self.author_length = cfg.get("inference", {}).get("length_scale", 1.0)
        o = ort.SessionOptions()
        o.log_severity_level = 3
        o.intra_op_num_threads = 2
        self.session = ort.InferenceSession(str(f / "baltic-sayfable.onnx"), o, providers=["CPUExecutionProvider"])
        self.helper = self._install_helper(f)
        self.proc = None
        self.lock = threading.Lock()

    @staticmethod
    def _install_helper(folder: Path) -> Path:
        src = Path(str(resources.files("kabardian_translator").joinpath("bin/baltic-phonemes")))
        dst = folder / "baltic-phonemes"
        if not dst.exists() or dst.stat().st_size != src.stat().st_size or dst.stat().st_mtime < src.stat().st_mtime:
            shutil.copy2(src, dst)
            dst.chmod(0o755)
        return dst

    def _phonemes(self, text: str, lang: str) -> str:
        if self.proc is None or self.proc.poll() is not None:
            self.proc = subprocess.Popen([str(self.helper)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                         text=True, encoding="utf-8", bufsize=1)
        self.proc.stdin.write(f"{lang}\t{text.replace(chr(10), ' ').replace(chr(9), ' ')}\n")
        self.proc.stdin.flush()
        return self.proc.stdout.readline().rstrip("\n")

    def _ids(self, phonemes: str) -> list:
        ids = [1, 0]
        for ch in unicodedata.normalize("NFD", phonemes):
            if ch in self.id_map:
                ids += self.id_map[ch]
                ids.append(0)
        ids.append(2)
        return ids

    def _pieces(self, sentence: str, lang: str) -> list:
        ids = self._ids(self._phonemes(sentence, lang))
        if len(ids) <= MAX_IDS:
            return [ids]
        parts = [p for p in re.split(r"(?<=[,;:—–])\s+", sentence) if p.strip()]
        if len(parts) < 2:
            w = sentence.split()
            parts = [" ".join(w[: len(w) // 2]), " ".join(w[len(w) // 2:])] if len(w) > 1 else [sentence]
            if len(parts) == 1:
                return [ids[:MAX_IDS - 1] + [2]]
        out, cur = [], ""
        for p in parts:
            cand = f"{cur} {p}".strip()
            if cur and len(self._ids(self._phonemes(cand, lang))) > MAX_IDS:
                out += self._pieces(cur, lang)
                cur = p
            else:
                cur = cand
        if cur:
            out += self._pieces(cur, lang)
        return out

    def _run(self, ids, sid, length_scale):
        scales = np.array([SCALES[0], self.author_length * length_scale, SCALES[2]], dtype=np.float32)
        feed = {"input": np.array([ids], dtype=np.int64), "input_lengths": np.array([len(ids)], dtype=np.int64),
                "scales": scales, "sid": np.array([sid], dtype=np.int64)}
        return self.session.run(["output"], feed)[0].reshape(-1).astype(np.float32)

    def synthesize(self, text: str, lang: str, voice: str | None = None, speed: float = 1.0) -> np.ndarray:
        from ..translator import split_sentences
        speaker = voice if voice in self.speakers else DEFAULT_VOICE[lang]
        sid = self.speakers[speaker]
        length = self.voices.get(speaker, {}).get("lengthScale", 1.0) / max(0.5, min(2.0, speed))
        out = []
        with self.lock:
            for sentence in split_sentences(text.strip()):
                if not re.search(r"\w", sentence):
                    continue
                for ids in self._pieces(sentence, lang):
                    if len(ids) > 3:
                        out.append(self._run(ids, sid, length))
                out.append(np.zeros(int(0.12 * SAMPLE_RATE), np.float32))
        return np.concatenate(out) if out else np.zeros(int(0.35 * SAMPLE_RATE), np.float32)

    def voice_list(self, lang: str) -> list:
        own = [{"speaker": s, "name": v["name"], "sex": v["sex"]} for s, v in self.voices.items() if v["lang"] == lang]
        return sorted(own, key=lambda v: v["speaker"] != DEFAULT_VOICE[lang])
