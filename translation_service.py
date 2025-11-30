# translation_service.py (IMPROVED VERSION)
# Translation service for M2M100 models with centralized tokenizer
# License: CC BY-NC 4.0 (Non-Commercial Use Only)

import time
import torch
from transformers import M2M100ForConditionalGeneration
import os
import gc
from tokenizer_manager import tokenizer_manager

class TranslationService:
    """Translation service with centralized tokenizer"""
    
    def __init__(self, device="mps", models_dir="models"):
        self.device = device
        self.models_dir = models_dir
        
        # Centralized tokenizer
        self.tokenizer = None
        
        # Models
        self.m2m100_ru_kbd_model = None
        self.m2m100_kbd_ru_model = None
        self.m2m100_base_model = None
        
        # Memory cleanup before loading
        self._cleanup_memory()
        
        # Loading
        self.load_models()
        self.supported_languages = self._get_supported_languages()
    
    def _cleanup_memory(self):
        """Clear memory cache"""
        gc.collect()
        if self.device == "mps":
            torch.mps.empty_cache()
        elif self.device == "cuda":
            torch.cuda.empty_cache()
        print("🧹 Memory cleared")
    
    def _check_model_files(self, path):
        """Check if model directory contains valid model files"""
        if not os.path.exists(path):
            return False
        
        # Check for modern model formats
        import glob
        model_files = glob.glob(os.path.join(path, "*.safetensors"))
        model_files.extend(glob.glob(os.path.join(path, "pytorch_model*.bin")))
        
        config_files = glob.glob(os.path.join(path, "config.json"))
        
        return len(model_files) > 0 and len(config_files) > 0
    
    def load_models(self):
        """Load models with centralized tokenizer"""
        print("🔥 Loading M2M100 models (float16)...")
        
        # 1. First load the tokenizer (one for all)
        try:
            self.tokenizer = tokenizer_manager.get_tokenizer()
            print("✅ Tokenizer loaded and ready")
        except Exception as e:
            raise RuntimeError(f"❌ Critical tokenizer loading error: {e}")
        
        # 2. Load specialized models with modern format support
        ru_kbd_path = os.path.join(self.models_dir, "m2m100_ru_kbd")
        if self._check_model_files(ru_kbd_path):
            print(f"📥 Loading M2M100 ru→kbd from {ru_kbd_path}...")
            self.m2m100_ru_kbd_model = self._load_model_safe(ru_kbd_path)
            if self.m2m100_ru_kbd_model:
                print("✅ M2M100 ru→kbd loaded (float16)")
        else:
            print(f"⚠️  ru→kbd model not found or incomplete in {ru_kbd_path}")
        
        kbd_ru_path = os.path.join(self.models_dir, "m2m100_kbd_ru")
        if self._check_model_files(kbd_ru_path):
            print(f"📥 Loading M2M100 kbd→ru from {kbd_ru_path}...")
            self.m2m100_kbd_ru_model = self._load_model_safe(kbd_ru_path)
            if self.m2m100_kbd_ru_model:
                print("✅ M2M100 kbd→ru loaded (float16)")
        else:
            print(f"⚠️  kbd→ru model not found or incomplete in {kbd_ru_path}")
        
        # 3. Load base model
        base_path = os.path.join(self.models_dir, "m2m100")
        if self._check_model_files(base_path):
            print(f"📥 Loading base M2M100 from {base_path}...")
            self.m2m100_base_model = self._load_model_safe(base_path)
        else:
            # Load from HuggingFace Hub
            print(f"📥 Loading base M2M100 from HuggingFace...")
            try:
                self.m2m100_base_model = self._load_model_safe("facebook/m2m100_1.2B")
            except Exception as e:
                print(f"⚠️  Failed to load base model from HuggingFace: {e}")
        
        if self.m2m100_base_model:
            print("✅ Base M2M100 loaded (float16)")
        
        # Check that at least one model is loaded
        if not any([self.m2m100_ru_kbd_model, self.m2m100_kbd_ru_model, self.m2m100_base_model]):
            raise RuntimeError("❌ No models loaded! Check models/ folder or run download_models.py")
        
        # Copy tokenizer to all folders (for future use)
        try:
            tokenizer_manager.save_tokenizer_to_all_models()
        except Exception as e:
            print(f"⚠️  Failed to copy tokenizer: {e}")
        
        # Cleanup after loading
        self._cleanup_memory()
    
    def _load_model_safe(self, path):
        """Safe model loading with error handling and modern format support"""
        try:
            model = M2M100ForConditionalGeneration.from_pretrained(
                path,
                torch_dtype=torch.float16,
                low_cpu_mem_usage=True,
                # Additional parameters for better compatibility
                trust_remote_code=False,
                local_files_only=os.path.exists(path)  # Only use local files if path exists
            ).to(self.device)
            model.eval()
            return model
        except Exception as e:
            print(f"❌ Error loading model from {path}: {e}")
            
            # Try alternative loading method
            try:
                print(f"🔄 Trying alternative loading for {path}...")
                model = M2M100ForConditionalGeneration.from_pretrained(
                    path,
                    torch_dtype=torch.float16,
                    local_files_only=True
                ).to(self.device)
                model.eval()
                print(f"✅ Alternative loading successful for {path}")
                return model
            except Exception as e2:
                print(f"❌ Alternative loading also failed: {e2}")
                return None
    
    def _get_supported_languages(self):
        """Returns supported languages by groups"""
        return {
            'slavic': {
                'rus_Cyrl': 'Russian',
                'ukr_Cyrl': 'Ukrainian', 
                'bel_Cyrl': 'Belarusian',
                'lav_Latn': 'Latvian',
            },
            'caucasian_turkic': {
                'kbd_Cyrl': 'Kabardian',
                'kaz_Cyrl': 'Kazakh',
                'kat_Geor': 'Georgian',
                'hye_Armn': 'Armenian',
                'azj_Latn': 'Azerbaijani',
            },
            'turkic': {
                'tur_Latn': 'Turkish',
            },
            'european': {
                'eng_Latn': 'English',
                'deu_Latn': 'German',
                'fra_Latn': 'French',
                'spa_Latn': 'Spanish',
            }
        }
    
    def get_flat_languages(self):
        """Returns flat list of all languages"""
        flat = {}
        for group in self.supported_languages.values():
            flat.update(group)
        return flat
    
    def _convert_lang_code(self, lang_code):
        """Convert language code to M2M100 format"""
        mapping = {
            'rus_Cyrl': 'ru',
            'ukr_Cyrl': 'uk',
            'bel_Cyrl': 'be', 
            'lav_Latn': 'lv',
            'kbd_Cyrl': 'zu',  # Zulu code for Kabardian
            'kaz_Cyrl': 'kk',
            'kat_Geor': 'ka',
            'hye_Armn': 'hy',
            'azj_Latn': 'az',
            'tur_Latn': 'tr',
            'eng_Latn': 'en',
            'deu_Latn': 'de',
            'fra_Latn': 'fr',
            'spa_Latn': 'es',
        }
        return mapping.get(lang_code)
    
    def _translate_with_model(self, text, source_m2m, target_m2m, model):
        """
        Universal translation method with SINGLE tokenizer
        
        IMPORTANT: Uses self.tokenizer for all models
        """
        with torch.no_grad():
            # Set source language
            self.tokenizer.src_lang = source_m2m
            
            # Tokenization
            inputs = self.tokenizer(
                text, 
                return_tensors="pt", 
                padding=True, 
                truncation=True, 
                max_length=512
            ).to(self.device)
            
            # Generation
            generated_tokens = model.generate(
                **inputs,
                forced_bos_token_id=self.tokenizer.get_lang_id(target_m2m),
                max_length=512,
                num_beams=5,
                early_stopping=True,
                repetition_penalty=1.2,
            )
            
            # Decoding
            translation = self.tokenizer.batch_decode(
                generated_tokens, 
                skip_special_tokens=True
            )[0]
            
            return translation
    
    def translate(self, text, source_lang, target_lang):
        """Main translation method with cascade logic"""
        start_time = time.time()
        
        if not text.strip():
            return self._empty_response(source_lang, target_lang)
        
        try:
            source_m2m = self._convert_lang_code(source_lang)
            target_m2m = self._convert_lang_code(target_lang)
            
            if not source_m2m or not target_m2m:
                return self._error_response(
                    f"Language not supported: {source_lang}→{target_lang}",
                    source_lang, target_lang
                )
            
            # CASCADE TRANSLATION LOGIC
            translation = None
            model_name = "unknown"
            cascade_used = False
            
            # 1. DIRECT: Kabardian → Russian
            if source_m2m == 'zu' and target_m2m == 'ru':
                if self.m2m100_kbd_ru_model:
                    print(f"🎯 Direct: kbd→ru")
                    translation = self._translate_with_model(
                        text, source_m2m, target_m2m,
                        self.m2m100_kbd_ru_model
                    )
                    model_name = "m2m100_kbd_ru"
            
            # 2. DIRECT: Russian → Kabardian  
            elif source_m2m == 'ru' and target_m2m == 'zu':
                if self.m2m100_ru_kbd_model:
                    print(f"🎯 Direct: ru→kbd")
                    translation = self._translate_with_model(
                        text, source_m2m, target_m2m,
                        self.m2m100_ru_kbd_model
                    )
                    model_name = "m2m100_ru_kbd"
            
            # 3. CASCADE: Kabardian → Target
            elif source_m2m == 'zu' and target_m2m != 'ru':
                if self.m2m100_kbd_ru_model and self.m2m100_base_model:
                    print(f"🔄 Cascade: kbd→ru→{target_m2m}")
                    
                    russian = self._translate_with_model(
                        text, 'zu', 'ru',
                        self.m2m100_kbd_ru_model
                    )
                    print(f"  ↳ Intermediate: {russian[:50]}...")
                    
                    translation = self._translate_with_model(
                        russian, 'ru', target_m2m,
                        self.m2m100_base_model
                    )
                    model_name = "cascade_kbd→ru→target"
                    cascade_used = True
            
            # 4. CASCADE: Source → Kabardian
            elif source_m2m != 'ru' and target_m2m == 'zu':
                if self.m2m100_base_model and self.m2m100_ru_kbd_model:
                    print(f"🔄 Cascade: {source_m2m}→ru→kbd")
                    
                    russian = self._translate_with_model(
                        text, source_m2m, 'ru',
                        self.m2m100_base_model
                    )
                    print(f"  ↳ Intermediate: {russian[:50]}...")
                    
                    translation = self._translate_with_model(
                        russian, 'ru', 'zu',
                        self.m2m100_ru_kbd_model
                    )
                    model_name = "cascade_source→ru→kbd"
                    cascade_used = True
            
            # 5. DIRECT: Other pairs
            else:
                if self.m2m100_base_model:
                    print(f"🌐 Direct: base ({source_m2m}→{target_m2m})")
                    translation = self._translate_with_model(
                        text, source_m2m, target_m2m,
                        self.m2m100_base_model
                    )
                    model_name = "m2m100_base"
            
            if not translation:
                return self._error_response(
                    f"Failed to translate {source_lang}→{target_lang}",
                    source_lang, target_lang
                )
            
            translation_time = round((time.time() - start_time) * 1000, 2)
            
            cascade_info = " (cascade)" if cascade_used else ""
            print(f"✅ Translation{cascade_info}: '{text[:50]}...' → '{translation[:50]}...' ({translation_time}ms)")
            
            return {
                'translation': translation,
                'direction': f"{source_lang}→{target_lang}",
                'source_lang': source_lang,
                'target_lang': target_lang,
                'time_ms': translation_time,
                'original_length': len(text),
                'translation_length': len(translation),
                'model_used': model_name,
                'cascade': cascade_used
            }
            
        except Exception as e:
            print(f"❌ Translation error: {e}")
            import traceback
            traceback.print_exc()
            return self._error_response(f"Error: {str(e)}", source_lang, target_lang)
    
    def get_supported_languages(self):
        """Returns list of supported languages"""
        return self.supported_languages
    
    def get_languages_by_group(self):
        """Returns languages grouped by categories"""
        groups = {
            'slavic': 'Slavic and Baltic',
            'caucasian_turkic': 'Caucasian and Turkic', 
            'turkic': 'Turkic languages',
            'european': 'European languages'
        }
        
        return {
            'groups': groups,
            'languages': self.supported_languages,
            'current_model': 'm2m100'
        }
    
    def get_tts_speaker(self, lang_code):
        """Determines speaker for language"""
        if lang_code in ['rus_Cyrl', 'ukr_Cyrl', 'bel_Cyrl', 'lav_Latn', 'deu_Latn', 'spa_Latn']:
            return 'ru_eduard'
        
        if lang_code in ['kbd_Cyrl', 'kaz_Cyrl', 'kat_Geor', 'hye_Armn', 'azj_Latn', 'tur_Latn']:
            return 'kbd_eduard'
        
        return None
    
    def health_check(self):
        """Service health check"""
        flat_langs = self.get_flat_languages()
        return {
            'status': 'healthy',
            'device': self.device,
            'tokenizer_loaded': self.tokenizer is not None,
            'models_loaded': {
                'ru_kbd': self.m2m100_ru_kbd_model is not None,
                'kbd_ru': self.m2m100_kbd_ru_model is not None,
                'base': self.m2m100_base_model is not None
            },
            'supported_languages_count': len(flat_langs)
        }
    
    def cleanup(self):
        """Cleanup models"""
        print("🧹 Cleaning translation models...")
        
        if self.m2m100_ru_kbd_model:
            del self.m2m100_ru_kbd_model
            self.m2m100_ru_kbd_model = None
        
        if self.m2m100_kbd_ru_model:
            del self.m2m100_kbd_ru_model
            self.m2m100_kbd_ru_model = None
        
        if self.m2m100_base_model:
            del self.m2m100_base_model
            self.m2m100_base_model = None
        
        self._cleanup_memory()
        print("✅ Models cleaned")
    
    def _empty_response(self, source_lang, target_lang):
        """Empty response"""
        return {
            'translation': '',
            'direction': f"{source_lang}→{target_lang}",
            'source_lang': source_lang,
            'target_lang': target_lang,
            'time_ms': 0,
            'original_length': 0,
            'translation_length': 0
        }
    
    def _error_response(self, error_msg, source_lang, target_lang):
        """Error response"""
        return {
            'translation': f"❌ {error_msg}",
            'direction': f"{source_lang}→{target_lang}",
            'source_lang': source_lang,
            'target_lang': target_lang,
            'time_ms': 0,
            'original_length': 0,
            'translation_length': 0,
            'error': error_msg
        }


# Global instance (will be created in app.py)
translator = None