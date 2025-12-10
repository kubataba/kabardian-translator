# translation_service.py
# Translation service with MarianMT support for Kabardian ↔ Russian
# License: CC BY-NC 4.0 (Non-Commercial Use Only)
# Version 1.0.4

import time
import torch
import os
import gc
import re
from pathlib import Path

class TranslationService:
    """Translation service using MarianMT for Kabardian and M2M100 for others"""
    
    def __init__(self, device="mps", models_dir="models"):
        self.device = device
        self.models_dir = Path(models_dir)
        
        # Initialize services (lazy loaded)
        self._marian_service = None
        self._m2m100_service = None
        
        # Language mapping
        self.supported_languages = self._get_supported_languages()
        
        print(f"🔥 Translation Service initialized on {device}")
        print("   MarianMT will be used ONLY for Kabardian ↔ Russian (direct)")
        print("   M2M100 will be used for ALL other language pairs (including cascades)")
    
    def _filter_latin_words(self, text, target_lang_code):
        """
        Фильтрует латинские слова из текста если целевой язык не использует латиницу.
        Упрощенная версия с сохранением пробелов.
        """
        if not text or not target_lang_code:
            return text
        
        # Языки, которые используют латиницу (не фильтруем для них)
        latin_languages = {'eng_Latn', 'deu_Latn', 'fra_Latn', 'spa_Latn', 
                        'tur_Latn', 'azj_Latn', 'lav_Latn'}
        
        if target_lang_code in latin_languages:
            return text
        
        import re
        
        # Простая логика: разбиваем на слова, проверяем каждое
        # Используем более умное разбиение с сохранением пробелов
        def process_word(match):
            word = match.group(0)
            
            # Быстрые проверки исключений
            if len(word) <= 1:
                return word
            
            # Римские цифры
            roman_numerals = {'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X'}
            if word.upper() in roman_numerals:
                return word
            
            # Содержит цифры
            if any(c.isdigit() for c in word):
                return word
            
            # Проверяем, состоит ли слово только из латинских букв
            if word.isalpha() and all('a' <= c.lower() <= 'z' for c in word):
                # Длинное латинское слово - удаляем
                if len(word) > 1:
                    print(f"🔠 Filtered: '{word}'")
                    return ''  # Удаляем слово
                else:
                    return word  # Короткое слово оставляем
            else:
                return word  # Не латинское слово оставляем
        
        # Обрабатываем слова в тексте
        filtered_text = re.sub(r'\b[a-zA-Z\']+\b', process_word, text)
        
        # Убираем лишние пробелы (могут появиться после удаления слов)
        filtered_text = re.sub(r'\s+', ' ', filtered_text).strip()
        
        return filtered_text

    @property
    def marian_service(self):
        """Lazy loader for MarianMT service"""
        if self._marian_service is None:
            self._marian_service = self._create_marian_service()
        return self._marian_service
    
    @property
    def m2m100_service(self):
        """Lazy loader for M2M100 service"""
        if self._m2m100_service is None:
            self._m2m100_service = self._create_m2m100_service()
        return self._m2m100_service
    
    def _convert_lang_code(self, lang_code):
        """Convert language code to M2M100 format - PUBLIC METHOD"""
        mapping = {
            'rus_Cyrl': 'ru', 'ukr_Cyrl': 'uk', 'bel_Cyrl': 'be',
            'lav_Latn': 'lv', 'kbd_Cyrl': 'zu', 'kaz_Cyrl': 'kk',
            'kat_Geor': 'ka', 'hye_Armn': 'hy', 'azj_Latn': 'az',
            'tur_Latn': 'tr', 'eng_Latn': 'en', 'deu_Latn': 'de',
            'fra_Latn': 'fr', 'spa_Latn': 'es',
        }
        return mapping.get(lang_code)
    
    def _create_marian_service(self):
        """Create MarianMT service with lazy loading - ONLY for kbd↔ru"""
        class LazyMarianService:
            def __init__(self, device, models_dir):
                self.device = device
                self.models_dir = models_dir
                self._ru_kbd_model = None
                self._kbd_ru_model = None
                self._ru_kbd_tokenizer = None
                self._kbd_ru_tokenizer = None
                
                # Special character mapping for Kabardian
                self.kbd_char_mapping = {
                    'Ӏ': 'I', 'ӏ': 'I', 'l': 'I', '|': 'I'
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
                    
                    # Download tokenizer
                    tokenizer = MarianTokenizer.from_pretrained(model_id)
                    tokenizer.save_pretrained(save_path)
                    
                    # Download model
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
                """Russian → Kabardian translation (ONLY direct)"""
                if not text.strip():
                    return {'success': True, 'translation': '', 'time_ms': 0}
                
                start_time = time.time()
                
                try:
                    # Ensure model is loaded
                    if self._ru_kbd_model is None:
                        if not self._load_ru_kbd():
                            return {'success': False, 'error': 'Model not available'}
                    
                    with torch.no_grad():
                        inputs = self._ru_kbd_tokenizer(
                            text, return_tensors="pt", padding=True, truncation=True, max_length=512
                        ).to(self.device)
                        
                        outputs = self._ru_kbd_model.generate(
                            **inputs, max_length=512, num_beams=4, early_stopping=True
                        )
                        
                        translation = self._ru_kbd_tokenizer.decode(outputs[0], skip_special_tokens=True)
                        
                        return {
                            'success': True,
                            'translation': translation,
                            'time_ms': round((time.time() - start_time) * 1000, 2),
                            'model': 'marian_ru_kbd'
                        }
                        
                except Exception as e:
                    return {
                        'success': False,
                        'error': str(e),
                        'translation': f"Error: {str(e)[:100]}",
                        'time_ms': round((time.time() - start_time) * 1000, 2)
                    }
            
            def translate_kbd_to_ru(self, text):
                """Kabardian → Russian translation (ONLY direct)"""
                if not text.strip():
                    return {'success': True, 'translation': '', 'time_ms': 0}
                
                start_time = time.time()
                
                try:
                    # Ensure model is loaded
                    if self._kbd_ru_model is None:
                        if not self._load_kbd_ru():
                            return {'success': False, 'error': 'Model not available'}
                    
                    # Preprocess Kabardian text
                    processed_text = text
                    for old_char, new_char in self.kbd_char_mapping.items():
                        processed_text = processed_text.replace(old_char, new_char)
                    
                    with torch.no_grad():
                        inputs = self._kbd_ru_tokenizer(
                            processed_text, return_tensors="pt", padding=True, truncation=True, max_length=512
                        ).to(self.device)
                        
                        outputs = self._kbd_ru_model.generate(
                            **inputs, max_length=512, num_beams=4, early_stopping=True
                        )
                        
                        translation = self._kbd_ru_tokenizer.decode(outputs[0], skip_special_tokens=True)
                        
                        return {
                            'success': True,
                            'translation': translation,
                            'time_ms': round((time.time() - start_time) * 1000, 2),
                            'model': 'marian_kbd_ru'
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
        
        return LazyMarianService(self.device, self.models_dir)
    
    def _create_m2m100_service(self):
        """Create M2M100 service with full cascade logic"""
        class LazyM2M100Service:
            def __init__(self, device, models_dir, parent_service):
                self.device = device
                self.models_dir = models_dir
                self.parent_service = parent_service  # Reference to parent TranslationService
                self._base_model = None
                self._tokenizer = None
            
            def _convert_lang_code(self, lang_code):
                """Convert language code to M2M100 format - USE PARENT'S METHOD"""
                # Используем метод родительского класса
                return self.parent_service._convert_lang_code(lang_code)
            
            def _check_m2m100_available(self):
                """Проверяет доступность M2M100 модели"""
                path = self.models_dir / "m2m100"
                if not path.exists():
                    return False
                
                # Проверяем что это не пустая папка (есть .no_model маркер)
                no_model_marker = path / ".no_model"
                if no_model_marker.exists():
                    return False
                
                # Проверяем что есть конфиг
                config_path = path / "config.json"
                return config_path.exists()
            
            def _load_base_model(self):
                """Load base M2M100 model"""
                try:
                    from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer
                    
                    path = self.models_dir / "m2m100"
                    if path.exists():
                        print(f"📥 Loading base M2M100 from {path}...")
                        self._tokenizer = M2M100Tokenizer.from_pretrained(path, local_files_only=True)
                        self._base_model = M2M100ForConditionalGeneration.from_pretrained(
                            path,
                            torch_dtype=torch.float32,  # Изменено на float32
                            local_files_only=True
                        ).to(self.device)
                    else:
                        print(f"📥 Loading base M2M100 (418M) from HuggingFace...")
                        # ИЗМЕНЕНИЕ: Используем более легкую модель
                        self._tokenizer = M2M100Tokenizer.from_pretrained("facebook/m2m100_418M")
                        self._base_model = M2M100ForConditionalGeneration.from_pretrained(
                            "facebook/m2m100_418M",
                            torch_dtype=torch.float32
                        ).to(self.device)
                    
                    self._base_model.eval()
                    print(f"✅ Base M2M100 (418M) loaded in float32")
                    return True
                    
                except Exception as e:
                    print(f"❌ Failed to load base M2M100: {e}")
                    return False

            def translate(self, text, source_lang, target_lang):
                """M2M100 translation with cascade logic - ALL translations go here except direct kbd↔ru"""
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
                    
                    # Проверяем доступность M2M100
                    m2m100_available = self._check_m2m100_available()
                    
                    # Если M2M100 недоступна - ОШИБКА для любых переводов
                    # (прямые kbd↔ru обрабатываются в основном методе translate)
                    if not m2m100_available:
                        return self._error_response(
                            f"M2M100 model not available for {source_lang}→{target_lang}",
                            source_lang, target_lang
                        )
                    
                    # ВСЕ переводы через M2M100 (если модель доступна)
                    cascade_used = False
                    translation = None
                    model_name = "m2m100_base"
                    
                    # 1. Cascade: Kabardian → Other (via Russian)
                    if source_m2m == 'zu' and target_m2m != 'ru':
                        print(f"🔄 Cascade: kbd→ru→{target_m2m}")
                        
                        # Get Marian service for kbd→ru (ONLY for first step)
                        marian = self.parent_service.marian_service
                        if marian:
                            # First: kbd→ru (using MarianMT)
                            step1 = marian.translate_kbd_to_ru(text)
                            if step1['success']:
                                intermediate = step1['translation']
                                print(f"  ↳ Intermediate (ru): {intermediate[:50]}...")
                                
                                # Second: ru→target using M2M100
                                if self._base_model is None:
                                    if not self._load_base_model():
                                        raise RuntimeError("Base M2M100 not available")
                                
                                with torch.no_grad():
                                    self._tokenizer.src_lang = 'ru'
                                    inputs = self._tokenizer(
                                        intermediate, 
                                        return_tensors="pt", 
                                        padding=True, 
                                        truncation=True, 
                                        max_length=512
                                    ).to(self.device)
                                    
                                    generated_tokens = self._base_model.generate(
                                        **inputs,
                                        forced_bos_token_id=self._tokenizer.get_lang_id(target_m2m),
                                        max_length=512,
                                        num_beams=5,
                                        early_stopping=True,
                                    )
                                    
                                    translation = self._tokenizer.batch_decode(
                                        generated_tokens, 
                                        skip_special_tokens=True
                                    )[0]
                                
                                cascade_used = True
                                model_name = "cascade_kbd→ru→target"
                    
                    # 2. Cascade: Other → Kabardian (via Russian)
                    elif source_m2m != 'ru' and target_m2m == 'zu':
                        print(f"🔄 Cascade: {source_m2m}→ru→kbd")
                        
                        # First: source→ru using M2M100
                        if self._base_model is None:
                            if not self._load_base_model():
                                raise RuntimeError("Base M2M100 not available")
                        
                        with torch.no_grad():
                            self._tokenizer.src_lang = source_m2m
                            inputs = self._tokenizer(
                                text, 
                                return_tensors="pt", 
                                padding=True, 
                                truncation=True, 
                                max_length=512
                            ).to(self.device)
                            
                            generated_tokens = self._base_model.generate(
                                **inputs,
                                forced_bos_token_id=self._tokenizer.get_lang_id('ru'),
                                max_length=512,
                                num_beams=5,
                                early_stopping=True,
                            )
                            
                            intermediate = self._tokenizer.batch_decode(
                                generated_tokens, 
                                skip_special_tokens=True
                            )[0]
                        
                        print(f"  ↳ Intermediate (ru): {intermediate[:50]}...")
                        
                        # Second: ru→kbd using MarianMT (ONLY for second step)
                        marian = self.parent_service.marian_service
                        if marian:
                            step2 = marian.translate_ru_to_kbd(intermediate)
                            if step2['success']:
                                translation = step2['translation']
                                cascade_used = True
                                model_name = "cascade_source→ru→kbd"
                    
                    # 3. Cascade: Other language → Russian (but not Kabardian)
                    elif source_m2m != 'zu' and target_m2m == 'ru':
                        print(f"🌐 Direct M2M100: {source_m2m}→ru")
                        
                        if self._base_model is None:
                            if not self._load_base_model():
                                raise RuntimeError("Base M2M100 not available")
                        
                        with torch.no_grad():
                            self._tokenizer.src_lang = source_m2m
                            inputs = self._tokenizer(
                                text, 
                                return_tensors="pt", 
                                padding=True, 
                                truncation=True, 
                                max_length=512
                            ).to(self.device)
                            
                            generated_tokens = self._base_model.generate(
                                **inputs,
                                forced_bos_token_id=self._tokenizer.get_lang_id('ru'),
                                max_length=512,
                                num_beams=5,
                                early_stopping=True,
                            )
                            
                            translation = self._tokenizer.batch_decode(
                                generated_tokens, 
                                skip_special_tokens=True
                            )[0]
                    
                    # 4. Cascade: Russian → Other (but not Kabardian)
                    elif source_m2m == 'ru' and target_m2m != 'zu':
                        print(f"🌐 Direct M2M100: ru→{target_m2m}")
                        
                        if self._base_model is None:
                            if not self._load_base_model():
                                raise RuntimeError("Base M2M100 not available")
                        
                        with torch.no_grad():
                            self._tokenizer.src_lang = 'ru'
                            inputs = self._tokenizer(
                                text, 
                                return_tensors="pt", 
                                padding=True, 
                                truncation=True, 
                                max_length=512
                            ).to(self.device)
                            
                            generated_tokens = self._base_model.generate(
                                **inputs,
                                forced_bos_token_id=self._tokenizer.get_lang_id(target_m2m),
                                max_length=512,
                                num_beams=5,
                                early_stopping=True,
                            )
                            
                            translation = self._tokenizer.batch_decode(
                                generated_tokens, 
                                skip_special_tokens=True
                            )[0]
                    
                    # 5. Direct: Other language pairs (no Kabardian, no Russian)
                    elif source_m2m != 'zu' and source_m2m != 'ru' and target_m2m != 'zu' and target_m2m != 'ru':
                        print(f"🌐 Direct M2M100: {source_m2m}→{target_m2m}")
                        
                        if self._base_model is None:
                            if not self._load_base_model():
                                raise RuntimeError("Base M2M100 not available")
                        
                        with torch.no_grad():
                            self._tokenizer.src_lang = source_m2m
                            inputs = self._tokenizer(
                                text, 
                                return_tensors="pt", 
                                padding=True, 
                                truncation=True, 
                                max_length=512
                            ).to(self.device)
                            
                            generated_tokens = self._base_model.generate(
                                **inputs,
                                forced_bos_token_id=self._tokenizer.get_lang_id(target_m2m),
                                max_length=512,
                                num_beams=5,
                                early_stopping=True,
                            )
                            
                            translation = self._tokenizer.batch_decode(
                                generated_tokens, 
                                skip_special_tokens=True
                            )[0]
                    
                    if not translation:
                        return self._error_response(
                            f"Failed to translate {source_lang}→{target_lang}",
                            source_lang, target_lang
                        )
                    
                    # Фильтруем латинские слова для не-латинских языков
                    filtered_translation = self.parent_service._filter_latin_words(translation, target_lang)
                    
                    translation_time = round((time.time() - start_time) * 1000, 2)
                    
                    cascade_info = " (cascade)" if cascade_used else ""
                    print(f"✅ M2M100{cascade_info}: '{text[:50]}...' → '{filtered_translation[:50]}...' ({translation_time}ms)")
                    
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
                    print(f"❌ M2M100 translation error: {e}")
                    import traceback
                    traceback.print_exc()
                    return self._error_response(f"M2M100 Error: {str(e)}", source_lang, target_lang)
            
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
                """Cleanup M2M100 models"""
                self._base_model = None
                self._tokenizer = None
                gc.collect()
                if self.device == "mps":
                    torch.mps.empty_cache()
        
        return LazyM2M100Service(self.device, self.models_dir, self)  # Передаем self как parent_service
    
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
    
    def translate(self, text, source_lang, target_lang):
        """Main translation method - uses MarianMT ONLY for direct Kabardian ↔ Russian"""
        start_time = time.time()
        
        if not text.strip():
            return self._empty_response(source_lang, target_lang)
        
        try:
            # Use MarianMT ONLY for direct Kabardian ↔ Russian
            if (source_lang == 'rus_Cyrl' and target_lang == 'kbd_Cyrl') or \
               (source_lang == 'kbd_Cyrl' and target_lang == 'rus_Cyrl'):
                print("🎯 Using MarianMT (ONLY for direct Kabardian ↔ Russian)")
                if source_lang == 'rus_Cyrl':
                    result = self.marian_service.translate_ru_to_kbd(text)
                else:
                    result = self.marian_service.translate_kbd_to_ru(text)
                return self._format_response(text, result, source_lang, target_lang, start_time)
            
            # ALL other translations use M2M100
            print(f"🌐 Using M2M100 ({source_lang}→{target_lang})")
            result = self.m2m100_service.translate(text, source_lang, target_lang)
            return result
                
        except Exception as e:
            print(f"❌ Translation error: {e}")
            import traceback
            traceback.print_exc()
            return self._error_response(f"Error: {str(e)}", source_lang, target_lang)
    
    def _format_response(self, original, result, source_lang, target_lang, start_time):
        """Format response from MarianMT result"""
        translation_time = round((time.time() - start_time) * 1000, 2)
        
        if result['success']:
            # Фильтруем латинские слова для не-латинских языков
            filtered_translation = self._filter_latin_words(
                result['translation'],
                target_lang
            )
            
            return {
                'translation': filtered_translation,
                'direction': f"{source_lang}→{target_lang}",
                'source_lang': source_lang,
                'target_lang': target_lang,
                'time_ms': translation_time,
                'original_length': len(original),
                'translation_length': len(filtered_translation),
                'model_used': result.get('model', 'marian'),
                'error': None
            }
        else:
            return self._error_response(result.get('error', 'Unknown error'), source_lang, target_lang)
    
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
            'current_model': 'hybrid (MarianMT ONLY for kbd↔ru, M2M100 for everything else)'
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
        # Try to check M2M100 availability
        m2m100_available = False
        try:
            if self._m2m100_service:
                # Используем метод из M2M100 сервиса
                m2m100_available = self._m2m100_service._check_m2m100_available()
        except:
            pass
        
        return {
            'status': 'healthy',
            'device': self.device,
            'marian_available': self._marian_service is not None,
            'm2m100_available': m2m100_available,
            'supported_languages_count': len(self.get_flat_languages())
        }
    
    def get_flat_languages(self):
        """Returns flat list of all languages"""
        flat = {}
        for group in self.supported_languages.values():
            flat.update(group)
        return flat
    
    def cleanup(self):
        """Cleanup all models"""
        print("🧹 Cleaning translation models...")
        
        if self._marian_service:
            self._marian_service.cleanup()
            self._marian_service = None
        
        if self._m2m100_service:
            self._m2m100_service.cleanup()
            self._m2m100_service = None
        
        gc.collect()
        if self.device == "mps":
            torch.mps.empty_cache()
        elif self.device == "cuda":
            torch.cuda.empty_cache()
        
        print("✅ All models cleaned")
    
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


# Global instance for compatibility
translator = None