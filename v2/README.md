# Kabardian Translator 3

Local translation and speech for **Kabardian** and **30–37 more languages** on macOS, Windows and Linux. Everything
runs on your computer — no text leaves it.

| | Mac with Apple Silicon | Windows, Linux (and Intel Macs) |
|---|---|---|
| Russian ↔ Kabardian | our model | our model |
| every other pair | **MADLAD-400 3B** on the Neural Engine, 37 languages — or SMaLL-100 by choice | **SMaLL-100**, 30 languages |
| speech | Silero, our Baltic model, Apple voices | Silero, our Baltic model; on Windows the Windows voices |
| models on disk | ≈ 1.7 GB with MADLAD, ≈ 0.8 GB with SMaLL-100 | ≈ 0.8 GB |

- **Russian ↔ Kabardian** — our own model ([kubataba/ru-kbd-bidirectional](https://huggingface.co/kubataba/ru-kbd-bidirectional),
  MarianMT 61M, int8 ONNX): FLORES-200 chrF **ru→kbd 57.4, kbd→ru 50.2**, with the rules of the SayFable app —
  sentence units, quoted speech, a guard against press names, lost numbers and loops, calque replacement.
- **Every other pair** — on a Mac with Apple Silicon **MADLAD-400 3B** (Google, Apache-2.0) in our Core ML build for
  the Apple Neural Engine; elsewhere **SMaLL-100** (Mohammadshahi et al., MIT) in our int8 ONNX build — lighter, a
  little weaker (5–10 chrF), no Kyrgyz, Tatar, Tajik, Bashkir, Uzbek, Catalan or Norwegian. Kabardian with any
  language other than Russian goes through Russian automatically.
- **Speech** — **Silero v5** on ONNX (Kabardian, Russian, Ukrainian, Belarusian, Kazakh, Kyrgyz, Tatar, Bashkir,
  Uzbek, Azerbaijani, Tajik; Georgian and Armenian through the Kabardian voice), **our Baltic model** (Latvian,
  Lithuanian, Estonian — 18 voices) on every system, and the system's voices for the rest: the **Apple voices** on a
  Mac, the **Windows voices** (OneCore and SAPI) on Windows. Linux has no system voices worth using, so languages
  without Silero or the Baltic model are not read aloud there.
- **No length limit** — texts and documents (`.txt`, `.md`, `.docx`) are translated paragraph by paragraph with
  progress. **Save** writes `.txt` or `.docx`: the translation alone, or the original and the translation sentence
  by sentence with both languages named (a two-column table in `.docx`).
- **Listening** — both the original and the translation; ▶ turns into ■ and stops at once. The translation is
  highlighted while it is read (sentences; words for Silero voices), and a click on a sentence plays from it.
- **Interface in Russian, English and Latvian**, with a page describing every language: script, route, measured
  quality, voice. Light (warm paper) and dark themes, switched with ☀/☾; until chosen, the system's is used.

## Install

```bash
pip install kabardian-translator
kabardian-translator               # opens http://127.0.0.1:5500
```

On the first start the models this system uses are downloaded in the background (once; progress is shown on the
page) — whatever is ready can be used at once. To download them beforehand: `kabardian-download-models all`; to start
without downloading: `kabardian-translator --no-download`.

Requirements: Python 3.11+. On a Mac with Apple Silicon (macOS 13+) about 3 GB of free memory while MADLAD is
loaded; its first start compiles the model for the Neural Engine (about two minutes), later starts are fast. On
Windows and Linux about 1.5 GB of free memory.

**MADLAD or SMaLL-100 on a Mac.** The engine name next to the language selectors is a switch. SMaLL-100 is for a
rough translation or a small disk: 289 MB instead of 1.3 GB and about ten times faster, but 7–8 chrF weaker on
average and 30 languages instead of 37. Only the chosen model stays on disk — switching downloads it and removes the
other; switching back downloads MADLAD again. The same from the terminal: `kabardian-download-models use small100`
(or `use madlad`). On Windows and Linux SMaLL-100 is the only choice. `KT_TRANSLATOR=small100` forces it for one run.

More Windows voices: Settings → Time & language → Speech → Add voices.

## Command line

```bash
kabardian-translate -s ru -t kbd "Добрый день!"
kabardian-translate -s en -t kbd -i story.docx -o story.kbd.docx --both
kabardian-translate -s kbd -t lv -i text.txt -o text.lv.txt --fast
```

`--fast` uses greedy search for the Kabardian model (about twice as fast, −1 chrF); `--both` writes the original
and the translation sentence by sentence, each line marked with its language code.

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

The list is MADLAD's; SMaLL-100 (Windows, Linux) has all of them but Kyrgyz, Tatar, Tajik, Bashkir, Uzbek, Catalan
and Norwegian. Quality per language (chrF, FLORES-200) for the engine of your system is on the **Languages** tab.
Pivots were chosen by measurement and are applied automatically: MADLAD translates Bashkir, Belarusian, Tatar, Tajik
and Georgian through Russian, Russian → Armenian and Russian → Turkish through English; SMaLL-100 goes through
English from Latvian, Azerbaijani, Georgian, Kazakh and Turkish and to Latvian, Belarusian and Turkish. Georgian is
weak on both engines and marked so.

## Models

| package | what | size | licence |
|---|---|---|---|
| `kbd-translate-v1` + `lang-v13/ru` | Russian ↔ Kabardian, int8 ONNX; Russian form dictionary for colour compounds | 80 MB + 3.6 MB | SIA Copper Line (release LICENCE); source model CC BY-NC 4.0; dictionary from Wiktionary via Kaikki, CC BY-SA 4.0 |
| `translate-madlad-v1` | MADLAD-400 3B, Core ML, 4-bit (Mac with Apple Silicon) | 1.33 GB | Apache-2.0 (modified, see ATTRIBUTION.md) |
| `translate-v1` | SMaLL-100, int8 ONNX (Windows, Linux, Intel Mac) | 289 MB | MIT (alirezamsh/small100; teacher facebook/m2m100_418M) |
| `v5.1` + `v5.3` | Silero v5 TTS, ONNX; Russian stress and homographs | 88 MB + 30 MB | CC BY-NC-SA 4.0 (snakers4/silero-models); stress: silero-stress, MIT |
| `baltic-sayfable-v1` + `lang-v2/lv`, `lang-v7/lt`, `lang-v4/et` | Latvian, Lithuanian, Estonian TTS (Piper); form dictionaries for the text layer | 94 MB + 2.2 MB | SIA Copper Line (release LICENCE); dictionaries from Wiktionary via Kaikki, CC BY-SA 4.0 |

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
- `engines/small100.py` — SMaLL-100: the app's SentencePiece BPE (96 of 96 of the app's tokenizer cases), greedy
  decoding over the merged ONNX decoder, sentence units, clauses over 60 tokens, loop guard, numbers carried from the
  original, the measured English pivots. FLORES-200 within ±0.4 chrF of the release notes on all eight directions.
- `tts/silero.py` — the five Silero graphs with the length regulation and inverse STFT in numpy (no PyTorch).
- `tts/stress.py` — stress marks for Russian, Ukrainian and Belarusian (the only languages of the no-stress model
  that need them): the logic of silero-stress 1.5 (MIT) in numpy, with the accentor networks and the Russian
  homograph BERT in ONNX. Identical to the original on 200 of 200 Russian FLORES sentences.
- `tts/piper_baltic.py` + `tts/baltic_text.py` — the Baltic model and the app's text layer and Latvian, Lithuanian,
  Estonian phonemizers ported from Swift, so the model reads exactly the input it was trained on: identical to the
  app's code on 600 parity lines, 3036 FLORES sentences and the hard cases (numbers, Roman numerals, ordinals,
  foreign letters). Letters of other scripts use the app's own answers, dumped by `tools/baltic_fold.swift`.
- `tts/windows.py` — Windows voices through OneCore (`winrt`) and SAPI 5 (`comtypes`).

## Licence

The code is CC BY-NC 4.0 (non-commercial). The models keep their own licences (table above). For commercial use
write to info@copperline.info.

© Eduard Emkuzhev (kubataba), SIA Copper Line.

**Thanks** to Anzor Kunashev for the open Kabardian texts (anzorq/kbd_monolingual) and the adiga-ai parallel corpus,
to Boris Orekhov for the open corpus of 19th-century Russian prose, to Google for MADLAD-400, to Alireza
Mohammadshahi and co-authors for SMaLL-100 and to Silero for their speech models.
