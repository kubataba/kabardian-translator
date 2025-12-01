#!/usr/bin/env python3
# download_models.py
# Script to download all required models for Kabardian Translator
# License: CC BY-NC 4.0 (Non-Commercial Use Only)

import os
import sys
from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer
from pathlib import Path
import glob

def print_progress(message, step=None, total=None):
    """Beautiful progress output"""
    prefix = f"[{step}/{total}] " if step and total else ""
    print(f"\n{prefix}{'='*60}")
    print(f"  {message}")
    print('='*60)

def check_disk_space(required_gb=15):
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
                sys.exit(1)
        else:
            print(f"✅ Free space: {free_gb:.1f}GB (sufficient)")
    except Exception as e:
        print(f"⚠️  Could not check disk space: {e}")

def download_model_with_tokenizer(model_id, save_path, description):
    """
    Download model and tokenizer with smart fallback
    
    CRITICAL: Fine-tuned models may not include tokenizers on HuggingFace.
    We use the base M2M100 tokenizer for all models as they are compatible.
    """
    print(f"\n📥 Downloading: {description}")
    print(f"   Model ID: {model_id}")
    print(f"   Save path: {save_path}")
    
    try:
        # Create directory
        Path(save_path).mkdir(parents=True, exist_ok=True)
        
        # Download model
        print("   ⏳ Downloading model...")
        model = M2M100ForConditionalGeneration.from_pretrained(
            model_id,
            torch_dtype="auto"  # Automatically determine best dtype
        )
        
        # Save model
        model.save_pretrained(save_path)
        print(f"   ✅ Model saved ({model.num_parameters()/1e9:.2f}B parameters)")
        
        # Tokenizer strategy: Use base tokenizer for ALL models
        print("   ⏳ Setting up tokenizer...")
        
        # Always use base tokenizer - compatible with all M2M100 variants
        base_tokenizer_id = "facebook/m2m100_1.2B"
        try:
            tokenizer = M2M100Tokenizer.from_pretrained(base_tokenizer_id)
            print(f"   ✅ Base tokenizer loaded: {base_tokenizer_id}")
        except Exception as e:
            print(f"   ❌ Failed to load base tokenizer: {e}")
            print("   ⏳ Trying to load tokenizer from model...")
            try:
                tokenizer = M2M100Tokenizer.from_pretrained(model_id)
                print("   ✅ Model tokenizer loaded as fallback")
            except Exception as e2:
                print(f"   ❌ All tokenizer options failed: {e2}")
                raise RuntimeError("Could not load any tokenizer")
        
        # Save tokenizer
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
    """Verify installation correctness with modern file formats"""
    print_progress("VERIFICATION")
    
    models_dir = "models"
    
    # Updated file patterns for modern HuggingFace models
    # - model.safetensors: new safe tensor format (replaces pytorch_model.bin)
    # - config.json: model configuration  
    # - tokenizer_config.json + sentencepiece.bpe.model: tokenizer files
    # - *.safetensors: any safetensors file pattern
    required_patterns = {
        "m2m100": [
            "config.json",
            "*.safetensors",  # New safety format instead of pytorch_model.bin
            "model.safetensors",
            "tokenizer_config.json",
            "sentencepiece.bpe.model"
        ],
        "m2m100_ru_kbd": [
            "config.json", 
            "*.safetensors",
            "model.safetensors",
            "tokenizer_config.json", 
            "sentencepiece.bpe.model"
        ],
        "m2m100_kbd_ru": [
            "config.json",
            "*.safetensors",
            "model.safetensors",
            "tokenizer_config.json",
            "sentencepiece.bpe.model"
        ]
    }
    
    all_ok = True
    
    for model_name, patterns in required_patterns.items():
        model_path = os.path.join(models_dir, model_name)
        print(f"\n📁 Checking {model_name}:")
        
        if not os.path.exists(model_path):
            print(f"   ❌ Directory not found: {model_path}")
            all_ok = False
            continue
        
        found_files = set()
        for pattern in patterns:
            matches = glob.glob(os.path.join(model_path, pattern))
            for match in matches:
                filename = os.path.basename(match)
                found_files.add(filename)
                size_mb = os.path.getsize(match) / (1024**2)
                print(f"   ✅ {filename} ({size_mb:.1f}MB)")
        
        # Check for critical files
        critical_files_found = any("safetensors" in f for f in found_files) or any("pytorch_model.bin" in f for f in found_files)
        config_found = "config.json" in found_files
        tokenizer_found = any(f in found_files for f in ["tokenizer_config.json", "sentencepiece.bpe.model"])
        
        if not critical_files_found:
            print(f"   ❌ CRITICAL: No model weights found (safetensors or bin)")
            all_ok = False
        if not config_found:
            print(f"   ❌ CRITICAL: config.json missing")
            all_ok = False  
        if not tokenizer_found:
            print(f"   ❌ CRITICAL: Tokenizer files missing")
            all_ok = False
        
        # List any missing expected files
        expected_files = ["config.json", "model.safetensors", "tokenizer_config.json", "sentencepiece.bpe.model"]
        for expected in expected_files:
            if expected not in found_files:
                # Check if there's an alternative
                if expected == "model.safetensors" and any(f.endswith(".safetensors") for f in found_files):
                    continue  # Some other safetensors file exists
                elif expected == "sentencepiece.bpe.model" and any("vocab.json" in f for f in found_files):
                    continue  # Alternative tokenizer file exists
                else:
                    print(f"   ⚠️  Missing (but maybe optional): {expected}")
    
    if all_ok:
        print("\n✅ All models installed correctly!")
        return True
    else:
        print("\n❌ Installation issues detected")
        return False

def main():
    """Main download function"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║           KABARDIAN TRANSLATOR MODEL DOWNLOADER           ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝

This script will download:
  1. Base M2M100 model (facebook/m2m100_1.2B) ~4.8GB
  2. Fine-tuned ru→kbd model (anzorq/...) ~4.8GB
  3. Fine-tuned kbd→ru model (anzorq/...) ~4.8GB
  
Total size: ~15GB
Download time: 10-30 minutes (depends on internet speed)

NOTE: All models use the same base tokenizer for compatibility.
""")
    
    response = input("Start download? (y/n): ")
    if response.lower() != 'y':
        print("Cancelled by user")
        sys.exit(0)
    
    # Check disk space
    check_disk_space(required_gb=20)
    
    models_to_download = [
        {
            'id': 'facebook/m2m100_1.2B',
            'path': 'models/m2m100',
            'description': 'Base M2M100 model (100 languages)'
        },
        {
            'id': 'anzorq/m2m100_1.2B_ft_ru-kbd_63K',
            'path': 'models/m2m100_ru_kbd',
            'description': 'Fine-tuned Russian → Kabardian'
        },
        {
            'id': 'anzorq/m2m100_1.2B_ft_kbd-ru_63K',
            'path': 'models/m2m100_kbd_ru',
            'description': 'Fine-tuned Kabardian → Russian'
        }
    ]
    
    total = len(models_to_download)
    success_count = 0
    
    for idx, model_info in enumerate(models_to_download, 1):
        print_progress(
            f"Downloading model {idx}/{total}",
            step=idx,
            total=total
        )
        
        if download_model_with_tokenizer(
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
    
    # Final verification
    print_progress("COMPLETION")
    
    if success_count == total:
        print(f"✅ Successfully downloaded {success_count}/{total} models")
        
        if verify_installation():
            print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║                 ✅ INSTALLATION COMPLETE!                 ║
║                                                           ║
║  You can now run the application:                        ║
║                                                           ║
║      python3 app.py                                      ║
║                                                           ║
║  Open browser: http://localhost:5500                     ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
""")
        else:
            print("\n⚠️  Verification found issues. Please run the script again.")
    else:
        print(f"⚠️  Only {success_count}/{total} models downloaded")
        print("Some features may not work")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user (Ctrl+C)")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)