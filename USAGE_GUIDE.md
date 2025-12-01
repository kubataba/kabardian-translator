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

**5. Download AI models (~15GB):**  

```bash
kabardian-download-models
```

**6. Launch the application:**  

```bash
kabardian-translator
```

**7. Open in browser:** http://localhost:5500

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


## 🛠️ Alternative: Development Setup

**From GitHub source:**

```bash
# Clone repository
git clone https://github.com/kubataba/kabardian-translator.git
cd kabardian-translator

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Download models
kabardian-download-models

# Run application
kabardian-translator
```

## 🔧 Key Features

### Translation Modes
- **Direct**: Russian ↔ Kabardian (specialized models)
- **Cascade**: Other languages via Russian
- **Base**: Direct for supported pairs

### Voice Synthesis
- Click speaker icons for TTS
- Automatic transliteration for 7 languages
- Preview shows transliterated text

### Interface Tips
- `Ctrl+Enter` - translate
- `Ctrl+↑` - swap languages  
- `Ctrl+Space` - speak text
- Theme toggle in top-right
- Language switcher (RU/EN) in header

## 🌐 Supported Languages

### With Direct Voice Synthesis
- **Russian, Ukrainian, Belarusian** - `ru_eduard` speaker
- **Kabardian, Kazakh** - `kbd_eduard` speaker

### With Transliteration + Voice
- **Turkish, Azerbaijani** → Kabardian speaker
- **Georgian, Armenian** → Kabardian speaker  
- **German, Spanish, Latvian** → Russian speaker

### Translation Only
- **English, French**

## 🔄 Translation Workflow

### Direct Translation (Fast)
- Russian → Kabardian
- Kabardian → Russian
- Between Slavic languages
- Between European languages

### Cascade Translation (High Quality)
- Any language → Kabardian (via Russian)
- Kabardian → Any language (via Russian)

## 🔊 Voice Synthesis Features

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

## ⚡ Performance Tips

### Apple Silicon Optimization
- Uses Metal Performance Shaders (MPS)
- Float16 precision for memory efficiency
- Lazy loading of TTS model

### Expected Performance (M4 Mac)
- **Startup**: ~10 seconds
- **Translation**: 200-900ms
- **TTS Synthesis**: 1-2 seconds
- **Peak Memory**: ~8GB

### Memory Management
- Automatic cleanup on exit
- Temporary audio file deletion
- Cache clearing between operations

## 🛠️ Troubleshooting  

### Common Issues

**Models won't download:**    

```bash
# Use mirror if needed
export HF_ENDPOINT=https://hf-mirror.com
kabardian-download-models
```

**Out of memory (Apple Silicon):**  

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
 
- Check internet connection (first load)
- Verify console for error messages
- Check audio output device

### Keyboard Shortcuts Reference  

| Shortcut | Action |
|----------|--------|
| `Ctrl+Enter` | Translate text |
| `Ctrl+↑` | Swap languages |
| `Ctrl+Space` | Speak selected text |
| `Ctrl+C` | Copy translation |

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
├── setup.py             # Package configuration
├── requirements.txt     # Dependencies
├── download_models.py   # Model downloader
└── models/             # AI models (created after download)
```

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
- Analyze translation quality
- Study phonetic representations
- Test transliteration accuracy

## 🔒 License & Usage

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

**Need help?**  

Open an issue on [GitHub](https://github.com/kubataba/kabardian-translator/issues) or check the [PyPI page](https://pypi.org/project/kabardian-translator/)!
```
