"""The languages of the translator: names in the three interface languages, script, how a pair is routed,
measured quality and which voice reads it.

Which engine translates depends on the computer (`system.translator()`): MADLAD or SMaLL-100 by the user's choice on
a Mac with Apple Silicon, SMaLL-100 elsewhere; it decides the language list, the routes and the quality shown.

Quality is chrF on FLORES-200 devtest, the first 50 sentences, greedy: for MADLAD as measured for the SayFable app
(prompt 405), for SMaLL-100 measured with this package's engine (prompt 418); for Kabardian all 200 sentences through
the app's pipeline (prompt 410). "via ru" / "via en" mark languages that an engine translates better through a pivot,
and the pivot is applied automatically.
"""
from .system import IS_MAC, IS_WINDOWS, translator

# code: (Russian, English, Latvian, script, group)
LANGS = {
    "ru":  ("Русский", "Russian", "Krievu", "Cyrillic", "core"),
    "kbd": ("Кабардинский", "Kabardian", "Kabardiešu", "Cyrillic", "core"),
    "en":  ("Английский", "English", "Angļu", "Latin", "europe"),
    "lv":  ("Латышский", "Latvian", "Latviešu", "Latin", "baltic"),
    "lt":  ("Литовский", "Lithuanian", "Lietuviešu", "Latin", "baltic"),
    "et":  ("Эстонский", "Estonian", "Igauņu", "Latin", "baltic"),
    "uk":  ("Украинский", "Ukrainian", "Ukraiņu", "Cyrillic", "slavic"),
    "be":  ("Белорусский", "Belarusian", "Baltkrievu", "Cyrillic", "slavic"),
    "pl":  ("Польский", "Polish", "Poļu", "Latin", "slavic"),
    "cs":  ("Чешский", "Czech", "Čehu", "Latin", "slavic"),
    "sk":  ("Словацкий", "Slovak", "Slovāku", "Latin", "slavic"),
    "sl":  ("Словенский", "Slovenian", "Slovēņu", "Latin", "slavic"),
    "hr":  ("Хорватский", "Croatian", "Horvātu", "Latin", "slavic"),
    "bg":  ("Болгарский", "Bulgarian", "Bulgāru", "Cyrillic", "slavic"),
    "de":  ("Немецкий", "German", "Vācu", "Latin", "europe"),
    "fr":  ("Французский", "French", "Franču", "Latin", "europe"),
    "es":  ("Испанский", "Spanish", "Spāņu", "Latin", "europe"),
    "it":  ("Итальянский", "Italian", "Itāļu", "Latin", "europe"),
    "pt":  ("Португальский", "Portuguese", "Portugāļu", "Latin", "europe"),
    "ca":  ("Каталанский", "Catalan", "Katalāņu", "Latin", "europe"),
    "ro":  ("Румынский", "Romanian", "Rumāņu", "Latin", "europe"),
    "nl":  ("Нидерландский", "Dutch", "Nīderlandiešu", "Latin", "europe"),
    "sv":  ("Шведский", "Swedish", "Zviedru", "Latin", "europe"),
    "da":  ("Датский", "Danish", "Dāņu", "Latin", "europe"),
    "no":  ("Норвежский", "Norwegian", "Norvēģu", "Latin", "europe"),
    "fi":  ("Финский", "Finnish", "Somu", "Latin", "europe"),
    "hu":  ("Венгерский", "Hungarian", "Ungāru", "Latin", "europe"),
    "el":  ("Греческий", "Greek", "Grieķu", "Greek", "europe"),
    "tr":  ("Турецкий", "Turkish", "Turku", "Latin", "turkic"),
    "az":  ("Азербайджанский", "Azerbaijani", "Azerbaidžāņu", "Latin", "turkic"),
    "kk":  ("Казахский", "Kazakh", "Kazahu", "Cyrillic", "turkic"),
    "ky":  ("Киргизский", "Kyrgyz", "Kirgīzu", "Cyrillic", "turkic"),
    "tt":  ("Татарский", "Tatar", "Tatāru", "Cyrillic", "turkic"),
    "ba":  ("Башкирский", "Bashkir", "Baškīru", "Cyrillic", "turkic"),
    "uz":  ("Узбекский", "Uzbek", "Uzbeku", "Latin", "turkic"),
    "hy":  ("Армянский", "Armenian", "Armēņu", "Armenian", "caucasus"),
    "ka":  ("Грузинский", "Georgian", "Gruzīnu", "Georgian", "caucasus"),
    "tg":  ("Таджикский", "Tajik", "Tadžiku", "Cyrillic", "iranian"),
}

GROUPS = {  # group: (Russian, English, Latvian)
    "core": ("Основные", "Main", "Galvenās"),
    "baltic": ("Балтийские и эстонский", "Baltic and Estonian", "Baltu un igauņu"),
    "slavic": ("Славянские", "Slavic", "Slāvu"),
    "europe": ("Европейские", "European", "Eiropas"),
    "turkic": ("Тюркские", "Turkic", "Turku"),
    "caucasus": ("Кавказ", "Caucasus", "Kaukāzs"),
    "iranian": ("Иранские", "Iranian", "Irāņu"),
}

# chrF on FLORES-200: (en→xx, ru→xx, xx→en, xx→ru) for MADLAD; pivots applied as marked.
QUALITY = {
    "ru": (62.3, None, 62.4, None), "de": (67.4, 57.7, 68.2, 58.5), "lv": (61.8, 56.2, 65.6, 54.7),
    "lt": (58.7, 50.3, 58.6, 48.0), "et": (58.1, 50.1, 60.6, 45.9), "uk": (58.3, 54.8, 67.3, 57.5),
    "kk": (49.5, 47.1, 58.3, 50.1), "tt": (36.2, 39.2, 31.2, 30.5), "hy": (44.7, 45.3, 56.4, 31.5),
    "be": (44.4, 43.8, 47.8, 49.4), "ba": (42.9, 41.4, 26.3, 32.4), "uz": (39.5, 39.5, 58.9, 46.9),
    "ky": (46.9, 44.3, 48.0, 39.5), "az": (44.0, 42.3, 45.1, 36.9), "tg": (30.2, 29.9, 36.7, 30.7),
    "tr": (62.6, 54.8, 63.5, 45.3), "fr": (75.0, 59.0, 71.1, 56.4), "es": (58.0, 52.2, 63.2, 54.3),
    "it": (61.3, 55.5, 62.3, 52.0), "pt": (72.4, 57.9, 72.8, 55.6), "nl": (62.6, 51.9, 65.8, 49.6),
    "sv": (68.2, 52.4, 70.4, 50.5), "da": (68.6, 52.4, 72.5, 52.8), "no": (62.9, 47.0, 67.2, 49.0),
    "pl": (55.8, 48.2, 60.5, 48.2), "cs": (57.8, 49.5, 67.0, 53.9), "sk": (63.5, 48.0, 64.9, 49.3),
    "hr": (59.6, 48.2, 64.0, 48.3), "bg": (69.8, 58.8, 67.2, 57.2), "sl": (55.9, 49.3, 62.5, 45.5),
    "ro": (71.3, 54.7, 72.8, 52.5), "ca": (70.0, 58.2, 70.6, 57.1), "el": (57.8, 46.7, 64.4, 49.0),
    "fi": (60.0, 53.0, 59.3, 45.0), "ka": (23.7, 23.9, 39.0, 24.3), "hu": (58.2, 47.3, 62.7, 48.5), "en": (None, 62.4, None, 62.3),
}
KBD_QUALITY = {"ru→kbd": 60.0, "kbd→ru": 51.7}

# SMaLL-100 (FLORES-200, first 50 sentences, greedy, this package's engine): (en→xx, ru→xx, xx→en, xx→ru)
QUALITY_SMALL = {
    "az": (29.5, 28.6, 39.9, 35.5), "be": (32.3, 31.6, 43.7, 41.5), "bg": (61.0, 53.3, 57.5, 48.3),
    "cs": (49.7, 42.4, 57.4, 47.1), "da": (61.6, 49.1, 63.2, 47.3), "de": (54.1, 47.6, 58.4, 47.2),
    "el": (48.9, 43.1, 55.6, 43.2), "en": (None, 53.3, None, 50.9), "es": (50.5, 45.7, 54.3, 44.2),
    "et": (49.2, 45.7, 52.9, 44.4), "fi": (47.0, 42.9, 51.1, 44.0), "fr": (61.9, 52.5, 61.3, 49.7),
    "hr": (51.9, 46.0, 54.7, 46.5), "hu": (51.3, 44.7, 51.8, 45.8), "hy": (33.9, 33.0, 48.9, 38.1),
    "it": (53.1, 46.1, 54.2, 43.9), "ka": (29.5, 28.6, 43.1, 37.9), "kk": (29.0, 29.3, 39.0, 34.2),
    "lt": (51.3, 46.7, 51.3, 45.8), "lv": (45.8, 40.8, 53.2, 45.1), "nl": (51.9, 46.6, 53.1, 43.4),
    "pl": (46.8, 42.1, 51.5, 44.1), "pt": (63.5, 51.2, 63.2, 51.5), "ro": (60.3, 49.2, 64.8, 50.9),
    "ru": (50.9, None, 53.3, None), "sk": (50.5, 45.7, 55.6, 46.8), "sl": (50.2, 46.8, 54.0, 45.1),
    "sv": (58.3, 46.6, 60.5, 46.8), "tr": (48.9, 41.6, 54.7, 42.0), "uk": (52.5, 51.3, 55.9, 52.1),
}
# languages SMaLL-100 does not offer: not in the model (ky, tt, tg, ca, no) or failing in it (ba, uz — prompt 379)
NOT_IN_SMALL = {"ky", "tt", "tg", "ca", "no", "ba", "uz"}
SMALL_VIA_EN = {"lv", "az", "ka", "kk", "tr", "be"}    # the measured English pivot (from lv az ka kk tr, to lv be tr)

VIA_RU_TARGETS = {"ba", "be", "tt", "tg", "ka"}   # MADLAD writes them far better from Russian (en→ba 27.7 → 42.9)
VIA_EN_FROM_RU = {"hy", "tr"}               # ru→hy 28.0 → 45.3, ru→tr 48.5 → 54.8 through English

# Speech: engine and voice per language (None = no voice). Silero v5 speakers, the Baltic Piper model, or the
# best Apple voice installed for the locale.
SPEECH = {
    "ru": ("silero", "ru_eduard"), "kbd": ("silero", "kbd_eduard"),
    "uk": ("silero", "ukr_igor"), "be": ("silero", "bel_anatoliy"),
    "kk": ("silero", "kz_M1"), "ky": ("silero", "kgz_nurgul"), "tt": ("silero", "tat_albina"),
    "ba": ("silero", "bak_aigul"), "uz": ("silero", "uzb_saida"), "az": ("silero", "aze_gamat"),
    "tg": ("silero", "tgk_onaxon"), "hy": ("silero", "hye_zara"), "ka": ("silero", "kat_vika"),
    "lv": ("baltic", "lv"), "lt": ("baltic", "lt"), "et": ("baltic", "et"),
}
APPLE_LOCALES = {
    "en": "en_US", "de": "de_DE", "fr": "fr_FR", "es": "es_ES", "it": "it_IT", "pt": "pt_PT", "nl": "nl_NL",
    "sv": "sv_SE", "da": "da_DK", "no": "nb_NO", "fi": "fi_FI", "pl": "pl_PL", "cs": "cs_CZ", "sk": "sk_SK",
    "hr": "hr_HR", "bg": "bg_BG", "sl": "sl_SI", "ro": "ro_RO", "ca": "ca_ES", "el": "el_GR", "hu": "hu_HU",
    "tr": "tr_TR",
}


ENGINE_NAMES = {"madlad": "MADLAD-400", "small100": "SMaLL-100"}


def available() -> list:
    """The language codes this computer translates."""
    small = translator() == "small100"
    return [c for c in LANGS if not small or c not in NOT_IN_SMALL]


def engine_name() -> str:
    return ENGINE_NAMES[translator()]


def name(code: str, ui: str = "en") -> str:
    ru, en, lv, *_ = LANGS[code]
    return {"ru": ru, "lv": lv}.get(ui, en)


def route(src: str, tgt: str) -> list:
    """The engine steps for a pair, e.g. [('madlad','en','ru'), ('kbd','ru','kbd')]."""
    if src == tgt:
        return []
    if {src, tgt} == {"ru", "kbd"}:
        return [("kbd", src, tgt)]
    if src == "kbd":
        return [("kbd", "kbd", "ru")] + route("ru", tgt)
    if tgt == "kbd":
        return route(src, "ru") + [("kbd", "ru", "kbd")]
    if translator() == "small100":
        return [("small100", src, tgt)]                 # the engine applies its own English pivot
    if tgt in VIA_RU_TARGETS and src != "ru":
        return [("madlad", src, "ru"), ("madlad", "ru", tgt)]
    if src == "ru" and tgt in VIA_EN_FROM_RU:
        return [("madlad", "ru", "en"), ("madlad", "en", tgt)]
    return [("madlad", src, tgt)]


def describe(ui: str = "en") -> list:
    """Rows for the languages page."""
    rows = []
    small = translator() == "small100"
    for code in available():
        _, _, _, script, group = LANGS[code]
        q = (QUALITY_SMALL if small else QUALITY).get(code)
        engine, voice = SPEECH.get(code, (None, None))
        if engine is None and code in APPLE_LOCALES:
            engine = "apple" if IS_MAC else "windows" if IS_WINDOWS else None
        if code == "kbd":
            how = "kbd"
        elif small:
            how = "via_en" if code in SMALL_VIA_EN else "direct"
        elif code in VIA_RU_TARGETS:
            how = "via_ru"
        else:
            how = "direct"
        rows.append({
            "code": code, "name": name(code, ui), "native": LANGS[code][0] if code in ("ru", "kbd") else None,
            "script": script, "group": group, "group_name": dict(zip(("ru", "en", "lv"), GROUPS[group])).get(ui),
            "route": how, "quality": q, "kbd_quality": KBD_QUALITY if code == "kbd" else None,
            "speech": engine,
        })
    return rows
