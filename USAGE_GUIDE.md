# Quick Start Guide

## 🎯 First Launch (Recommended)

**1. Check Python version (requires 3.11+):**  

```bash
python --version
# or
python3 --version
```

**2. Create virtual environment with Python 3.11:**  

```bash
python3.11 -m venv venv
```

**3. Activate virtual environment:**  

```bash
# Linux/Mac:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

**4. Install from PyPI:**  

```bash
pip install kabardian-translator
```

**5. Download AI models (~3GB):**  

```bash
kabardian-download-models
```

**6. Launch the application:**  

```bash
kabardian-translator
```

**7. Open in browser:** http://localhost:5500

---

## 🛠️ Alternative: Development Setup

**From GitHub source:**

```bash
# Clone repository
git clone https://github.com/kubataba/kabardian-translator.git
cd kabardian-translator

# Check Python version
python3.11 --version

# Create virtual environment
python3.11 -m venv venv

# Activate
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Download models
kabardian-download-models

# Run application
kabardian-translator
```

---

## 📦 Installation Modes (v1.0.3)

**Minimal Installation** (Kabardian ↔ Russian only):  

```bash
kabardian-download-models --minimal  # ~600MB
```  

**Full Installation** (All 14 languages):  

```bash
kabardian-download-models --full     # ~3GB
```  

---

## 🔧 Key Features

### Translation Modes
- **Direct**: Russian ↔ Kabardian (specialized 80M parameter models)
- **Cascade**: Other languages via Russian
- **Base**: Direct for supported pairs using M2M100 418M

### Voice Synthesis
- Click speaker icons for TTS
- Automatic transliteration for 7 languages
- Preview shows transliterated text
- Uses Silero TTS V5 CIS model

### Interface Tips
- `Ctrl+Enter` - translate
- `Ctrl+→` - swap languages  
- `Ctrl+Space` - speak text
- Theme toggle in top-right
- Language switcher (RU/EN) in header

---

## 🌍 Supported Languages

### With Direct Voice Synthesis
- **Russian, Ukrainian, Belarusian** - `ru_eduard` speaker
- **Kabardian, Kazakh** - `kbd_eduard` speaker

### With Transliteration + Voice
- **Turkish, Azerbaijani** → Kabardian speaker
- **Georgian, Armenian** → Kabardian speaker  
- **German, Spanish, Latvian** → Russian speaker

### Translation Only
- **English, French**

---

## 🔄 Translation Workflow

### Direct Translation (Fast)
- Russian ↔ Kabardian (Specialized Opus-MT 80M models)
- Between Slavic languages (M2M100 418M)
- Between European languages (M2M100 418M)

### Cascade Translation (High Quality)
- Any language → Kabardian (via Russian)
- Kabardian → Any language (via Russian)

---

## 📊 Voice Synthesis Features

### Automatic Transliteration
- **Georgian/Armenian alphabets** → Cyrillic for readability
- **Turkish/Azerbaijani** → Kazakh Cyrillic for pronunciation
- **German/Spanish/Latvian** → Hybrid Cyrillic

### Quality Levels
- **95-98%**: Russian, Ukrainian, Belarusian
- **92-95%**: Kabardian, Kazakh  
- **88-92%**: Georgian, Armenian (transliterated)
- **85-88%**: Turkish, Azerbaijani (transliterated)
- **78-82%**: German, Spanish, Latvian (transliterated)

---

## ⚡ Performance Tips

### System Requirements (v1.0.3)
- **Minimum**: 4GB RAM (basic Kabardian ↔ Russian)
- **Recommended**: 8GB RAM (all 14 languages)
- **Optimal**: 16GB RAM (Apple Silicon with MPS acceleration)
- **Storage**: ~3GB (down from ~15GB in v1.0)

### Apple Silicon Optimization
- Uses Metal Performance Shaders (MPS) when available
- Float32 precision for stability
- Lazy loading of TTS model

### Expected Performance

**On 4GB RAM Computer:**
- Startup: ~5 seconds
- RU↔KBD translation: 200-600ms
- Memory usage: ~2GB peak

**On 8GB RAM Computer:**
- Startup: ~8 seconds
- Any translation: 300-800ms
- Memory usage: ~4GB peak

**On Apple Silicon (16GB RAM):**
- Startup: ~10 seconds
- MPS-accelerated translation: 150-400ms
- TTS Synthesis: 1-2 seconds
- Memory usage: ~6GB peak

### Memory Management
- Automatic cleanup on exit
- Temporary audio file deletion
- Cache clearing between operations

---

## 🛠️ Troubleshooting  

### Common Issues

**Models won't download:**    

```bash
# Use mirror if Hugging Face is blocked
export HF_ENDPOINT=https://hf-mirror.com
kabardian-download-models
```

**Low RAM (4GB systems):**

```bash
# Minimal installation
kabardian-download-models --minimal

# Force CPU mode
kabardian-translator --cpu-only
```

**Out of memory (Apple Silicon with 8GB RAM):**  

```bash
# Force CPU mode
export PYTORCH_ENABLE_MPS_FALLBACK=1
kabardian-translator
```

**Command not found after pip install:**  

```bash
# Reinstall
pip uninstall kabardian-translator
pip install kabardian-translator

# Or run directly
python -m kabardian_translator.cli
```

**TTS not working:** 
 
- Check internet connection (first load downloads model)
- Verify console for error messages
- Check audio output device

---

## ⌨️ Keyboard Shortcuts Reference  

| Shortcut | Action |
|----------|--------|
| `Ctrl+Enter` | Translate text |
| `Ctrl+→` | Swap languages |
| `Ctrl+Space` | Speak selected text |
| `Ctrl+C` | Copy translation |

---

## 📁 Project Structure

```
kabardian-translator/
├── kabardian_translator/  # Python package
│   ├── __init__.py
│   ├── app.py            # Main application
│   ├── translation_service.py
│   ├── tts_service.py
│   ├── transliterator.py
│   ├── tokenizer_manager.py
│   └── cli.py           # CLI entry point
├── benchmarks/          # Reproducible tests (v1.0.3)
│   ├── README.md
│   ├── requirements.txt
│   ├── bench.py
│   └── BENCHMARK_500.md
├── setup.py             # Package configuration
├── requirements.txt     # Dependencies
├── download_models.py   # Model downloader
└── models/             # AI models (created after download)
```

---

## 🎓 Educational Use Cases

### For Language Learners
- Practice Kabardian pronunciation
- Compare translations across languages
- Understand phonetic structure

### For Teachers
- Generate audio examples
- Prepare multilingual materials
- Demonstrate transliteration

### For Researchers
- Analyze translation quality (see benchmarks/)
- Study phonetic representations
- Test transliteration accuracy
- Reproduce results with provided benchmark scripts

---

## 📏 License & Usage

**Non-Commercial Educational Use Only**    
- ✅ Personal use  
- ✅ Educational institutions    
- ✅ Research projects  
- ✅ Modifications with attribution  

**Prohibited**  
- ❌ Commercial services  
- ❌ Paid integrations  
- ❌ Profit-driven applications  

Full license: [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/)

---

## 🆕 What's New in v1.0.3

### Major Improvements
- **5x smaller**: 3GB vs 15GB total size
- **4x more efficient**: Runs on 4GB RAM minimum
- **Better quality**: Specialized 80M Opus-MT models for RU↔KBD
- **Reproducible benchmarks**: Full test suite in benchmarks/ folder

### Technical Changes
- Replaced M2M100 1.2B with M2M100 418M (3x lighter)
- Added specialized Opus-MT models for Kabardian
- Enhanced transliterator with improved phonetic rules
- Lazy TTS loading for faster startup

---

**Need help?**  

- 📖 [Full Documentation](https://github.com/kubataba/kabardian-translator#readme)
- 🐛 [Report Issues](https://github.com/kubataba/kabardian-translator/issues)
- 📊 [Run Benchmarks](https://github.com/kubataba/kabardian-translator/tree/main/benchmarks)
- 📦 [PyPI Page](https://pypi.org/project/kabardian-translator/)
