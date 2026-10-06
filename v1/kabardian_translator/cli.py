#!/usr/bin/env python3
# cli.py - Version 2.0.0
import os
import sys
import argparse

def main():
    """
    CLI for Kabardian Translator (NLLB-200 Edition)
    """
    # CHECK AND LOAD MODELS BEFORE STARTUP
    try:
        from kabardian_translator import ensure_models_downloaded
        if not ensure_models_downloaded():
            print("❌ Failed to load models. Application cannot start.")
            sys.exit(1)
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure package is installed correctly")
        sys.exit(1)
    
    parser = argparse.ArgumentParser(
        description="🌐 Kabardian Translator - Voice-enabled multilingual translator with NLLB-200",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage examples:
  kabardian-translator                    # Start server on port 5500
  kabardian-translator --port 8080        # Start server on port 8080
  kabardian-translator --host localhost   # Local access only
  
  # Command to download models:
  kabardian-download-models               # Download all models (~1.7GB)
  
  # Translation CLI:
  kabardian-translate                     # Interactive translation mode
        """
    )
    
    parser.add_argument("--port", type=int, default=5500, 
                       help="Port for server (default: 5500)")
    parser.add_argument("--host", default="0.0.0.0", 
                       help="Host for server (default: 0.0.0.0)")
    parser.add_argument("--debug", action="store_true",
                       help="Flask debug mode")
    parser.add_argument("--version", action="store_true",
                       help="Show version information")
    
    args = parser.parse_args()
    
    if args.version:
        from kabardian_translator import __version__
        print(f"Kabardian Translator v{__version__}")
        print("NLLB-200 Edition with MarianMT for Kabardian ↔ Russian")
        sys.exit(0)
    
    # Import here to avoid slowing down CLI startup
    try:
        from kabardian_translator.app import app as flask_app
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure all files are in current directory")
        sys.exit(1)
    
    print("🚀 Starting Kabardian Translator (NLLB-200 Edition)...")
    print(f"🌐 Server will be available at: http://{args.host}:{args.port}")
    print("⚡ Press Ctrl+C to stop")
    print("-" * 50)
    
    try:
        flask_app.run(
            host=args.host,
            port=args.port,
            debug=args.debug
        )
    except KeyboardInterrupt:
        print("\n👋 Stopping server...")
    except Exception as e:
        print(f"❌ Server startup error: {e}")

def translate_cli():
    """
    CLI translation interface
    """
    parser = argparse.ArgumentParser(
        description="CLI translation interface for Kabardian Translator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  kabardian-translate --text "Hello" --source eng_Latn --target rus_Cyrl
  kabardian-translate --text "Привет" --source rus_Cyrl --target kbd_Cyrl
  kabardian-translate --file input.txt --source rus_Cyrl --target eng_Latn
  
Available languages:
  rus_Cyrl     Russian
  kbd_Cyrl     Kabardian
  eng_Latn     English
  deu_Latn     German
  fra_Latn     French
  spa_Latn     Spanish
  tur_Latn     Turkish
  azj_Latn     Azerbaijani
  ukr_Cyrl     Ukrainian
  bel_Cyrl     Belarusian
  kaz_Cyrl     Kazakh
  kat_Geor     Georgian
  hye_Armn     Armenian
  lav_Latn     Latvian
        """
    )
    
    parser.add_argument("--text", help="Text to translate")
    parser.add_argument("--file", help="File containing text to translate")
    parser.add_argument("--source", required=True, help="Source language code")
    parser.add_argument("--target", required=True, help="Target language code")
    parser.add_argument("--output", help="Output file (default: stdout)")
    
    args = parser.parse_args()
    
    # Get text from file or argument
    if args.file:
        if not os.path.exists(args.file):
            print(f"❌ File not found: {args.file}")
            sys.exit(1)
        with open(args.file, 'r', encoding='utf-8') as f:
            text = f.read().strip()
    elif args.text:
        text = args.text.strip()
    else:
        print("❌ Either --text or --file must be specified")
        sys.exit(1)
    
    if not text:
        print("❌ No text to translate")
        sys.exit(1)
    
    try:
        # Import translation service
        from kabardian_translator.translation_service import TranslationService
        translator = TranslationService()
        
        print(f"🌐 Translating: {args.source} → {args.target}")
        print(f"📝 Text: {text[:100]}..." if len(text) > 100 else f"📝 Text: {text}")
        
        # Perform translation
        result = translator.translate(text, args.source, args.target)
        
        if result.get('error'):
            print(f"❌ Translation error: {result['error']}")
            sys.exit(1)
        
        translation = result['translation']
        time_ms = result['time_ms']
        model_used = result.get('model_used', 'unknown')
        
        print(f"✅ Translation complete ({time_ms}ms)")
        print(f"🤖 Model: {model_used}")
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(translation)
            print(f"💾 Saved to: {args.output}")
        else:
            print("\n" + "="*50)
            print("TRANSLATION:")
            print("="*50)
            print(translation)
            print("="*50)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()