# kabardian_translator/__init__.py
"""
Kabardian Translator Package - Version 1.0.3
MarianMT for Kabardian ↔ Russian, M2M100 for other languages
"""

import os
import sys
from pathlib import Path

__version__ = "1.0.3"
__author__ = "Kubataba"
__email__ = "info@copperline.info"

def check_models():
    """Проверяет наличие моделей и возвращает статус"""
    models_status = {
        'marian_ru_kbd': False,  # Russian → Kabardian
        'marian_kbd_ru': False,  # Kabardian → Russian
        'm2m100_base': False,    # Base model for other languages
    }
    
    # Проверяем MarianMT модели (ОБЯЗАТЕЛЬНЫЕ)
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
    
    # Проверяем M2M100 base модель (ОБЯЗАТЕЛЬНАЯ)
    m2m100_path = "models/m2m100"
    if os.path.exists(m2m100_path):
        config_path = os.path.join(m2m100_path, "config.json")
        if os.path.exists(config_path):
            models_status['m2m100_base'] = True
            print(f"✅ m2m100_base: found")
        else:
            print(f"⚠️  m2m100_base: found but incomplete")
    else:
        print(f"❌ m2m100_base: not found")
    
    # Определяем статус системы
    all_required_ok = all(models_status.values())
    
    if all_required_ok:
        print("\n✅ All required models found - full functionality available")
        return {'status': 'full', 'models': models_status}
    else:
        print("\n❌ Some required models are missing")
        return {'status': 'failed', 'models': models_status}

def ensure_models_downloaded():
    """Автоматическая загрузка ВСЕХ требуемых моделей без вопросов"""
    print("\n" + "="*70)
    print("  KABARDIAN TRANSLATOR v1.0.3 - MODEL DOWNLOAD")
    print("="*70)
    
    # Сначала проверяем что уже есть
    print("\n🔍 Checking existing models...")
    status = check_models()
    
    if status['status'] == 'full':
        print("\n✅ All models already installed!")
        return True
    
    # Если не все модели найдены - скачиваем ВСЕ
    print("\n📥 Downloading ALL required models...")
    print("\n" + "="*70)
    print("  DOWNLOADING:")
    print("  1. MarianMT Russian → Kabardian (~250MB)")
    print("  2. MarianMT Kabardian → Russian (~250MB)")
    print("  3. Base M2M100 for 100+ languages (~1.6GB)")
    print("")
    print("  Total size: ~2.3GB")
    print("  Download time: 3-10 minutes")
    print("="*70)
    
    try:
        # Импортируем здесь, чтобы избежать циклических импортов
        from .download_models import download_marian_model, download_m2m100_model
        
        # Создаем папку models если ее нет
        models_dir = Path("models")
        models_dir.mkdir(exist_ok=True)
        
        # Шаг 1: Скачиваем MarianMT модели
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
            # Продолжаем, возможно M2M100 скачается
        
        # Шаг 2: Скачиваем M2M100 base модель (БЕЗ ВОПРОСОВ)
        print("\n" + "="*70)
        print("  DOWNLOADING BASE M2M100 MODEL")
        print("="*70)
        print("\n📥 Downloading base M2M100 model (facebook/m2m100_418M)...")
        print("   Size: ~1.6GB")
        print("   This model enables translations between 100+ languages")
        print("   Download may take 3-10 minutes...")
        
        try:
            if download_m2m100_model(
                'facebook/m2m100_418M',
                'models/m2m100',
                'Base M2M100 model 418M (100 languages)'
            ):
                print("\n✅ M2M100 418M model downloaded successfully!")
            else:
                print("\n❌ Failed to download M2M100 418M model")
                print("   Non-Kabardian translations will not work")
                print("   But Kabardian ↔ Russian will still work")
        except Exception as e:
            print(f"\n⚠️  Error downloading M2M100 418M: {e}")
            print("   Non-Kabardian translations will not work")
            print("   But Kabardian ↔ Russian will still work")
        
        # Проверяем итоговый статус
        print("\n" + "="*70)
        print("  DOWNLOAD COMPLETE")
        print("="*70)
        
        final_status = check_models()
        
        if final_status['status'] == 'full':
            print("\n🎉 ALL MODELS DOWNLOADED SUCCESSFULLY!")
            print("   Full multilingual translation is now available!")
            return True
        else:
            print("\n⚠️  SOME MODELS MAY BE MISSING")
            print("   The application will start with limited functionality")
            
            # Проверяем какие модели есть
            if final_status['models']['marian_ru_kbd'] and final_status['models']['marian_kbd_ru']:
                print("   ✓ Kabardian ↔ Russian translations available")
            
            if final_status['models']['m2m100_base']:
                print("   ✓ Full multilingual support available")
            else:
                print("   ✗ Non-Kabardian translations not available")
            
            return True  # Все равно запускаем приложение
        
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
    """Возвращает подробный статус установки"""
    status = check_models()
    
    if status['status'] == 'full':
        return {
            'status': 'full',
            'message': 'All models installed - full functionality',
            'capabilities': {
                'kabardian_russian': '✓ Direct MarianMT translation',
                'other_languages': '✓ Direct M2M100 translation',
                'cascade': '✓ Full cascade support',
                'tts': '✓ Voice synthesis for all languages'
            }
        }
    else:
        missing_models = []
        if not status['models']['marian_ru_kbd']:
            missing_models.append('MarianMT Russian → Kabardian')
        if not status['models']['marian_kbd_ru']:
            missing_models.append('MarianMT Kabardian → Russian')
        if not status['models']['m2m100_base']:
            missing_models.append('Base M2M100 418M')
        
        capabilities = {}
        limitations = []
        
        if status['models']['marian_ru_kbd'] and status['models']['marian_kbd_ru']:
            capabilities['kabardian_russian'] = '✓ Direct MarianMT translation'
        else:
            capabilities['kabardian_russian'] = '✗ Not available'
            limitations.append('Kabardian ↔ Russian translations not available')
        
        if status['models']['m2m100_base']:
            capabilities['other_languages'] = '✓ Direct M2M100 translation'
            capabilities['cascade'] = '✓ Full cascade support'
        else:
            capabilities['other_languages'] = '✗ Not available'
            capabilities['cascade'] = '⚠️ Limited to Russian intermediate'
            limitations.append('Non-Kabardian translations not available')
        
        capabilities['tts'] = '✓ Voice synthesis for supported languages'
        
        return {
            'status': 'partial',
            'message': f'Missing: {", ".join(missing_models)}',
            'capabilities': capabilities,
            'limitations': limitations,
            'instructions': 'Run: kabardian-download-models --full'
        }

def check_disk_space():
    """Проверяет доступное место на диске"""
    try:
        import shutil
        stat = shutil.disk_usage(".")
        free_gb = stat.free / (1024**3)
        
        print(f"\n💾 Disk space check:")
        print(f"   Available: {free_gb:.1f}GB")
        
        # Примерный размер всех моделей: 2.0GB
        required_gb = 2.5  # С запасом
        
        if free_gb < required_gb:
            print(f"   ⚠️  WARNING: Less than {required_gb}GB available")
            print(f"   Models require ~2.0GB total")
            print(f"   You may need to free up disk space")
            return False
        else:
            print(f"   ✅ Sufficient disk space available")
            return True
    except Exception as e:
        print(f"   ⚠️  Could not check disk space: {e}")
        return True  # Продолжаем даже если не смогли проверить

# Функция для удобного тестирования
def test_model_check():
    """Тестирует проверку моделей"""
    print("🧪 Testing model check...")
    status = check_models()
    print(f"\nStatus: {status['status']}")
    print(f"Models: {status['models']}")
    
    install_status = get_installation_status()
    print(f"\nInstallation Status:")
    print(f"  Message: {install_status['message']}")
    
    if 'capabilities' in install_status:
        print(f"  Capabilities:")
        for capability, desc in install_status['capabilities'].items():
            print(f"    • {capability}: {desc}")
    
    if 'limitations' in install_status:
        print(f"  Limitations:")
        for limitation in install_status['limitations']:
            print(f"    • {limitation}")

if __name__ == "__main__":
    test_model_check()