"""Russian compound colour adjectives before ru→kbd translation (prompts 413–414, port of
`scripts/kbd408/compound_adj.py`, the reference of the app's `RussianColourCompounds`).

The model copies a hyphenated colour into Kabardian half-Russian («тёмно-синим»); written as two words it translates
it. A shade becomes two agreed adjectives («тёмно-синим» → «тёмным синим»), two colours are joined by «и»
(«чёрно-белых» → «чёрных и белых»); terms («военно-морской») are not colours and are not touched. Every form is checked
by the Russian form dictionary `ru-morph.txt` (language pack `ru`); without it the text is left as it is.

The dictionary is read only when a text has a hyphenated colour at all, and only its adjective rows are kept.
"""
from __future__ import annotations

import collections
import re
import threading
from pathlib import Path

ADJ = re.compile(r"\b([А-ЯЁа-яё]{3,}[оеё])-([а-яё]{3,})\b")
HARD = ["ыми", "ого", "ому", "ый", "ая", "ое", "ые", "ым", "ом", "ой", "ую", "ых"]
SOFT = ["ими", "его", "ему", "ий", "яя", "ее", "ие", "им", "ем", "ей", "юю", "их"]
SLOT = {e: i for i, e in enumerate(HARD)} | {e: i for i, e in enumerate(SOFT)}
VELAR = set("кгхжшщч")
ADJ_LEMMA = ("ый", "ий", "ой", "ая", "яя", "ое", "ее")
ENDINGS = tuple(sorted(SLOT, key=len, reverse=True))
COLOUR_STEM = re.compile(
    r"(красн|син|зел[её]н|ж[её]лт|бел|ч[её]рн|сер|голуб|коричнев|розов|фиолетов|оранжев|рыж|багров|ал|лилов|бур|"
    r"пурпурн|золотист|золот|серебрист|сиз|изумрудн|бирюзов|малинов|пепельн|оливков|лимонн|кремов|палев|ржав|смугл|"
    r"русы|медн|бронзов|стальн|молочн|песочн|кирпичн|вишн[её]в|сирен[её]в|соломенн|кар)(оват|еват)?")


def _keys(word):
    w = word.lower()
    return {w, w.replace("ё", "е")}


def _ending(word):
    for e in ENDINGS:
        if word.endswith(e) and len(word) > len(e) + 1:
            return e
    return None


class Colours:
    def __init__(self, morph_path: Path):
        self.path = Path(morph_path)
        self._adj = None
        self._lock = threading.Lock()

    @property
    def adj(self):
        with self._lock:
            if self._adj is None:
                adj = collections.defaultdict(set)
                with open(self.path, encoding="utf-8") as f:
                    for line in f:
                        p = line.rstrip("\n").split("\t")
                        if len(p) < 2:
                            continue
                        form = p[0].lower()
                        if not form.endswith(ENDINGS):
                            continue                         # only adjective-shaped forms are ever looked up
                        lemma = p[1].lower()
                        adj[form].add(lemma)
                        adj[form.replace("ё", "е")].add(lemma)
                self._adj = adj
            return self._adj

    def _lemmas(self, word):
        return {l for k in _keys(word) for l in self.adj.get(k, ())}

    def _is_adj_form(self, word):
        return bool(_ending(word.lower())) and any(l.endswith(ADJ_LEMMA) for l in self._lemmas(word))

    def _first_lemma(self, first):
        stem = first[:-1].lower()
        for e in ("ый", "ий", "ой"):
            if any(k in self.adj for k in _keys(stem + e)):
                return stem, e
        return None

    def _agree(self, first, second):
        fl, e2 = self._first_lemma(first), _ending(second.lower())
        if not fl or not e2:
            return None
        stem, lemma_end = fl
        if e2 in ("ый", "ий", "ой") and any(k in self._lemmas(second) for k in _keys(second)):
            form = stem + lemma_end
            return form[0].upper() + form[1:] if first[0].isupper() else form
        soft = lemma_end == "ий" and stem[-1] not in VELAR
        e1 = (SOFT if soft else HARD)[SLOT[e2]]
        if stem[-1] in VELAR and e1.startswith("ы"):
            e1 = "и" + e1[1:]
        form = stem + e1
        if not any(k in self.adj for k in _keys(form)):
            return None
        return form[0].upper() + form[1:] if first[0].isupper() else form

    @staticmethod
    def _is_colour(second):
        w = second.lower()
        e = _ending(w)
        return bool(e and COLOUR_STEM.fullmatch(w[: -len(e)]))

    @staticmethod
    def _two_colours(first):
        stem = first.lower()[:-1]
        return bool(COLOUR_STEM.fullmatch(stem)) and not stem.endswith(("оват", "еват", "ист"))

    def rewrite(self, text: str) -> str:
        """«тёмно-синим» → «тёмным синим», «чёрно-белых» → «чёрных и белых»; anything else unchanged."""
        cands = [m for m in ADJ.finditer(text) if self._is_colour(m.group(2))]
        if not cands or not self.path.exists():
            return text
        res, pos = [], 0
        for m in cands:
            first, second = m.group(1), m.group(2)
            if not (self._is_adj_form(second) and self._first_lemma(first)):
                continue
            res.append(text[pos:m.start()])
            joint = " и " if self._two_colours(first) else " "
            res.append(f"{self._agree(first, second) or first}{joint}{second}")
            pos = m.end()
        res.append(text[pos:])
        return "".join(res)
