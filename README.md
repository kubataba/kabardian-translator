# Kabardian Translator

Translation and speech synthesis for Kabardian and other languages, running locally.

| version | folder | platform | translation | speech |
|---|---|---|---|---|
| **3** (current) | [`v2/`](v2/) | macOS, Windows, Linux | our Russian ↔ Kabardian model (FLORES chrF 57.4 / 50.2) + MADLAD-400 on the Neural Engine (Mac with Apple Silicon, 38 languages) or SMaLL-100 (31 languages), any pair | Silero v5, our Baltic model; Apple voices on a Mac, Windows voices on Windows |
| 2 | [`v1/`](v1/) | Windows, Linux, macOS | MarianMT ru↔kbd + NLLB-200 | Silero v5 (PyTorch) |

```bash
pip install kabardian-translator          # version 3
pip install "kabardian-translator<3"      # version 2
```

Details: [v2/README.md](v2/README.md) · [v1/readme.md](v1/readme.md)

Licence: CC BY-NC 4.0 for the code; models under their own licences. © Eduard Emkuzhev (kubataba), SIA Copper Line.
