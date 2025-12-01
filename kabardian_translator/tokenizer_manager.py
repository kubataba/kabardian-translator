# tokenizer_manager.py
# Centralized tokenizer management for M2M100 models
# License: CC BY-NC 4.0 (Non-Commercial Use Only)

from transformers import M2M100Tokenizer
import os
import glob

class TokenizerManager:
    """
    Centralized tokenizer management
    
    CRITICAL: All M2M100 models (base and fine-tuned) use the 
    SAME tokenizer from the base facebook/m2m100_1.2B model.
    """
    
    def __init__(self, models_dir="models"):
        self.models_dir = models_dir
        self.base_tokenizer = None
        self._tokenizer_loaded = False
    
    def _find_tokenizer_path(self, model_path):
        """
        Find tokenizer files in model directory with modern format support
        """
        if not os.path.exists(model_path):
            return None
            
        # Check for tokenizer files with modern patterns
        tokenizer_files = [
            "tokenizer_config.json",
            "sentencepiece.bpe.model", 
            "vocab.json",
            "special_tokens_map.json",
            "added_tokens.json"
        ]
        
        # Check if directory contains tokenizer files
        found_files = []
        for file_pattern in tokenizer_files:
            matches = glob.glob(os.path.join(model_path, file_pattern))
            found_files.extend(matches)
        
        if found_files:
            print(f"  📁 Found tokenizer files in: {model_path}")
            return model_path
        return None
    
    def load_tokenizer(self):
        """
        Load base tokenizer once for all models
        
        Strategy: Use base tokenizer for maximum compatibility
        Fine-tuned models may not include tokenizers on HuggingFace
        """
        if self._tokenizer_loaded:
            return self.base_tokenizer
        
        print("📥 Loading M2M100 base tokenizer...")
        
        # Priority order for tokenizer loading:
        # 1. From local base model (modern format)
        # 2. From any local model (they all use the same tokenizer)  
        # 3. From HuggingFace Hub
        
        potential_paths = [
            os.path.join(self.models_dir, "m2m100"),           # Base model
            os.path.join(self.models_dir, "m2m100_ru_kbd"),    # ru→kbd
            os.path.join(self.models_dir, "m2m100_kbd_ru"),    # kbd→ru
            "facebook/m2m100_1.2B"                             # HuggingFace Hub
        ]
        
        for path in potential_paths:
            try:
                # For local paths, check if tokenizer files exist
                if os.path.exists(path):
                    tokenizer_path = self._find_tokenizer_path(path)
                    if tokenizer_path:
                        self.base_tokenizer = M2M100Tokenizer.from_pretrained(tokenizer_path)
                        self._tokenizer_loaded = True
                        print(f"✅ Tokenizer loaded locally: {tokenizer_path}")
                        return self.base_tokenizer
                else:
                    # For HuggingFace paths, try direct loading
                    self.base_tokenizer = M2M100Tokenizer.from_pretrained(path)
                    self._tokenizer_loaded = True
                    print(f"✅ Tokenizer loaded from HuggingFace: {path}")
                    return self.base_tokenizer
                    
            except Exception as e:
                print(f"⚠️  Failed to load tokenizer from {path}: {e}")
                continue
        
        raise RuntimeError(
            "❌ Could not load tokenizer from any source!\n"
            "Please ensure at least one model is downloaded locally, "
            "or you have access to HuggingFace Hub."
        )
    
    def get_tokenizer(self):
        """
        Return loaded tokenizer (load if necessary)
        """
        if not self._tokenizer_loaded:
            self.load_tokenizer()
        return self.base_tokenizer
    
    def save_tokenizer_to_all_models(self):
        """
        Copy base tokenizer to all model directories
        
        IMPORTANT: Call this after model downloads to ensure
        all model directories have the tokenizer files
        """
        if not self._tokenizer_loaded:
            self.load_tokenizer()
        
        model_dirs = [
            os.path.join(self.models_dir, "m2m100"),
            os.path.join(self.models_dir, "m2m100_ru_kbd"), 
            os.path.join(self.models_dir, "m2m100_kbd_ru")
        ]
        
        print("\n📋 Copying tokenizer to all models...")
        
        for model_dir in model_dirs:
            if os.path.exists(model_dir):
                try:
                    # Check if tokenizer already exists
                    if not self._find_tokenizer_path(model_dir):
                        self.base_tokenizer.save_pretrained(model_dir)
                        print(f"  ✅ Tokenizer saved to {model_dir}")
                    else:
                        print(f"  ⏭️  Tokenizer already exists in {model_dir}")
                except Exception as e:
                    print(f"  ⚠️  Error saving to {model_dir}: {e}")
        
        print("✅ Tokenizer synchronization completed")


# Global instance
tokenizer_manager = TokenizerManager()