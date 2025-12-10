# tts_service.py
# Text-to-Speech service using Silero TTS with lazy loading and transliteration
# License: CC BY-NC 4.0 (Non-Commercial Use Only)

import torch
import numpy as np
import soundfile as sf
import os
import tempfile
import uuid
from threading import Lock
from pathlib import Path
import gc

# ИСПРАВЛЕННЫЙ ИМПОРТ
try:
    from .transliterator import transliterator
except ImportError:
    # Fallback for direct execution
    from transliterator import transliterator

class TTSService:
    """Speech synthesis service with lazy model loading and transliteration"""
    
    def __init__(self, device='cpu'):
        self.device = torch.device(device)
        self.sample_rate = 48000
        self.model = None
        self.temp_dir = None
        self.file_lock = Lock()
        self.temp_files = set()
        self._model_loaded = False
        
        # Character mapping for Kabardian normalization
        self.kbd_normalization_map = {
            'I': 'Ӏ',    # Latin I → Cyrillic palochka
            'l': 'Ӏ',    # Latin l → Cyrillic palochka
            '|': 'Ӏ',    # Vertical bar → Cyrillic palochka
            'ӏ': 'Ӏ',    # Alternative palochka → standard palochka
            # All variants should map to standard Ӏ
        }
        
        self._setup_temp_dir()
    
    def _normalize_kabardian_text(self, text):
        """
        Normalize Kabardian text for TTS.
        Ensures all character variants are converted to standard Kabardian alphabet.
        
        Args:
            text: input text to normalize
            
        Returns:
            normalized text with standardized Kabardian characters
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
                print(f"🔤 Kabardian normalization: {', '.join(changed_chars[:5])}")
        
        return normalized_text
    
    def _load_model(self):
        """Lazy loading of Silero TTS model"""
        if self._model_loaded:
            return
        
        print("🔊 Loading Silero TTS model (on first use)...")
        
        try:
            model_id = 'v5_cis_base'
            self.model, _ = torch.hub.load(
                repo_or_dir='snakers4/silero-models',
                model='silero_tts',
                language='ru',
                speaker=model_id
            )
            self._model_loaded = True
            print("✅ Silero TTS loaded successfully!")
        except Exception as e:
            print(f"❌ Error loading Silero TTS: {e}")
            raise
    
    def _setup_temp_dir(self):
        """Create temporary directory for audio files"""
        self.temp_dir = tempfile.mkdtemp(prefix='tts_audio_')
        print(f"📁 Temporary audio directory: {self.temp_dir}")
    
    def prepare_text_for_tts(self, text, lang_code):
        """
        Prepare text for TTS: transliteration if needed
        
        Returns:
            tuple: (prepared_text, actual_speaker)
        """
        if not text.strip():
            return text, 'ru_eduard'
        
        # Apply Kabardian normalization if needed
        if lang_code == 'kbd_Cyrl':
            text = self._normalize_kabardian_text(text)
        
        # Check if transliteration is needed
        if transliterator.needs_transliteration(lang_code):
            print(f"🔤 Transliteration for TTS: {lang_code}")
            
            # Determine target alphabet
            if lang_code in ['kat_Geor', 'hye_Armn']:
                target_script = 'kbd'  # Georgian and Armenian → Kabardian
            else:
                target_script = 'kbd'  # Turkish and Azerbaijani → Kabardian
            
            # Transliterate text
            transliterated_text = transliterator.transliterate_for_tts(
                text, lang_code, target_script
            )
            
            # Apply normalization to transliterated text if it's Kabardian
            if target_script == 'kbd':
                transliterated_text = self._normalize_kabardian_text(transliterated_text)
            
            # Determine speaker
            actual_speaker = transliterator.get_target_speaker(lang_code)
            
            print(f"🎯 TTS: {lang_code} → {actual_speaker} ('{text[:30]}...' → '{transliterated_text[:30]}...')")
            
            return transliterated_text, actual_speaker
        else:
            # For languages without transliteration
            # Apply Kabardian normalization for Kabardian text
            if lang_code == 'kbd_Cyrl':
                text = self._normalize_kabardian_text(text)
            
            # Determine speaker based on language
            if lang_code in ['rus_Cyrl', 'ukr_Cyrl', 'bel_Cyrl', 'lav_Latn', 'deu_Latn', 'spa_Latn']:
                actual_speaker = 'ru_eduard'
            elif lang_code in ['kbd_Cyrl', 'kaz_Cyrl', 'kat_Geor', 'hye_Armn', 'azj_Latn', 'tur_Latn']:
                actual_speaker = 'kbd_eduard'
            else:
                actual_speaker = 'ru_eduard'
            
            return text, actual_speaker
    
    def synthesize(self, text, speaker='ru_eduard', lang_code=None, max_length=200):
        """
        Speech synthesis from text with transliteration support
        
        Args:
            text: text for synthesis
            speaker: requested speaker
            lang_code: text language code (for transliteration)
            max_length: maximum text length
        
        Returns:
            dict with path to audio file and metadata
        """
        # Lazy model loading on first use
        if not self._model_loaded:
            self._load_model()
        
        try:
            # Apply Kabardian normalization BEFORE any processing
            if lang_code == 'kbd_Cyrl':
                text = self._normalize_kabardian_text(text)
                print(f"🔤 Applied Kabardian normalization for TTS")
            
            # Prepare text (transliteration if needed)
            if lang_code and transliterator.needs_transliteration(lang_code):
                prepared_text, actual_speaker = self.prepare_text_for_tts(text, lang_code)
                transliterated = True
            else:
                prepared_text = text
                # Use the provided speaker
                actual_speaker = speaker
                transliterated = False
            
            # Apply Kabardian normalization to prepared text if it's Kabardian
            if lang_code == 'kbd_Cyrl':
                prepared_text = self._normalize_kabardian_text(prepared_text)
            
            # Limit text length
            if len(prepared_text) > max_length:
                prepared_text = prepared_text[:max_length] + "..."
                truncated = True
            else:
                truncated = False
            
            if not prepared_text.strip():
                return {'error': 'Empty text'}
            
            # Log normalization if applied
            original_preview = text[:50] if len(text) > 50 else text
            prepared_preview = prepared_text[:50] if len(prepared_text) > 50 else prepared_text
            if original_preview != prepared_preview and lang_code == 'kbd_Cyrl':
                print(f"🔤 Kabardian TTS input: '{original_preview}' → '{prepared_preview}'")
            
            # Create simple SSML
            ssml_text = f'<speak><p><s>{prepared_text}</s></p></speak>'
            
            # Synthesis with torch.no_grad() for optimization
            with torch.no_grad():
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
            
            return {
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
                'truncated': truncated,
                'normalized': lang_code == 'kbd_Cyrl'  # Flag if normalization was applied
            }
            
        except Exception as e:
            print(f"❌ Synthesis error: {e}")
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
                print(f"🗑️  Temporary file deleted: {filepath}")
        except Exception as e:
            print(f"⚠️  Error deleting file {filepath}: {e}")
    
    def cleanup_all(self):
        """Delete all temporary files"""
        print("🧹 Cleaning up temporary audio files...")
        
        with self.file_lock:
            files_to_remove = list(self.temp_files)
        
        for filepath in files_to_remove:
            self.cleanup_file(filepath)
        
        # Remove temporary directory
        try:
            if self.temp_dir and os.path.exists(self.temp_dir):
                os.rmdir(self.temp_dir)
                print(f"✅ Temporary directory deleted: {self.temp_dir}")
        except Exception as e:
            print(f"⚠️  Error deleting directory: {e}")
        
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
            print("✅ TTS model cleaned up")
    
    def get_available_speakers(self):
        """Returns list of available speakers"""
        return {
            'ru_eduard': 'Russian (Eduard)',
            'kbd_eduard': 'Kabardian (Eduard)'
        }
    
    def normalize_text_for_speech(self, text, lang_code):
        """
        Public method to normalize text for speech synthesis.
        Can be used externally to prepare text.
        
        Args:
            text: text to normalize
            lang_code: language code
            
        Returns:
            normalized text
        """
        if lang_code == 'kbd_Cyrl':
            return self._normalize_kabardian_text(text)
        return text
    
    def __del__(self):
        """Cleanup when object is deleted"""
        self.cleanup_all()
