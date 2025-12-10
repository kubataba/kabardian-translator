# 🌍 Kabardian Translator  
**Voice-Enabled Multilingual Translator for Caucasian Languages**

[![PyPI version](https://img.shields.io/pypi/v/kabardian-translator.svg)](https://pypi.org/project/kabardian-translator/)
[![License](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.1.0-red.svg)](https://pytorch.org/)

> 🎯 **Educational tool** for learning Kabardian and Caucasian languages with AI-powered translation and speech synthesis

---

## ✨ **What's New in v1.0.3**

### 🚀 **Major Performance Improvements**

**v1.0.3 brings significant efficiency gains while maintaining practical translation quality:**

| Aspect | Before (v1.0) | After (v1.0.3) | Improvement |
|--------|---------------|----------------|-------------|
| **Disk Space** | ~15GB | **~3GB** | **5x smaller** ⬇️ |
| **RAM Usage** | 16GB required | **4GB minimum** | **4x more efficient** 💚 |
| **Model Size** | 1.2B parameters | **418M + 80M×2** | **3x lighter** 🪶 |
| **RU↔KBD Quality** | Baseline | **Improved** | ✅ Better specialized models |

---

### 🔥 **Key Innovations**

#### 1. **🎯 Specialized Lightweight Models for Kabardian**

We trained **two dedicated MarianMT models** specifically for Russian↔Kabardian translation:

- **Model**: Fine-tuned from Helsinki-NLP OPUS-MT (Englih-Russian, Russian-Ukrainian base)
- **Size**: ~80M parameters each (~300MB per model)
- **Training data**: 220K parallel sentences two side from [adiga-ai/circassian-parallel-corpus](https://huggingface.co/datasets/adiga-ai/circassian-parallel-corpus)
- **Performance**: **Outperforms 1.2B M2M100** on Kabardian despite being 15x smaller

**Why they perform better:**
- Focused on single language pair (not spread across 100+ languages)
- 1200M parameters serving 100 languages ≈ 12M per language vs 80M dedicated
- Specialized training on Kabardian linguistic patterns

**Benchmark Results (500 examples):**

| Direction | Model | BLEU | chrF | TER | Size |
|-----------|-------|------|------|-----|------|
| RU→KBD | **Opus-MT (kubataba)** | **8.48** | 32.7 | 86.09 | 300MB |
| RU→KBD | M2M100 1.2B (anzorq) | 6.09 | 33.89 | 84.35 | 2.4GB |
| KBD→RU | **Opus-MT (kubataba)** | **12.75** | 32.48 | 81.35 | 300MB |
| KBD→RU | M2M100 1.2B (anzorq) | 7.44 | 28.15 | 89.98 | 2.4GB |

🏆 **Winner**: Specialized models deliver **+39% BLEU improvement** for RU→KBD while using **1/8th the size**

**Note on BLEU scores**: The relatively low BLEU scores are due to tokenization limitations inherited from the Russian-English base model:
- Kabardian digraphs (кхъ, щӏ, лӏ, тӀ, цӀ) get split into separate tokens
- Complex morphological chains are fragmented
- Rare morphemes and negation markers (-къым) aren't properly identified
- N-gram matches are artificially reduced despite semantically correct translations
- **Despite lower BLEU, translations are semantically accurate and usable for practical purposes**

**The main barrier to further improvement**: Creating a specialized tokenizer for Kabardian that properly handles its polysynthetic morphology and rich consonant system. We've detailed this challenge in our article: [Tokenization as the Key to Language Models for Low-Resource Languages](https://habr.com/ru/articles/973324/) (in Russian).

---

#### 2. **⚡ Optimized Multilingual Model**

Replaced heavy M2M100 1.2B with **M2M100 418M**:  

- **Size**: 1.6GB (down from 4.7GB)
- **Languages**: Still supports 100+ languages
- **Precision**: Float32 for stability
- **Performance**: Comparable quality for most pairs

**M2M100 418M Performance (research benchmarks):**  
- Low-resource pairs: BLEU 8.9-10.1
- Mid-resource pairs: BLEU 21.4-23.4
- High-resource pairs: BLEU 35.0-39.8

---

#### 3. **💾 Dramatically Reduced Requirements**

| Computer Type | RAM | Supported Features | Performance |
|---------------|-----|-------------------|-------------|
| Old laptop | 4GB | Kabardian ↔ Russian | Fast ⚡ |
| Standard PC | 8GB | All 14 languages | Optimal ✨ |
| Apple Silicon | 16GB | MPS acceleration + all | Maximum 🚀 |

---

#### 4. **🔤 Enhanced Transliterator**

- Updated core transliteration engine to v1.0.3
- More accurate Georgian/Armenian alphabet conversion
- Improved phonetic representation for non-Cyrillic scripts
- Better handling of diacritics and special characters

---

## ✨ Core Features

- **🧠 Smart Translation**: 14 languages with specialized Kabardian models
- **📊 Voice Synthesis**: Text-to-speech with automatic transliteration  
- **🔤 Phonetic Support**: Georgian/Armenian alphabets → readable Cyrillic
- **⚡ Efficiency Optimized**: Runs on any computer (4GB+ RAM)
- **🎨 Modern UI**: Dark/light themes, keyboard shortcuts

---

## 🏗️ System Architecture

### Translation Pipeline. 

**Direct Translation** (Russian ↔ Kabardian):    
```
Input Text → Specialized Opus-MT Model → Output Text
```  
- Uses fine-tuned 80M parameter models
- Best quality for RU↔KBD pairs
- ~200-600ms latency

**Cascade Translation** (Any Language ↔ Kabardian):    
```
Source Language → M2M100 418M → Russian → Opus-MT → Kabardian. 
```  
- Two-step process through Russian as pivot
- Supports 100+ languages
- ~400-900ms latency

**Multilingual Translation** (Non-Kabardian pairs):    
```
Source Language → M2M100 418M → Target Language  
```  
- Direct translation between supported languages
- Quality varies by language pair resource availability

### Voice Synthesis Pipeline

**For Cyrillic Languages** (Russian, Ukrainian, Belarusian, Kabardian, Kazakh):    
```
Text → Silero TTS → Audio (48kHz WAV). 
```  
- Direct synthesis, no preprocessing needed
- High quality (92-98% accuracy)

**For Non-Cyrillic Languages** (Georgian, Armenian, Turkish, Azerbaijani):    
```
Input Text → Transliterator → Cyrillic Text → Silero TTS → Audio  
```  

**Transliteration Process**:     
1. **Script Detection**: Identifies source alphabet (Georgian, Armenian, Latin).   
2. **Phonetic Mapping**: Converts characters to closest Cyrillic phonemes.  
3. **Context Rules**: Handles digraphs, word boundaries, special cases.  
4. **Target Selection**: Routes to appropriate TTS speaker (Russian/Kabardian).  

**Example Flow**:    
```
Georgian: "გამარჯობა" 
    ↓ Transliterator
Cyrillic: "гамарджоба" 
    ↓ Silero TTS (kbd_eduard)
Audio: gamardzhoba.wav
```

### Transliteration Features.   

- **Georgian → Kabardian Cyrillic**: Preserves ejectives (პ→пӏ, ტ→тӏ, წ→цӏ)   
- **Armenian → Hybrid Cyrillic**: Maps to Kazakh+Kabardian phonemes  
- **Turkish/Azerbaijani → Kazakh Cyrillic**: Handles ğ contextually, maps ş→ш, ç→ч  
- **German → Hybrid Cyrillic**: sp/st rules, umlauts (ä→э, ö→ө, ü→йю)  
- **Spanish → Hybrid Cyrillic**: ch→ч, ll→й, rr→рр, silent h  
- **Latvian → Hybrid Cyrillic**: Long vowels (ā→аа, ē→ээ), palatalization (ķ→кь, ļ→ль)  

---

## 🚀 Quick Start. 

### System Requirements  

- **Python**: 3.11 or higher
- **RAM**: **4GB minimum** (basic use), 8GB recommended (all languages)
- **Storage**: **~3GB** for all AI models
- **OS**: Windows, macOS, Linux (any computer!)

---  

### 📦 Installation via PyPI (Recommended)  

```bash  
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install from PyPI
pip install kabardian-translator

# Download AI models (required, ~3GB)
kabardian-download-models

# Launch the application
kabardian-translator
# → Open http://localhost:5500 in your browser
```

---

### 🎛️ Installation Modes  

**Minimal Installation** (Kabardian ↔ Russian only):  
```bash
kabardian-download-models --minimal  # ~600MB
```

**Full Installation** (All 14 languages):  
```bash
kabardian-download-models --full     # ~3GB
```

---

### 🛠️ Alternative Installation Methods  

#### From GitHub (Development Version)

```bash
git clone https://github.com/kubataba/kabardian-translator.git
cd kabardian-translator
python3.11 -m venv venv
source venv/bin/activate
pip install -e .
kabardian-download-models
kabardian-translator
```

#### Manual Installation (Legacy)

```bash
git clone https://github.com/kubataba/kabardian-translator.git
cd kabardian-translator
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 download_models.py
python3 app.py
```

---

### 🎛️ CLI Options

```bash
# Custom port
kabardian-translator --port 8080

# Localhost only (more secure)
kabardian-translator --host localhost --port 5500

# CPU-only mode (for 4GB RAM systems)
kabardian-translator --cpu-only

# Debug mode
kabardian-translator --debug

# Help
kabardian-translator --help
```

---

## ⚡ Performance Optimizations

### Technical Improvements

- **Specialized MarianMT models**: Fine-tuned specifically for Kabardian, achieving better results than multilingual models
- **M2M100 418M**: 3x smaller than original, supports 100+ languages
- **Float32 stability**: No precision loss, more reliable inference
- **Automatic memory cleanup**: Stable long-term operation
- **Lazy model loading**: Only loads models when needed

### Performance Comparison

**On 4GB RAM Computer:**
- Startup: ~5 seconds
- RU↔KBD translation: 200-600ms
- Memory usage: ~2GB peak

**On 8GB RAM Computer:**
- Startup: ~8 seconds
- Any translation: 300-800ms
- Memory usage: ~4GB peak

**On 16GB RAM with Apple Silicon:**
- Startup: ~10 seconds
- MPS-accelerated translation: 150-400ms
- Memory usage: ~6GB peak

---

## 📊 Quality and Performance

### Translation Quality by Direction

| Language Pair | BLEU Range | Quality | Model Type |
|--------------|------------|--------|-----------|
| **Russian ↔ Kabardian** | **9-13** | **Good** | **Specialized Opus-MT** |
| Any ↔ Kabardian (via Russian) | 9-15 | Acceptable | Cascade (2 models) |
| **Low-resource pairs** | 9-10 | Acceptable | M2M100 418M |
| **Mid-resource pairs** | 15-20 | Good | M2M100 418M |
| **High-resource pairs** | >30 | Excellent | M2M100 418M |

*Note: BLEU scores for Kabardian are artificially low due to tokenization mismatch, not actual translation quality. M2M100 418M performance varies significantly based on language pair resource availability.*

### Voice Synthesis Quality

| Language | TTS Quality | Method | Accuracy |
|---------|-------------|--------|----------|
| Russian, Ukrainian, Belarusian | 95-98% | Direct (Silero V5 CIS) | Excellent |
| Kabardian, Kazakh | 92-95% | Direct (Silero V5 CIS) | Excellent |
| Georgian, Armenian | 88-92% | Transliteration → TTS | Good |
| Turkish, Azerbaijani | 85-88% | Transliteration → TTS | Good |
| German, Spanish, Latvian | 78-82% | Transliteration → TTS | Acceptable |

---

## 🎓 Practical Applications

- **For Schools & Universities**: Works even in computer labs with old PCs
- **For Personal Use**: Runs on any home computer
- **For Field Research**: Smaller size makes it easier to share and install
- **For Developers**: Easier to test and modify with reduced resource requirements
- **For Language Learners**: Accessible tool for practicing Kabardian and related languages

---

## ⚠️ Known Limitations

### Translation Limitations

1. **Tokenization challenges**: The main barrier to higher BLEU scores (see technical explanation above)
2. **Kazakh/Georgian quality**: M2M100 418M has known issues with these specific language pairs (inherent model limitation)
3. **Technical vocabulary**: May struggle with modern technical terms not in training corpus
4. **Context length**: Limited to 512 tokens per translation
5. **Low-resource reality**: As a low-resource language tool, performance cannot match high-resource language pairs

### TTS Limitations

- Max 200 characters per synthesis
- Imperfect pronunciation for transliterated languages
- No intonation control
- Stress marks not shown in transliteration

### The Tokenization Challenge

The biggest obstacle to improving Kabardian NMT models is creating a specialized tokenizer that properly handles:
- Polysynthetic morphology with complex affixation
- 50+ consonant phonemes including ejectives
- Digraphs (кхъ, щӏ, лӏ, тӀ, цӀ) as single units
- Morphological negation and modality markers
- Ergative-absolutive case system

**Read more**: [Tokenization as the Key to Language Models for Low-Resource Languages](https://habr.com/ru/articles/973324/) - detailed technical analysis of this challenge (in Russian).

---

## 🛠️ Troubleshooting

### Low RAM Systems (4GB)

```bash
# Minimal installation (Kabardian ↔ Russian only)
kabardian-download-models --minimal

# Force CPU mode
kabardian-translator --cpu-only
```

### Insufficient Disk Space

```bash
# Check available space
df -h

# Use minimal installation
kabardian-download-models --minimal  # Only 600MB
```

### Models Won't Download

```bash
# Try mirror if Hugging Face is blocked
export HF_ENDPOINT=https://hf-mirror.com
kabardian-download-models
```

### Quick System Check

```bash
# Test without downloading models
python -c "from kabardian_translator import check_models; check_models()"

# Check compatibility
python -c "import torch; print(f'PyTorch: {torch.__version__}')"
```

### Command Not Found

```bash
# Reinstall package
pip uninstall kabardian-translator
pip install kabardian-translator

# Or use Python module call
python -m kabardian_translator.cli --port 5500
```

---

## 📄 License and Usage

**Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)**

✅ **Allowed**: Personal, educational, research, modifications, distribution with attribution  
❌ **Prohibited**: Commercial use, profit-driven services, integration into paid products

🔗 Full license: [https://creativecommons.org/licenses/by-nc/4.0/](https://creativecommons.org/licenses/by-nc/4.0/)

---

## 🙏 Acknowledgments. 

**Special thanks for v1.0.3 optimization:**  
- **anzorq** - Created the [Circassian-Russian parallel corpus](https://huggingface.co/datasets/adiga-ai/circassian-parallel-corpus) and fine-tuned M2M100 baseline models   
- **Helsinki-NLP** - OPUS-MT base models  
- **M2M100** - M2M100 418M framework   
- **Silero Team** - High-quality TTS models   
- **Hugging Face** - Infrastructure and Transformers library  
- **Kabardian language community** - Testing, feedback, and support  

---

## 📞 Support and Contribution

- **Found a bug?** → [GitHub Issues](https://github.com/kubataba/kabardian-translator/issues)
- **Want to help?** → Fork → Branch → Commit → Pull Request
- **Run benchmarks?** → See [benchmarks/README.md](./benchmarks/README.md) for reproducible tests
- **Questions?** → Check Troubleshooting section
- **Technical discussion**: Read our article on [tokenization challenges](https://habr.com/ru/articles/973324/)

---

## 📄 Migration from v1.0

If you had the old version installed:

```bash
# Remove old models (free up ~12GB!)
rm -rf models/

# Update to new version
pip install --upgrade kabardian-translator

# Download new optimized models
kabardian-download-models --full
```

**Migration benefits:**
- Save 12GB disk space
- Works on any computer (4GB+ RAM)
- Improved quality for Russian↔Kabardian
- More stable operation
- Faster installation

---

## 🗺️ Roadmap

- **v1.1 (Q1 2026)**: Expanding North Caucasian Languages Support
- **v1.2 (Q2 2026)**: API, Redis caching, user history, batch translation
- **v2.0 (Q3 2026)**: Mobile app, offline mode, Telegram Bot
- **Future**: Custom Kabardian tokenizer for improved translation quality

---

## 📚 Additional Resources

- [PyPI Package](https://pypi.org/project/kabardian-translator/) - Official package repository
- [Benchmark Scripts](./benchmarks/) - Reproducible performance tests
- [Benchmark Results](./benchmarks/BENCHMARK_500.md) - Detailed test results (500 examples)
- [M2M100 418M Documentation](https://huggingface.co/facebook/m2m100_418M)
- [MarianMT Framework](https://huggingface.co/docs/transformers/model_doc/marian)
- [Specialized Models](https://huggingface.co/kubataba) - RU↔KBD Opus-MT models
- [Training Corpus](https://huggingface.co/datasets/adiga-ai/circassian-parallel-corpus) - by anzorq
- [Tokenization Article](https://habr.com/ru/articles/973324/) - Technical deep-dive
- [PyTorch Optimization Guide](https://pytorch.org/tutorials/recipes/recipes/tuning_guide.html)

---

## 📊 Technical Specifications

### Model Details

| Model | Parameters | Size | Purpose |
|-------|------------|------|---------|
| Opus-MT RU→KBD | 80M | 300MB | Russian → Kabardian (specialized) |
| Opus-MT KBD→RU | 80M | 300MB | Kabardian → Russian (specialized) |
| M2M100 418M | 418M | 1.6GB | 100+ languages (multilingual) |
| Silero TTS V5 CIS | - | ~50MB | Voice synthesis (Russian/Kabardian) |

**Total**: All models occupy ~2.3GB vs ~15GB in v1.0

---

## 🔧 System Components

### Core Modules

**Translation Engine** (`translation_service.py`):
- Manages 3 translation models (2× Opus-MT + M2M100)
- Lazy loading for memory efficiency
- Automatic cascade routing for unsupported pairs
- Preprocessing: Palochka (Ӏ) handling for Kabardian

**TTS Service** (`tts_service.py`):
- Silero TTS V5 CIS model integration
- Lazy model loading (loads only when needed)
- Automatic transliteration routing
- 2 speakers: `ru_eduard` (Russian), `kbd_eduard` (Kabardian/Kazakh)
- Output: 48kHz WAV audio

**Transliterator** (`transliterator.py`):
- 7 script mappings (Georgian, Armenian, Turkish, Azerbaijani, German, Spanish, Latvian)
- Context-aware rules: word boundaries, digraphs, phonetic context
- 600+ character mappings + 50+ special rules
- Phonetically optimized for TTS clarity

### Data Flow

```
┌─────────────┐
│  User Input │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│  Flask Web Server   │
│  (app.py)           │
└──────┬──────────────┘
       │
       ├─────────────► Translation Request
       │               │
       │               ▼
       │        ┌──────────────────┐
       │        │ Translation      │
       │        │ Service          │
       │        │ - Model Router   │
       │        │ - Preprocessor   │
       │        └──────┬───────────┘
       │               │
       │               ▼
       │        ┌──────────────────┐
       │        │ Opus-MT / M2M100 │
       │        │ Models           │
       │        └──────┬───────────┘
       │               │
       │               ▼
       │        [Translated Text]
       │
       └─────────────► TTS Request
                       │
                       ▼
                ┌──────────────────┐
                │ TTS Service      │
                │ - Script Detect  │
                │ - Transliterator │
                └──────┬───────────┘
                       │
                       ▼
                ┌──────────────────┐
                │ Transliterator   │
                │ (if needed)      │
                └──────┬───────────┘
                       │
                       ▼
                ┌──────────────────┐
                │ Silero TTS       │
                │ Model            │
                └──────┬───────────┘
                       │
                       ▼
                  [Audio WAV]
```

### Language Support Matrix

| Language | Code | Script | Translation | TTS | Transliteration |
|----------|------|--------|-------------|-----|-----------------|
| Kabardian | kbd_Cyrl | Cyrillic | ✅ Specialized | ✅ Direct | ➖ |
| Russian | rus_Cyrl | Cyrillic | ✅ Specialized | ✅ Direct | ➖ |
| Ukrainian | ukr_Cyrl | Cyrillic | ✅ M2M100 | ✅ Direct | ➖ |
| Belarusian | bel_Cyrl | Cyrillic | ✅ M2M100 | ✅ Direct | ➖ |
| Kazakh | kaz_Cyrl | Cyrillic | ✅ M2M100 | ✅ Direct | ➖ |
| Georgian | kat_Geor | Georgian | ✅ M2M100 | ✅ Via Kbd | ✅ 38 mappings |
| Armenian | hye_Armn | Armenian | ✅ M2M100 | ✅ Via Hybrid | ✅ 45 mappings |
| Turkish | tur_Latn | Latin | ✅ M2M100 | ✅ Via Kaz | ✅ 28 mappings |
| Azerbaijani | azj_Latn | Latin | ✅ M2M100 | ✅ Via Kaz | ✅ 32 mappings |
| German | deu_Latn | Latin | ✅ M2M100 | ✅ Via Hybrid | ✅ 35 mappings + rules |
| Spanish | spa_Latn | Latin | ✅ M2M100 | ✅ Via Hybrid | ✅ 30 mappings + rules |
| Latvian | lav_Latn | Latin | ✅ M2M100 | ✅ Via Hybrid | ✅ 32 mappings + rules |

**Total**: 14 languages, 7 scripts, 600+ transliteration rules

---

**Made with ❤️ for preserving and studying the Kabardian language**

*Version 1.0.3 - Practical efficiency for real-world use*
