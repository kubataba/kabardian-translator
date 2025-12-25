# Usage Guide

## Quick Start

### Prerequisites

**Python 3.11 or higher** (required for Silero Stress)

Check your Python version:  

```bash
python --version
# or
python3 --version
```   

If you need Python 3.11+, download from [python.org](https://www.python.org/downloads/). 

---  

## Installation

### Standard Installation (Recommended)

**1. Create virtual environment:**

```bash
# Linux/macOS
python3.11 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate.bat
```

**2. Install package:**

```bash
pip install kabardian-translator
```

**3. Download models (~2.9GB):**

```bash
kabardian-download-models
```

**4. Launch application:**

```bash
kabardian-translator
```

**5. Open browser:**

Navigate to `http://localhost:5500`

---

### Windows-Specific Installation

**1. Verify Python installation:**

```bash
python --version
```

If Python not found, try:  

```bash
py --version
python3 --version
```

**2. Create virtual environment:**

```bash
python -m venv venv
venv\Scripts\activate.bat
```

If `pip` command not found, use:    

```bash
python -m pip install kabardian-translator
```   

**3. Download models:**

```bash
python -m kabardian_translator.download_models
# or
kabardian-download-models
```

**4. Launch:**

```bash
python -m kabardian_translator.cli
# or
kabardian-translator
```

**Common Windows issues:**  
- If port 5500 blocked: use `--port 8080`  
- If browser shows security warning: click "Advanced" → "Proceed to localhost"  
- If SSL errors: add `--trusted-host pypi.org --trusted-host files.pythonhosted.org` to pip commands  

---  

### Development Installation

**From GitHub source:**

```bash
git clone https://github.com/kubataba/kabardian-translator.git
cd kabardian-translator

# Linux/macOS
python3.11 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Download models
kabardian-download-models

# Launch
python -m kabardian_translator.cli
```

---

## Model Installation Options

**Full installation** (all features):  

```bash
kabardian-download-models --full  # ~2.9GB
```  

Components:  
- MarianMT RU↔KBD models (~600MB)  
- NLLB-200 multilingual model (~2.3GB)  
- Silero TTS model (~50MB, auto-downloaded on first use)  

**Minimal installation** (Kabardian↔Russian only):    

```bash
kabardian-download-models --minimal  # ~600MB
```  

Components:  
- MarianMT RU↔KBD models only  
- No multilingual support  

**Base NLLB-200 only**:    

```bash
kabardian-download-models --base-only  # ~2.3GB
```  

Components:  
- NLLB-200 for 200+ languages  
- No specialized Kabardian models  

---    

## Application Features  

### Translation Modes  

**Direct translation** (Russian ↔ Kabardian):  
- Uses specialized MarianMT models  
- Best quality: BLEU 28.13 (KBD→RU), 18.65 (RU→KBD)  
- Fastest performance: 37-144ms per sentence  

**Cascade translation** (Other languages ↔ Kabardian):    
- Routes through Russian as pivot language  
- Two-step process via NLLB-200 + MarianMT  
- Latency: 100-300ms per sentence  

**Multilingual translation** (between other languages):    
- Direct via NLLB-200  
- 200+ language pairs  
- Quality varies by language pair  

### Voice Synthesis  

**Cyrillic languages** (direct TTS):    
- Russian, Ukrainian, Belarusian: Silero Stress (95-98% accuracy)  
- Kabardian, Kazakh, Bashkir, Kyrgyz: SimpleAccentor (85-90% accuracy)  
- Full automatic stress marking  

**Non-Cyrillic languages** (via transliteration):    
- Georgian → Kabardian Cyrillic (preserves ejectives)  
- Armenian → Hybrid Cyrillic (Kazakh+Kabardian phonemes)  
- Turkish/Azerbaijani → Kazakh Cyrillic  
- German/Spanish/Latvian → Hybrid Cyrillic  
- Quality: 75-85% accuracy  

**TTS usage:**  
- Click speaker icon next to text  
- Maximum 200 characters per synthesis  
- Audio plays automatically  
- Transliterated preview shown for non-Cyrillic  

### Interface Controls  

**Keyboard shortcuts:**  
- `Ctrl+Enter` - Translate text  
- `Ctrl+→` - Swap source/target languages  
- `Ctrl+Space` - Synthesize speech  
- `Ctrl+C` - Copy translation  

**UI elements:**  
- Language selector dropdowns  
- Theme toggle (dark/light mode)  
- UI language switcher (Russian/English)  
- Clear buttons for text areas  
- Download audio button (after synthesis)  

---  

## Language Support  

### Translation Support  

| Language | Code | Translation Quality | Notes |
|----------|------|---------------------|-------|
| Kabardian | kbd_Cyrl | Excellent (via MarianMT) | Specialized models |
| Russian | rus_Cyrl | Excellent (via MarianMT) | Specialized models |
| Ukrainian | ukr_Cyrl | Very Good (via NLLB-200) | High-resource |
| Belarusian | bel_Cyrl | Very Good (via NLLB-200) | High-resource |
| Kazakh | kaz_Cyrl | Good (via NLLB-200) | Mid-resource |
| Bashkir | bak_Cyrl | Good (via NLLB-200) | Low-resource |
| Kyrgyz | kir_Cyrl | Good (via NLLB-200) | Low-resource |
| Georgian | kat_Geor | Good (via NLLB-200) | Mid-resource |
| Armenian | hye_Armn | Good (via NLLB-200) | Mid-resource |
| Turkish | tur_Latn | Very Good (via NLLB-200) | High-resource |
| Azerbaijani | azj_Latn | Good (via NLLB-200) | Mid-resource |
| English | eng_Latn | Excellent (via NLLB-200) | High-resource |
| German | deu_Latn | Excellent (via NLLB-200) | High-resource |
| French | fra_Latn | Excellent (via NLLB-200) | High-resource |
| Spanish | spa_Latn | Excellent (via NLLB-200) | High-resource |
| Latvian | lvs_Latn | Very Good (via NLLB-200) | Mid-resource |

**Plus 185+ additional languages via NLLB-200**  

### TTS Support  

| Language | Accent Quality | Method |
|----------|----------------|--------|
| Russian | 98% | Silero Stress |
| Ukrainian | 95% | Silero Stress |
| Belarusian | 95% | Silero Stress |
| Kabardian | 90% | SimpleAccentor |
| Kazakh | 90% | SimpleAccentor |
| Bashkir | 88% | SimpleAccentor |
| Kyrgyz | 87% | SimpleAccentor |
| Georgian | 85% | Transliteration + Accents |
| Armenian | 85% | Transliteration + Accents |
| Turkish | 80% | Transliteration + Accents |
| Azerbaijani | 80% | Transliteration + Accents |
| German | 75% | Transliteration + Accents |
| Spanish | 75% | Transliteration + Accents |
| Latvian | 75% | Transliteration + Accents |

---

## System Requirements  

### Minimum Configuration  
- **Python**: 3.11 or higher
- **RAM**: 4GB
- **Storage**: 3GB free space
- **OS**: Windows 10+, macOS 10.14+, Linux

Performance with 4GB RAM:  
- Startup: 3-5 seconds
- Translation: 50-200ms per sentence
- Memory usage: ~2GB peak
- Recommended: minimal installation

### Recommended Configuration  
- **Python**: 3.11 or higher
- **RAM**: 8GB
- **Storage**: 5GB free space
- **OS**: Windows 10+, macOS 10.14+, Linux

Performance with 8GB RAM:  
- Startup: 5-8 seconds
- Translation: 50-150ms per sentence
- TTS synthesis: 1-2 seconds
- Memory usage: ~3GB peak

### Optimal Configuration  
- **Python**: 3.11 or higher
- **RAM**: 16GB
- **Storage**: 5GB free space
- **GPU/MPS**: Optional hardware acceleration

Performance with 16GB RAM + MPS:  
- Startup: 8-10 seconds
- Translation: 20-100ms per sentence
- TTS synthesis: 0.5-1 second
- Memory usage: ~4GB peak

---

## CLI Options  

**Basic usage:**  

```bash
kabardian-translator
```  

**Custom configuration:**  

```bash
# Custom port
kabardian-translator --port 8080

# Localhost only (more secure)
kabardian-translator --host localhost --port 5500

# Force CPU mode (disable GPU/MPS)
kabardian-translator --cpu-only

# Verbose logging
kabardian-translator --verbose
```  

**Command-line translation:**  

```bash
# Translate text directly
kabardian-translate --text "Hello world" --source eng_Latn --target rus_Cyrl

# From file
kabardian-translate --file input.txt --source eng_Latn --target kbd_Cyrl

# Help
kabardian-translate --help
```  

**Environment variables:**  

```bash
# Batch size (lower = less memory)
export KBD_TRANSLATE_BATCH_SIZE=4

# Custom model directory
export KBD_MODELS_PATH=/path/to/models

# Force CPU mode
export KBD_FORCE_CPU=1

# Launch
kabardian-translator
```  

---  

## Troubleshooting

### Installation Issues  

**Python version error:**  

```bash
# Check current version
python --version

# Install Python 3.11+ from python.org
# Then create new environment
python3.11 -m venv venv
```  

**pip not found (Windows):**  

```bash
# Use module form
python -m pip install kabardian-translator

# Or upgrade pip
python -m pip install --upgrade pip
```  

**Virtual environment issues:**  

```bash
# Remove old environment
rm -rf venv  # Linux/macOS
rmdir /s venv  # Windows

# Create fresh environment
python3.11 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate.bat
pip install kabardian-translator
```  

### Model Download Issues  

**Slow download:**  

```bash
# Use mirror (if primary site slow)
export HF_ENDPOINT=https://hf-mirror.com
kabardian-download-models
```  

**Download fails:**  

```bash
# Clear cache and retry
rm -rf ~/.cache/huggingface  # Linux/macOS
rmdir /s %USERPROFILE%\.cache\huggingface  # Windows

# Manual download
python -c "from kabardian_translator import ensure_models_downloaded; ensure_models_downloaded()"
```  

**Disk space issues:**  

```bash
# Check available space
df -h  # Linux/macOS
dir  # Windows

# Use minimal installation
kabardian-download-models --minimal
```  

### Runtime Issues  

**Out of memory:**  

```bash
# Reduce batch size
export KBD_TRANSLATE_BATCH_SIZE=1

# Force CPU mode
kabardian-translator --cpu-only

# Use minimal installation
kabardian-download-models --minimal
```  

**Port already in use:**  

```bash
# Find process using port
lsof -i :5500  # Linux/macOS
netstat -ano | findstr :5500  # Windows

# Kill process or use different port
kabardian-translator --port 8080
```  

**TTS not working:**  

```bash
# Check Silero Stress installation
pip install silero_stress

# Verify internet connection (first load downloads model)
# Check console for error messages
# Test with: python -c "from kabardian_translator.tts_service import TTSService; tts = TTSService()"
```  

**Browser shows security warning:**  
- Normal for localhost servers
- Click "Advanced" → "Proceed to localhost"
- Or type `thisisunsafe` on warning page (Chrome)
- Or use Firefox/Edge (more permissive for localhost)

### Performance Issues

**Slow startup:**  

```bash
# Normal for first launch (model loading)
# Subsequent launches faster due to caching
# Use --verbose to see loading progress
kabardian-translator --verbose
```  

**Slow translation:**  

```bash
# Check system resources
# Close other applications
# Use CPU mode if GPU/MPS unstable
kabardian-translator --cpu-only
```  

**Memory leaks:**  

```bash
# Restart application periodically
# Clear browser cache
# Check for console errors
```  

---  

## System Check  

**Verify installation:**  

```bash
# Check package
pip list | grep kabardian

# Check models
python -c "from kabardian_translator import check_models; check_models()"

# Check PyTorch
python -c "import torch; print(f'PyTorch {torch.__version__}, CUDA: {torch.cuda.is_available()}, MPS: {torch.backends.mps.is_available()}')"

# Check Silero Stress
python -c "import silero_stress; print('Silero Stress OK')"
```  

**Test translation:**  

```bash
kabardian-translate --text "Test" --source eng_Latn --target rus_Cyrl
```  

**Test TTS:**  

```bash
python -c "
from kabardian_translator.tts_service import TTSService
tts = TTSService()
tts.synthesize('Тест', 'rus_Cyrl', 'ru_eduard')
print('TTS OK')
"
```  

---  

## Use Cases  

### Language Learning  
- Practice pronunciation with TTS
- Compare translations across languages
- Study transliteration patterns
- Learn Kabardian phonetics

### Teaching  
- Generate audio examples for lessons
- Create multilingual materials
- Demonstrate phonetic representations
- Prepare comparative language exercises

### Research  
- Analyze translation quality (see benchmarks)
- Study low-resource NLP
- Test transliteration accuracy
- Compare model performance
- Document endangered languages

### Community Use  
- Accessible tool for native speakers
- Support for language preservation
- Cultural heritage documentation
- Cross-linguistic communication

---  

## Project Structure

```
kabardian-translator/
├── kabardian_translator/     # Main package
│   ├── __init__.py
│   ├── cli.py               # CLI entry point
│   ├── app.py               # Flask application
│   ├── models/              # Model management
│   ├── translation/         # Translation pipeline
│   ├── tts/                 # TTS service
│   ├── transliteration/     # Script conversion
│   └── web/                 # Web interface
├── requirements.txt         # Dependencies
├── setup.py                # Package config
└── README.md               # Documentation
```

---

## License

**Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)**

**Permitted:**  
- Personal use
- Educational purposes
- Research projects
- Modifications with attribution
- Non-commercial distribution

**Prohibited:**  
- Commercial services
- Paid integrations
- Profit-driven applications
- Selling translations or generated content

Full license: https://creativecommons.org/licenses/by-nc/4.0/

---

## Additional Resources  

- [GitHub Repository](https://github.com/kubataba/kabardian-translator)
- [PyPI Package](https://pypi.org/project/kabardian-translator/)
- [Fine-tuned Models](https://huggingface.co/kubataba) - KBD↔RU MarianMT
- [Training Corpus](https://huggingface.co/datasets/adiga-ai/circassian-parallel-corpus)
- [Issue Tracker](https://github.com/kubataba/kabardian-translator/issues)
- [Benchmarks](https://github.com/kubataba/kabardian-translator/tree/main/benchmarks)

---

## Version History  

### v2.0.0 (Current)
- Enhanced MarianMT models (BLEU 28.13/18.65)
- NLLB-200 integration (200+ languages)
- Full accentuation system
- Bashkir and Kyrgyz support
- Silero Stress integration
- ~2.9GB total size

### v1.0.0
- Initial M2M100-based implementation
- Basic TTS support
- 14 language pairs
- ~3GB total size

---  

**Need help?**  

- Read full [README](https://github.com/kubataba/kabardian-translator#readme)
- Check [troubleshooting section](#troubleshooting)
- Report [issues on GitHub](https://github.com/kubataba/kabardian-translator/issues)
- Review [benchmarks](https://github.com/kubataba/kabardian-translator/tree/main/benchmarks)
