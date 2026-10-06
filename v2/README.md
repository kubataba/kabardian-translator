# Kabardian Translator 3

Local translation and speech for **Kabardian** and **36 more languages** on a Mac with Apple Silicon. Everything
runs on your computer — no text leaves it.

- **Russian ↔ Kabardian** — our own model ([kubataba/ru-kbd-bidirectional](https://huggingface.co/kubataba/ru-kbd-bidirectional),
  MarianMT 61M, int8 ONNX): FLORES-200 chrF **ru→kbd 57.4, kbd→ru 50.2**, with the rules of the SayFable app —
  sentence units, quoted speech, a guard against press names, lost numbers and loops, calque replacement.
- **Every other pair** — **MADLAD-400 3B** (Google, Apache-2.0) in our Core ML build for the Apple Neural Engine.
  Kabardian with any language other than Russian goes through Russian automatically.
- **Speech** — **Silero v5** on ONNX (Kabardian, Russian, Ukrainian, Belarusian, Kazakh, Kyrgyz, Tatar, Bashkir,
  Uzbek, Azerbaijani, Tajik; Georgian and Armenian through the Kabardian voice), **our Baltic model** (Latvian,
  Lithuanian, Estonian — 18 voices) and the **Apple voices** installed on the Mac for the rest.
- **No length limit** — texts and documents (`.txt`, `.md`, `.docx`) are translated paragraph by paragraph with
  progress; the result downloads as `.txt` or `.docx`, alone or side by side with the original.
- **Interface in Russian, English and Latvian**, with a page describing every language: script, route, measured
  quality, voice.

> Windows and Linux: use version 2.0 (`pip install "kabardian-translator<3"`, folder `v1/` of this repository).

## Install

```bash
pip install kabardian-translator
kabardian-download-models all      # ≈ 1.7 GB on disk, once; or install from the Models tab
kabardian-translator               # opens http://127.0.0.1:5500
```

Requirements: macOS 13+ on Apple Silicon (M1 or newer), Python 3.11+, about 3 GB of free memory while MADLAD is
loaded. The first MADLAD start compiles the model for the Neural Engine (about a minute); later starts are fast.

## Command line

```bash
kabardian-translate -s ru -t kbd "Добрый день!"
kabardian-translate -s en -t kbd -i story.docx -o story.kbd.docx --both
kabardian-translate -s kbd -t lv -i text.txt -o text.lv.txt --fast
```

`--fast` uses greedy search for the Kabardian model (about twice as fast, −1 chrF); `--both` writes the original
and the translation paragraph by paragraph.

## Languages

| group | languages |
|---|---|
| main | Russian, Kabardian |
| Baltic and Estonian | Latvian, Lithuanian, Estonian |
| Slavic | Ukrainian, Belarusian, Polish, Czech, Slovak, Slovenian, Croatian, Bulgarian |
| European | English, German, French, Spanish, Italian, Portuguese, Catalan, Romanian, Dutch, Swedish, Danish, Norwegian, Finnish, Hungarian, Greek |
| Turkic | Turkish, Azerbaijani, Kazakh, Kyrgyz, Tatar, Bashkir, Uzbek |
| Caucasus | Armenian, Georgian |
| Iranian | Tajik |

Quality per language (chrF, FLORES-200) is on the **Languages** tab. Bashkir, Belarusian, Tatar, Tajik and Georgian
are translated through Russian; Russian → Armenian and Russian → Turkish through English — the pivots were chosen
by measurement. Georgian (chrF ≈ 24) and Uzbek (≈ 40) are weak and marked so.

## Models

| package | what | size | licence |
|---|---|---|---|
| `kbd-translate-v1` + `lang-v13/ru` | Russian ↔ Kabardian, int8 ONNX; Russian form dictionary for colour compounds | 80 MB + 3.6 MB | SIA Copper Line (release LICENCE); source model CC BY-NC 4.0; dictionary from Wiktionary via Kaikki, CC BY-SA 4.0 |
| `translate-madlad-v1` | MADLAD-400 3B, Core ML, 4-bit | 1.33 GB | Apache-2.0 (modified, see ATTRIBUTION.md) |
| `v5.1` + `v5.3` | Silero v5 TTS, ONNX; Russian stress and homographs | 88 MB + 30 MB | CC BY-NC-SA 4.0 (snakers4/silero-models); stress: silero-stress, MIT |
| `baltic-sayfable-v1` | Latvian, Lithuanian, Estonian TTS (Piper) | 94 MB | SIA Copper Line (release LICENCE) |

All packages come from the releases of [kubataba/sayfable-models](https://github.com/kubataba/sayfable-models) —
the same files the SayFable iOS app uses — and are verified by SHA-256 before installation. They are stored in
`~/.kabardian-translator/models/`.

## How it is built

- `engines/kbd.py` — the Kabardian model: SentencePiece tokens (parity with MarianTokenizer on 800 of 800 FLORES
  lines), beam 4 / greedy over the merged ONNX decoder, the app's sentence and quote rules, the guard ladder,
  calque replacement, Russian colour compounds resolved before translation («тёмно-синим» → «тёмным синим»), the
  palochka normalizer on input and output.
- `engines/madlad.py` — MADLAD: embeddings outside the graph, 4 encoder + 4 decoder Core ML chunks, greedy decoding,
  splitting at clause punctuation over 50 tokens, loop guard, Uzbek Cyrillic → Latin.
- `tts/silero.py` — the five Silero graphs with the length regulation and inverse STFT in numpy (no PyTorch).
- `tts/stress.py` — stress marks for Russian, Ukrainian and Belarusian (the only languages of the no-stress model
  that need them): the logic of silero-stress 1.5 (MIT) in numpy, with the accentor networks and the Russian
  homograph BERT in ONNX. Identical to the original on 200 of 200 Russian FLORES sentences.
- `tts/piper_baltic.py` + `bin/baltic-phonemes` — the Baltic model; its text layer and phonemizers are the app's own
  Swift code compiled into a small helper (`tools/baltic-phonemes/build.sh`), so the model reads exactly the input it
  was trained on.

## Licence

The code is CC BY-NC 4.0 (non-commercial). The models keep their own licences (table above). For commercial use
write to info@copperline.info.

© Eduard Emkuzhev (kubataba), SIA Copper Line.

**Thanks** to Anzor Kunashev for the open Kabardian texts (anzorq/kbd_monolingual) and the adiga-ai parallel corpus,
to Boris Orekhov for the open corpus of 19th-century Russian prose, to Google for MADLAD-400 and to Silero for their
speech models.
