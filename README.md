# Kabardian Translator

Translation and speech for Kabardian and 37 more languages, running locally on macOS, Windows and Linux — no text
leaves the computer.

**Translation**
- **Russian ↔ Kabardian** — our own model (FLORES-200 chrF 60.0 / 51.7). Kabardian with any other language goes
  through Russian automatically.
- **Any other pair** — on a Mac with Apple Silicon **MADLAD-400 3B** on the Neural Engine, all 37 languages; on
  Windows, Linux and Intel Macs **SMaLL-100**, 30 of them (no Kyrgyz, Tatar, Tajik, Bashkir, Uzbek, Catalan or
  Norwegian). The languages: English, German, French, Spanish, Italian, Portuguese, Catalan, Romanian, Dutch,
  Swedish, Danish, Norwegian, Finnish, Hungarian, Greek; Ukrainian, Belarusian, Polish, Czech, Slovak, Slovenian,
  Croatian, Bulgarian; Latvian, Lithuanian, Estonian; Turkish, Azerbaijani, Kazakh, Kyrgyz, Tatar, Bashkir, Uzbek;
  Armenian, Georgian, Tajik; Russian.

**Speech**
- **Silero `v5_cis_base_nostress`** ([snakers4/silero-models](https://github.com/snakers4/silero-models),
  CC BY-NC-SA 4.0; our ONNX export, no PyTorch) — Russian, Kabardian, Ukrainian, Belarusian, Kazakh, Kyrgyz, Tatar,
  Bashkir, Uzbek, Azerbaijani, Tajik, Armenian, Georgian; stress for Russian, Ukrainian and Belarusian is placed
  before synthesis (silero-stress);
- **our Baltic model** — Latvian, Lithuanian, Estonian (18 voices);
- **system voices** for the other European languages and Turkish — Apple voices on a Mac, Windows voices on Windows
  (whatever is installed).

| version | folder | platform | translation | speech |
|---|---|---|---|---|
| **3** (current) | [`v2/`](v2/) | macOS, Windows, Linux | our Russian ↔ Kabardian model, version 2 (FLORES chrF 60.0 / 51.7) + MADLAD-400 on the Neural Engine (Mac with Apple Silicon, 38 languages) or SMaLL-100 (31 languages), any pair | Silero v5, our Baltic model; Apple voices on a Mac, Windows voices on Windows |
| 2 | [`v1/`](v1/) | Windows, Linux, macOS | MarianMT ru↔kbd + NLLB-200 | Silero v5 (PyTorch) |

```bash
pip install kabardian-translator          # version 3 (Python 3.11+)
pip install "kabardian-translator<3"      # version 2
```

Version 3 needs Python 3.11 or newer. On a Mac, MADLAD-400 works with Python 3.11–3.13 (coremltools has no build for
3.14 yet; with 3.14 the Mac uses SMaLL-100), and the system `python3` (3.9) is too old — install with
`uv tool install --python 3.11 kabardian-translator`. Step by step for Windows, Mac and Linux:
[v2/README.md → Install](v2/README.md#install).

Details: [v2/README.md](v2/README.md) · [v1/readme.md](v1/readme.md)

Licence: CC BY-NC 4.0 for the code; models under their own licences. © Eduard Emkuzhev (kubataba), SIA Copper Line.
