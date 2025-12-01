# kabardian_translator/__init__.py
"""
Kabardian Translator Package
"""

import os
import sys

__version__ = "1.0.1"
__author__ = "Kubataba"
__email__ = "info@copperline.info"

def check_models():
    """Проверяет наличие моделей"""
    required_models = [
        "models/m2m100",
        "models/m2m100_ru_kbd", 
        "models/m2m100_kbd_ru"
    ]
    
    for model in required_models:
        # Проверяем относительно текущей директории
        if not os.path.exists(model):
            return False
        
        # Проверяем что модель загружена (есть config.json)
        config_path = os.path.join(model, "config.json")
        if not os.path.exists(config_path):
            return False
    
    return True

def ensure_models_downloaded():
    """Автоматическая загрузка моделей"""
    if check_models():
        return True
    
    print("❌ Модели не найдены! Требуется загрузка (~10GB)")
    print("📥 Запускаю загрузку...")
    
    try:
        from .download_models import main as download_main
        download_main()
        
        # Проверим после загрузки
        if check_models():
            print("✅ Модели успешно загружены!")
            return True
        else:
            print("⚠️  Модели загружены не полностью")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка загрузки: {e}")
        print("\n📋 Попробуйте вручную:")
        print("   kabardian-download-models")
        return False
