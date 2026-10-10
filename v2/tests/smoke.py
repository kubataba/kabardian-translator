"""Smoke test of an installed kabardian-translator on any system (GitHub Actions: Ubuntu, Windows).

Expects the models of this system installed (`kabardian-download-models all`). Checks:
  * the Baltic text layer gives the Swift app's phonemes on 38 recorded cases (tests/baltic_cases.json);
  * translation: en→ru, ru→kbd, kbd→en, ru→lv (SMaLL-100 + our Kabardian model, or MADLAD on Apple Silicon);
  * speech: Silero (ru), the Baltic model (lv), and on Windows a Windows voice for English.
Exit code 1 on the first failure.
"""
import json
import re
import sys
from pathlib import Path

from kabardian_translator import languages, models
from kabardian_translator.system import SYSTEM_VOICES, translator
from kabardian_translator.translator import Translator
from kabardian_translator.tts import Speech, baltic_text

print(f"system: translator={translator()}, system voices={SYSTEM_VOICES}, languages={len(languages.available())}")
missing = [k for k in models.available() if not models.installed(k)]
assert not missing, f"models not installed: {missing}"

baltic_text.set_folder(models.folder("baltic"))
cases = json.loads((Path(__file__).parent / "baltic_cases.json").read_text("utf-8"))
bad = [c for c in cases if baltic_text.phonemes(c["text"], c["lang"]) != c["phonemes"]]
for c in bad[:5]:
    print("BALTIC MISMATCH", c["lang"], c["text"], "\n  expected", c["phonemes"],
          "\n  got     ", baltic_text.phonemes(c["text"], c["lang"]))
assert not bad, f"Baltic phonemes: {len(bad)} of {len(cases)} differ"
print(f"baltic phonemes: {len(cases)} / {len(cases)}")

tr = Translator()
checks = [("en", "ru", "The old castle stood on the hill above the river.", r"[А-Яа-яЁё]{3}"),
          ("ru", "kbd", "Старинный замок стоял на горе.", r"[ӏ]|[А-Яа-я]{3}"),
          ("kbd", "en", "Уи пщыхьэщхьэ фӏыуэ!", r"[A-Za-z]{3}"),
          ("ru", "lv", "Мы долго шли по лесу.", r"[a-zāēīūčšž]{3}"),
          # the sentence that broke on Windows (x86 without VNNI) into ">>kbd<<" with the 8-bit model
          ("ru", "kbd", "И день и ночь мы мчимся прочь от боли страха и забот и наконец закончив путь мечтаем вновь "
                        "его вернуть.", r"[ӏ]")]
for s, t, text, pattern in checks:
    out = tr.text(text, s, t)
    print(f"{s}->{t}: {out}")
    assert out.strip() and out.strip() != text and re.search(pattern, out), f"{s}->{t} failed"
    assert ">>" not in out, f"{s}->{t}: a model tag in the output"

sp = Speech()
for lang, text in [("ru", "Старинный замок стоял на горе."), ("lv", "Grāmata iznāca 1984. gadā.")]:
    y, rate = sp.synthesize(text, lang)
    print(f"speech {lang}: {sp.options(lang)[0]['label']}, {len(y) / rate:.2f} s")
    assert len(y) / rate > 0.8, f"speech {lang} too short"

if SYSTEM_VOICES == "windows":
    from kabardian_translator.tts import windows
    vs = windows.voices()
    print(f"windows voices: {len(vs)}", [(v['name'], v['locale'], v['api']) for v in vs][:12])
    opts = sp.options("en")
    assert opts, "no Windows voice for English"
    y, rate = sp.synthesize("The old castle stood on the hill.", "en", opts[0]["id"])
    print(f"speech en: {opts[0]['label']}, {len(y) / rate:.2f} s at {rate} Hz")
    assert len(y) / rate > 0.8, "Windows voice too short"
    sapi = [v for v in vs if v["api"] == "sapi"]
    if sapi:
        y, rate = sp.synthesize("Hello.", sapi[0]["lang"], "win:" + sapi[0]["id"])
        print(f"SAPI {sapi[0]['name']}: {len(y) / rate:.2f} s at {rate} Hz")
        assert len(y) / rate > 0.2

print("OK")
sys.exit(0)
