#!/usr/bin/env python3
# download_models.py
# Script to download models for Kabardian Translator
# License: CC BY-NC 4.0 (Non-Commercial Use Only)
# Version 2.0.0 - Migrated to NLLB-200 model

import os
import sys
import argparse
from pathlib import Path
import glob

def print_progress(message, step=None, total=None):
    """Beautiful progress output"""
    prefix = f"[{step}/{total}] " if step and total else ""
    print(f"\n{prefix}{'='*60}")
    print(f"  {message}")
    print('='*60)

def check_disk_space(required_gb):
    """Check available disk space"""
    try:
        import shutil
        stat = shutil.disk_usage(".")
        free_gb = stat.free / (1024**3)
        
        if free_gb < required_gb:
            print(f"⚠️  WARNING: Low disk space!")
            print(f"   Available: {free_gb:.1f}GB, Required: {required_gb}GB")
            response = input("Continue? (y/n): ")
            if response.lower() != 'y':
                return False
        else:
            print(f"✅ Free space: {free_gb:.1f}GB (sufficient)")
        return True
    except Exception as e:
        print(f"⚠️  Could not check disk space: {e}")
        return True

def download_marian_model(model_id, save_path, description):
    """Download MarianMT model and tokenizer"""
    print(f"\n📥 Downloading MarianMT: {description}")
    print(f"   Model ID: {model_id}")
    print(f"   Save path: {save_path}")
    
    try:
        from transformers import MarianMTModel, MarianTokenizer
        
        # Create directory
        Path(save_path).mkdir(parents=True, exist_ok=True)
        
        # Download tokenizer
        print("   ⏳ Downloading tokenizer...")
        tokenizer = MarianTokenizer.from_pretrained(model_id)
        tokenizer.save_pretrained(save_path)
        print(f"   ✅ Tokenizer saved")
        
        # Download model
        print("   ⏳ Downloading model...")
        model = MarianMTModel.from_pretrained(model_id)
        model.save_pretrained(save_path)
        
        # Get model info
        num_params = sum(p.numel() for p in model.parameters())
        size_str = f"{num_params/1e6:.1f}M" if num_params < 1e9 else f"{num_params/1e9:.2f}B"
        print(f"   ✅ Model saved ({size_str} parameters)")
        
        # Memory cleanup
        del model
        del tokenizer
        
        return True
        
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def download_nllb_model(model_id, save_path, description):
    """Download NLLB-200 model and tokenizer"""
    print(f"\n📥 Downloading NLLB-200: {description}")
    print(f"   Model ID: {model_id}")
    print(f"   Save path: {save_path}")
    
    try:
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        
        # Create directory
        Path(save_path).mkdir(parents=True, exist_ok=True)
        
        # Download model
        print("   ⏳ Downloading model...")
        model = AutoModelForSeq2SeqLM.from_pretrained(model_id)
        model.save_pretrained(save_path)
        
        # Get model info
        num_params = sum(p.numel() for p in model.parameters())
        print(f"   ✅ Model saved ({num_params/1e9:.2f}B parameters)")
        
        # Download tokenizer
        print("   ⏳ Downloading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        tokenizer.save_pretrained(save_path)
        print(f"   ✅ Tokenizer saved to {save_path}")
        
        # Memory cleanup
        del model
        del tokenizer
        
        return True
        
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_installation():
    """Verify installation correctness"""
    print_progress("VERIFICATION")
    
    models_dir = "models"
    all_ok = True
    
    # Required models
    required = {
        "marian_ru_kbd": "Russian → Kabardian (MarianMT)",
        "marian_kbd_ru": "Kabardian → Russian (MarianMT)",
    }
    
    # Optional but recommended
    optional = {
        "nllb200": "Base NLLB-200 for other languages",
    }
    
    # Check required models
    print("🔍 Required models:")
    for model_name, description in required.items():
        model_path = os.path.join(models_dir, model_name)
        if os.path.exists(model_path):
            config_path = os.path.join(model_path, "config.json")
            if os.path.exists(config_path):
                print(f"✅ {description}: found")
            else:
                print(f"❌ {description}: config missing")
                all_ok = False
        else:
            print(f"❌ {description}: not found")
            all_ok = False
    
    # Check optional models
    print("\n🔍 Optional models:")
    for model_name, description in optional.items():
        model_path = os.path.join(models_dir, model_name)
        if os.path.exists(model_path):
            config_path = os.path.join(model_path, "config.json")
            if os.path.exists(config_path):
                print(f"✅ {description}: found (full functionality)")
            else:
                print(f"⚠️  {description}: found but incomplete")
        else:
            print(f"⚠️  {description}: not found (limited functionality)")
    
    return all_ok

def download_minimal_models():
    """Download minimal required models (MarianMT only)"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║           MINIMAL MODEL DOWNLOAD (v2.0.0)                 ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

This will download ONLY the required MarianMT models:
  1. MarianMT ru→kbd model (kubataba/ru-kbd-opus) ~250MB
  2. MarianMT kbd→ru model (kubataba/kbd-ru-opus) ~250MB
  
Total size: ~500MB
Download time: 1-5 minutes

These models enable Kabardian ↔ Russian translations.
For other languages, you'll need the base NLLB-200 model separately.
""")
    
    response = input("Start download? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled by user")
        return False
    
    if not check_disk_space(required_gb=1):
        return False
    
    marian_models = [
        {
            'id': 'kubataba/ru-kbd-opus',
            'path': 'models/marian_ru_kbd',
            'description': 'MarianMT Russian → Kabardian'
        },
        {
            'id': 'kubataba/kbd-ru-opus',
            'path': 'models/marian_kbd_ru',
            'description': 'MarianMT Kabardian → Russian'
        }
    ]
    
    total = len(marian_models)
    success_count = 0
    
    for idx, model_info in enumerate(marian_models, 1):
        print_progress(
            f"Downloading MarianMT model {idx}/{total}",
            step=idx,
            total=total
        )
        
        if download_marian_model(
            model_info['id'],
            model_info['path'],
            model_info['description']
        ):
            success_count += 1
        else:
            print(f"\n⚠️  Failed to download {model_info['description']}")
            response = input("Continue with next model? (y/n): ")
            if response.lower() != 'y':
                break
    
    return success_count == total

def download_base_nllb():
    """Download only base NLLB-200 model"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║           BASE NLLB-200 MODEL DOWNLOAD                    ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

This will download the base NLLB-200 model:
  • NLLB-200 Distilled 600M (facebook/nllb-200-distilled-600M) ~1.2GB
  
This model enables translations between non-Kabardian languages:
  • 200+ languages support
  • Better quality than M2M100
  • Modern transformer architecture
  
Without this model, only Kabardian ↔ Russian will work.
""")
    
    response = input("Start download? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled by user")
        return False
    
    if not check_disk_space(required_gb=2):
        return False
    
    print_progress("Downloading base NLLB-200 model", step=1, total=1)
    
    success = download_nllb_model(
        'facebook/nllb-200-distilled-600M',
        'models/nllb200',
        'Base NLLB-200 model (200+ languages)'
    )
    
    if success:
        print("\n✅ Base NLLB-200 model downloaded successfully!")
        print("   You now have full multilingual translation support.")
        print("   Features:")
        print("   • 200+ languages support")
        print("   • Better translation quality")
        print("   • Support for rare languages")
        return True
    else:
        print("\n❌ Failed to download base NLLB-200 model")
        print("   Kabardian ↔ Russian will still work with MarianMT.")
        return False

def download_all_models():
    """Download all models (full installation)"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║           FULL MODEL DOWNLOAD (v2.0.0)                    ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

This will download ALL models:
  1. MarianMT ru→kbd (kubataba/ru-kbd-opus) ~250MB
  2. MarianMT kbd→ru (kubataba/kbd-ru-opus) ~250MB
  3. Base NLLB-200 (facebook/nllb-200-distilled-600M) ~1.2GB
  
Total size: ~1.7GB
Download time: 3-10 minutes

This provides complete functionality:
  • Kabardian ↔ Russian (MarianMT, better quality)
  • 200+ other language pairs (NLLB-200)
  • Modern transformer architecture
  • Better translation quality
""")
    
    response = input("Start download? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled by user")
        return False
    
    if not check_disk_space(required_gb=2):
        return False
    
    # Download MarianMT models first
    print("\n📥 Phase 1: Downloading MarianMT models...")
    if not download_minimal_models():
        print("⚠️  MarianMT download failed, continuing with NLLB-200...")
    
    # Download base NLLB-200
    print("\n📥 Phase 2: Downloading base NLLB-200...")
    if download_base_nllb():
        print("\n✅ All models downloaded successfully!")
        print("   You have complete translation functionality.")
        print("   Key features:")
        print("   • Kabardian ↔ Russian via MarianMT")
        print("   • 200+ other languages via NLLB-200")
        print("   • Cascade translation when needed")
        return True
    else:
        print("\n⚠️  Some models may be missing")
        print("   Kabardian ↔ Russian should still work.")
        return False

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="Download models for Kabardian Translator v2.0.0 (NLLB-200)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Download options:
  Default (no arguments): Interactive menu
  --minimal:    Only MarianMT for Kabardian ↔ Russian (~500MB)
  --full:       All models for complete functionality (~1.7GB)
  --base-only:  Only base NLLB-200 for other languages (~1.2GB)
  --check:      Check installed models

Examples:
  kabardian-download-models           # Interactive menu
  kabardian-download-models --minimal # MarianMT only
  kabardian-download-models --full    # All models
  kabardian-download-models --check   # Check installation
        """
    )
    
    parser.add_argument("--minimal", action="store_true",
                       help="Download only MarianMT models (~500MB)")
    parser.add_argument("--full", action="store_true",
                       help="Download all models (~1.7GB)")
    parser.add_argument("--base-only", action="store_true",
                       help="Download only base NLLB-200 (~1.2GB)")
    parser.add_argument("--check", action="store_true",
                       help="Check installed models")
    
    args = parser.parse_args()
    
    if args.check:
        print("🔍 Checking installed models...")
        return verify_installation()
    
    if args.minimal:
        return download_minimal_models()
    elif args.full:
        return download_all_models()
    elif args.base_only:
        return download_base_nllb()
    else:
        # Interactive mode
        return interactive_menu()

def interactive_menu():
    """Interactive download menu"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║           KABARDIAN TRANSLATOR MODEL DOWNLOADER           ║
║                     Version 2.0.0                         ║
║                   (NLLB-200 Edition)                      ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

Select download option:

  1. Minimal (Recommended)
     • MarianMT models only (~500MB)
     • Enables Kabardian ↔ Russian
     • Best for most users

  2. Full Installation
     • All models (~1.7GB)
     • MarianMT + Base NLLB-200
     • Complete multilingual support (200+ languages)

  3. Base NLLB-200 only
     • Base model only (~1.2GB)
     • For other language pairs
     • Requires MarianMT for Kabardian

  4. Check existing installation
     • Verify installed models

  5. Exit
""")
    
    while True:
        choice = input("\nEnter choice (1-5): ").strip()
        
        if choice == '1':
            return download_minimal_models()
        elif choice == '2':
            return download_all_models()
        elif choice == '3':
            return download_base_nllb()
        elif choice == '4':
            return verify_installation()
        elif choice == '5':
            print("Exiting...")
            return True
        else:
            print("Invalid choice. Please enter 1-5.")

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user (Ctrl+C)")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)