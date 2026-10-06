# tts_service.py
# Text-to-Speech service using Silero TTS with lazy loading, transliteration and accentuation
# Version 2.0.0 Silero Accentors integration, adding Bashkir and Kyrgyz languages
# License: CC BY-NC 4.0 (Non-Commercial Use Only)

import torch
import numpy as np
import soundfile as sf
import os
import tempfile
import uuid
import logging
import re
from threading import Lock
from pathlib import Path
import gc

# ИСПРАВЛЕННЫЙ ИМПОРТ
try:
    from .transliterator import transliterator
except ImportError:
    # Fallback for direct execution
    from transliterator import transliterator

# Setup logging
logger = logging.getLogger(__name__)

class TTSService:
    """Speech synthesis service with lazy model loading, transliteration and accentuation"""
    
    def __init__(self, device='cpu'):
        self.device = torch.device(device)
        self.sample_rate = 48000
        self.model = None
        self.temp_dir = None
        self.file_lock = Lock()
        self.temp_files = set()
        self._model_loaded = False
        self.accentors = {}  # Cache for accentors
        
        # Character mapping for Kabardian normalization
        self.kbd_normalization_map = {
            'I': 'Ӏ',    # Latin I → Cyrillic palochka
            'l': 'Ӏ',    # Latin l → Cyrillic palochka
            '|': 'Ӏ',    # Vertical bar → Cyrillic palochka
            'Ӏ': 'Ӏ',    # Alternative palochka → standard palochka
        }
        
        self._setup_temp_dir()
    
    def _normalize_kabardian_text(self, text):
        """
        Normalize Kabardian text for TTS.
        Ensures all character variants are converted to standard Kabardian alphabet.
        """
        if not text or not isinstance(text, str):
            return text
        
        normalized_text = text
        
        # Replace all variants with standard Kabardian palochka
        for variant, standard in self.kbd_normalization_map.items():
            normalized_text = normalized_text.replace(variant, standard)
        
        # Optional: log if normalization changed something
        if normalized_text != text:
            changed_chars = []
            for i in range(min(len(text), len(normalized_text))):
                if text[i] != normalized_text[i]:
                    changed_chars.append(f"'{text[i]}'→'{normalized_text[i]}'")
            
            if changed_chars:
                logger.info(f"🔤 Kabardian normalization: {', '.join(changed_chars[:5])}")
        
        return normalized_text
    
    def _get_accentor_code(self, lang_code):
        """
        Convert lang_code (composite like 'rus_Cyrl') to accentor language code
        Based on tester.py logic
        """
        if not lang_code or lang_code == "none":
            return None
        
        # Direct mapping for composite codes
        mapping = {
            # Russian
            'rus_Cyrl': 'ru',
            'ru': 'ru',
            
            # Ukrainian
            'ukr_Cyrl': 'ukr',
            'ukr': 'ukr',
            
            # Belarusian
            'bel_Cyrl': 'bel',
            'bel': 'bel',
            
            # Georgian
            'kat_Geor': 'kat',
            'kat': 'kat',
            
            # Armenian
            'hye_Armn': 'hye',
            'hye': 'hye',
            
            # Bashkir
            'bak': 'bak',
            
            # Chuvash
            'chv': 'chv',
            
            # Erzya
            'erz': 'erz',
            
            # Kazakh
            'kaz_Cyrl': 'kaz',
            'kaz': 'kaz',

            # Bashkir
            'bak_Cyrl': 'bak',  # Добавлено
            'bak': 'bak',

            # Kyrgyz
            'kir_Cyrl': 'kir',  # Добавлено
            'kir': 'kir',
            
            # Kabardian
            'kbd_Cyrl': 'kbd',
            'kbd': 'kbd',
            
            # Kyrgyz
            'kir_Cyrl': 'kir',
            'kir': 'kir',
            
            # Khakas
            'kjh': 'kjh',
            
            # Moksha
            'mdf': 'mdf',
            
            # Yakut
            'sah_Cyrl': 'sah',
            'sah': 'sah',
            
            # Tatar
            'tat_Cyrl': 'tat',
            'tat': 'tat',
            
            # Tajik
            'tgk_Cyrl': 'tgk',
            'tgk': 'tgk',
            
            # Udmurt
            'udm': 'udm',
            
            # Kalmyk
            'xal': 'xal',
        }
        
        # Try exact match first
        if lang_code in mapping:
            return mapping[lang_code]
        
        # Try prefix matching (e.g., 'rus' -> 'ru')
        lang_prefix = lang_code.split('_')[0] if '_' in lang_code else lang_code
        
        # Special cases for prefixes
        prefix_mapping = {
            'rus': 'ru',
            'ukr': 'ukr',
            'bel': 'bel',
            'kat': 'kat',
            'hye': 'hye',
            'bak': 'bak',
            'chv': 'chv',
            'erz': 'erz',
            'kaz': 'kaz',
            'kbd': 'kbd',
            'kir': 'kir',
            'kjh': 'kjh',
            'mdf': 'mdf',
            'sah': 'sah',
            'tat': 'tat',
            'tgk': 'tgk',
            'udm': 'udm',
            'xal': 'xal',
        }
        
        if lang_prefix in prefix_mapping:
            return prefix_mapping[lang_prefix]
        
        logger.warning(f"No accentor mapping found for language code: {lang_code}")
        return None
    
    def _load_accentor(self, lang_code):
        """Load accentor for specific language"""
        # Languages without accentors (not supported for stress marks)
        no_accent_langs = [
            'uzb_lat', 'aze_lat', 'uzb_cyr', 'aze_cyr',  # Uzbek and Azerbaijani
            'lvs_Latn', 'deu_Latn', 'spa_Latn'  # Latvian, German, Spanish
        ]
        
        # Check if language is in no-accent list
        if any(lang_code.startswith(lang) for lang in ['uzb', 'aze', 'lvs', 'deu', 'spa']):
            logger.info(f"Accentor disabled for language: {lang_code}")
            return None
        
        # Get accentor language code
        accentor_code = self._get_accentor_code(lang_code)
        if not accentor_code:
            logger.warning(f"No accentor code for language: {lang_code}")
            return None
        
        if lang_code in self.accentors:
            return self.accentors[lang_code]
        
        try:
            accentor = None
            
            # Load appropriate accentor based on code
            if accentor_code in ['ru', 'ukr', 'bel']:
                from silero_stress import load_accentor as load_accentor_func
                accentor = load_accentor_func(lang=accentor_code)
                logger.info(f"✅ Loaded standard accentor for: {accentor_code} (from {lang_code})")
            else:
                try:
                    from silero_stress.simple_accentor import SimpleAccentor
                    supported_langs = [
                        'bak', 'chv', 'erz', 'hye', 'kat',
                        'kaz', 'kbd', 'kir', 'kjh', 'mdf', 'sah',
                        'tat', 'tgk', 'udm', 'xal'
                    ]
                    if accentor_code in supported_langs:
                        accentor = SimpleAccentor(lang=accentor_code)
                        logger.info(f"✅ Loaded SimpleAccentor for: {accentor_code} (from {lang_code})")
                    else:
                        logger.warning(f"⚠️ Language {accentor_code} not supported by SimpleAccentor")
                except ImportError as e:
                    logger.warning(f"⚠️ silero_stress simple_accentor module not found: {e}")
                    accentor = None
            
            self.accentors[lang_code] = accentor
            return accentor
            
        except Exception as e:
            logger.error(f"❌ Error loading accentor for {lang_code} (code: {accentor_code}): {e}")
            self.accentors[lang_code] = None
            return None
    
    def apply_accent(self, text, lang_code, use_accent=True):
        """Apply stress marks to text if accentor is available"""
        if not use_accent or not text or lang_code == "none":
            logger.info(f"🔇 Accent disabled or no text for {lang_code}")
            return text
        
        # Check for languages without accentors
        no_accent_prefixes = ['uzb', 'aze', 'lvs', 'deu', 'spa']
        if any(lang_code.startswith(prefix) for prefix in no_accent_prefixes):
            logger.info(f"🔇 Accentor disabled for language (no stress marks): {lang_code}")
            return text
        
        accentor = self._load_accentor(lang_code)
        if accentor:
            try:
                accented_text = accentor(text)
                # Show original and accented text comparison
                if accented_text != text:
                    # Find differences (just first few)
                    orig_words = text.split()
                    acc_words = accented_text.split()
                    differences = []
                    for i in range(min(len(orig_words), len(acc_words))):
                        if orig_words[i] != acc_words[i]:
                            differences.append(f"'{orig_words[i]}'→'{acc_words[i]}'")
                            if len(differences) >= 3:
                                break
                    
                    if differences:
                        diff_info = ", ".join(differences)
                        logger.info(f"✅ Applied accent for {lang_code}: {diff_info}")
                    else:
                        logger.info(f"✅ Applied accent for {lang_code}")
                    
                    # Log full text with accent marks
                    accent_chars = [c for c in accented_text if c == '\u0301' or c == '\u0300']
                    if accent_chars:
                        logger.info(f"📝 Accented text preview: '{accented_text[:100]}...'")
                        logger.info(f"🔤 Found {len(accent_chars)} accent marks in text")
                else:
                    logger.info(f"ℹ️ No accent marks added for {lang_code} (text unchanged)")
                    
                return accented_text
            except Exception as e:
                logger.error(f"❌ Error applying accent for {lang_code}: {e}")
                return text
        else:
            logger.warning(f"⚠️ No accentor available for language: {lang_code}")
            return text
    
    def _generate_ssml(self, text):
        """
        Generate simple SSML with automatic pauses on punctuation.
        Adds natural pauses for better speech quality.
        
        Args:
            text: processed text (already accented/transliterated if needed)
            
        Returns:
            SSML markup string
        """
        if not text or not text.strip():
            return ""
        
        # Escape XML special characters but preserve existing SSML tags
        ssml_tags = re.findall(r'<[^>]+>', text)
        processed_text = text
        
        # Temporarily replace SSML tags with placeholders
        for i, tag in enumerate(ssml_tags):
            placeholder = f'___SSML_TAG_{i}___'
            processed_text = processed_text.replace(tag, placeholder)
        
        # Escape XML special characters
        processed_text = (processed_text
                         .replace('&', '&amp;')
                         .replace('<', '&lt;')
                         .replace('>', '&gt;'))
        
        # Restore SSML tags
        for i, tag in enumerate(ssml_tags):
            placeholder = f'___SSML_TAG_{i}___'
            processed_text = processed_text.replace(placeholder, tag)
        
        # Add pauses after punctuation marks
        # Longer pause after sentence endings (.!?)
        processed_text = re.sub(
            r'([.!?])(\s+)', 
            r'\1<break time="500ms"/>\2', 
            processed_text
        )
        
        # Shorter pause after commas, colons, semicolons
        processed_text = re.sub(
            r'([,:;])(\s+)', 
            r'\1<break time="200ms"/>\2', 
            processed_text
        )
        
        # Wrap in SSML speak tag with paragraph and sentence structure
        ssml = f'<speak><p><s>{processed_text}</s></p></speak>'
        
        return ssml
    
    def _load_model(self):
        """Lazy loading of Silero TTS model"""
        if self._model_loaded:
            return
        
        logger.info("📊 Loading Silero TTS model (on first use)...")
        
        try:
            model_id = 'v5_cis_base'
            self.model, _ = torch.hub.load(
                repo_or_dir='snakers4/silero-models',
                model='silero_tts',
                language='ru',
                speaker=model_id
            )
            self.model.to(self.device)
            self._model_loaded = True
            logger.info("✅ Silero TTS loaded successfully!")
        except Exception as e:
            logger.error(f"❌ Error loading Silero TTS: {e}")
            raise
    
    def _setup_temp_dir(self):
        """Create temporary directory for audio files"""
        self.temp_dir = tempfile.mkdtemp(prefix='tts_audio_')
        logger.info(f"📁 Temporary audio directory: {self.temp_dir}")
    
    def prepare_text_for_tts(self, text, lang_code, use_accent=True):
        """
        Prepare text for TTS: accentuation and transliteration if needed
        For Georgian and Armenian: apply accents first, then transliterate
        
        Returns:
            tuple: (prepared_text, actual_speaker, transliteration_info)
        """
        logger.info(f"🔄 Preparing text for TTS: lang={lang_code}, use_accent={use_accent}")
        logger.info(f"📝 Original text: '{text[:100]}...'")
        
        if not text.strip():
            return text, 'ru_eduard', None
        
        transliteration_info = None
        
        # Apply Kabardian normalization if needed
        if lang_code == 'kbd_Cyrl':
            text = self._normalize_kabardian_text(text)
            logger.info(f"🔤 Applied Kabardian normalization")
        
        # Step 1: Apply accents BEFORE transliteration for Georgian and Armenian
        accented_text = text
        if use_accent and lang_code in ['kat_Geor', 'hye_Armn']:
            logger.info(f"🔤 Applying accents BEFORE transliteration for {lang_code}")
            accented_text = self.apply_accent(text, lang_code, use_accent)
            if accented_text != text:
                logger.info(f"✅ Applied accents BEFORE transliteration for {lang_code}")
        
        # Step 2: Check if transliteration is needed
        if transliterator.needs_transliteration(lang_code):
            logger.info(f"🔤 Transliteration for TTS: {lang_code}")
            
            # Determine target alphabet
            if lang_code in ['kat_Geor', 'hye_Armn']:
                target_script = 'kbd'  # Georgian and Armenian → Kabardian
            else:
                target_script = 'kbd'  # Turkish and Azerbaijani → Kabardian
            
            # Use accented text for Georgian/Armenian, original text for others
            text_to_transliterate = accented_text if lang_code in ['kat_Geor', 'hye_Armn'] else text
            
            # Transliterate text
            transliterated_text = transliterator.transliterate_for_tts(
                text_to_transliterate, lang_code, target_script
            )
            
            # Apply normalization to transliterated text if it's Kabardian
            if target_script == 'kbd':
                transliterated_text = self._normalize_kabardian_text(transliterated_text)
            
            # Determine speaker
            actual_speaker = transliterator.get_target_speaker(lang_code)
            
            transliteration_info = {
                'type': lang_code,
                'original_text': text,
                'transliterated_text': transliterated_text,
                'target_speaker': actual_speaker,
                'accent_applied_before': lang_code in ['kat_Geor', 'hye_Armn']
            }
            
            logger.info(f"🎯 TTS: {lang_code} → {actual_speaker}")
            logger.info(f"📤 Original: '{text[:50]}...'")
            logger.info(f"📥 Transliterated: '{transliterated_text[:50]}...'")
            
            return transliterated_text, actual_speaker, transliteration_info
        else:
            # For languages without transliteration
            # Apply accents for non-Georgian/Armenian languages
            if use_accent and lang_code not in ['kat_Geor', 'hye_Armn']:
                logger.info(f"🔤 Applying accents for {lang_code}")
                accented_text = self.apply_accent(text, lang_code, use_accent)
            else:
                logger.info(f"🔇 Accents not applied for {lang_code}")
            
            # Apply Kabardian normalization for Kabardian text
            if lang_code == 'kbd_Cyrl':
                accented_text = self._normalize_kabardian_text(accented_text)
            
            # Determine speaker based on language
            if lang_code in ['rus_Cyrl', 'ukr_Cyrl', 'bel_Cyrl', 'lvs_Latn', 'deu_Latn', 'spa_Latn']:
                actual_speaker = 'ru_eduard'
                logger.info(f"🎙️ Selected Russian speaker for {lang_code}")
            elif lang_code in ['kbd_Cyrl', 'kaz_Cyrl', 'bak_Cyrl', 'kir_Cyrl', 'kat_Geor', 'hye_Armn', 'azj_Latn', 'tur_Latn']:
                actual_speaker = 'kbd_eduard'
                logger.info(f"🎙️ Selected Kabardian speaker for {lang_code}")
            else:
                actual_speaker = 'ru_eduard'
                logger.info(f"🎙️ Default Russian speaker for {lang_code}")
            
            logger.info(f"📤 Original text: '{text[:50]}...'")
            logger.info(f"📥 Prepared text: '{accented_text[:50]}...'")
            
            return accented_text, actual_speaker, None
    
    def synthesize(self, text, speaker='ru_eduard', lang_code=None, use_accent=True, max_length=200):
        """
        Speech synthesis from text with transliteration and accentuation support
        
        Args:
            text: text for synthesis
            speaker: requested speaker
            lang_code: text language code (for transliteration and accentuation)
            use_accent: whether to apply stress marks
            max_length: maximum text length
        
        Returns:
            dict with path to audio file and metadata
        """
        logger.info(f"🔊 TTS synthesis request: lang={lang_code}, speaker={speaker}, use_accent={use_accent}")
        logger.info(f"📝 Input text preview: '{text[:100]}...'")
        
        # Lazy model loading on first use
        if not self._model_loaded:
            self._load_model()
        
        try:
            # Apply Kabardian normalization BEFORE any processing
            if lang_code == 'kbd_Cyrl':
                text = self._normalize_kabardian_text(text)
                logger.info(f"🔤 Applied Kabardian normalization for TTS")
            
            # Prepare text (accentuation and transliteration if needed)
            if lang_code:
                prepared_text, actual_speaker, transliteration_info = self.prepare_text_for_tts(
                    text, lang_code, use_accent
                )
                transliterated = transliteration_info is not None
            else:
                prepared_text = text
                actual_speaker = speaker
                transliteration_info = None
                transliterated = False
            
            # Apply Kabardian normalization to prepared text if it's Kabardian
            if lang_code == 'kbd_Cyrl':
                prepared_text = self._normalize_kabardian_text(prepared_text)
            
            # Limit text length
            if len(prepared_text) > max_length:
                prepared_text = prepared_text[:max_length] + "..."
                truncated = True
                logger.info(f"✂️ Text truncated to {max_length} chars")
            else:
                truncated = False
            
            if not prepared_text.strip():
                logger.error("❌ Empty prepared text")
                return {'error': 'Empty text'}
            
            # Log normalization if applied
            original_preview = text[:50] if len(text) > 50 else text
            prepared_preview = prepared_text[:50] if len(prepared_text) > 50 else prepared_text
            if original_preview != prepared_preview and lang_code == 'kbd_Cyrl':
                logger.info(f"🔤 Kabardian TTS input: '{original_preview}' → '{prepared_preview}'")
            
            # Generate SSML with automatic pauses
            ssml_text = self._generate_ssml(prepared_text)
            
            # DEBUG: Log text with accent marks
            accent_chars = [c for c in prepared_text if c == '\u0301' or c == '\u0300']
            logger.info(f"🔤 Prepared text has {len(accent_chars)} accent marks")
            if accent_chars:
                logger.info(f"📝 Prepared text with accents: '{prepared_text[:150]}...'")
            
            logger.info(f"📝 Generated SSML (preview): {ssml_text[:200]}...")
            
            # Synthesis with torch.no_grad() for optimization
            with torch.no_grad():
                # Move model to GPU if available for inference
                if self.device.type == 'cuda':
                    self.model.to(self.device)
                
                logger.info(f"🎙️ Synthesizing with speaker: {actual_speaker}")
                audio = self.model.apply_tts(
                    ssml_text=ssml_text,
                    speaker=actual_speaker,
                    sample_rate=self.sample_rate
                )
            
            audio_np = audio.cpu().numpy()
            
            # Save to temporary file
            filename = f"tts_{uuid.uuid4().hex}.wav"
            filepath = os.path.join(self.temp_dir, filename)
            
            sf.write(filepath, audio_np, self.sample_rate)
            
            # Register file
            with self.file_lock:
                self.temp_files.add(filepath)
            
            duration = len(audio_np) / self.sample_rate
            
            result = {
                'success': True,
                'path': filepath,
                'filename': filename,
                'duration': round(duration, 2),
                'sample_rate': self.sample_rate,
                'speaker': actual_speaker,
                'requested_speaker': speaker,
                'text_length': len(text),
                'prepared_text': prepared_text,
                'transliterated': transliterated,
                'accent_applied': use_accent,
                'truncated': truncated,
                'normalized': lang_code == 'kbd_Cyrl',  # Flag if normalization was applied
                'lang_code': lang_code,
                'ssml_generated': True,  # Flag that SSML was used
                'ssml_preview': ssml_text[:200]  # Add SSML preview to result
            }
            
            # Add transliteration info if available
            if transliteration_info:
                result['transliteration_info'] = transliteration_info
            
            # Add accentor info if accents were applied
            if use_accent and lang_code:
                accentor_code = self._get_accentor_code(lang_code)
                result['accentor_code'] = accentor_code
            
            logger.info(f"✅ Synthesis successful: {duration:.2f}s, speaker: {actual_speaker}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Synthesis error: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def cleanup_file(self, filepath):
        """Delete specific temporary file"""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                with self.file_lock:
                    self.temp_files.discard(filepath)
                logger.info(f"🗑️ Temporary file deleted: {filepath}")
        except Exception as e:
            logger.error(f"⚠️ Error deleting file {filepath}: {e}")
    
    def cleanup_all(self):
        """Delete all temporary files"""
        logger.info("🧹 Cleaning up temporary audio files...")
        
        with self.file_lock:
            files_to_remove = list(self.temp_files)
        
        for filepath in files_to_remove:
            self.cleanup_file(filepath)
        
        # Remove temporary directory
        try:
            if self.temp_dir and os.path.exists(self.temp_dir):
                os.rmdir(self.temp_dir)
                logger.info(f"✅ Temporary directory deleted: {self.temp_dir}")
        except Exception as e:
            logger.error(f"⚠️ Error deleting directory: {e}")
        
        # Clean up model
        if self.model:
            del self.model
            self.model = None
            self._model_loaded = False
            gc.collect()
            if torch.backends.mps.is_available():
                torch.mps.empty_cache()
            elif torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.info("✅ TTS model cleaned up")
    
    def get_available_speakers(self):
        """Returns list of available speakers"""
        return {
            'ru_eduard': 'Russian (Eduard)',
            'kbd_eduard': 'Kabardian (Eduard)'
        }
    
    def normalize_text_for_speech(self, text, lang_code, use_accent=True):
        """
        Public method to normalize text for speech synthesis.
        Can be used externally to prepare text.
        
        Args:
            text: text to normalize
            lang_code: language code
            use_accent: whether to apply stress marks
            
        Returns:
            tuple: (normalized_text, metadata)
        """
        logger.info(f"📝 Normalizing text: lang={lang_code}, use_accent={use_accent}")
        logger.info(f"📤 Original: '{text[:100]}...'")
        
        if lang_code == 'kbd_Cyrl':
            text = self._normalize_kabardian_text(text)
        
        # Apply accents if needed
        accented_text = self.apply_accent(text, lang_code, use_accent)
        
        # Log result
        if accented_text != text:
            logger.info(f"✅ Text normalized with accents")
            logger.info(f"📥 Result: '{accented_text[:100]}...'")
        else:
            logger.info(f"ℹ️ Text unchanged after normalization")
        
        metadata = {
            'original_text': text,
            'accent_applied': accented_text != text,
            'lang_code': lang_code,
            'accentor_code': self._get_accentor_code(lang_code) if use_accent else None
        }
        
        return accented_text, metadata
    
    def apply_accent_to_text(self, text, lang_code):
        """
        Simple method to apply accent to text without synthesis
        Useful for testing accent placement
        
        Args:
            text: text to accent
            lang_code: language code (e.g., 'rus_Cyrl', 'ukr_Cyrl', 'bel_Cyrl')
            
        Returns:
            accented text
        """
        logger.info(f"🔤 Testing accent application for: {lang_code}")
        logger.info(f"📝 Input: '{text[:100]}...'")
        
        result = self.apply_accent(text, lang_code, use_accent=True)
        
        if result != text:
            logger.info(f"✅ Accents applied successfully")
            logger.info(f"📝 Result: '{result[:100]}...'")
        else:
            logger.info(f"ℹ️ No accent marks added (text unchanged)")
        
        return result
    
    def get_accentor_info(self, lang_code):
        """
        Get information about accentor for a specific language
        
        Args:
            lang_code: language code
            
        Returns:
            dict with accentor info
        """
        accentor_code = self._get_accentor_code(lang_code)
        has_accentor = lang_code in self.accentors and self.accentors[lang_code] is not None
        
        info = {
            'lang_code': lang_code,
            'accentor_code': accentor_code,
            'has_accentor': has_accentor,
            'accentor_loaded': has_accentor,
            'accentor_type': 'standard' if accentor_code in ['ru', 'ukr', 'bel'] else 'simple' if accentor_code else 'none'
        }
        
        logger.info(f"🔍 Accentor info for {lang_code}: {info}")
        return info
    
    def __del__(self):
        """Cleanup when object is deleted"""
        self.cleanup_all()