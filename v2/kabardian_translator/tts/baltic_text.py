"""The text side of the Baltic model: the SayFable app's text layer and Latvian, Lithuanian and Estonian phonemizers,
ported from its Swift sources (`PiperTextPrep`, `BalticPhonemes`, `LatvianPhonemizer`, `LithuanianPhonemizer`,
`EstonianPhonemizer`, `NumeralSpeller`, `RomanNumeral`; prompts 352, 357, 392, 401) so the model gets exactly the input
it was trained on, on every system.

Swift compares `Character`s (canonical equivalence); here the text is NFC-normalized first, which gives the same
answers for the letters of these languages. Two things are data rather than code:
  * the dictionaries — `lt.dict` / `et.dict` (word → phonemes) come with the model, `lv-morph` / `lt-morph` /
    `et-morph` (form → lemma, POS) from the language packs; they decide a single Roman letter in a heading
    («X skyrius») and the case of an Estonian ordinal;
  * `data/baltic-fold.json` — the app's answer for every letter outside a language's alphabet (its table, then
    diacritics, then ICU transliteration), dumped from the Swift code itself, so no ICU is needed here.
"""
from __future__ import annotations

import json
import re
import threading
import unicodedata
from importlib import resources
from pathlib import Path

# ---------------------------------------------------------------------------------------------- dictionaries
_FOLDER: Path | None = None
_cache: dict = {}
_lock = threading.Lock()


def set_folder(folder: Path) -> None:
    global _FOLDER
    _FOLDER = Path(folder)


def _load(name: str, kind: str) -> dict:
    with _lock:
        if name not in _cache:
            path = (_FOLDER / name) if _FOLDER else None
            table: dict = {}
            if path and path.exists():
                with open(path, encoding="utf-8") as f:
                    for line in f:
                        line = line.rstrip("\n")
                        if kind == "dict":
                            if line.startswith("#") or " " not in line:
                                continue
                            k, v = line.split(" ", 1)
                            table[k] = v
                        else:
                            parts = line.split("\t", 2)
                            if len(parts) == 3:
                                table[parts[0]] = (parts[1], parts[2])
            _cache[name] = table
        return _cache[name]


def _fold_table() -> dict:
    with _lock:
        if "fold" not in _cache:
            _cache["fold"] = json.loads(resources.files("kabardian_translator").joinpath("data/baltic-fold.json")
                                        .read_text("utf-8"))
        return _cache["fold"]


def _is_number(ch: str) -> bool:
    """Swift `Character.isNumber`: any numeric character."""
    return unicodedata.numeric(ch, None) is not None


def _digit_value(ch: str):
    """Swift `wholeNumberValue` for a single digit, else None."""
    v = unicodedata.numeric(ch, None)
    return int(v) if v is not None and v == int(v) and 0 <= v < 10 else None


# ---------------------------------------------------------------------------------------------- Roman numerals
ROMAN_CEILING = 200
_ROMAN = {"i": 1, "v": 5, "x": 10, "l": 50, "c": 100, "d": 500, "m": 1000}


def roman_canonical(n: int) -> str:
    out = ""
    for v, s in ((100, "c"), (90, "xc"), (50, "l"), (40, "xl"), (10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")):
        while n >= v:
            out += s
            n -= v
    return out


def roman_value(word: str):
    w = word.lower()
    if len(w) < 2 or not (word == w or word == word.upper()) or not all(c in _ROMAN for c in w):
        return None
    total = highest = 0
    for c in reversed(w):
        v = _ROMAN[c]
        total += -v if v < highest else v
        highest = max(highest, v)
    if total <= 0 or total > ROMAN_CEILING:
        return None
    return total if roman_canonical(total) == w else None


# ---------------------------------------------------------------------------------------------- numbers
MAX_SPELLED = 999_999_999
_T = {
    "et": dict(ones=["null", "üks", "kaks", "kolm", "neli", "viis", "kuus", "seitse", "kaheksa", "üheksa"],
               stems=["null", "üks", "kaks", "kolm", "neli", "viis", "kuus", "seitse", "kaheksa", "üheksa"],
               tens_stems=None, teen="teist", ten="kümme", tens="kümmend", hundred="sada", hundred_pl=None,
               thousand="tuhat", thousand_pl=None, million="miljon", million_pl=None, joins=True, point="koma"),
    "lv": dict(ones=["nulle", "viens", "divi", "trīs", "četri", "pieci", "seši", "septiņi", "astoņi", "deviņi"],
               stems=["", "vien", "div", "trīs", "četr", "piec", "seš", "septiņ", "astoņ", "deviņ"],
               tens_stems=None, teen="padsmit", ten="desmit", tens="desmit", hundred="simts", hundred_pl="simti",
               thousand="tūkstotis", thousand_pl="tūkstoši", million="miljons", million_pl="miljoni", joins=False,
               point="komats"),
    "lt": dict(ones=["nulis", "vienas", "du", "trys", "keturi", "penki", "šeši", "septyni", "aštuoni", "devyni"],
               stems=["", "vienuo", "dvy", "try", "keturio", "penkio", "šešio", "septynio", "aštuonio", "devynio"],
               tens_stems=["", "", "dvi", "tris", "keturias", "penkias", "šešias", "septynias", "aštuonias",
                           "devynias"],
               teen="lika", ten="dešimt", tens="dešimt", hundred="šimtas", hundred_pl="šimtai",
               thousand="tūkstantis", thousand_pl="tūkstančiai", million="milijonas", million_pl="milijonai",
               joins=False, point="kablelis"),
}


def _table(language: str):
    return _T.get(language.lower()[:2])


def _below1000(n: int, t: dict) -> list:
    out = []
    h, r = n // 100, n % 100
    if h == 1:
        out.append(t["hundred"])
    elif h > 1:
        if t["joins"]:
            out.append(t["ones"][h] + t["hundred"])
        else:
            out += [t["ones"][h], t["hundred_pl"] or t["hundred"]]
    if r > 0:
        tens, u = r // 10, r % 10
        if tens == 1:
            out.append(t["ten"] if r == 10 else t["stems"][u] + t["teen"])
        else:
            if tens > 1:
                stem = (t["tens_stems"] or t["stems"])[tens]
                out.append(t["ones"][tens] + " " + t["tens"] if t["joins"] else stem + t["tens"])
            if u > 0:
                out.append(t["ones"][u])
    return out


def spell(n: int, language: str):
    t = _table(language)
    if t is None:
        return None
    v = abs(n)
    if v == 0:
        return [t["ones"][0]]
    if v > MAX_SPELLED:
        return None
    out = []
    millions, rest = v // 1_000_000, v % 1_000_000
    if millions > 0:
        if millions == 1:
            out.append(t["million"])
        else:
            out += _below1000(millions, t) + [t["million_pl"] or t["million"]]
    thousands, below = rest // 1000, rest % 1000
    if thousands > 0:
        if thousands == 1:
            out.append(t["thousand"])
        else:
            out += _below1000(thousands, t) + [t["thousand_pl"] or t["thousand"]]
    if below > 0:
        out += _below1000(below, t)
    return out


def _spell_or_digits(digits: str, t: dict, language: str) -> str:
    if digits.isascii() and len(digits) <= 9 and not (len(digits) > 1 and digits.startswith("0")):
        n = int(digits)
        if n <= MAX_SPELLED:
            words = spell(n, language)
            if words:
                return " ".join(words)
    return " ".join(t["ones"][d] for d in (_digit_value(c) for c in digits) if d is not None)


def expand_numbers(text: str, language: str) -> str:
    t = _table(language)
    if t is None or not any(_is_number(c) for c in text):
        return text
    out, digits, pending = [], "", None
    i, n = 0, len(text)

    def flush():
        nonlocal digits, pending
        if not digits:
            return
        words = _spell_or_digits(digits, t, language)
        if pending is not None:
            out.append(words + " " + t["point"] + " " + _spell_or_digits(pending, t, language))
            pending = None
        else:
            out.append(words)
        digits = ""

    while i < n:
        ch = text[i]
        if _is_number(ch) and _digit_value(ch) is not None:
            digits += ch
            i += 1
            continue
        if ch in ",." and digits and pending is None and i + 1 < n and _is_number(text[i + 1]):
            j, frac = i + 1, ""
            while j < n and _is_number(text[j]):
                frac += text[j]
                j += 1
            pending = frac
            i = j
            continue
        flush()
        out.append(ch)
        i += 1
    flush()
    return "".join(out)


# -- ordinals
NOM, GEN, DAT, ACC, INS, LOC, PAR, ILL, INE, ELA, ALL, ADE, ABL, TRA = range(14)


class Form:
    __slots__ = ("case", "feminine", "plural", "definite")

    def __init__(self, case=NOM, feminine=False, plural=False, definite=True):
        self.case, self.feminine, self.plural, self.definite = case, feminine, plural, definite


_LV_UNITS = ["", "pirm", "otr", "treš", "ceturt", "piekt", "sest", "septīt", "astot", "devīt"]
_LT_UNITS = ["", "pirm", "antr", "treči", "ketvirt", "penkt", "šešt", "septint", "aštunt", "devint"]
_ET_NOM = ["", "esimene", "teine", "kolmas", "neljas", "viies", "kuues", "seitsmes", "kaheksas", "üheksas"]
_ET_GEN = ["", "esimese", "teise", "kolmanda", "neljanda", "viienda", "kuuenda", "seitsmenda", "kaheksanda",
           "üheksanda"]
_ET_CARD_GEN = ["", "ühe", "kahe", "kolme", "nelja", "viie", "kuue", "seitsme", "kaheksa", "üheksa"]


def _latvian_ordinal(n: int, f: Form):
    lv = _T["lv"]
    if 1 <= n <= 9:
        stem = _LV_UNITS[n]
    elif n == 10:
        stem = "desmit"
    elif 11 <= n <= 19:
        stem = lv["stems"][n % 10] + "padsmit"
    elif 20 <= n <= 90 and n % 10 == 0:
        stem = lv["stems"][n // 10] + "desmit"
    elif 100 <= n <= 900 and n % 100 == 0:
        stem = "simt" if n == 100 else lv["stems"][n // 100] + "simt"
    elif 1000 <= n <= 9000 and n % 1000 == 0:
        stem = "tūkstoš" if n == 1000 else lv["stems"][n // 1000] + "tūkstoš"
    else:
        return None
    p, fem, c = f.plural, f.feminine, f.case
    if not p and not fem and c == NOM:
        e = "ais"
    elif not p and not fem and c == GEN:
        e = "ā"
    elif not p and not fem and c == DAT:
        e = "ajam"
    elif not p and fem and c == NOM:
        e = "ā"
    elif not p and fem and c == GEN:
        e = "ās"
    elif not p and fem and c == DAT:
        e = "ajai"
    elif not p and c in (ACC, INS):
        e = "o"
    elif not p and c == LOC:
        e = "ajā"
    elif p and not fem and c == NOM:
        e = "ie"
    elif p and fem and c in (NOM, ACC):
        e = "ās"
    elif p and not fem and c == ACC:
        e = "os"
    elif p and c == GEN:
        e = "o"
    elif p and not fem and c in (DAT, INS):
        e = "ajiem"
    elif p and fem and c in (DAT, INS):
        e = "ajām"
    elif p and not fem and c == LOC:
        e = "ajos"
    elif p and fem and c == LOC:
        e = "ajās"
    else:
        e = "ā" if fem else "ais"
    return stem + e


def _lithuanian_ordinal(n: int, f: Form):
    lt = _T["lt"]
    if 1 <= n <= 9:
        stem = _LT_UNITS[n]
    elif n == 10:
        stem = "dešimt"
    elif 11 <= n <= 19:
        stem = lt["stems"][n % 10] + "likt"
    elif 20 <= n <= 90 and n % 10 == 0:
        stem = lt["tens_stems"][n // 10] + "dešimt"
    elif n == 100:
        stem = "šimt"
    elif n == 1000:
        stem = "tūkstant"
    else:
        return None
    definite = {NOM: ("asis", "oji"), GEN: ("ojo", "osios"), DAT: ("ajam", "ajai"), ACC: ("ąjį", "ąją"),
                INS: ("uoju", "ąja"), LOC: ("ajame", "ojoje")}
    indefinite = {NOM: ("as", "a"), GEN: ("o", "os"), DAT: ("am", "ai"), ACC: ("ą", "ą"), INS: ("u", "a"),
                  LOC: ("ame", "oje")}
    pl_def = {NOM: ("ieji", "osios"), GEN: ("ųjų", "ųjų"), LOC: ("uosiuose", "osiose")}
    pl_indef = {NOM: ("i", "os"), GEN: ("ų", "ų"), LOC: ("uose", "ose")}
    table = (pl_def if f.definite else pl_indef) if f.plural else (definite if f.definite else indefinite)
    pair = table.get(f.case, table[NOM])
    return stem + (pair[1] if f.feminine else pair[0])


def _estonian_ordinal(n: int, f: Form):
    if 1 <= n <= 9:
        nom, gen = _ET_NOM[n], _ET_GEN[n]
    elif n == 10:
        nom, gen = "kümnes", "kümnenda"
    elif 11 <= n <= 19:
        nom, gen = _ET_CARD_GEN[n % 10] + "teistkümnes", _ET_CARD_GEN[n % 10] + "teistkümnenda"
    elif 20 <= n <= 90 and n % 10 == 0:
        nom, gen = _ET_CARD_GEN[n // 10] + "kümnes", _ET_CARD_GEN[n // 10] + "kümnenda"
    elif 100 <= n <= 900 and n % 100 == 0:
        p = "" if n == 100 else _ET_CARD_GEN[n // 100]
        nom, gen = p + "sajas", p + "sajanda"
    elif 1000 <= n <= 9000 and n % 1000 == 0:
        p = "" if n == 1000 else _ET_CARD_GEN[n // 1000]
        nom, gen = p + "tuhandes", p + "tuhandenda"
    else:
        return None
    short = gen[:-1] if gen.endswith("se") else gen
    c = f.case
    if f.plural:
        stem = short + "te"
        return {NOM: gen + "d", GEN: stem, PAR: stem, ILL: stem + "sse", INE: stem + "s", ELA: stem + "st",
                ALL: stem + "le", ADE: stem + "l", ABL: stem + "lt", TRA: stem + "ks"}.get(c, gen + "d")
    if c == PAR:
        return short + "t" if gen.endswith("se") else gen + "t"
    if c == ILL:
        return short + "se" if gen.endswith("se") else gen + "sse"
    return {NOM: nom, GEN: gen, INE: gen + "s", ELA: gen + "st", ALL: gen + "le", ADE: gen + "l",
            ABL: gen + "lt", TRA: gen + "ks"}.get(c, nom)


def estonian_genitive_cardinal(n: int) -> list:
    def below1000(n):
        out = []
        h, r = n // 100, n % 100
        if h > 0:
            out.append(("" if h == 1 else _ET_CARD_GEN[h]) + "saja")
        if r == 10:
            out.append("kümne")
        elif 10 < r < 20:
            out.append(_ET_CARD_GEN[r % 10] + "teistkümne")
        else:
            if r >= 20:
                out.append(_ET_CARD_GEN[r // 10] + "kümne")
            if r % 10 > 0:
                out.append(_ET_CARD_GEN[r % 10])
        return out
    out = []
    th, rest = n // 1000, n % 1000
    if th > 0:
        out += ([] if th == 1 else below1000(th)) + ["tuhande"]
    return out + below1000(rest)


def ordinal(n: int, language: str, form: Form | None = None):
    form = form or Form()
    if n <= 0 or n > 999_999:
        return None
    lang = language.lower()[:2]
    r = n % 100
    if r != 0:
        last = r if (r <= 20 or r % 10 == 0) else r % 10
    elif n % 1000 != 0:
        last = n % 1000
    else:
        last = n % 1_000_000
        if last // 1000 >= 10:
            return None
    head = n - last
    if lang == "lv":
        word = _latvian_ordinal(last, form)
        prefix = (spell(head, "lv") or []) if head > 0 else []
    elif lang == "lt":
        word = _lithuanian_ordinal(last, form)
        prefix = (spell(head, "lt") or []) if head > 0 else []
    elif lang == "et":
        word = _estonian_ordinal(last, form)
        prefix = estonian_genitive_cardinal(head) if head > 0 else []
    else:
        return None
    return None if word is None else " ".join(prefix + [word])


# ---------------------------------------------------------------------------------------------- Latvian
LV_ALPHABET = set("aābcčdeēfgģhiījkķlļmnņoprsštuūvzž")
_LV_VOWELS = set("aāeēiīuūo")
_LV_MAP_KEYS = set(" !\"#$'(),-.0123456789:;?X^_abcdefghijklmnopqrstuvwxyzæçðøħŋœǀǁǂǃɐɑɒɓɔɕɖɗɘəɚɛɜɞɟɠɡɢɣɤɥɦɧɨɪ"
                   "ɫɬɭɮɯɰɱɲɳɴɵɶɸɹɺɻɽɾʀʁʂʃʄʈʉʊʋʌʍʎʏʐʑʒʔʕʘʙʛʜʝʟʡʢʦʰʲˈˌːˑ˞ˤ̧̩̪̯̺̃"
                   "̻βεθχᵻ↑↓ⱱ")
_LV_LOAN_O = {
    "opera", "operas", "operā", "operu", "orkestris", "orkestri", "orkestrī", "organs", "orgāns", "organi", "ors",
    "oris", "ota", "otas", "otrs", "otra", "otri", "otrā", "objekts", "objekti", "oktobris", "oktobrī", "omārs",
    "omāri", "onkul", "onkulis", "onkuļi", "orhideja", "orhidejas", "osm", "osms", "procent", "procenti",
    "procents", "profesors", "profesori", "programma", "programmas", "proz", "proza", "radio", "stadions",
    "stadioni", "teorija", "teorijas", "televizor", "televizors", "televizori", "telefon", "telefons", "telefoni",
    "zooloģija", "zoologs", "kontrole", "kontroles", "komiteja", "komitejas", "kopija", "kopijas", "koris", "kori",
    "kosmoss", "kosmosa", "mikrofons", "mikrofoni", "monitors", "monitori", "motors", "motori", "nometne",
    "nometnes", "norma", "normas"}
_LV_CONS = {"b": "b", "c": "ts", "č": "tʃ", "d": "d", "f": "f", "g": "ɡ", "ģ": "ɟ", "h": "h", "j": "j", "k": "k",
            "ķ": "c", "l": "l", "ļ": "ʎ", "m": "m", "ņ": "ɲ", "p": "p", "r": "r", "s": "s", "š": "ʃ", "t": "t",
            "v": "ʋ", "z": "z", "ž": "ʒ"}
_LV_VOW = {"a": "a", "ā": "aː", "e": "e", "ē": "æː", "i": "i", "ī": "iː", "u": "u", "ū": "uː"}


def _lv_word(word: str) -> str:
    chars, n = list(word), len(word)
    first = next((i for i, c in enumerate(chars) if c in _LV_VOWELS), None)
    out, i = [], 0
    while i < n:
        ch = chars[i]
        nxt = chars[i + 1] if i + 1 < n else None
        nxt2 = chars[i + 2] if i + 2 < n else None
        if i == first:
            out.append("ˈ")
        if ch == "d":
            if nxt == "z":
                if nxt2 == "ž":
                    out.append("dʒ")
                    i += 3
                    continue
                out.append("dz")
                i += 2
                continue
            if nxt == "ž":
                out.append("dʒ")
                i += 2
                continue
        if ch in _LV_VOW:
            out.append(_LV_VOW[ch])
        elif ch == "o":
            out.append("oː" if word.lower() in _LV_LOAN_O else "uo")
        elif ch == "n":
            out.append("ŋ" if nxt in ("k", "g") else "n")
        elif ch in _LV_CONS:
            out.append(_LV_CONS[ch])
        else:
            out.append(ch)
        i += 1
    return "".join(out)


def latvian_phonemes(text: str) -> str:
    t = expand_numbers(text, "lv").lower()
    allowed = LV_ALPHABET | set(" .,!?")
    t = "".join(c if c in allowed else " " for c in t)
    t = re.sub(r"\s+", " ", t).strip(" ")
    out = []
    for i, w in enumerate(t.split(" ")):
        if i > 0:
            out.append(" ")
        if w:
            out.append(_lv_word(w))
    return "".join(c for c in "".join(out) if c in _LV_MAP_KEYS)


# ---------------------------------------------------------------------------------------------- Lithuanian
LT_ALPHABET = set("aąbcčdeęėfghiįyjklmnoprsštuųūvzž")
_KEPT = set(".,!?;:")
_LT_VOWELS = set("aąeęėiįyouųū")
_LT_SOFT = set("eęėiįy")
_LT_VIPA = {"a": "a", "ą": "aː", "e": "e", "ę": "ɛː", "ė": "eː", "i": "ɪ", "į": "iː", "y": "iː", "o": "oː", "u": "ʊ",
            "ų": "uː", "ū": "uː"}
_LT_DIPH = {"ai": "ai", "au": "au", "ei": "ei", "ie": "ie", "ui": "ui", "uo": "uo", "oi": "oi", "ou": "ou",
            "eu": "eu", "ia": "ia"}
_LT_CIPA = {"b": "b", "c": "ts", "č": "tʃ", "d": "d", "f": "f", "g": "ɡ", "h": "h", "j": "j", "k": "k", "l": "ɭ",
            "m": "m", "n": "n", "p": "p", "r": "r", "s": "s", "š": "ʃ", "t": "t", "v": "v", "z": "z", "ž": "ʒ"}


def _tokenize(text: str, language: str, alphabet: set) -> list:
    out, cur = [], ""
    for ch in expand_numbers(text, language).lower():
        if ch in alphabet:
            cur += ch
        else:
            if cur:
                out.append((True, cur))
                cur = ""
            out.append((False, ch if ch in _KEPT or ch == " " else " "))
    if cur:
        out.append((True, cur))
    return out


def _lt_rules(word: str) -> str:
    chars, pieces, i = list(word), [], 0
    while i < len(chars):
        ch = chars[i]
        if ch in _LT_VOWELS:
            if i + 1 < len(chars) and chars[i + 1] in _LT_VOWELS and (chars[i] + chars[i + 1]) in _LT_DIPH:
                pieces.append((_LT_DIPH[chars[i] + chars[i + 1]], True))
                i += 2
                continue
            pieces.append((_LT_VIPA.get(ch, ch), True))
            i += 1
        elif ch in _LT_CIPA:
            soft = i + 1 < len(chars) and chars[i + 1] in _LT_SOFT
            pieces.append((_LT_CIPA[ch] + ("ʲ" if soft else ""), False))
            i += 1
        else:
            i += 1
    vowels = [k for k, p in enumerate(pieces) if p[1]]
    if not vowels:
        return "".join(p[0] for p in pieces)
    target = vowels[max(0, len(vowels) - 2)]
    return "".join(("ˋ" if k == target else "") + p[0] for k, p in enumerate(pieces))


def lithuanian_phonemes(text: str) -> str:
    d = _load("lt.dict", "dict")
    return "".join((d.get(s.lower()) or _lt_rules(s.lower())) if word else s
                   for word, s in _tokenize(text, "lt", LT_ALPHABET))


# ---------------------------------------------------------------------------------------------- Estonian
ET_ALPHABET = set("abcdefghijklmnopqrsšzžtuvwõäöüxy")
_ET_VOWELS = set("aeiouõäöüy")
_ET_WEAK = set("bdghjlmnrsvf")
_ET_SON = set("lnr")
_ET_TRANSP = set("ndstkgl")
_ET_STOPS = set("ptk")
_ET_OFFGLIDE = set("lts")
_ET_PAL = {"l": "ʎ", "n": "ɲ", "s": "s^", "t": "t^", "d": "d^"}
_ET_DEVOICE = {"b": "p", "d": "t", "g": "k"}
_ET_REDUCE = {"a": "ɑ", "e": "ɛ", "i": "ɪ", "u": "ʊ", "o": "ɔ"}
_ET_LONG = {"aa": "aː", "ee": "eː", "ii": "iː", "oo": "oː", "uu": "uː", "õõ": "ɵː", "ää": "æː", "öö": "øː",
            "üü": "yː"}
_ET_DIPH = {"ae", "ai", "ao", "au", "ea", "ei", "eo", "eu", "ie", "iu", "oa", "oe", "oi", "ou", "õa", "õe", "õi",
            "õo", "õu", "äe", "äi", "äo", "äu", "öa", "öi", "öu", "üa", "üi", "ui"}
_ET_BASE = {"a": "a", "e": "e", "i": "i", "o": "o", "u": "u", "õ": "ɵ", "ä": "æ", "ö": "ø", "ü": "y", "y": "y",
            "b": "b", "d": "d", "f": "f", "g": "ɡ", "h": "h", "j": "j", "k": "k", "l": "l", "m": "m", "n": "n",
            "p": "p", "r": "r", "s": "s", "t": "t", "v": "v", "z": "z", "š": "ʃ", "ž": "ʒ", "c": "ts", "q": "k",
            "w": "v", "x": "ks"}


def _et_nuclei(w):
    out, i = [], 0
    while i < len(w):
        if w[i] not in _ET_VOWELS:
            i += 1
            continue
        j = i + 1
        if j < len(w) and w[j] in _ET_VOWELS:
            pair = w[i] + w[j]
            if pair in _ET_LONG:
                j += 1
            elif pair in _ET_DIPH and (not out or w[j] == "u"):
                j += 1
        out.append((i, j))
        i = j
    return out


def _et_syllables(w, nu):
    out = []
    for k, (s, e) in enumerate(nu):
        if k + 1 < len(nu):
            gap_end = nu[k + 1][0]
            coda = gap_end - 1 if gap_end - e >= 2 else e
        else:
            coda = len(w)
        out.append((s, e, coda))
    return out


def _et_heavy(s):
    return (s[1] - s[0]) > 1 or s[2] > s[1]


def _et_marks(w, syls):
    k = len(syls)
    m = [""] * k
    if k == 0:
        return m
    stems = [x for x in range(1, max(k, 1)) if "".join(w[syls[x][0]:syls[x][1]]) in _ET_LONG]
    start = 2
    if stems:
        last = stems[-1]
        m[last] = "ˈ"
        first = "".join(w[syls[0][0]:syls[0][1]])
        if first in _ET_LONG:
            m[0] = "ˈ"
        elif len(first) == 2 or last > 1:
            m[0] = "ˌ"
        start = last + 2
    else:
        m[0] = "ˈ"
    i = start
    while i <= k - 1:
        p = i
        if i + 1 <= k - 1 and not _et_heavy(syls[i]) and _et_heavy(syls[i + 1]):
            p = i + 1
        if p >= k - 1:
            break
        m[p] = "ˌ"
        i = p + 2
    return m


def _et_palatalizes(w, i):
    ch = w[i]
    if ch not in _ET_PAL:
        return False
    j = i + 1
    while j < len(w) and w[j] == ch:
        j += 1
    if j < len(w) and w[j] in ("i", "j"):
        return True
    if j < len(w) and w[j] in _ET_TRANSP:
        k = j + 1
        while k < len(w) and w[k] == w[j]:
            k += 1
        if k < len(w) and w[k] in ("i", "j"):
            return True
    if ch == "n" and j >= len(w) and i > 0 and w[i - 1] in _ET_VOWELS:
        return False
    if ch == "n" and j < len(w) and w[j] == "t" and j + 1 >= len(w):
        return True
    return False


def _et_rules(word: str) -> str:
    w = list(word.lower())
    nu = _et_nuclei(w)
    if not nu:
        return "".join(_ET_BASE.get(c, c) for c in w)
    syls = _et_syllables(w, nu)
    marks = _et_marks(w, syls)
    light = len(nu) >= 2 and nu[0][1] - nu[0][0] == 1 and nu[1][0] - nu[0][1] == 1 and w[nu[0][1]] in _ET_WEAK
    at = {s: k for k, (s, _) in enumerate(nu)}
    out, i, n = [], 0, len(w)
    prev_end, prev_span, prev_hiatus = -1, 0, False
    while i < n:
        ch = w[i]
        if ch in _ET_VOWELS and i in at:
            k = at[i]
            s, end = nu[k]
            span = "".join(w[s:end])
            hiatus = s == prev_end
            prev_hiatus = hiatus
            if span in _ET_LONG:
                ph = _ET_LONG[span]
                if len(nu) == 1 and not (end < n and w[end] in _ET_STOPS):
                    ph = _ET_BASE.get(span[0], "") + ph
            elif len(span) == 2:
                ph = "".join(_ET_BASE.get(c, c) for c in span)
            else:
                b = _ET_BASE.get(ch, ch)
                next_vowel = end < n and w[end] in _ET_VOWELS
                if light and k == 1 and not next_vowel and ch in _ET_REDUCE:
                    b = _ET_REDUCE[ch]
                ph = b
            glide = ""
            if hiatus and prev_span == 2:
                last = w[prev_end - 1]
                glide = "j" if last == "i" else "w" if last == "u" else ""
            out.append(glide + marks[k] + ph)
            prev_end, prev_span = end, end - s
            i = end
            continue
        nxt = w[i + 1] if i + 1 < n else None
        b = _ET_BASE.get(ch, ch)
        after = i == prev_end
        coda = nxt is not None and nxt not in _ET_VOWELS and nxt != ch
        eligible = after and (prev_end == nu[0][1] or coda)
        if ch == "t" and after and prev_span == 2:
            if nxt == "s":
                out.append("i" + _ET_PAL["t"])
                i += 1
                continue
            eligible = False
        if eligible and _et_palatalizes(w, i):
            b = _ET_PAL[ch]
        if i == 0 and ch in _ET_DEVOICE and not (ch == "d" and nxt == "i"):
            b = _ET_DEVOICE[ch]
        if ch == "n" and nxt in ("k", "g"):
            b = "ŋ"
        if ch == "m" and nxt == "b":
            b = "mm"
        if nxt == ch:
            gem = b + "ː" if ch in _ET_STOPS else b + b
            if i + 2 >= n and ch in _ET_OFFGLIDE and after and prev_span == 1:
                p = _ET_PAL.get(ch, b)
                gem = p + "ː" if ch in _ET_STOPS else p + p
                out.append("i")
            out.append(gem)
            i += 2
            continue
        palatalized = b != _ET_BASE.get(ch, ch)
        if ch in _ET_STOPS and after and not palatalized:
            if prev_span == 2 and nxt is not None and (nxt in _ET_VOWELS or nxt in "lr"):
                b += "ː"
            elif prev_span == 1 and nxt == "r":
                b += "ː"
            elif prev_span == 1 and nxt == "l" and ch in "tk":
                b += "ː"
            elif prev_hiatus and nxt is not None and nxt in _ET_VOWELS:
                b += "ː"
        if ch == "k" and i > 0 and w[i - 1] in _ET_SON and nxt is not None and nxt in _ET_VOWELS:
            b += "ː"
        out.append(b)
        i += 1
    return "".join(out)


def estonian_phonemes(text: str) -> str:
    d = _load("et.dict", "dict")
    return "".join((d.get(s.lower()) or _et_rules(s.lower())) if word else s
                   for word, s in _tokenize(text, "et", ET_ALPHABET))


# ---------------------------------------------------------------------------------------------- the model's input
def without_stress_marks(text: str) -> str:
    return unicodedata.normalize("NFC", "".join(c for c in unicodedata.normalize("NFD", text)
                                                if ord(c) not in (0x300, 0x301, 0x303)))


def _latvian_text(text: str) -> str:
    t = re.sub(r"(\w)'(\w)", r"\1\2", text)
    t = re.sub(r"(\w)'(?=\W|$)", r"\1", t)
    out, piece = [], ""
    for ch in t:
        if ch in ";:":
            out.append(latvian_phonemes(piece) + ch)
            piece = ""
        else:
            piece += ch
    out.append(latvian_phonemes(piece))
    s = re.sub(r"\s+", " ", "".join(out))
    s = re.sub(r"\s+([;:])", r"\1", s)
    s = re.sub(r"([;:])(?=\S)", r"\1 ", s)
    return s.strip()


def _replace_all(s: str, pairs) -> str:
    for a, b in pairs:
        s = s.replace(a, b)
    return s


def unify(s: str, language: str) -> str:
    if language == "lv":
        return _replace_all(s, [("ɲ", "nʲ"), ("ʎ", "lʲ"), ("c", "kʲ"), ("ɟ", "ɡʲ"), ("ʋ", "v")])
    if language == "et":
        return _replace_all(s, [("^", "ʲ"), ("ɲ", "nʲ"), ("ʎ", "lʲ")])
    if language == "lt":
        t = s.replace("ˈ", "\x01").replace("ˌ", "\x02").replace("ˋ", "\x03")
        t = _replace_all(t, [("ɭʲ", "lʲ"), ("ɭ", "lʲ"), ("l̩", "l"), ("ʂ", "ʃ"), ("ɕ", "ʃʲ"), ("ʑ", "ʒʲ"),
                             ("ʲʲ", "ʲ")])
        t = t.replace("\x01", "ˈ↓").replace("\x02", "ˈ↑").replace("\x03", "ˈ")
        return t.rstrip() + "."
    return s


def phoneme_string(text: str, language: str):
    """The model's phonemes for prepared text (`prepare`), or None for a language the model does not know."""
    if language == "lv":
        return unify(_latvian_text(text), "lv")
    if language == "et":
        return unify(estonian_phonemes(text), "et")
    if language == "lt":
        return unify(lithuanian_phonemes(without_stress_marks(text)), "lt")
    return None


# ---------------------------------------------------------------------------------------------- the text layer
_ALPHABETS = {"lv": LV_ALPHABET, "lt": LT_ALPHABET, "et": ET_ALPHABET}


def _fold_letter(ch: str, language: str, alphabet: set):
    """The app's `fold` for one letter (already lowercased); the dumped table first, then its diacritics step."""
    table = _fold_table()[language]
    if ch in table:
        return table[ch] or None
    small = {"w": "v", "q": "k", "x": "ks", "y": "i", "ß": "ss", "ø": "ö" if language == "et" else "o", "č": "tš"}
    if ch in small:
        return small[ch]
    sc = unicodedata.normalize("NFD", ch)
    for k in range(len(sc) - 1, 0, -1):
        c = unicodedata.normalize("NFC", sc[:k])
        if c in alphabet:
            return c
        if c in small:
            return small[c]
    return None


def fold_foreign_letters(text: str, language: str) -> str:
    alphabet = _ALPHABETS.get(language)
    if alphabet is None:
        return text
    known = lambda c: c in alphabet or c.lower() in alphabet
    if not any(c.isalpha() and not known(c) for c in text):
        return text
    out = []
    for ch in text:
        if not ch.isalpha() or known(ch):
            out.append(ch)
            continue
        r = _fold_letter(ch.lower(), language, alphabet)
        if r:
            out.append(r[:1].upper() + r[1:] if ch.isupper() else r)
        else:
            out.append(ch)
    return "".join(out)


_LN = r"[^\W_]"            # \p{L} or \p{N}
_ORDINAL = re.compile(rf"(?<!{_LN})([IVXLCDM]+(?:\s*[–-]\s*[IVXLCDM]+)?)(?!{_LN})"
                      rf"|(?<!{_LN})(?<![.,])(\d{{1,6}})\.(?=\s+([^\W\d_]))")
_NEXT_WORD = re.compile(r"^\s+((?:[^\W_]|[’'-])+\.?)")
_NOT_ROMAN = {"CC", "CV", "LV", "XL", "LI", "CI", "DI", "MI"}
_CENTURY = {"lt": {"a": "amžiaus", "amž": "amžiaus"}, "lv": {"gs": "gadsimta", "gads": "gadsimta"},
            "et": {"saj": "sajandi"}}
_CONJ = {"ir", "ar", "iki", "arba", "bei", "un", "vai", "līdz", "ja", "või", "kuni"}
_ET_HOMONYMS = {"aasta": GEN, "mail": ADE}


def _next_token(after: str):
    m = _NEXT_WORD.match(after)
    if not m:
        return None
    raw = m.group(1)
    return raw, "".join(c for c in raw if c.isalpha()).lower(), m.end()


def _next_word(after: str):
    t = _next_token(after)
    return t if t and t[1] else None


def _previous_word(before: str):
    s = before.rstrip()
    i = len(s)
    while i > 0 and not s[i - 1].isspace():
        i -= 1
    return s[i:] or None


def _is_dictionary_word(w: str, language: str) -> bool:
    if len(w) <= 1:
        return False
    name = {"lv": "lv-morph.txt", "lt": "lt-morph.txt", "et": "et-morph.txt"}.get(language)
    return bool(name) and w in _load(name, "morph")


def _governing_word(after: str, is_number):
    n1 = _next_token(after)
    if not n1:
        return None, False
    if n1[1] not in _CONJ:
        return (n1 if n1[1] else None), False
    rest = after[n1[2]:]
    n2 = _next_token(rest)
    if not n2 or not is_number(n2[0]):
        return n1, False
    rest2 = rest[n2[2]:]
    n3 = _next_token(rest2)
    if not n3 or not n3[1]:
        return None, True
    return n3, True


def _roman_token(raw: str) -> bool:
    t = raw[:-1] if raw.endswith(".") else raw
    return t == t.upper() and roman_value(t) is not None


def _after_conjunction_with_number(before: str) -> bool:
    toks = before.split()[-2:]
    if len(toks) != 2 or toks[1].lower() not in _CONJ:
        return False
    return _roman_token(toks[0].strip("".join(c for c in toks[0] if unicodedata.category(c).startswith("P"))))


def _previous_word_starts_sentence(before: str) -> bool:
    s = before.rstrip()
    i = len(s)
    while i > 0 and not s[i - 1].isspace():
        i -= 1
    rest = s[:i].rstrip()
    if not rest:
        return True
    return rest[-1] in ".!?:;\"„“«»–—("


def _is_feminine(name: str, language: str) -> bool:
    n = name.lower()
    if language == "lv":
        return n.endswith(("a", "e"))
    if language == "lt":
        return n.endswith(("a", "ė"))
    return False


def _is_all_caps(w: str) -> bool:
    letters = "".join(c for c in w if c.isalpha())
    return len(letters) >= 2 and letters == letters.upper() and letters != letters.lower() \
        and roman_value(letters) is None


def _ends_sentence(after: str, offset: int) -> bool:
    rest = after[offset:].lstrip()
    return not rest or rest[0].isupper()


def _looks_like_initial(after: str) -> bool:
    if not after.startswith("."):
        return False
    rest = after[1:].lstrip()
    return bool(rest) and rest[0].isupper()


def _latvian_form(w: str) -> Form:
    rules = [("iem", DAT, False, True), ("ām", DAT, True, True), ("os", LOC, False, True), ("ās", LOC, True, True),
             ("am", DAT, False, False), ("ai", DAT, True, False), ("ei", DAT, True, False),
             ("as", GEN, True, False), ("es", GEN, True, False), ("ā", LOC, False, False), ("ī", LOC, False, False),
             ("ē", LOC, True, False), ("ū", LOC, False, False), ("a", GEN, False, False), ("e", NOM, True, False),
             ("u", ACC, False, False), ("i", NOM, False, True)]
    for end, c, fem, pl in rules:
        if w.endswith(end) and len(w) > len(end) + 1:
            return Form(c, fem, pl)
    return Form()


def _lithuanian_form(w: str) -> Form:
    rules = [("iaus", GEN, False, False), ("aus", GEN, False, False), ("iuje", LOC, False, False),
             ("uje", LOC, False, False), ("yje", LOC, False, False), ("ėje", LOC, True, False),
             ("oje", LOC, True, False), ("ių", ACC, False, False), ("ų", GEN, False, True), ("os", GEN, True, False),
             ("ės", GEN, True, False), ("ius", NOM, False, False), ("as", NOM, False, False),
             ("is", NOM, False, False), ("ys", NOM, False, False), ("us", NOM, False, False),
             ("ai", NOM, False, True), ("ui", DAT, False, False), ("io", GEN, False, False), ("o", GEN, False, False),
             ("ą", ACC, False, False), ("į", ACC, False, False), ("ė", NOM, True, False), ("a", NOM, True, False),
             ("e", LOC, False, False)]
    for end, c, fem, pl in rules:
        if w.endswith(end) and len(w) > len(end) + 1:
            return Form(c, fem, pl)
    return Form()


def _estonian_form(w: str):
    entry = _load("et-morph.txt", "morph").get(w)
    if not entry or entry[1] not in ("noun", "propn"):
        return None
    lemma = entry[0]
    if w in _ET_HOMONYMS:
        return Form(_ET_HOMONYMS[w])
    if w == lemma:
        return Form()
    if w == lemma + "d":
        return Form(plural=True)

    def shares(r):
        k = min(len(lemma), len(r)) - 1
        return k >= 2 and r[:k] == lemma[:k]
    for end, c in (("sse", ILL), ("ks", TRA), ("st", ELA), ("lt", ABL), ("le", ALL), ("ga", GEN), ("ni", GEN),
                   ("s", INE), ("l", ADE), ("t", PAR)):
        if not w.endswith(end):
            continue
        r = w[: len(w) - len(end)]
        if not shares(r) or len(r) < len(lemma) - 1:
            continue
        if c == PAR and not (r and r[-1] in "aeiouõäöü"):
            continue
        return Form(c, plural=len(r) > len(lemma) and r.endswith(("te", "de")))
    return Form(GEN, plural=len(w) > len(lemma) + 1 and w.endswith(("te", "de")))


def _form_from_next_word(word: str, language: str):
    if language == "lv":
        return _latvian_form(word)
    if language == "lt":
        return _lithuanian_form(word)
    if language == "et":
        return _estonian_form(word)
    return None


def _expansion(m, text: str, language: str):
    whole = m.group(0)
    before, after = text[: m.start()], text[m.end():]
    nxt = _next_word(after)
    if m.group(2) is not None:
        if language == "lt" or not m.group(3).islower():
            return None
        digits = m.group(2)
        if not digits.isascii():
            return None
        n = int(digits)
        fw, _ = _governing_word(after, lambda r: bool(r) and _is_number(r[0]) and r.endswith("."))
        if not fw or not fw[1]:
            return None
        full = _CENTURY.get(language, {}).get(fw[1])
        if fw[0].endswith(".") and full and nxt and nxt[1] == fw[1]:
            words = ordinal(n, language, Form(GEN))
            if not words:
                return None
            dot = "." if _ends_sentence(after, nxt[2]) else ""
            return words + " " + full + dot, nxt[2]
        form = _form_from_next_word(fw[1], language)
        if form is None:
            return None
        words = ordinal(n, language, form)
        return (words, 0) if words else None

    parts = [p.strip() for p in re.split(r"[–-]", whole)]
    values = []
    for part in parts:
        v = {"I": 1, "V": 5, "X": 10}.get(part) if len(part) == 1 else \
            (None if part in _NOT_ROMAN else roman_value(part))
        if v is None:
            return None
        values.append(v)
    prev = _previous_word(before)
    if len(parts) == 1 and len(parts[0]) == 1:
        is_head = prev is None and not before.strip() and len(text.split()) <= 4
        if not is_head or _looks_like_initial(after):
            return None
        if nxt and not _is_dictionary_word(nxt[1], language):
            return None
    if prev and _is_all_caps(prev):
        return None
    if nxt and _is_all_caps(nxt[0]):
        return None
    form, consumed, tail = Form(), 0, ""
    if nxt and nxt[0].endswith(".") and nxt[1] in _CENTURY.get(language, {}):
        form.case = GEN
        consumed = nxt[2]
        tail = " " + _CENTURY[language][nxt[1]] + ("." if _ends_sentence(after, nxt[2]) else "")
    elif prev and prev[0].isupper() and len(prev) >= 2 and all(c.isalpha() for c in prev) \
            and not _previous_word_starts_sentence(before):
        form.feminine = _is_feminine(prev, language)
    else:
        g, via = _governing_word(after, _roman_token)
        if g:
            if g[0].endswith(".") and g[1] in _CENTURY.get(language, {}):
                form.case = GEN
            else:
                f = _form_from_next_word(g[1], language)
                if f is not None:
                    form = f
        if len(parts) > 1 or via or _after_conjunction_with_number(before):
            form.plural = False
            if language == "lt" and form.case == ACC:
                form.case = GEN
    spelled = [ordinal(v, language, form) for v in values]
    if any(s is None for s in spelled):
        return None
    return " – ".join(spelled) + tail, consumed


def expand_ordinals(text: str, language: str) -> str:
    if language not in ("lv", "lt", "et") or not any(_is_number(c) or c in "IVXLCDM" for c in text):
        return text
    result = text
    for m in reversed(list(_ORDINAL.finditer(text))):
        e = _expansion(m, text, language)
        if not e:
            continue
        replacement, consumed = e
        result = result[: m.start()] + replacement + result[m.end() + consumed:]
    return result


def prepare(text: str, language: str) -> str:
    text = unicodedata.normalize("NFC", text)
    return fold_foreign_letters(expand_ordinals(text, language), language)


def phonemes(text: str, language: str) -> str:
    """Text → the model's phoneme string: the text layer, then the phonemizer of the book's language."""
    return phoneme_string(prepare(text, language), language) or ""
