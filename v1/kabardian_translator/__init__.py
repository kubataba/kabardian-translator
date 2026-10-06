# kabardian_translator/__init__.py
"""
Kabardian Translator Package - Version 2.0.0
MarianMT for Kabardian ↔ Russian, NLLB-200 for other languages (200+ languages)
"""

import os
import sys
from pathlib import Path

__version__ = "2.0.0"
__author__ = "Kubataba"
__email__ = "info@copperline.info"
__description__ = "Advanced multilingual translator for Kabardian and Caucasian languages with NLLB-200 model"

def check_models():
    """Check if required models are installed and return status"""
    models_status = {
        'marian_ru_kbd': False,  # Russian → Kabardian
        'marian_kbd_ru': False,  # Kabardian → Russian
        'nllb200_base': False,   # Base model for other languages
    }
    
    # Check MarianMT models (REQUIRED)
    marian_models = {
        'marian_ru_kbd': "models/marian_ru_kbd",
        'marian_kbd_ru': "models/marian_kbd_ru",
    }
    
    for name, path in marian_models.items():
        if os.path.exists(path):
            config_path = os.path.join(path, "config.json")
            if os.path.exists(config_path):
                models_status[name] = True
                print(f"✅ {name}: found")
            else:
                print(f"❌ {name}: config missing")
        else:
            print(f"❌ {name}: not found")
    
    # Check NLLB-200 base model (REQUIRED for full functionality)
    nllb_path = "models/nllb200"
    if os.path.exists(nllb_path):
        config_path = os.path.join(nllb_path, "config.json")
        if os.path.exists(config_path):
            models_status['nllb200_base'] = True
            print(f"✅ nllb200_base: found")
        else:
            print(f"⚠️  nllb200_base: found but incomplete")
    else:
        print(f"❌ nllb200_base: not found")
    
    # Determine system status
    marian_ok = models_status['marian_ru_kbd'] and models_status['marian_kbd_ru']
    nllb_ok = models_status['nllb200_base']
    
    if marian_ok and nllb_ok:
        print("\n✅ All models found - full functionality available")
        return {'status': 'full', 'models': models_status}
    elif marian_ok:
        print("\n⚠️  MarianMT models found, but NLLB-200 missing")
        print("   Kabardian ↔ Russian available, other languages not supported")
        return {'status': 'partial', 'models': models_status}
    else:
        print("\n❌ Critical models missing")
        return {'status': 'failed', 'models': models_status}

def ensure_models_downloaded():
    """Automatically download ALL required models without questions"""
    print("\n" + "="*70)
    print("  KABARDIAN TRANSLATOR v2.0.0 - MODEL DOWNLOAD")
    print("  (NLLB-200 Edition)")
    print("="*70)
    
    # First check what we already have
    print("\n🔍 Checking existing models...")
    status = check_models()
    
    if status['status'] == 'full':
        print("\n✅ All models already installed!")
        return True
    
    # If not all models found - download ALL
    print("\n📥 Downloading ALL required models...")
    print("\n" + "="*70)
    print("  DOWNLOADING:")
    print("  1. MarianMT Russian → Kabardian (~250MB)")
    print("  2. MarianMT Kabardian → Russian (~250MB)")
    print("  3. Base NLLB-200 for 200+ languages (~1.2GB)")
    print("")
    print("  Total size: ~1.7GB")
    print("  Download time: 3-10 minutes")
    print("="*70)
    
    try:
        # Import here to avoid circular imports
        from .download_models import download_marian_model, download_nllb_model
        
        # Create models directory if it doesn't exist
        models_dir = Path("models")
        models_dir.mkdir(exist_ok=True)
        
        # Step 1: Download MarianMT models
        print("\n" + "="*70)
        print("  DOWNLOADING MARIANMT MODELS")
        print("="*70)
        
        marian_models = [
            ("kubataba/ru-kbd-opus", "models/marian_ru_kbd", "Russian → Kabardian"),
            ("kubataba/kbd-ru-opus", "models/marian_kbd_ru", "Kabardian → Russian"),
        ]
        
        marian_success_count = 0
        for model_id, save_path, description in marian_models:
            print(f"\n📥 Downloading {description}...")
            if download_marian_model(model_id, save_path, description):
                marian_success_count += 1
                print(f"✅ {description} downloaded successfully")
            else:
                print(f"❌ Failed to download {description}")
        
        if marian_success_count < len(marian_models):
            print(f"\n❌ Only {marian_success_count}/{len(marian_models)} MarianMT models downloaded")
            print("   Application may not work correctly")
            # Continue, maybe NLLB-200 will download
        
        # Step 2: Download NLLB-200 base model (NO QUESTIONS)
        print("\n" + "="*70)
        print("  DOWNLOADING BASE NLLB-200 MODEL")
        print("="*70)
        print("\n📥 Downloading base NLLB-200 model (facebook/nllb-200-distilled-600M)...")
        print("   Size: ~1.2GB")
        print("   This model enables translations between 200+ languages")
        print("   Download may take 3-10 minutes...")
        
        try:
            if download_nllb_model(
                'facebook/nllb-200-distilled-600M',
                'models/nllb200',
                'Base NLLB-200 model (200+ languages)'
            ):
                print("\n✅ NLLB-200 model downloaded successfully!")
                print("   Features:")
                print("   • 200+ languages support")
                print("   • Better translation quality")
                print("   • Support for rare languages")
            else:
                print("\n❌ Failed to download NLLB-200 model")
                print("   Non-Kabardian translations will not work")
                print("   But Kabardian ↔ Russian will still work")
        except Exception as e:
            print(f"\n⚠️  Error downloading NLLB-200: {e}")
            print("   Non-Kabardian translations will not work")
            print("   But Kabardian ↔ Russian will still work")
        
        # Check final status
        print("\n" + "="*70)
        print("  DOWNLOAD COMPLETE")
        print("="*70)
        
        final_status = check_models()
        
        if final_status['status'] == 'full':
            print("\n🎉 ALL MODELS DOWNLOADED SUCCESSFULLY!")
            print("   Full multilingual translation is now available!")
            print("   Supported: 200+ languages via NLLB-200")
            return True
        elif final_status['status'] == 'partial':
            print("\n⚠️  PARTIAL INSTALLATION")
            print("   The application will start with limited functionality")
            
            # Check what models we have
            if final_status['models']['marian_ru_kbd'] and final_status['models']['marian_kbd_ru']:
                print("   ✓ Kabardian ↔ Russian translations available")
            
            if final_status['models']['nllb200_base']:
                print("   ✓ Full multilingual support (200+ languages)")
            else:
                print("   ✗ Non-Kabardian translations not available")
            
            return True  # Start application anyway
        
        else:
            print("\n❌ CRITICAL MODELS MISSING")
            print("   Application cannot start")
            return False
        
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("💡 Make sure all dependencies are installed: pip install transformers torch")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error during download: {e}")
        import traceback
        traceback.print_exc()
        print("\n💡 You can try manual download:")
        print("   1. kabardian-download-models --full")
        print("   2. Or download models manually from HuggingFace")
        return False

def get_installation_status():
    """Return detailed installation status"""
    status = check_models()
    
    if status['status'] == 'full':
        return {
            'status': 'full',
            'message': 'All models installed - full functionality',
            'version': __version__,
            'capabilities': {
                'kabardian_russian': '✓ Direct MarianMT translation',
                'other_languages': '✓ Direct NLLB-200 translation (200+ languages)',
                'cascade': '✓ Full cascade support',
                'tts': '✓ Voice synthesis for all languages',
                'transliteration': '✓ Automatic transliteration for TTS'
            }
        }
    elif status['status'] == 'partial':
        missing_models = []
        if not status['models']['marian_ru_kbd']:
            missing_models.append('MarianMT Russian → Kabardian')
        if not status['models']['marian_kbd_ru']:
            missing_models.append('MarianMT Kabardian → Russian')
        if not status['models']['nllb200_base']:
            missing_models.append('Base NLLB-200')
        
        capabilities = {}
        limitations = []
        
        if status['models']['marian_ru_kbd'] and status['models']['marian_kbd_ru']:
            capabilities['kabardian_russian'] = '✓ Direct MarianMT translation'
        else:
            capabilities['kabardian_russian'] = '✗ Not available'
            limitations.append('Kabardian ↔ Russian translations not available')
        
        if status['models']['nllb200_base']:
            capabilities['other_languages'] = '✓ Direct NLLB-200 translation (200+ languages)'
            capabilities['cascade'] = '✓ Full cascade support'
        else:
            capabilities['other_languages'] = '✗ Not available'
            capabilities['cascade'] = '⚠️ Limited to Russian intermediate'
            limitations.append('Non-Kabardian translations not available')
        
        capabilities['tts'] = '✓ Voice synthesis for supported languages'
        capabilities['transliteration'] = '✓ Automatic transliteration for TTS'
        
        return {
            'status': 'partial',
            'message': f'Missing: {", ".join(missing_models)}',
            'version': __version__,
            'capabilities': capabilities,
            'limitations': limitations,
            'instructions': 'Run: kabardian-download-models --full'
        }
    else:
        return {
            'status': 'failed',
            'message': 'Critical models missing',
            'version': __version__,
            'instructions': 'Run: kabardian-download-models --full'
        }

def check_disk_space():
    """Check available disk space"""
    try:
        import shutil
        stat = shutil.disk_usage(".")
        free_gb = stat.free / (1024**3)
        
        print(f"\n💾 Disk space check:")
        print(f"   Available: {free_gb:.1f}GB")
        
        # Approximate size of all models: 1.7GB
        required_gb = 2.0  # With margin
        
        if free_gb < required_gb:
            print(f"   ⚠️  WARNING: Less than {required_gb}GB available")
            print(f"   Models require ~1.7GB total")
            print(f"   You may need to free up disk space")
            return False
        else:
            print(f"   ✅ Sufficient disk space available")
            return True
    except Exception as e:
        print(f"   ⚠️  Could not check disk space: {e}")
        return True  # Continue even if we couldn't check

# Function for easy testing
def test_model_check():
    """Test model checking"""
    print("🧪 Testing model check...")
    print(f"Kabardian Translator v{__version__}")
    print("NLLB-200 Edition")
    status = check_models()
    print(f"\nStatus: {status['status']}")
    print(f"Models: {status['models']}")
    
    install_status = get_installation_status()
    print(f"\nInstallation Status:")
    print(f"  Version: {install_status['version']}")
    print(f"  Message: {install_status['message']}")
    
    if 'capabilities' in install_status:
        print(f"  Capabilities:")
        for capability, desc in install_status['capabilities'].items():
            print(f"    • {capability}: {desc}")
    
    if 'limitations' in install_status:
        print(f"  Limitations:")
        for limitation in install_status['limitations']:
            print(f"    • {limitation}")
    
    if 'instructions' in install_status:
        print(f"  Instructions: {install_status['instructions']}")

# Export commonly used functions
__all__ = [
    '__version__',
    '__author__',
    '__description__',
    'check_models',
    'ensure_models_downloaded',
    'get_installation_status',
    'check_disk_space',
    'test_model_check'
]

if __name__ == "__main__":
    test_model_check()