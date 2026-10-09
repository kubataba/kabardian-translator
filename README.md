# Kabardian Translator

Translation and speech synthesis for Kabardian and other languages, running locally.

| version | folder | platform | translation | speech |
|---|---|---|---|---|
| **3** (current) | [`v2/`](v2/) | macOS, Windows, Linux | our Russian ↔ Kabardian model, version 2 (FLORES chrF 60.0 / 51.9) + MADLAD-400 on the Neural Engine (Mac with Apple Silicon, 38 languages) or SMaLL-100 (31 languages), any pair | Silero v5, our Baltic model; Apple voices on a Mac, Windows voices on Windows |
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
