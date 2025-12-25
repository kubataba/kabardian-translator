# 🌐 Kabardian Translator  
**Multilingual Translation and Speech Synthesis for Caucasian Languages**

[![PyPI version](https://img.shields.io/pypi/v/kabardian-translator.svg)](https://pypi.org/project/kabardian-translator/)
[![License](https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by-nc/4.0/)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.1+-red.svg)](https://pytorch.org/)

> Educational tool for Kabardian and Caucasian language learning with neural machine translation and speech synthesis.

---

## Overview

Kabardian Translator is a specialized translation system focused on low-resource Caucasian languages. The system combines fine-tuned MarianMT models for Russian↔Kabardian translation with NLLB-200 for multilingual support, providing 200+ language pairs with text-to-speech capabilities.

**Key capabilities:**  
- Specialized Russian↔Kabardian translation models  
- 200+ language support via NLLB-200  
- Text-to-speech with automatic stress marking  
- Transliteration support for multiple scripts  
- Web-based interface with bilingual UI (Russian/English)  

---   

## Version 2.0.0 Changes

### Translation Models

**Enhanced MarianMT models** for Russian↔Kabardian:  
- Custom fine-tuned from Helsinki-NLP OPUS-MT base  
- Improved BLEU scores: 28.13 (KBD→RU), 18.65 (RU→KBD)  
- Performance: 27.1 examples/sec (KBD→RU), 6.9 examples/sec (RU→KBD)  
- Models available at: 
- [kubataba/kbd-ru-opus](https://huggingface.co/kubataba/kbd-ru-opus) and - [kubataba/ru-kbd-opus](https://huggingface.co/kubataba/ru-kbd-opus)  

**NLLB-200 integration**:  
- Replaces M2M100 for broader language coverage  
- 200+ languages with improved quality for low-resource pairs  
- ~2.3GB model size (600M distilled version)  
- Better handling of morphologically complex languages  

### Speech Synthesis. 

**Accentuation system**:  
- Automatic stress marking for Cyrillic languages  
- Russian: Silero Stress (98% accuracy)  
- Ukrainian/Belarusian: Silero Stress (95% accuracy)  
- Kabardian/Kazakh/Bashkir/Kyrgyz: SimpleAccentor (85-90% accuracy)   
- Transliteration-based accents for Georgian, Armenian, Turkish, Azerbaijani    

**New language support**:  
- Bashkir (`bak_Cyrl`) with TTS  
- Kyrgyz (`kir_Cyrl`) with TTS  
- Enhanced transliteration rules for non-Cyrillic scripts  

### Resource Optimization  

- Total size: ~2.9GB (all models)  
- Memory requirements: 4GB minimum, 8GB recommended  
- Lazy loading for efficient resource usage  
- Improved sentence chunking for long texts  

---  

## System Architecture

### Translation Pipeline  

**Direct translation** (Russian ↔ Kabardian):  
```  
Input → MarianMT Model → Output
```  
- Fine-tuned 80M parameter models  
- Latency: 37-144ms per example  

**Cascade translation** (Other languages ↔ Kabardian):  
```  
Source Language → NLLB-200 → Russian → MarianMT → Kabardian
```  
- Two-step process using Russian as pivot  
- Latency: 100-300ms depending on source language  

**Multilingual translation** (between other language pairs):  
```  
Source Language → NLLB-200 → Target Language
```  
- Direct translation for 200+ language pairs  

### Speech Synthesis Pipeline  

**Cyrillic languages with stress marking**:  
```  
Text → Accentuation → Silero TTS → Audio (48kHz WAV)
```  

**Non-Cyrillic languages**:  
```  
Text → Transliteration → Cyrillic → Accentuation → Silero TTS → Audio
```  

**Supported transliterations**:  
- Georgian → Kabardian Cyrillic (preserves ejectives)  
- Armenian → Hybrid Cyrillic (Kazakh+Kabardian phonemes)  
- Turkish/Azerbaijani → Kazakh Cyrillic  
- German/Spanish/Latvian → Hybrid Cyrillic with custom rules  

---  

## Installation

### System Requirements

- **Python**: 3.11 or higher (required for Silero Stress)
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: ~2.9GB for all models
- **OS**: Windows 10/11, macOS, Linux

### Installation on Windows

**1. Install Python 3.11+**  

Download from [python.org](https://www.python.org/downloads/):  
- Download Python 3.11.9 or newer: https://www.python.org/downloads/  
- Run installer and **check "Add Python to PATH"**  
- Restart command prompt after installation  

**2. Verify installation**  

Open Command Prompt (CMD):
```bash
python --version
```  
Should show Python 3.11.x or higher

**3. Install package**

```bash
# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate.bat

# Install from PyPI
pip install kabardian-translator

# Download AI models (~2.9GB)
kabardian-download-models

# Launch application
kabardian-translator
```

Open browser and navigate to `http://localhost:5500`

**4. If `pip` command not found**  

Use `python -m pip` instead:  
  
```bash
python -m pip install kabardian-translator
```    

### Installation on macOS/Linux. 

```bash
# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install package
pip install kabardian-translator

# Download models
kabardian-download-models

# Launch
kabardian-translator
```

### Installation from GitHub

```bash
git clone https://github.com/kubataba/kabardian-translator.git
cd kabardian-translator

# Windows
python -m venv venv
venv\Scripts\activate.bat

# macOS/Linux
python3.11 -m venv venv
source venv/bin/activate

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

**Full installation** (all features, ~2.9GB):  

```bash
kabardian-download-models --full
```  

**Minimal installation** (Kabardian↔Russian only, ~600MB):  

```bash
kabardian-download-models --minimal
```  

**Base NLLB-200 only** (~2.3GB):  

```bash
kabardian-download-models --base-only
```  

---  

## CLI Usage

```bash
# Start web server
kabardian-translator

# Custom port
kabardian-translator --port 8080

# Localhost only
kabardian-translator --host localhost --port 5500

# CPU-only mode (disable GPU/MPS)
kabardian-translator --cpu-only

# Translation from command line
kabardian-translate --text "Hello" --source eng_Latn --target rus_Cyrl

# Help
kabardian-translator --help
```

---

## Language Support

### Translation Quality (BLEU scores)

| Language Pair | BLEU | Model | Performance |
|--------------|------|-------|-------------|
| Kabardian → Russian | 28.13 | MarianMT | 27.1 ex/sec |
| Russian → Kabardian | 18.65 | MarianMT | 6.9 ex/sec |
| Other low-resource | 10-15 | NLLB-200 | 5-10 ex/sec |
| Mid-resource languages | 20-25 | NLLB-200 | 5-10 ex/sec |
| High-resource languages | 30+ | NLLB-200 | 5-10 ex/sec |

### TTS Support

| Language | Script | TTS Method | Stress Accuracy |
|----------|--------|------------|-----------------|
| Russian | Cyrillic | Direct + Silero Stress | 98% |
| Ukrainian | Cyrillic | Direct + Silero Stress | 95% |
| Belarusian | Cyrillic | Direct + Silero Stress | 95% |
| Kabardian | Cyrillic | Direct + SimpleAccentor | 90% |
| Kazakh | Cyrillic | Direct + SimpleAccentor | 90% |
| Bashkir | Cyrillic | Direct + SimpleAccentor | 88% |
| Kyrgyz | Cyrillic | Direct + SimpleAccentor | 87% |
| Georgian | Georgian | Transliteration + Accents | 85% |
| Armenian | Armenian | Transliteration + Accents | 85% |
| Turkish | Latin | Transliteration + Accents | 80% |
| Azerbaijani | Latin | Transliteration + Accents | 80% |
| German | Latin | Transliteration + Accents | 75% |
| Spanish | Latin | Transliteration + Accents | 76% |
| Latvian | Latin | Transliteration + Accents | 75% |

### Supported Languages

**Cyrillic script**: Russian, Ukrainian, Belarusian, Kabardian, Kazakh, Bashkir, Kyrgyz

**Other scripts**: Georgian, Armenian, Turkish, Azerbaijani, English, German, French, Spanish, Latvian

**Additional languages**: 185+ languages via NLLB-200 (translation only, no TTS)

Full language codes: see [NLLB-200 documentation](https://huggingface.co/facebook/nllb-200-distilled-600M)

---

## Performance Benchmarks

### Hardware Requirements

**4GB RAM system**:  
- Startup: 3-5 seconds
- Translation: 50-200ms per sentence
- Memory usage: ~2GB peak
- Minimal installation recommended

**8GB RAM system**:  
- Startup: 5-8 seconds
- Translation: 50-150ms per sentence
- Memory usage: ~3GB peak
- Full installation supported

**16GB RAM with GPU/MPS**:  
- Startup: 8-10 seconds
- Translation: 20-100ms per sentence
- Memory usage: ~4GB peak
- Hardware acceleration enabled

### Translation Performance  

Based on official test set (500 examples):  

**Kabardian → Russian**:  
- BLEU: 28.13, CHRF: 50.07, TER: 63.50
- Speed: 27.1 examples/second
- Latency: 37ms per example

**Russian → Kabardian**:  
- BLEU: 18.65, CHRF: 52.66, TER: 67.57
- Speed: 6.9 examples/second
- Latency: 144ms per example

---  

## Known Limitations

### Translation

- Complex morphology: Kabardian's polysynthetic structure remains challenging
- Context length: Limited to 512 tokens per translation
- Technical vocabulary: Limited coverage for modern/specialized terms
- Dialect variations: Standard dialects only

### Speech Synthesis

- Character limit: 200 characters per synthesis request
- Stress accuracy: Not perfect for all words, especially rare forms
- Transliteration quality: Some non-Cyrillic pronunciations may sound unnatural

### The Kabardian Challenge

Kabardian presents unique difficulties:
- 50+ consonant phonemes including ejectives
- Complex polysynthetic morphology
- Rich affixation system
- Limited parallel training data

Current models show significant improvement but are not suitable for production translation services.

---

## Troubleshooting  

### Windows-Specific Issues  

**Python not found**:  

```bash
# Try alternative commands
py --version
python3 --version

# Or use full path
C:\Users\YourName\AppData\Local\Programs\Python\Python311\python.exe --version
```  

**pip not found**:  

```bash
# Use module form
python -m pip install kabardian-translator
```  

**SSL certificate errors**:  

```bash
# Windows may need certificates
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org kabardian-translator
```  

### General Issues  

**Low memory systems**:    

```bash
# Use minimal installation
kabardian-download-models --minimal

# Force CPU mode
kabardian-translator --cpu-only

# Set batch size
set KBD_TRANSLATE_BATCH_SIZE=1
kabardian-translator
```  

**Model download failures**:  

```bash
# Clear cache and retry
rmdir /s %USERPROFILE%\.cache\huggingface
kabardian-download-models

# Manual download
python -c "from kabardian_translator import ensure_models_downloaded; ensure_models_downloaded()"
```   

**Port already in use**:    

```bash
# Use different port
kabardian-translator --port 8080
```  

**Browser security warnings**:  

- This is normal for localhost servers. 
- Click "Advanced" → "Proceed to localhost". 
- Or type `thisisunsafe` on the warning page (Chrome)  

### System Check  

```bash
# Verify installation
python -c "from kabardian_translator import check_models; check_models()"

# Check PyTorch
python -c "import torch; print(f'PyTorch: {torch.__version__}')"

# Test translation
kabardian-translate --text "Hello" --source eng_Latn --target rus_Cyrl
```

---  

## Technical Documentation

### Models

| Component | Size | Parameters | Source |
|-----------|------|------------|--------|
| MarianMT KBD→RU | 300MB | 80M | [kubataba/kbd-ru-opus](https://huggingface.co/kubataba/kbd-ru-opus)|
| MarianMT RU→KBD | 300MB | 80M | [kubataba/ru-kbd-opus](https://huggingface.co/kubataba/ru-kbd-opus)|
| NLLB-200 | 2.3GB | 600M | [NLLB200-distilled-600M](https://huggingface.co/facebook/nllb-200-distilled-600M)|
| Silero TTS | 50MB | - | [snakers4/silero-models] (https://github.com/snakers4/silero-models)|

### API Endpoints

```
POST /translate
{
  "text": "string",
  "source_lang": "kbd_Cyrl",
  "target_lang": "rus_Cyrl"
}

POST /synthesize
{
  "text": "string",
  "lang_code": "rus_Cyrl",
  "speaker": "ru_eduard"
}
```

### Configuration  

Environment variables:  

```bash
KBD_TRANSLATE_BATCH_SIZE=8    # Batch size for translation
KBD_MODELS_PATH=./models       # Custom model directory
KBD_FORCE_CPU=1                # Force CPU mode
```  

---  

## Use Cases

- **Language learning**: Study Kabardian and related languages
- **Academic research**: Low-resource NLP experiments
- **Field linguistics**: Language documentation tools
- **Community use**: Accessible for native speakers
- **Comparative linguistics**: Multi-language analysis

---

## License

**Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)**

**Permitted**:
- Personal and educational use
- Research purposes
- Modifications and derivatives (with attribution)
- Non-commercial distribution

**Prohibited**:
- Commercial use
- Integration into paid products or services
- Profit-driven applications

Full license: https://creativecommons.org/licenses/by-nc/4.0/

---

## Credits

**Development**:  
- anzorq - Circassian-Russian parallel corpus and benchmarks  
- Helsinki-NLP - OPUS-MT framework  
- Silero Team - TTS models and stress marking  
- Hugging Face - Infrastructure and model hosting  

**Models**:
- NLLB-200 multilingual translation model  
- MarianMT framework for specialized models  
- Silero TTS for speech synthesis  

**Community**:
- Kabardian language speakers for testing and feedback  
- Contributors for code and documentation  

---

## Development

### Project Structure  

```
kabardian-translator/
├── kabardian_translator/  # Python package
│   ├── __init__.py
│   ├── app.py            # Main application
│   ├── translation_service.py
│   ├── tts_service.py
│   ├── transliterator.py
│   ├── download_models.py   # Model downloader
│   ├── tokenizer_manager.py
│   └── cli.py           # CLI entry point
├── setup.py             # Package configuration
├── requirements.txt     # Dependencies
└── models/             # AI models (created after download)
```  

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit pull request with description

Issues and suggestions: [GitHub Issues](https://github.com/kubataba/kabardian-translator/issues)

---

## Resources

- [PyPI Package](https://pypi.org/project/kabardian-translator/)
- [GitHub Repository](https://github.com/kubataba/kabardian-translator)
- [Fine-tuned Models](https://huggingface.co/kubataba) - KBD↔RU MarianMT models
- [Training Corpus](https://huggingface.co/datasets/adiga-ai/circassian-parallel-corpus)
- [NLLB-200 Model](https://huggingface.co/facebook/nllb-200-distilled-600M)
- [MarianMT Documentation](https://huggingface.co/docs/transformers/model_doc/marian)
- [Silero TTS](https://github.com/snakers4/silero-models)

---

## Changelog

### Version 2.0.0
- Enhanced MarianMT models with improved BLEU scores
- NLLB-200 integration (200+ languages)
- Full accentuation system for TTS
- Added Bashkir and Kyrgyz support
- Optimized resource usage (~2.9GB total)
- Improved transliteration rules

### Version 1.0.0
- Initial M2M100-based implementation
- Basic TTS support
- 14 language pairs

---

**Version 2.0.0** | Educational tool for Kabardian language preservation
