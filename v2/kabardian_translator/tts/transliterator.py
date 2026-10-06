# Transliteration of Georgian and Armenian into Kabardian Cyrillic for the kbd_eduard voice — from v1 unchanged.
# transliterator_final.py
# Enhanced transliteration for TTS with accurate phonetic representation
# + Restored language detection and processing logic from original code
# Version: 2.0.0
# License: CC BY-NC 4.0 (Non-Commercial Use Only)

import re

class TransliteratorFinal:
    """
    Enhanced transliterator with maximum phonetic accuracy.
    RESTORED WORKING LOGIC FROM ORIGINAL CODE:
    - detect_script
    - Proper word boundary handling
    - Working functionality
    """
    
    def __init__(self):
        self.setup_transliteration_rules()
    
    def setup_transliteration_rules(self):
        """Setup transliteration rules"""
        
        # TURKISH (Latin) → Kazakh Cyrillic
        self.turkish_to_kazakh = {
            'a': 'а', 'A': 'А',
            'b': 'б', 'B': 'Б', 
            'c': 'җ', 'C': 'Җ',
            'ç': 'ч', 'Ç': 'Ч',
            'd': 'д', 'D': 'Д',
            'e': 'е', 'E': 'Е',
            'f': 'ф', 'F': 'Ф',
            'g': 'г', 'G': 'Г',
            'h': 'һ', 'H': 'Һ',
            'ı': 'ы', 'I': 'Ы',
            'i': 'і', 'İ': 'І',
            'j': 'ж', 'J': 'Ж',
            'k': 'к', 'K': 'К',
            'l': 'л', 'L': 'Л',
            'm': 'м', 'M': 'М',
            'n': 'н', 'N': 'Н',
            'o': 'о', 'O': 'О',
            'ö': 'ө', 'Ö': 'Ө',
            'p': 'п', 'P': 'П',
            'r': 'р', 'R': 'Р',
            's': 'с', 'S': 'С',
            'ş': 'ш', 'Ş': 'Ш',
            't': 'т', 'T': 'Т',
            'u': 'у', 'U': 'У',
            'ü': 'ү', 'Ü': 'Ү',
            'v': 'в', 'V': 'В',
            'y': 'й', 'Y': 'Й',
            'z': 'з', 'Z': 'З',
            "'": "", "’": ""
        }
        
        # AZERBAIJANI (Latin) → Kazakh Cyrillic  
        self.azerbaijani_to_kazakh = {
            'a': 'а', 'A': 'А',
            'b': 'б', 'B': 'Б',
            'c': 'җ', 'C': 'Җ',
            'ç': 'ч', 'Ç': 'Ч',
            'd': 'д', 'D': 'Д',
            'e': 'е', 'E': 'Е',
            'ə': 'а', 'Ə': 'А',
            'f': 'ф', 'F': 'Ф',
            'g': 'г', 'G': 'Г',
            'ğ': 'ғ', 'Ğ': 'Ғ',
            'h': 'һ', 'H': 'Һ',
            'x': 'х', 'X': 'Х',
            'ı': 'ы', 'I': 'Ы',
            'i': 'і', 'İ': 'І',
            'j': 'ж', 'J': 'Ж',
            'k': 'к', 'K': 'К',
            'q': 'қ', 'Q': 'Қ',
            'l': 'л', 'L': 'Л',
            'm': 'м', 'M': 'М',
            'n': 'н', 'N': 'Н',
            'o': 'о', 'O': 'О',
            'ö': 'ө', 'Ö': 'Ө',
            'p': 'п', 'P': 'П',
            'r': 'р', 'R': 'Р',
            's': 'с', 'S': 'С',
            'ş': 'ш', 'Ş': 'Ш',
            't': 'т', 'T': 'Т',
            'u': 'у', 'U': 'У',
            'ü': 'йю', 'Ü': 'Йю',
            'v': 'в', 'V': 'В',
            'y': 'й', 'Y': 'Й',
            'z': 'з', 'Z': 'З',
        }
        
        # LATVIAN (Latin) → hybrid Kazakh + Kabardian Cyrillic
        self.latvian_to_hybrid = {
            'a': 'а', 'A': 'А',
            'b': 'б', 'B': 'Б',
            'c': 'ц', 'C': 'Ц',
            'd': 'д', 'D': 'Д',
            'e': 'э', 'E': 'Э',
            'f': 'ф', 'F': 'Ф',
            'g': 'г', 'G': 'Г',
            'h': 'х', 'H': 'Х',
            'i': 'и', 'I': 'И',
            'j': 'й', 'J': 'Й',
            'k': 'к', 'K': 'К',
            'l': 'л', 'L': 'Л',
            'm': 'м', 'M': 'М',
            'n': 'н', 'N': 'Н',
            'o': 'о', 'O': 'О',
            'p': 'п', 'P': 'П',
            'r': 'р', 'R': 'Р',
            's': 'с', 'S': 'С',
            't': 'т', 'T': 'Т',
            'u': 'у', 'U': 'У',
            'v': 'в', 'V': 'В',
            'z': 'з', 'Z': 'З',
            
            'ā': 'аа', 'Ā': 'Аа',
            'č': 'ч', 'Č': 'Ч',
            'ē': 'ээ', 'Ē': 'Ээ',
            'ģ': 'гь', 'Ģ': 'Гь',
            'ī': 'ии', 'Ī': 'Ии',
            'ķ': 'кь', 'Ķ': 'Кь',
            'ļ': 'ль', 'Ļ': 'Ль',
            'ņ': 'нь', 'Ņ': 'Нь',
            'š': 'ш', 'Š': 'Ш',
            'ū': 'уу', 'Ū': 'Уу',
            'ž': 'ж', 'Ž': 'Ж',
        }
        
        # GERMAN (Latin) → hybrid Cyrillic
        self.german_to_hybrid = {
            'a': 'а', 'A': 'А',
            'b': 'б', 'B': 'Б',
            'c': 'ц', 'C': 'Ц',
            'd': 'д', 'D': 'Д',
            'e': 'э', 'E': 'Э',
            'f': 'ф', 'F': 'Ф',
            'g': 'г', 'G': 'Г',
            'h': 'х', 'H': 'Х',
            'i': 'и', 'I': 'И',
            'j': 'й', 'J': 'Й',
            'k': 'к', 'K': 'К',
            'l': 'л', 'L': 'Л',
            'm': 'м', 'M': 'М',
            'n': 'н', 'N': 'Н',
            'o': 'о', 'O': 'О',
            'p': 'п', 'P': 'П',
            'q': 'кв', 'Q': 'Кв',
            'r': 'р', 'R': 'Р',
            's': 'с', 'S': 'С',
            't': 'т', 'T': 'Т',
            'u': 'у', 'U': 'У',
            'v': 'ф', 'V': 'Ф',
            'w': 'в', 'W': 'В',
            'x': 'кс', 'X': 'Кс',
            'y': 'ю', 'Y': 'Ю',
            'z': 'ц', 'Z': 'Ц',
            
            # Umlauts
            'ä': 'э', 'Ä': 'Э',
            'ö': 'ө', 'Ö': 'Ө',
            'ü': 'йю', 'Ü': 'Йю',
            'ß': 'сс', 'ẞ': 'Сс',
            
            "'": "", "'": "", "-": "-", " ": " "
        }
        
        # SPANISH (Latin) → hybrid Cyrillic
        self.spanish_to_hybrid = {
            'a': 'а', 'A': 'А',
            'b': 'б', 'B': 'Б',
            'c': 'к', 'C': 'К',
            'd': 'д', 'D': 'Д',
            'e': 'э', 'E': 'Э',
            'f': 'ф', 'F': 'Ф',
            'g': 'г', 'G': 'Г',
            'h': '', 'H': '',
            'i': 'и', 'I': 'И',
            'j': 'х', 'J': 'Х',
            'k': 'к', 'K': 'К',
            'l': 'л', 'L': 'Л',
            'm': 'м', 'M': 'М',
            'n': 'н', 'N': 'Н',
            'o': 'о', 'O': 'О',
            'p': 'п', 'P': 'П',
            'q': 'к', 'Q': 'К',
            'r': 'р', 'R': 'Р',
            's': 'с', 'S': 'С',
            't': 'т', 'T': 'Т',
            'u': 'у', 'U': 'У',
            'v': 'б', 'V': 'Б',
            'w': 'в', 'W': 'В',
            'x': 'кс', 'X': 'Кс',
            'y': 'й', 'Y': 'Й',
            'z': 'с', 'Z': 'С',
            
            'á': 'а', 'Á': 'А',
            'é': 'э', 'É': 'Э',
            'í': 'и', 'Í': 'И',
            'ó': 'о', 'Ó': 'О',
            'ú': 'у', 'Ú': 'У',
            'ñ': 'нь', 'Ñ': 'Нь',
            'ü': 'у', 'Ü': 'У',
            
            "'": "", "'": "", "-": "-", " ": " "
        }
        
        # GEORGIAN (original alphabet) → Kabardian Cyrillic
        self.georgian_to_kabardian = {
            'ა': 'а', 'ბ': 'б', 'გ': 'г', 'დ': 'д', 'ე': 'э', 'ვ': 'в',
            'ზ': 'з', 'თ': 'тъ', 'ი': 'ы', 'კ': 'къ', 'ლ': 'л', 'მ': 'м',
            'ნ': 'н', 'ო': 'о', 'პ': 'пӏ', 'ჟ': 'ж', 'რ': 'р', 'ს': 'с',
            'ტ': 'тӏ', 'უ': 'у', 'ფ': 'п', 'ქ': 'к', 'ღ': 'гъ', 'ყ': 'къ',
            'შ': 'ш', 'ჩ': 'ч', 'ც': 'ц', 'ძ': 'дз', 'წ': 'цӏ', 'ჭ': 'чӏ',
            'ხ': 'хъ', 'ჯ': 'дж', 'ჰ': 'һ',
            
            'Ა': 'А', 'Ბ': 'Б', 'Გ': 'Г', 'Დ': 'Д', 'Ე': 'Э', 'Ვ': 'В',
            'Ზ': 'З', 'Თ': 'Тъ', 'Ი': 'Ы', 'Კ': 'Къ', 'Ლ': 'Л', 'Მ': 'М',
            'Ნ': 'Н', 'Ო': 'О', 'Პ': 'Пӏ', 'Ჟ': 'Ж', 'Რ': 'Р', 'Ს': 'С',
            'Ტ': 'Тӏ', 'Უ': 'У', 'Ფ': 'П', 'Ქ': 'К', 'Ღ': 'Гъ', 'Ყ': 'Къ',
            'Შ': 'Ш', 'Ჩ': 'Ч', 'Ც': 'Ц', 'Ძ': 'Дз', 'Წ': 'Цӏ', 'Ჭ': 'Чӏ',
            'Ხ': 'Хъ', 'Ჯ': 'Дж', 'Ჰ': 'Һ',
        }
        
        # ARMENIAN (original alphabet) → hybrid Kazakh + Kabardian
        self.armenian_to_hybrid = {
            'ա': 'а', 'բ': 'б', 'գ': 'г', 'դ': 'д', 'ե': 'е', 'զ': 'з',
            'է': 'э', 'ը': 'ы', 'թ': 'тъ', 'ժ': 'ж', 'ի': 'и', 'լ': 'л',
            'խ': 'хъ', 'ծ': 'ц', 'կ': 'к', 'հ': 'һ', 'ձ': 'дз', 'ղ': 'гъ',
            'ճ': 'дж', 'մ': 'м', 'յ': 'й', 'ն': 'н', 'շ': 'ш', 'ո': 'о',
            'չ': 'ч', 'պ': 'пһ', 'ջ': 'дж', 'ռ': 'р', 'ս': 'с', 'վ': 'в',
            'տ': 'тһ', 'ր': 'р', 'ց': 'ц', 'ւ': 'в', 'փ': 'пъ', 'ք': 'къ',
            'օ': 'о', 'ֆ': 'ф', 'ու': 'у', 'և': 'ев',
            
            'Ա': 'А', 'Բ': 'Б', 'Գ': 'Г', 'Դ': 'Д', 'Ե': 'Е', 'Զ': 'З',
            'Է': 'Э', 'Ը': 'Ы', 'Թ': 'Тъ', 'Ժ': 'Ж', 'Ի': 'И', 'Լ': 'Л',
            'Խ': 'Хъ', 'Ծ': 'Ц', 'Կ': 'К', 'Հ': 'Һ', 'Ձ': 'Дз', 'Ղ': 'Гъ',
            'Ճ': 'Дж', 'Մ': 'М', 'Յ': 'Й', 'Ն': 'Н', 'Շ': 'Ш', 'Ո': 'О',
            'Չ': 'Ч', 'Պ': 'Пһ', 'Ջ': 'Дж', 'Ռ': 'Р', 'Ս': 'С', 'Վ': 'В',
            'Տ': 'Тһ', 'Ր': 'Р', 'Ց': 'Ц', 'Ւ': 'В', 'Փ': 'Пъ', 'Ք': 'Къ',
            'Օ': 'О', 'Ֆ': 'Ф', 'ՈՒ': 'У', 'ԵՎ': 'Ев',
        }
        
        # SPECIAL RULES
        
        # Latvian rules
        self.latvian_special_rules = [
            (r'ch', 'х'), (r'Ch', 'Х'), (r'CH', 'Х'),
            (r'dz', 'дз'), (r'Dz', 'Дз'), (r'DZ', 'Дз'),
            (r'dž', 'дж'), (r'Dž', 'Дж'), (r'DŽ', 'Дж'),
            (r'ie', 'ие'), (r'Ie', 'Ие'), (r'IE', 'Ие'),
        ]
        
        # German rules (IMPROVED)
        self.german_special_rules = [
            # 4-character combinations
            (r'tsch', 'ч'), (r'Tsch', 'Ч'), (r'TSCH', 'Ч'),
            
            # 3-character combinations
            (r'sch', 'ш'), (r'Sch', 'Ш'), (r'SCH', 'Ш'),
            
            # 2-character: diphthongs
            (r'ie', 'ии'), (r'Ie', 'Ии'), (r'IE', 'ИИ'),
            (r'ei', 'ай'), (r'Ei', 'Ай'), (r'EI', 'Ай'),
            (r'eu', 'ой'), (r'Eu', 'Ой'), (r'EU', 'Ой'),
            (r'äu', 'ой'), (r'Äu', 'Ой'), (r'ÄU', 'Ой'),
            
            # 2-character: vowels with h (doubling for length)
            (r'oh', 'оо'), (r'Oh', 'Оо'), (r'OH', 'ОО'),
            (r'ah', 'аа'), (r'Ah', 'Аа'), (r'AH', 'АА'),
            (r'eh', 'ээ'), (r'Eh', 'Ээ'), (r'EH', 'ЭЭ'),
            (r'ih', 'ии'), (r'Ih', 'Ии'), (r'IH', 'ИИ'),
            (r'uh', 'уу'), (r'Uh', 'Уу'), (r'UH', 'УУ'),
            (r'äh', 'ээ'), (r'Äh', 'Ээ'), (r'ÄH', 'ЭЭ'),
            (r'öh', 'өө'), (r'Öh', 'Өө'), (r'ÖH', 'ӨӨ'),
            (r'üh', 'йю'), (r'Üh', 'Йю'), (r'ÜH', 'Йю'),
            
            # 2-character: consonant combinations
            (r'ch', 'х'), (r'Ch', 'Х'), (r'CH', 'Х'),
            (r'ck', 'к'), (r'Ck', 'к'), (r'CK', 'К'),
            (r'ph', 'ф'), (r'Ph', 'Ф'), (r'PH', 'Ф'),
            (r'th', 'т'), (r'Th', 'Т'), (r'TH', 'Т'),
        ]
        
        # Spanish rules
        self.spanish_special_rules = [
            (r'ch', 'ч'), (r'Ch', 'Ч'), (r'CH', 'Ч'),
            (r'll', 'й'), (r'Ll', 'Й'), (r'LL', 'Й'),
            (r'rr', 'рр'), (r'Rr', 'Рр'), (r'RR', 'Рр'),
            (r'qu', 'к'), (r'Qu', 'К'), (r'QU', 'К'),
            (r'ce', 'се'), (r'Ce', 'Се'), (r'CE', 'Се'),
            (r'ci', 'си'), (r'Ci', 'Си'), (r'CI', 'Си'),
            (r'ge', 'хе'), (r'Ge', 'Хе'), (r'GE', 'Хе'),
            (r'gi', 'хи'), (r'Gi', 'Хи'), (r'GI', 'Хи'),
            (r'ca', 'ка'), (r'Ca', 'Ка'), (r'CA', 'Ка'),
            (r'co', 'ко'), (r'Co', 'Ко'), (r'CO', 'Ко'),
            (r'cu', 'ку'), (r'Cu', 'Ку'), (r'CU', 'Ку'),
            (r'ga', 'га'), (r'Ga', 'Га'), (r'GA', 'Га'),
            (r'go', 'го'), (r'Go', 'Го'), (r'GO', 'Го'),
            (r'gu', 'гу'), (r'Gu', 'Гу'), (r'GU', 'Гу'),
            (r'güe', 'гве'), (r'Güe', 'Гве'), (r'GÜE', 'Гве'),
            (r'güi', 'гви'), (r'Güi', 'Гви'), (r'GÜI', 'гви'),
        ]
        
        # Armenian rules
        self.armenian_special_rules = [
            (r'ու', 'у'), (r'ՈՒ', 'У'),
            (r'և', 'ев'),
        ]
        
        # Georgian rules
        self.georgian_special_rules = [
            (r'ღ', 'гъ'), (r'Ღ', 'Гъ'),
        ]
        
        # Turkish rules for ğ
        self.turkish_special_rules = [
            (r'([aeiouöüıAEİOUÖÜI])ğ([aeiouöüıAEİOUÖÜI])', r'\1й\2'),
            (r'([aeiouöüıAEİOUÖÜI])ğ\b', r'\1\1'),
            (r'ğ', ''), (r'Ğ', ''),
        ]
    
    def is_word_boundary(self, text, position):
        """Checks if position is at word boundary"""
        if position == 0 or position >= len(text):
            return True
        return not text[position-1].isalpha() or not text[position].isalpha()
    
    def detect_script(self, text):
        """
        Detects text script (for debugging)
        """
        # Check for Georgian characters
        georgian_chars = set('აბგდევზთიკლმნოპჟრსტუფქღყშჩცძწჭხჯჰ')
        if any(char in georgian_chars for char in text):
            return 'georgian'
        
        # Check for Armenian characters
        armenian_chars = set('աբգդեզէըթժիլխծկհձղճմյնշոչպջռսվտրցւփքօֆև')
        if any(char in armenian_chars for char in text):
            return 'armenian'
        
        # Check for Latvian characters
        latvian_chars = set('āčēģīķļņšūžĀČĒĢĪĶĻŅŠŪŽ')
        if any(char in latvian_chars for char in text):
            return 'latvian'
        
        # Check for German characters
        german_chars = set('äöüßÄÖÜẞ')
        if any(char in german_chars for char in text):
            return 'german'
        
        # Check for Spanish characters
        spanish_chars = set('áéíóúñÁÉÍÓÚÑ')
        if any(char in spanish_chars for char in text):
            return 'spanish'
        
        # Check for Turkish/Azerbaijani characters
        turkish_chars = set('çğıöşüâîûÇĞİÖŞÜÂÎÛ')
        if any(char in turkish_chars for char in text):
            return 'turkish/latin'
        
        # If Cyrillic present
        cyrillic_chars = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюя')
        if any(char.lower() in cyrillic_chars for char in text):
            return 'cyrillic'
        
        # If Latin present
        latin_chars = set('abcdefghijklmnopqrstuvwxyz')
        if any(char.lower() in latin_chars for char in text):
            return 'latin'
        
        return 'unknown'
    
    def transliterate_turkish_with_context(self, text):
        """Turkish transliteration with ğ handling"""
        for pattern, replacement in self.turkish_special_rules:
            text = re.sub(pattern, replacement, text)
        
        result = []
        for char in text:
            if char in self.turkish_to_kazakh:
                result.append(self.turkish_to_kazakh[char])
            else:
                result.append(char)
        
        return ''.join(result)
    
    def transliterate_german_with_boundaries(self, text):
        """German transliteration with word boundary handling"""
        result = []
        i = 0
        text_length = len(text)
        
        while i < text_length:
            char = text[i]
            matched = False
            
            # sp/st at word beginnings
            if self.is_word_boundary(text, i):
                if i + 2 <= text_length and text[i:i+2].lower() == 'sp':
                    result.append('шп' if text[i:i+2].islower() else 'Шп')
                    i += 2
                    matched = True
                elif i + 2 <= text_length and text[i:i+2].lower() == 'st':
                    result.append('шт' if text[i:i+2].islower() else 'Шт')
                    i += 2
                    matched = True
            
            if not matched:
                # s before vowel at word/syllable beginning = [z] → "з"
                if char.lower() == 's' and self.is_word_boundary(text, i):
                    # Check that vowel follows s
                    if i + 1 < text_length and text[i+1].lower() in 'aeiouäöü':
                        result.append('з' if char.islower() else 'З')
                        i += 1
                        matched = True
            
            if not matched:
                # First check special rules
                for pattern, replacement in self.german_special_rules:
                    pattern_len = len(pattern)
                    if i + pattern_len <= text_length and text[i:i+pattern_len] == pattern:
                        result.append(replacement)
                        i += pattern_len
                        matched = True
                        break
            
            if not matched:
                # er at word endings
                if i + 2 <= text_length and text[i:i+2].lower() == 'er' and self.is_word_boundary(text, i+2):
                    result.append('а' if text[i:i+2].islower() else 'А')
                    i += 2
                    matched = True
            
            if not matched:
                # Regular character replacement
                if char in self.german_to_hybrid:
                    result.append(self.german_to_hybrid[char])
                else:
                    result.append(char)
                i += 1
        
        return ''.join(result)

    def transliterate_spanish_with_boundaries(self, text):
        """Spanish transliteration"""
        result = []
        i = 0
        text_length = len(text)
        
        while i < text_length:
            char = text[i]
            matched = False
            
            # r at word beginning
            if char.lower() == 'r' and self.is_word_boundary(text, i):
                result.append('рр' if char.islower() else 'Рр')
                i += 1
                matched = True
            
            if not matched:
                for pattern, replacement in self.spanish_special_rules:
                    pattern_len = len(pattern)
                    if i + pattern_len <= text_length and text[i:i+pattern_len] == pattern:
                        result.append(replacement)
                        i += pattern_len
                        matched = True
                        break
            
            if not matched:
                if char in self.spanish_to_hybrid:
                    result.append(self.spanish_to_hybrid[char])
                else:
                    result.append(char)
                i += 1
        
        return ''.join(result)
    
    def transliterate_latvian_with_boundaries(self, text):
        """Latvian transliteration"""
        result = []
        i = 0
        text_length = len(text)
        
        while i < text_length:
            char = text[i]
            matched = False
            
            # o at word beginning/end
            if char.lower() == 'o':
                if self.is_word_boundary(text, i) or (i == text_length - 1) or self.is_word_boundary(text, i + 1):
                    result.append('уо' if char.islower() else 'Уо')
                    i += 1
                    matched = True
            
            if not matched:
                for pattern, replacement in self.latvian_special_rules:
                    pattern_len = len(pattern)
                    if i + pattern_len <= text_length and text[i:i+pattern_len] == pattern:
                        result.append(replacement)
                        i += pattern_len
                        matched = True
                        break
            
            if not matched:
                if char in self.latvian_to_hybrid:
                    result.append(self.latvian_to_hybrid[char])
                else:
                    result.append(char)
                i += 1
        
        return ''.join(result)
    
    def transliterate_georgian_direct(self, text):
        """Georgian transliteration"""
        for pattern, replacement in self.georgian_special_rules:
            text = re.sub(pattern, replacement, text)
        
        result = []
        for char in text:
            if char in self.georgian_to_kabardian:
                result.append(self.georgian_to_kabardian[char])
            else:
                result.append(char)
        
        return ''.join(result)
    
    def transliterate_armenian_direct(self, text):
        """Armenian transliteration"""
        for pattern, replacement in self.armenian_special_rules:
            text = re.sub(pattern, replacement, text)
        
        result = []
        for char in text:
            if char in self.armenian_to_hybrid:
                result.append(self.armenian_to_hybrid[char])
            else:
                result.append(char)
        
        return ''.join(result)
    
    def transliterate_azerbaijani_direct(self, text):
        """Azerbaijani transliteration"""
        result = []
        for char in text:
            if char in self.azerbaijani_to_kazakh:
                result.append(self.azerbaijani_to_kazakh[char])
            else:
                result.append(char)
        return ''.join(result)
    
    def transliterate_for_tts(self, text, source_lang, target_script='kbd'):
        """
        Text transliteration for TTS
        """
        if not text.strip():
            return text
        
        original_text = text
        
        try:
            if source_lang == 'tur_Latn':
                transliterated = self.transliterate_turkish_with_context(text)
                
            elif source_lang == 'azj_Latn':
                transliterated = self.transliterate_azerbaijani_direct(text)
                
            elif source_lang == 'lvs_Latn':
                transliterated = self.transliterate_latvian_with_boundaries(text)
                target_script = 'hybrid'
                
            elif source_lang == 'deu_Latn':
                transliterated = self.transliterate_german_with_boundaries(text)
                target_script = 'hybrid'
                
            elif source_lang == 'spa_Latn':
                transliterated = self.transliterate_spanish_with_boundaries(text)
                target_script = 'hybrid'
                
            elif source_lang == 'kat_Geor':
                transliterated = self.transliterate_georgian_direct(text)
                target_script = 'kbd'
                
            elif source_lang == 'hye_Armn':
                transliterated = self.transliterate_armenian_direct(text)
                target_script = 'kbd'
                
            else:
                return text
            
            return transliterated
            
        except Exception as e:
            print(f"❌ Transliteration error {source_lang}: {e}")
            import traceback
            traceback.print_exc()
            return text
    
    def needs_transliteration(self, lang_code):
        """
        Checks if transliteration is needed for the language
        """
        return lang_code in ['tur_Latn', 'azj_Latn', 'kat_Geor', 'hye_Armn', 'lvs_Latn', 'deu_Latn', 'spa_Latn']
    
    def get_target_speaker(self, lang_code):
        """
        Determines which speaker to use after transliteration
        """
        if lang_code in ['lvs_Latn', 'deu_Latn', 'spa_Latn']:
            return 'ru_eduard'
        return 'kbd_eduard'

# Global instance
transliterator = TransliteratorFinal()

# Test functions
def test_transliteration():
    """Testing transliteration with word boundaries"""
    test_cases = [
        # German examples - UPDATED!
        ('deu_Latn', 'sport', 'шпорт'),
        ('deu_Latn', 'Student', 'Штудент'),
        ('deu_Latn', 'Hallo', 'Халло'),
        ('deu_Latn', 'tschüss', 'чюсс'),
        ('deu_Latn', 'schön', 'шөн'),
        ('deu_Latn', 'München', 'Мйюнхен'),
        ('deu_Latn', 'Straße', 'Штрассе'),
        ('deu_Latn', 'Sprache', 'Шпрахэ'),
        ('deu_Latn', 'Boot', 'боот'),
        ('deu_Latn', 'Sohn', 'зоон'),
        ('deu_Latn', 'Bahn', 'баан'),
        ('deu_Latn', 'gehen', 'гээн'),
        ('deu_Latn', 'See', 'зээ'),
        ('deu_Latn', 'Liebe', 'лиибе'),
        ('deu_Latn', 'Deutsch', 'дойч'),
        ('deu_Latn', 'Philosophie', 'философии'),
        ('deu_Latn', 'über', 'йюбер'),
        ('deu_Latn', 'sowohl', 'зовал'),
        
        # Spanish examples
        ('spa_Latn', 'Hola', 'Ола'),
        ('spa_Latn', 'gracias', 'грасиас'),
        ('spa_Latn', 'mañana', 'маньана'),
        ('spa_Latn', 'chico', 'чико'),
        ('spa_Latn', 'llamar', 'йамар'),
        
        # Latvian examples
        ('lvs_Latn', 'labdien', 'лабдиен'),
        ('lvs_Latn', 'paldies', 'палдиес'),
        ('lvs_Latn', 'Rīga', 'Рийга'),
        
        # Georgian examples
        ('kat_Geor', 'გამარჯობა', 'гамарджоба'),
        ('kat_Geor', 'თბილისი', 'тъбилисы'),
        
        # Armenian examples  
        ('hye_Armn', 'բարև', 'барев'),
        ('hye_Armn', 'երեկան', 'ерекан'),
        
        # Turkish examples
        ('tur_Latn', 'merhaba', 'мерһаба'),
        
        # Azerbaijani examples
        ('azj_Latn', 'salam', 'салам'),
    ]
    
    print("🧪 Testing transliteration with word boundaries:")
    for lang, original, expected in test_cases:
        result = transliterator.transliterate_for_tts(original, lang)
        status = "✅" if result == expected else "❌"
        print(f"{status} {lang}: '{original}' → '{result}' (expected: '{expected}')")

if __name__ == "__main__":
    test_transliteration()