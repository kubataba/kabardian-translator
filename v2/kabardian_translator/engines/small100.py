"""SMaLL-100 (package translate-v1, int8 ONNX — the SayFable app's files): every pair but Kabardian on Linux and
Windows, where MADLAD (Core ML) does not run.

A port of the app's `SmallTranslateEngine` / `SmallTranslateTokenizer` / `SmallTranslatePivotRule` (prompts 377, 379):
  * SentencePiece BPE over `bpe_vocab.tsv` (line = piece, line number = merge rank, then the id in the trimmed model);
    NFKC, `▁` prefix, merges by the FULL vocabulary, a piece missing from the trimmed model is split into the
    longest pieces it has; the input is `[target language] + pieces + [EOS]` — the source language is not given;
  * greedy decoding over the merged decoder with its cache, start token EOS; a 1…8-token loop repeated 4× is cut;
  * the unit is a SENTENCE, a sentence over 60 tokens is cut at clause marks (; : , — –); an empty translation
    keeps the original; numbers are carried from the original when both sides have as many digit groups;
  * the measured English pivot: from lv az ka kk tr, to lv be tr.
"""
from __future__ import annotations

import json
import re
import threading
import unicodedata
from pathlib import Path

import numpy as np

from .. import models

HEADS, HEAD = 16, 64
POSITION_LIMIT = 1000        # 1024 positions + 2 offsets; past them the graph fails
CLAUSE_LIMIT = 60            # tokens of one pass; longer sentences are cut into clauses
HOP_WHEN_SOURCE = {"lv", "az", "ka", "kk", "tr"}
HOP_WHEN_TARGET = {"lv", "be", "tr"}
HOP = "en"
# the languages the app offers (prompt 379: ba and uz are in the model but fail 40 of 40 sentences)
LANGUAGES = ("az", "be", "bg", "cs", "da", "de", "el", "en", "es", "et", "fi", "fr", "hr", "hu", "hy", "it", "ka",
             "kk", "lt", "lv", "nl", "pl", "pt", "ro", "ru", "sk", "sl", "sv", "tr", "uk")


def pivot(src: str | None, tgt: str) -> str | None:
    if src == HOP or tgt == HOP:
        return None
    if tgt in HOP_WHEN_TARGET or src in HOP_WHEN_SOURCE:
        return HOP
    return None


def cycle_length(produced: list) -> int | None:
    for n in range(1, 9):
        if len(produced) >= 4 * n and produced[-4 * n:] == produced[-n:] * 4:
            return n
    return None


# ---------------------------------------------------------------------------------------------- numbers
_GROUP = re.compile(r"\d+(?:[,.:]\d+)*")


def carry_numbers(source: str, translation: str) -> str:
    """Digit groups of the original replace those of the translation when both have as many (a translation must not
    change a quantity); with different counts nothing is done — the number went missing with its phrase."""
    a, b = list(_GROUP.finditer(source)), list(_GROUP.finditer(translation))
    if len(a) != len(b) or not a:
        return translation
    digits = lambda m: re.sub(r"\D", "", m.group())
    if all(digits(x) == digits(y) for x, y in zip(a, b)):
        return translation
    out = translation
    for x, y in reversed(list(zip(a, b))):
        if digits(x) != digits(y):
            out = out[: y.start()] + x.group() + out[y.end():]
    return out


# ---------------------------------------------------------------------------------------------- tokenizer
class Tokenizer:
    def __init__(self, folder: Path):
        ids = json.loads((folder / "token_ids.json").read_text("utf-8"))
        self.eos, self.pad, self.unk = ids["special"]["eos"], ids["special"]["pad"], ids["special"]["unk"]
        self.lang = ids["langs"]
        self.rank, self.id, self.piece = {}, {}, {}
        with open(folder / "bpe_vocab.tsv", encoding="utf-8") as f:
            for line, row in enumerate(f):
                row = row.rstrip("\n")
                tab = row.rfind("\t")
                if tab < 0:
                    continue
                p, i = row[:tab], int(row[tab + 1:] or -1)
                self.rank[p] = line
                if i >= 0:
                    self.id[p], self.piece[i] = i, p

    def pieces(self, text: str) -> list:
        words = unicodedata.normalize("NFKC", text).split()
        out = []
        for w in words:
            toks = ["▁"] + list(w)
            while len(toks) > 1:
                best, at = None, -1
                for i in range(len(toks) - 1):
                    r = self.rank.get(toks[i] + toks[i + 1])
                    if r is not None and (best is None or r < best):
                        best, at = r, i
                if at < 0:
                    break
                toks[at:at + 2] = [toks[at] + toks[at + 1]]
            out += toks
        return out

    def _ids(self, p: str) -> list:
        if p in self.id:
            return [self.id[p]]
        out, rest = [], p
        while rest:
            for end in range(len(rest), 0, -1):
                if rest[:end] in self.id:
                    out.append(self.id[rest[:end]])
                    rest = rest[end:]
                    break
            else:
                out.append(self.unk)
                rest = rest[1:]
        return out

    def encode(self, text: str, target: str) -> list:
        return [self.lang[target]] + [i for p in self.pieces(text) for i in self._ids(p)] + [self.eos]

    def decode(self, ids: list) -> str:
        return "".join(self.piece.get(i, "") for i in ids if i not in (self.eos, self.pad)).replace("▁", " ").strip()


# ---------------------------------------------------------------------------------------------- the engine
class Small100:
    def __init__(self, folder: Path | None = None, threads: int = 2):
        import onnxruntime as ort
        f = Path(folder or models.folder("small100"))
        o = ort.SessionOptions()
        o.intra_op_num_threads = threads
        o.log_severity_level = 3
        self.enc = ort.InferenceSession(str(f / "encoder_model.int8.onnx"), o, providers=["CPUExecutionProvider"])
        self.dec = ort.InferenceSession(str(f / "decoder_merged.int8.int32flag.onnx"), o,
                                        providers=["CPUExecutionProvider"])
        self.past = [i.name for i in self.dec.get_inputs() if i.name.startswith("past_key_values")]
        self.outs = [x.name for x in self.dec.get_outputs()]
        self.tok = Tokenizer(f)
        self.lock = threading.Lock()

    def _generate(self, ids: list) -> str:
        if len(ids) > POSITION_LIMIT:
            ids = ids[: POSITION_LIMIT - 1] + [self.tok.eos]
        src = np.array([ids], dtype=np.int64)
        mask = np.ones_like(src)
        hid = self.enc.run(["last_hidden_state"], {"input_ids": src, "attention_mask": mask})[0]
        feed = {"encoder_attention_mask": mask, "input_ids": np.array([[self.tok.eos]], dtype=np.int64),
                "encoder_hidden_states": hid, "use_cache_branch_i32": np.array([0], dtype=np.int32)}
        for n in self.past:
            feed[n] = np.zeros((1, HEADS, 0, HEAD), dtype=np.float32)
        out = dict(zip(self.outs, self.dec.run(self.outs, feed)))
        past = {n.replace("present", "past_key_values"): v for n, v in out.items() if n.startswith("present")}
        nxt = int(out["logits"][0, -1].argmax())
        produced = []
        limit = min(max(64, len(ids) * 3), POSITION_LIMIT - 2)
        while nxt != self.tok.eos and len(produced) < limit:
            produced.append(nxt)
            n = cycle_length(produced)
            if n:
                del produced[-3 * n:]
                break
            feed = {"encoder_attention_mask": mask, "input_ids": np.array([[nxt]], dtype=np.int64),
                    "encoder_hidden_states": hid, "use_cache_branch_i32": np.array([1], dtype=np.int32)}
            for name in self.past:
                feed[name] = past[name]
            out = dict(zip(self.outs, self.dec.run(self.outs, feed)))
            # in the cache branch the cross-attention KV outputs are placeholders: keep those of the first step
            for name, v in out.items():
                if name.startswith("present") and ".decoder." in name:
                    past[name.replace("present", "past_key_values")] = v
            nxt = int(out["logits"][0, -1].argmax())
        return self.tok.decode(produced)

    def _clauses(self, sentence: str, tgt: str) -> list:
        n = lambda s: len(self.tok.encode(s, tgt))
        if n(sentence) <= CLAUSE_LIMIT:
            return [sentence]
        pieces, buf = [], ""
        for w in sentence.split():
            buf = f"{buf} {w}" if buf else w
            if w[-1] in ";:,—–":
                pieces.append(buf)
                buf = ""
        if buf:
            pieces.append(buf)
        out, cur = [], ""
        for p in pieces:
            cand = f"{cur} {p}" if cur else p
            if cur and n(cand) > CLAUSE_LIMIT:
                out.append(cur)
                cur = p
            else:
                cur = cand
        if cur:
            out.append(cur)
        return out or [sentence]

    def _part(self, part: str, tgt: str) -> str:
        piece = self._generate(self.tok.encode(part, tgt))
        return carry_numbers(part, piece) if piece.strip() else part

    def _step(self, text: str, tgt: str) -> str:
        from ..translator import split_sentences
        parts = [c for s in split_sentences(text) for c in self._clauses(s, tgt)]
        return " ".join(self._part(p, tgt) for p in parts) if parts else text

    def translate(self, text: str, src: str | None, tgt: str) -> str:
        """One piece of text (a paragraph or a sentence); `src` only decides the pivot."""
        if tgt not in self.tok.lang:
            raise ValueError(f"SMaLL-100 does not translate into {tgt!r}")
        with self.lock:
            hop = pivot(src, tgt)
            if hop:
                return self._step(self._step(text, hop), tgt)
            return self._step(text, tgt)
