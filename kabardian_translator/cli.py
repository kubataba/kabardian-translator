#!/usr/bin/env python3
import os
import sys
import argparse

def main():
    """
    CLI для Kabardian Translator
    """
    # ПРОВЕРКА И ЗАГРУЗКА МОДЕЛЕЙ ПЕРЕД ЗАПУСКОМ
    try:
        from kabardian_translator import ensure_models_downloaded
        if not ensure_models_downloaded():
            print("❌ Не удалось загрузить модели. Приложение не может запуститься.")
            sys.exit(1)
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("💡 Убедитесь, что пакет установлен корректно")
        sys.exit(1)
    
    parser = argparse.ArgumentParser(
        description="🌐 Kabardian Translator - Voice-enabled multilingual translator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  kabardian-translator                    # Запуск на порту 5500
  kabardian-translator --port 8080        # Запуск на порту 8080
  kabardian-translator --host localhost   # Только локальный доступ
  
  # Команда для загрузки моделей:
  kabardian-download-models               # Скачать модели (~10GB)
        """
    )
    
    parser.add_argument("--port", type=int, default=5500, 
                       help="Порт для запуска сервера (по умолчанию: 5500)")
    parser.add_argument("--host", default="0.0.0.0", 
                       help="Хост для запуска сервера (по умолчанию: 0.0.0.0)")
    parser.add_argument("--debug", action="store_true",
                       help="Режим отладки Flask")
    
    args = parser.parse_args()
    
    # Импортируем здесь, чтобы не замедлять запуск CLI
    try:
        from kabardian_translator.app import app as flask_app
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("💡 Убедитесь, что все файлы в текущей директории")
        sys.exit(1)
    
    print("🚀 Запуск Kabardian Translator...")
    print(f"🌐 Сервер будет доступен по адресу: http://{args.host}:{args.port}")
    print("⚡ Для остановки нажмите Ctrl+C")
    print("-" * 50)
    
    try:
        flask_app.run(
            host=args.host,
            port=args.port,
            debug=args.debug
        )
    except KeyboardInterrupt:
        print("\n👋 Остановка сервера...")
    except Exception as e:
        print(f"❌ Ошибка запуска сервера: {e}")

if __name__ == "__main__":
    main()
