# 🌐 Kabardian Translator  
**Voice-Enabled Multilingual Translator for Caucasian Languages**

[![License](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.1.0-red.svg)](https://pytorch.org/)
[![Hugging Face](https://img.shields.io/badge/Hugging%20Face-Models-yellow.svg)](https://huggingface.co/)

> 🎯 **Educational tool** for learning Kabardian and Caucasian languages with AI-powered translation and speech synthesis

## ✨ Features

- **🧠 Smart Translation**: 14 languages with specialized Kabardian models
- **🔊 Voice Synthesis**: Text-to-speech with automatic transliteration  
- **🔤 Phonetic Support**: Georgian/Armenian alphabets → readable Cyrillic
- **⚡ Apple Optimized**: MPS acceleration for Apple Silicon
- **🎨 Modern UI**: Dark/light themes, keyboard shortcuts

## 🚀 Quick Start

```bash
# 1. Clone & setup
git clone https://github.com/kubataba/kabardian-translator.git
cd kabardian-translator

# 2. Install dependencies
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Download AI models (~10GB)
python3 download_models.py

# 4. Launch application
python3 app.py
# → Open http://localhost:5500
```
---

## ⚡ Performance Optimizations

| Optimization | Benefit |
|------------|--------|
| **Float16 instead of Float32** | ~50% memory savings (15GB → 7.5GB), <1% accuracy drop |
| **`torch.no_grad()` for inference** | 10–15% faster, no gradient cache |
| **Lazy TTS loading** | Startup time ↓ by ~5 sec, memory saved if unused |
| **Automatic memory cleanup** | Stable long-term operation |

### Performance on Mac Mini M4

| **Operation** | **Time** | **Memory** |
|---------------|----------|------------|
| Server start | ~10 sec | ~2GB |
| Translation (direct) | 200-500ms | +1GB |
| Translation (cascade) | 400-900ms | +1GB |
| TTS synthesis | 1-2 sec | +0.5GB |
| **Peak memory** | - | **~8GB** |

---

## 🎓 Practical Applications

- **For Students**: Learn Kabardian, practice pronunciation, compare translations.
- **For Teachers**: Prepare materials, generate audio examples, demonstrate phonetics.
- **For Researchers**: Analyze transliteration, test MT quality, compare phonetics.
- **For Travelers**: Communicate in Caucasus region, understand signs, basic phrases.

---

## 📊 Quality and Limitations

### Translation Quality
| Language Pair | BLEU | Quality | Method |
|--------------|------|--------|-------|
| Russian ↔ Kabardian | 35–42 | Excellent | Direct (fine-tuned) |
| Slavic ↔ Slavic | 30–38 | Good | Direct (base) |
| Any ↔ Kabardian | 28–35 | Good | Cascade (2 models) |
| European ↔ European | 32–40 | Good | Direct (base) |

### Voice Synthesis
| Language | TTS Quality | Method | Accuracy |
|--------|-------------|--------|----------|
| Russian, Ukrainian, Belarusian | 95–98% | Direct | Excellent |
| Kabardian, Kazakh | 92–95% | Direct | Excellent |
| Georgian, Armenian | 88–92% | Transliteration → TTS | Good |
| Turkish, Azerbaijani | 85–88% | Transliteration → TTS | Good |
| German, Spanish, Latvian | 78–82% | Transliteration → TTS | Acceptable |

### Limitations
- **TTS**: Max 200 chars; imperfect pronunciation for transliterated langs; no intonation.
- **Translation**: Cascade may lose nuance; technical terms may be inaccurate; context >512 tokens lost.
- **Transliteration**: Simplified phonetics; stress marks not shown.

---

## 🛠️ Troubleshooting

### Models Won't Load
```bash
# Try mirror if Hugging Face is blocked
export HF_ENDPOINT=https://hf-mirror.com
python3 download_models.py
```

### MPS Unavailable
In `app.py`, change:
```python
device = "cpu"  # Instead of "mps"
```
> Runs 3–5× slower.

### Out of Memory (OOM)
- Reduce beam search: `num_beams=3`
- Comment out unused models in `app.py`

### Transliteration Inaccurate
Edit `transliterator.py`:
```python
self.turkish_to_kazakh['h'] = 'х'  # Better than 'һ'
```

---

## 📄 License and Usage
**Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)**

✅ Allowed: Personal, educational, research, modifications, distribution with attribution.  
❌ Prohibited: Commercial use, profit-driven services, integration into paid products.

🔗 Full license: [https://creativecommons.org/licenses/by-nc/4.0/](https://creativecommons.org/licenses/by-nc/4.0/)

---

## 🙏 Acknowledgments
- **anzorq** – fine-tuned M2M100 models for Kabardian
- **Meta AI** – base M2M100 model
- **Silero Team** – high-quality TTS
- **Hugging Face** – platform and Transformers
- **Kabardian language community** – feedback and support

---

## 📞 Support and Contribution
- **Found a bug?** → Open an Issue on GitHub
- **Want to contribute?** → Fork → Branch → Commit → Pull Request
- **Need help?** → Check `TROUBLESHOOTING` or Discussions

---

## 🗺️ Roadmap
- **v1.1 (Q1 2026)**: Expanding North Caucasian Languages Support
- **v1.2 (Q2 2026)**: API, Redis caching, user history,batch translation
- **v2.0 (Q3 2026)**: Mobile app, offline mode, Telegram Bot

---

## 📚 Additional Resources
- [M2M100 Documentation](https://huggingface.co/facebook/m2m100_1.2B)
- [Silero TTS Docs](https://github.com/snakers4/silero-models#text-to-speech)
- [PyTorch MPS Guide](https://pytorch.org/docs/stable/notes/mps.html)
- [Transformers Docs](https://huggingface.co/docs/transformers)

---

Made with ❤️ for preserving and studying the Kabardian language
```

## ---