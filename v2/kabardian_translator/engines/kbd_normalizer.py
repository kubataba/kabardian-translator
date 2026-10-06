"""Kabardian palochka normalizer — the same rule as the SayFable app (`KabardianNormalizer.swift`, prompts 168,
409, 413, 414): a palochka stand-in (I i l L 1 | і І Ӏ) becomes U+04CF only inside a word that contains a Cyrillic
letter; Roman numerals typed with Cyrillic Х/С/М become Latin («ХIХ» → «XIX»); digit runs stay digits
(«ӏ928гъэм» → «1928гъэм»); formulas, brands and codes keep their letters («КCl», «Телеstudio», «1С»).
The model knows only U+04CF, so input is normalized before translation and output after it.
"""
PALOCHKA = "ӏ"
VARIANTS = set("IilL1|іІӀ")

ROMAN_GLYPHS = {"I": "I", "V": "V", "X": "X", "L": "L", "C": "C", "M": "M", "Х": "X", "С": "C", "М": "M",
                "І": "I", "Ӏ": "I", "ӏ": "I", "1": "I", "l": "I", "|": "I"}
ROMAN_CEILING = 200
LOOKALIKE = set("aceopxykACEHKMOPTXYB")       # Latin letters with a Cyrillic twin (mixed-layout Kabardian)
DIGIT_STANDINS = set("ӀӏIіІ1")


def _is_cyr(ch):
    return ch not in VARIANTS and ("Ѐ" <= ch <= "ԯ")


def _is_word(ch):
    return ch.isalnum() or ch == "|"


def _roman_canonical(n):
    out = ""
    for v, sym in ((100, "c"), (90, "xc"), (50, "l"), (40, "xl"), (10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")):
        while n >= v:
            out, n = out + sym, n - v
    return out


def roman_value(word):
    w = word.lower()
    if len(w) < 2 or not (word == w or word == word.upper()):
        return None
    vals = {"i": 1, "v": 5, "x": 10, "l": 50, "c": 100, "d": 500, "m": 1000}
    if not all(c in vals for c in w):
        return None
    total = highest = 0
    for c in reversed(w):
        v = vals[c]
        total += -v if v < highest else v
        highest = max(highest, v)
    if not (0 < total <= ROMAN_CEILING):
        return None
    return total if _roman_canonical(total) == w else None


def _roman_latin(word):
    if len(word) < 2 or not all(c in ROMAN_GLYPHS for c in word):
        return None
    if not any(c in VARIANTS or c == PALOCHKA for c in word):
        return None
    latin = "".join(ROMAN_GLYPHS[c] for c in word)
    return latin if roman_value(latin) is not None else None


def _latin_word(word):
    return any(c.isascii() and c.isalpha() and c not in VARIANTS and c not in LOOKALIKE for c in word)


def _keep_l(word, i):
    return word[i] == "l" and i > 0 and word[i - 1].isupper() and not (
        i + 1 < len(word) and _is_cyr(word[i + 1]) and word[i + 1].islower())


def _numeric_runs(word, after_decimal_point=False):
    mask, i = [False] * len(word), 0

    def like(c):
        return ("0" <= c <= "9") or c in DIGIT_STANDINS
    while i < len(word):
        if not like(word[i]):
            i += 1
            continue
        j = i
        while j < len(word) and like(word[j]):
            j += 1
        if after_decimal_point and i == 0 and j > 2 and "0" <= word[0] <= "9" and "0" <= word[1] <= "9" \
                and not ("0" <= word[2] <= "9"):
            j = 2
        run = word[i:j]
        if any("0" <= c <= "9" and c != "1" for c in run) or (len(run) >= 2 and all(c == "1" for c in run)):
            mask[i:j] = [True] * (j - i)
        i = j
    if any("0" <= c <= "9" and c != "1" for c in word):
        mask = [m or c == "1" for m, c in zip(mask, word)]
    letters = [c for c in word if c.isalpha() and c not in VARIANTS]
    if letters and len(letters) <= 3 and all(c.isupper() for c in letters):
        for k in (0, len(word) - 1):
            if word[k] == "1":
                mask[k] = True
    return mask


def _flush(word, cyr, out, after_decimal_point=False):
    roman = _roman_latin(word) if cyr else None
    if roman is not None:
        out.append(roman)
    elif cyr and not _latin_word(word):
        numeric = _numeric_runs(word, after_decimal_point)
        out.extend((c if "0" <= c <= "9" else "1") if numeric[i] else
                   (c if _keep_l(word, i) else PALOCHKA if c in VARIANTS else c) for i, c in enumerate(word))
    else:
        out.extend(word)


def palochka(text: str) -> str:
    out, word, cyr, after = [], [], False, False
    prev = prev2 = " "
    for ch in text:
        if _is_word(ch):
            if not word:
                after = prev == "." and "0" <= prev2 <= "9"
            word.append(ch)
            cyr = cyr or _is_cyr(ch)
        else:
            _flush(word, cyr, out, after)
            word, cyr = [], False
            out.append(ch)
        prev2, prev = prev, ch
    _flush(word, cyr, out, after)
    return "".join(out)
