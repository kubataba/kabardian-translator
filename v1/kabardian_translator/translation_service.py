# translation_service.py
# Translation service with MarianMT support for Kabardian ↔ Russian
# License: CC BY-NC 4.0 (Non-Commercial Use Only)
# Version 2.0.0 - Migrated from M2M100 to NLLB-200

import time
import torch
import os
import gc
import re
from pathlib import Path

class TranslationService:
    """Translation service using MarianMT for Kabardian and NLLB-200 for others"""
    
    # Translation presets for ru↔kbd
    TRANSLATION_PRESETS = {
        "ru_kbd": {"name": "📖 RU KBD", "num_beams": 4, "min_length": 20, "max_length": 256, "length_penalty": 1.5},
        "kbd_ru": {"name": "🌐 KBD RU", "num_beams": 4, "min_length": 20, "max_length": 256, "length_penalty": 0.9},
    }
    
    def __init__(self, device="mps", models_dir="models"):
        self.device = device
        self.models_dir = Path(models_dir)
        
        # Initialize services (lazy loaded)
        self._marian_service = None
        self._nllb_service = None
        
        # Language mapping
        self.supported_languages = self._get_supported_languages()
        
        print(f"🔥 Translation Service initialized on {device}")
        print("   MarianMT will be used ONLY for Kabardian ↔ Russian (direct)")
        print("   NLLB-200 will be used for ALL other language pairs (including cascades)")
        print("   ✨ Sentence chunking enabled for all translations")
        print("   ⚙️ Translation presets enabled for ru↔kbd")

    def _split_into_sentences(self, text):
        """Split text into sentences based on punctuation marks"""
        if not text or not text.strip():
            return []
        
        # Pattern to split on sentence-ending punctuation (.!?…) followed by whitespace or end of string
        # Parentheses capture the punctuation marks
        sentence_pattern = r'([.!?…]+)(?:\s+|$)'
        parts = re.split(sentence_pattern, text)
        
        sentences = []
        current = ""
        
        # Reconstruct sentences with their original punctuation
        for i, part in enumerate(parts):
            if not part:
                continue
            
            # Check if this part is punctuation marks
            if re.match(r'^[.!?…]+$', part):
                # Add punctuation to current sentence
                current += part
                # If we have content, save this as a complete sentence
                if current.strip():
                    sentences.append(current.strip())
                    current = ""
            else:
                # This is text content
                current += part
        
        # Handle any remaining content
        if current.strip():
            sentences.append(current.strip())
        
        # Filter out empty strings while preserving all punctuation
        sentences = [s for s in sentences if s.strip()]
        return sentences

    def _filter_latin_words(self, text, target_lang_code):
        """Filter Latin words from text if target language doesn't use Latin script"""
        if not text or not target_lang_code:
            return text
        
        latin_languages = {'eng_Latn', 'deu_Latn', 'fra_Latn', 'spa_Latn', 
                        'tur_Latn', 'azj_Latn', 'lvs_Latn'}
        
        if target_lang_code in latin_languages:
            return text
        
        def process_word(match):
            word = match.group(0)
            
            if len(word) <= 1:
                return word
            
            roman_numerals = {'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X'}
            if word.upper() in roman_numerals:
                return word
            
            if any(c.isdigit() for c in word):
                return word
            
            if word.isalpha() and all('a' <= c.lower() <= 'z' for c in word):
                if len(word) > 1:
                    print(f"🔍 Filtered: '{word}'")
                    return ''
                else:
                    return word
            else:
                return word
        
        filtered_text = re.sub(r'\b[a-zA-Z\']+\b', process_word, text)
        filtered_text = re.sub(r'\s+', ' ', filtered_text).strip()
        
        return filtered_text

    @property
    def marian_service(self):
        """Lazy loader for MarianMT service"""
        if self._marian_service is None:
            self._marian_service = self._create_marian_service()
        return self._marian_service
    
    @property
    def nllb_service(self):
        """Lazy loader for NLLB-200 service"""
        if self._nllb_service is None:
            self._nllb_service = self._create_nllb_service()
        return self._nllb_service
    
    def _convert_lang_code(self, lang_code):
        """Convert language code to NLLB-200 format"""
        mapping = {
            'rus_Cyrl': 'rus_Cyrl', 'ukr_Cyrl': 'ukr_Cyrl', 'bel_Cyrl': 'bel_Cyrl',
            'lvs_Latn': 'lvs_Latn', 'kbd_Cyrl': 'kbd_Cyrl', 'kaz_Cyrl': 'kaz_Cyrl',
            'bak_Cyrl': 'bak_Cyrl', 'kir_Cyrl': 'kir_Cyrl',
            'kat_Geor': 'kat_Geor', 'hye_Armn': 'hye_Armn', 'azj_Latn': 'azj_Latn',
            'tur_Latn': 'tur_Latn', 'eng_Latn': 'eng_Latn', 'deu_Latn': 'deu_Latn',
            'fra_Latn': 'fra_Latn', 'spa_Latn': 'spa_Latn',
        }
        return mapping.get(lang_code, lang_code)
    
    def _create_marian_service(self):
        """Create MarianMT service with lazy loading - ONLY for kbd↔ru"""
        class LazyMarianService:
            def __init__(self, device, models_dir, presets):
                self.device = device
                self.models_dir = models_dir
                self.presets = presets
                self._ru_kbd_model = None
                self._kbd_ru_model = None
                self._ru_kbd_tokenizer = None
                self._kbd_ru_tokenizer = None
                
                self.kbd_char_mapping = {
                    'Ӏ': 'I', 'Ӏ': 'I', 'l': 'I', '|': 'I'
                }
            
            def _download_model_if_needed(self, model_id, save_path):
                """Download model if not present"""
                from transformers import MarianMTModel, MarianTokenizer
                
                if save_path.exists():
                    print(f"📁 MarianMT model found: {save_path}")
                    return True
                
                print(f"📥 Downloading MarianMT {model_id}...")
                try:
                    save_path.mkdir(parents=True, exist_ok=True)
                    tokenizer = MarianTokenizer.from_pretrained(model_id)
                    tokenizer.save_pretrained(save_path)
                    model = MarianMTModel.from_pretrained(model_id)
                    model.save_pretrained(save_path)
                    print(f"✅ MarianMT model downloaded to {save_path}")
                    return True
                except Exception as e:
                    print(f"❌ Failed to download MarianMT: {e}")
                    if save_path.exists():
                        import shutil
                        shutil.rmtree(save_path)
                    return False
            
            def _load_ru_kbd(self):
                """Load Russian → Kabardian model"""
                try:
                    from transformers import MarianMTModel, MarianTokenizer
                    
                    path = self.models_dir / "marian_ru_kbd"
                    if not self._download_model_if_needed("kubataba/ru-kbd-opus", path):
                        raise RuntimeError("Failed to download ru→kbd")
                    
                    self._ru_kbd_tokenizer = MarianTokenizer.from_pretrained(path, local_files_only=True)
                    self._ru_kbd_model = MarianMTModel.from_pretrained(
                        path,
                        torch_dtype=torch.float16 if self.device in ["mps", "cuda"] else torch.float32,
                        local_files_only=True
                    ).to(self.device)
                    self._ru_kbd_model.eval()
                    return True
                except Exception as e:
                    print(f"❌ Failed to load MarianMT ru→kbd: {e}")
                    return False
            
            def _load_kbd_ru(self):
                """Load Kabardian → Russian model"""
                try:
                    from transformers import MarianMTModel, MarianTokenizer
                    
                    path = self.models_dir / "marian_kbd_ru"
                    if not self._download_model_if_needed("kubataba/kbd-ru-opus", path):
                        raise RuntimeError("Failed to download kbd→ru")
                    
                    self._kbd_ru_tokenizer = MarianTokenizer.from_pretrained(path, local_files_only=True)
                    self._kbd_ru_model = MarianMTModel.from_pretrained(
                        path,
                        torch_dtype=torch.float16 if self.device in ["mps", "cuda"] else torch.float32,
                        local_files_only=True
                    ).to(self.device)
                    self._kbd_ru_model.eval()
                    return True
                except Exception as e:
                    print(f"❌ Failed to load MarianMT kbd→ru: {e}")
                    return False

            def translate_ru_to_kbd(self, text):
                """Russian → Kabardian translation with presets"""
                if not text.strip():
                    return {'success': True, 'translation': '', 'time_ms': 0}
                
                start_time = time.time()
                
                try:
                    if self._ru_kbd_model is None:
                        if not self._load_ru_kbd():
                            return {'success': False, 'error': 'Model not available'}
                    
                    preset = self.presets.get("ru_kbd", {})
                    num_beams = preset.get("num_beams", 4)
                    min_length = preset.get("min_length", 20)
                    max_length = preset.get("max_length", 256)
                    length_penalty = preset.get("length_penalty", 1.5)
                    
                    print(f"⚙️ Using preset {preset.get('name', 'ru_kbd')}: beams={num_beams}, length_penalty={length_penalty}")
                    
                    with torch.no_grad():
                        inputs = self._ru_kbd_tokenizer(
                            text, return_tensors="pt", padding=True, truncation=True, max_length=512
                        ).to(self.device)
                        
                        outputs = self._ru_kbd_model.generate(
                            **inputs,
                            max_length=max_length,
                            min_length=min(min_length, len(text.split())),
                            num_beams=num_beams,
                            length_penalty=length_penalty,
                            early_stopping=True
                        )
                        
                        translation = self._ru_kbd_tokenizer.decode(outputs[0], skip_special_tokens=True)
                        
                        # Extract and preserve original punctuation from source text
                        # Check if source text ends with any punctuation marks
                        if text.rstrip().endswith(('.', '!', '?', '...', '…')):
                            # Get the trimmed source text without trailing spaces
                            original_trimmed = text.rstrip()
                            
                            # Find all consecutive punctuation characters at the end
                            last_punctuation = ''
                            for char in reversed(original_trimmed):
                                if char in '.!?…':
                                    # Prepend to maintain original order
                                    last_punctuation = char + last_punctuation
                                else:
                                    # Stop when we encounter non-punctuation
                                    break
                            
                            # Remove trailing spaces from translation and add punctuation
                            translation = translation.rstrip()
                            
                            # Add punctuation only if translation doesn't already end with it
                            if last_punctuation and not translation.endswith(last_punctuation):
                                translation += last_punctuation
                        
                        # Character mapping for Cyrillic compatibility
                        reverse_mapping = {'I': 'Ӏ', 'l': 'Ӏ', '|': 'Ӏ', 'Ӏ': 'Ӏ'}
                        for latin_char, cyrillic_char in reverse_mapping.items():
                            translation = translation.replace(latin_char, cyrillic_char)
                        
                        return {
                            'success': True,
                            'translation': translation,
                            'time_ms': round((time.time() - start_time) * 1000, 2),
                            'model': 'marian_ru_kbd',
                            'preset': preset.get('name')
                        }
                except Exception as e:
                    return {
                        'success': False,
                        'error': str(e),
                        'translation': f"Error: {str(e)[:100]}",
                        'time_ms': round((time.time() - start_time) * 1000, 2)
                    }

            def translate_kbd_to_ru(self, text):
                """Kabardian → Russian translation with presets"""
                if not text.strip():
                    return {'success': True, 'translation': '', 'time_ms': 0}
                
                start_time = time.time()
                
                try:
                    if self._kbd_ru_model is None:
                        if not self._load_kbd_ru():
                            return {'success': False, 'error': 'Model not available'}
                    
                    processed_text = text
                    for old_char, new_char in self.kbd_char_mapping.items():
                        processed_text = processed_text.replace(old_char, new_char)
                    
                    preset = self.presets.get("kbd_ru", {})
                    num_beams = preset.get("num_beams", 4)
                    min_length = preset.get("min_length", 20)
                    max_length = preset.get("max_length", 256)
                    length_penalty = preset.get("length_penalty", 0.9)
                    
                    print(f"⚙️ Using preset {preset.get('name', 'kbd_ru')}: beams={num_beams}, length_penalty={length_penalty}")
                    
                    with torch.no_grad():
                        inputs = self._kbd_ru_tokenizer(
                            processed_text, return_tensors="pt", padding=True, truncation=True, max_length=512
                        ).to(self.device)
                        
                        outputs = self._kbd_ru_model.generate(
                            **inputs,
                            max_length=max_length,
                            min_length=min(min_length, len(processed_text.split())),
                            num_beams=num_beams,
                            length_penalty=length_penalty,
                            early_stopping=True
                        )
                        
                        translation = self._kbd_ru_tokenizer.decode(outputs[0], skip_special_tokens=True)
                        
                        return {
                            'success': True,
                            'translation': translation,
                            'time_ms': round((time.time() - start_time) * 1000, 2),
                            'model': 'marian_kbd_ru',
                            'preset': preset.get('name')
                        }
                except Exception as e:
                    return {
                        'success': False,
                        'error': str(e),
                        'translation': f"Error: {str(e)[:100]}",
                        'time_ms': round((time.time() - start_time) * 1000, 2)
                    }

            def cleanup(self):
                """Cleanup MarianMT models"""
                self._ru_kbd_model = None
                self._kbd_ru_model = None
                self._ru_kbd_tokenizer = None
                self._kbd_ru_tokenizer = None
                gc.collect()
                if self.device == "mps":
                    torch.mps.empty_cache()
                elif self.device == "cuda":
                    torch.cuda.empty_cache()
        
        return LazyMarianService(self.device, self.models_dir, self.TRANSLATION_PRESETS)
    
    def _create_nllb_service(self):
        """Create NLLB-200 service with full cascade logic"""
        class LazyNLLBService:
            def __init__(self, device, models_dir, parent_service):
                self.device = device
                self.models_dir = models_dir
                self.parent_service = parent_service
                self._base_model = None
                self._tokenizer = None
            
            def _convert_lang_code(self, lang_code):
                return self.parent_service._convert_lang_code(lang_code)
            
            def _check_nllb_available(self):
                path = self.models_dir / "nllb200"
                if not path.exists():
                    return False
                no_model_marker = path / ".no_model"
                if no_model_marker.exists():
                    return False
                config_path = path / "config.json"
                return config_path.exists()
            
            def _load_base_model(self):
                """Load base NLLB-200 model"""
                try:
                    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
                    
                    path = self.models_dir / "nllb200"
                    if path.exists():
                        print(f"🔥 Loading base NLLB-200 from {path}...")
                        self._tokenizer = AutoTokenizer.from_pretrained(path, local_files_only=True)
                        self._base_model = AutoModelForSeq2SeqLM.from_pretrained(
                            path, torch_dtype=torch.float32, local_files_only=True
                        ).to(self.device)
                    else:
                        print(f"🔥 Loading base NLLB-200 (600M) from HuggingFace...")
                        self._tokenizer = AutoTokenizer.from_pretrained("facebook/nllb-200-distilled-600M")
                        self._base_model = AutoModelForSeq2SeqLM.from_pretrained(
                            "facebook/nllb-200-distilled-600M", torch_dtype=torch.float32
                        ).to(self.device)
                    
                    self._base_model.eval()
                    print(f"✅ Base NLLB-200 (600M) loaded in float32")
                    return True
                except Exception as e:
                    print(f"❌ Failed to load base NLLB-200: {e}")
                    return False

            def translate(self, text, source_lang, target_lang):
                """NLLB-200 translation with cascade logic"""
                start_time = time.time()
                
                if not text.strip():
                    return self._empty_response(source_lang, target_lang)
                
                try:
                    source_nllb = self._convert_lang_code(source_lang)
                    target_nllb = self._convert_lang_code(target_lang)
                    
                    if not source_nllb or not target_nllb:
                        return self._error_response(
                            f"Language not supported: {source_lang}→{target_lang}",
                            source_lang, target_lang
                        )
                    
                    if not self._check_nllb_available():
                        return self._error_response(
                            f"NLLB-200 model not available",
                            source_lang, target_lang
                        )
                    
                    cascade_used = False
                    translation = None
                    model_name = "nllb200_base"
                    
                    # Cascade: kbd → other (via ru)
                    if source_nllb == 'kbd_Cyrl' and target_nllb != 'rus_Cyrl':
                        print(f"🔄 Cascade: kbd→ru→{target_nllb}")
                        marian = self.parent_service.marian_service
                        if marian:
                            step1 = marian.translate_kbd_to_ru(text)
                            if step1['success']:
                                intermediate = step1['translation']
                                print(f"  ↳ Intermediate (ru): {intermediate[:50]}...")
                                
                                if self._base_model is None:
                                    if not self._load_base_model():
                                        raise RuntimeError("Base NLLB-200 not available")
                                
                                with torch.no_grad():
                                    self._tokenizer.src_lang = 'rus_Cyrl'
                                    inputs = self._tokenizer(
                                        intermediate, return_tensors="pt", padding=True, 
                                        truncation=True, max_length=512
                                    ).to(self.device)
                                    
                                    forced_token_id = self._tokenizer.convert_tokens_to_ids(target_nllb)
                                    
                                    generated_tokens = self._base_model.generate(
                                        **inputs,
                                        forced_bos_token_id=forced_token_id,
                                        max_length=512, num_beams=5, early_stopping=True,
                                    )
                                    
                                    translation = self._tokenizer.batch_decode(
                                        generated_tokens, skip_special_tokens=True
                                    )[0]
                                
                                cascade_used = True
                                model_name = "cascade_kbd→ru→target"
                    
                    # Cascade: other → kbd (via ru)
                    elif source_nllb != 'rus_Cyrl' and target_nllb == 'kbd_Cyrl':
                        print(f"🔄 Cascade: {source_nllb}→ru→kbd")
                        
                        if self._base_model is None:
                            if not self._load_base_model():
                                raise RuntimeError("Base NLLB-200 not available")
                        
                        with torch.no_grad():
                            self._tokenizer.src_lang = source_nllb
                            inputs = self._tokenizer(
                                text, return_tensors="pt", padding=True, 
                                truncation=True, max_length=512
                            ).to(self.device)
                            
                            forced_token_id = self._tokenizer.convert_tokens_to_ids('rus_Cyrl')
                            
                            generated_tokens = self._base_model.generate(
                                **inputs,
                                forced_bos_token_id=forced_token_id,
                                max_length=512, num_beams=5, early_stopping=True,
                            )
                            
                            intermediate = self._tokenizer.batch_decode(
                                generated_tokens, skip_special_tokens=True
                            )[0]
                        
                        print(f"  ↳ Intermediate (ru): {intermediate[:50]}...")
                        
                        marian = self.parent_service.marian_service
                        if marian:
                            step2 = marian.translate_ru_to_kbd(intermediate)
                            if step2['success']:
                                translation = step2['translation']
                                cascade_used = True
                                model_name = "cascade_source→ru→kbd"
                    
                    # Direct NLLB-200
                    else:
                        print(f"🌐 Direct NLLB-200: {source_nllb}→{target_nllb}")
                        
                        if self._base_model is None:
                            if not self._load_base_model():
                                raise RuntimeError("Base NLLB-200 not available")
                        
                        with torch.no_grad():
                            self._tokenizer.src_lang = source_nllb
                            inputs = self._tokenizer(
                                text, return_tensors="pt", padding=True, 
                                truncation=True, max_length=512
                            ).to(self.device)
                            
                            forced_token_id = self._tokenizer.convert_tokens_to_ids(target_nllb)
                            
                            generated_tokens = self._base_model.generate(
                                **inputs,
                                forced_bos_token_id=forced_token_id,
                                max_length=512, num_beams=5, early_stopping=True,
                            )
                            
                            translation = self._tokenizer.batch_decode(
                                generated_tokens, skip_special_tokens=True
                            )[0]
                    
                    if not translation:
                        return self._error_response(
                            f"Failed to translate",
                            source_lang, target_lang
                        )
                    
                    filtered_translation = self.parent_service._filter_latin_words(translation, target_lang)
                    translation_time = round((time.time() - start_time) * 1000, 2)
                    
                    cascade_info = " (cascade)" if cascade_used else ""
                    print(f"✅ NLLB-200{cascade_info}: '{text[:50]}...' → '{filtered_translation[:50]}...' ({translation_time}ms)")
                    
                    return {
                        'translation': filtered_translation,
                        'direction': f"{source_lang}→{target_lang}",
                        'source_lang': source_lang,
                        'target_lang': target_lang,
                        'time_ms': translation_time,
                        'original_length': len(text),
                        'translation_length': len(filtered_translation),
                        'model_used': model_name,
                        'cascade': cascade_used,
                        'error': None
                    }
                    
                except Exception as e:
                    print(f"❌ NLLB-200 translation error: {e}")
                    import traceback
                    traceback.print_exc()
                    return self._error_response(f"NLLB-200 Error: {str(e)}", source_lang, target_lang)
            
            def _empty_response(self, source_lang, target_lang):
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
            
            def cleanup(self):
                """Cleanup NLLB-200 models"""
                self._base_model = None
                self._tokenizer = None
                gc.collect()
                if self.device == "mps":
                    torch.mps.empty_cache()
        
        return LazyNLLBService(self.device, self.models_dir, self)
    
    def _get_supported_languages(self):
        """Returns supported languages by groups"""
        return {
            'slavic': {
                'rus_Cyrl': 'Russian',
                'ukr_Cyrl': 'Ukrainian', 
                'bel_Cyrl': 'Belarusian',
                'lvs_Latn': 'Latvian',
            },
            'caucasian_turkic': {
                'kbd_Cyrl': 'Kabardian',
                'kaz_Cyrl': 'Kazakh',
                'bak_Cyrl': 'Bashkir',
                'kir_Cyrl': 'Kyrgyz',
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
    
    def translate(self, text, source_lang, target_lang):
        """Main translation method with sentence chunking"""
        start_time = time.time()
        
        if not text.strip():
            return self._empty_response(source_lang, target_lang)
        
        try:
            # Split text into sentences
            sentences = self._split_into_sentences(text)
            
            if not sentences:
                return self._empty_response(source_lang, target_lang)
            
            print(f"📄 Split into {len(sentences)} sentence(s)")
            for i, sent in enumerate(sentences, 1):
                print(f"  {i}. '{sent[:50]}...'")
            
            # Translate each sentence
            translated_sentences = []
            total_chunk_time = 0
            cascade_used = False
            model_used = None
            
            for i, sentence in enumerate(sentences, 1):
                print(f"\n🔄 Translating chunk {i}/{len(sentences)}: '{sentence[:50]}...'")
                
                chunk_result = self._translate_single_chunk(sentence, source_lang, target_lang)
                
                if chunk_result.get('error'):
                    return chunk_result
                
                translated_sentences.append(chunk_result['translation'])
                total_chunk_time += chunk_result['time_ms']
                
                if chunk_result.get('cascade'):
                    cascade_used = True
                
                if model_used is None:
                    model_used = chunk_result.get('model_used', 'unknown')
                
                print(f"  ✅ Chunk {i} done: '{chunk_result['translation'][:50]}...' ({chunk_result['time_ms']}ms)")
            
            # Combine all translated sentences
            final_translation = ' '.join(translated_sentences)
            filtered_translation = self._filter_latin_words(final_translation, target_lang)
            total_time = round((time.time() - start_time) * 1000, 2)
            
            print(f"\n✅ All chunks translated in {total_time}ms (processing: {total_chunk_time}ms)")
            print(f"   Final: '{filtered_translation[:100]}...'")
            
            return {
                'translation': filtered_translation,
                'direction': f"{source_lang}→{target_lang}",
                'source_lang': source_lang,
                'target_lang': target_lang,
                'time_ms': total_time,
                'original_length': len(text),
                'translation_length': len(filtered_translation),
                'model_used': model_used,
                'cascade': cascade_used,
                'chunks_count': len(sentences),
                'error': None
            }
                
        except Exception as e:
            print(f"❌ Translation error: {e}")
            import traceback
            traceback.print_exc()
            return self._error_response(f"Error: {str(e)}", source_lang, target_lang)
    
    def _translate_single_chunk(self, text, source_lang, target_lang):
        """Translate a single chunk (sentence)"""
        if not text.strip():
            return {'translation': '', 'time_ms': 0, 'error': None}
        
        try:
            # Use MarianMT ONLY for direct kbd↔ru
            if (source_lang == 'rus_Cyrl' and target_lang == 'kbd_Cyrl') or \
               (source_lang == 'kbd_Cyrl' and target_lang == 'rus_Cyrl'):
                print("🎯 Using MarianMT (with presets)")
                if source_lang == 'rus_Cyrl':
                    result = self.marian_service.translate_ru_to_kbd(text)
                else:
                    result = self.marian_service.translate_kbd_to_ru(text)
                
                if result['success']:
                    return {
                        'translation': result['translation'],
                        'time_ms': result['time_ms'],
                        'model_used': result.get('model', 'marian'),
                        'preset': result.get('preset'),
                        'error': None
                    }
                else:
                    return {
                        'translation': '',
                        'time_ms': 0,
                        'error': result.get('error', 'Unknown error')
                    }
            
            # ALL other translations use NLLB-200
            print(f"🌐 Using NLLB-200 (default params)")
            result = self.nllb_service.translate(text, source_lang, target_lang)
            return result
                
        except Exception as e:
            print(f"❌ Chunk translation error: {e}")
            return {
                'translation': '',
                'time_ms': 0,
                'error': str(e)
            }
    
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
            'current_model': 'hybrid (MarianMT with presets for kbd↔ru, NLLB-200 for everything else)',
            'features': {
                'sentence_chunking': True,
                'translation_presets': True,
                'cascade_translation': True
            }
        }
    
    def get_flat_languages(self):
        """Returns flat list of all languages"""
        flat = {}
        for group in self.supported_languages.values():
            flat.update(group)
        return flat
    
    def get_tts_speaker(self, lang_code):
        """Determines speaker for language"""
        if lang_code in ['rus_Cyrl', 'ukr_Cyrl', 'bel_Cyrl', 'lvs_Latn', 'deu_Latn', 'spa_Latn']:
            return 'ru_eduard'
        
        if lang_code in ['kbd_Cyrl', 'kaz_Cyrl', 'bak_Cyrl', 'kir_Cyrl', 'kat_Geor', 'hye_Armn', 'azj_Latn', 'tur_Latn']:
            return 'kbd_eduard'
        
        return None
    
    def health_check(self):
        """Service health check"""
        nllb_available = False
        try:
            if self._nllb_service:
                nllb_available = self._nllb_service._check_nllb_available()
        except:
            pass
        
        return {
            'status': 'healthy',
            'device': self.device,
            'marian_available': self._marian_service is not None,
            'nllb_available': nllb_available,
            'supported_languages_count': len(self.get_flat_languages()),
            'features': {
                'sentence_chunking': True,
                'translation_presets_ru_kbd': list(self.TRANSLATION_PRESETS.keys()),
                'cascade_translation': True
            }
        }
    
    def _empty_response(self, source_lang, target_lang):
        """Empty response"""
        return {
            'translation': '',
            'direction': f"{source_lang}→{target_lang}",
            'source_lang': source_lang,
            'target_lang': target_lang,
            'time_ms': 0,
            'original_length': 0,
            'translation_length': 0,
            'chunks_count': 0
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
    
    def cleanup(self):
        """Cleanup all models"""
        print("🧹 Cleaning translation models...")
        
        if self._marian_service:
            self._marian_service.cleanup()
            self._marian_service = None
        
        if self._nllb_service:
            self._nllb_service.cleanup()
            self._nllb_service = None
        
        gc.collect()
        if self.device == "mps":
            torch.mps.empty_cache()
        elif self.device == "cuda":
            torch.cuda.empty_cache()
        
        print("✅ All models cleaned")


# Global instance for compatibility
translator = None