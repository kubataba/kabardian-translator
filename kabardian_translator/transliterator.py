# transliterator.py
# Transliteration for TTS: Turkish, Azerbaijani, Georgian, Armenian, Latvian, German, Spanish → Kazakh/Kabardian Cyrillic
# License: CC BY-NC 4.0 (Non-Commercial Use Only)

import re

class Transliterator:
    """Transliterator for TTS with proper word boundary handling"""
    
    def __init__(self):
        self.setup_transliteration_rules()
    
    def setup_transliteration_rules(self):
        """Setup transliteration rules"""
        
        # TURKISH (Latin) → Kazakh Cyrillic
        self.turkish_to_kazakh = {
            'a': 'а', 'A': 'А',
            'b': 'б', 'B': 'Б', 
            'c': 'ж', 'C': 'Ж',  # Turkish c = [dʒ]
            'ç': 'ч', 'Ç': 'Ч',
            'd': 'д', 'D': 'Д',
            'e': 'е', 'E': 'Е',
            'f': 'ф', 'F': 'Ф',
            'g': 'г', 'G': 'Г',
            'ğ': 'ғ', 'Ğ': 'Ғ',  # Kazakh ғ
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
            "'": "", "’": ""  # remove apostrophes
        }
        
        # AZERBAIJANI (Latin) → Kazakh Cyrillic  
        self.azerbaijani_to_kazakh = {
            'a': 'а', 'A': 'А',
            'b': 'б', 'B': 'Б',
            'c': 'ж', 'C': 'Ж',
            'ç': 'ч', 'Ç': 'Ч',
            'd': 'д', 'D': 'Д',
            'e': 'е', 'E': 'Е',
            'ə': 'ә', 'Ə': 'Ә',  # important sound!
            'f': 'ф', 'F': 'Ф',
            'g': 'г', 'G': 'Г',
            'ğ': 'ғ', 'Ğ': 'Ғ',
            'h': 'һ', 'H': 'Һ',
            'x': 'х', 'X': 'Х',  # separate letter for [x]
            'ı': 'ы', 'I': 'Ы',
            'i': 'і', 'İ': 'І',
            'j': 'ж', 'J': 'Ж',
            'k': 'к', 'K': 'К',
            'q': 'г', 'Q': 'Г',  # Azerbaijani q = [g]
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
        }
        
        # LATVIAN (Latin) → hybrid Kazakh + Kabardian Cyrillic
        self.latvian_to_hybrid = {
            # Basic letters
            'a': 'а', 'A': 'А',
            'b': 'б', 'B': 'Б',
            'c': 'ц', 'C': 'Ц',
            'd': 'д', 'D': 'Д',
            'e': 'э', 'E': 'Э',  # Latvian e = [ɛ] like Russian "э"
            'f': 'ф', 'F': 'Ф',
            'g': 'г', 'G': 'Г',
            'h': 'х', 'H': 'Х',  # Latvian h = [x]
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
            
            # Latvian diacritical letters
            'ā': 'аа', 'Ā': 'Аа',  # long a [aː]
            'č': 'ч', 'Č': 'Ч',     # č = [tʃ]
            'ē': 'ээ', 'Ē': 'Ээ',   # long e [ɛː]
            'ģ': 'гь', 'Ģ': 'Гь',   # palatalized g
            'ī': 'ий', 'Ī': 'Ий',   # long i [iː]
            'ķ': 'кь', 'Ķ': 'Кь',   # palatalized k
            'ļ': 'ль', 'Ļ': 'Ль',   # palatalized l
            'ņ': 'нь', 'Ņ': 'Нь',   # palatalized n
            'š': 'ш', 'Š': 'Ш',     # š = [ʃ]
            'ū': 'уу', 'Ū': 'Уу',   # long u [uː]
            'ž': 'ж', 'Ž': 'Ж',     # ž = [ʒ]
        }
        
        # GERMAN (Latin) → hybrid Cyrillic
        self.german_to_hybrid = {
            # Basic letters
            'a': 'а', 'A': 'А',
            'b': 'б', 'B': 'Б',
            'c': 'ц', 'C': 'Ц',
            'd': 'д', 'D': 'Д',
            'e': 'э', 'E': 'Э',  # German e = [ɛ]
            'f': 'ф', 'F': 'Ф',
            'g': 'г', 'G': 'Г',
            'h': 'х', 'H': 'Х',  # German h = [h] at start, [x] after vowels
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
            'v': 'ф', 'V': 'Ф',  # German v = [f]
            'w': 'в', 'W': 'В',  # German w = [v]
            'x': 'кс', 'X': 'Кс',
            'y': 'ю', 'Y': 'Ю',  # German y = [y]
            'z': 'ц', 'Z': 'Ц',  # German z = [ts]
            
            # Umlauts and special symbols
            'ä': 'ә', 'Ä': 'Ә',  # [ɛ] → ә
            'ö': 'ө', 'Ö': 'Ө',  # [ø] → ө
            'ü': 'ү', 'Ü': 'Ү',  # [y] → ү
            'ß': 'сс', 'ẞ': 'СС', # eszett = [s]
            
            # Additional symbols
            "'": "", "’": "", "-": "-", " ": " "
        }
        
        # SPANISH (Latin) → hybrid Cyrillic
        self.spanish_to_hybrid = {
            # Basic letters
            'a': 'а', 'A': 'А',
            'b': 'б', 'B': 'Б',
            'c': 'к', 'C': 'К',  # will be processed by special rules
            'd': 'д', 'D': 'Д',
            'e': 'э', 'E': 'Э',  # Spanish e = [e]
            'f': 'ф', 'F': 'Ф',
            'g': 'г', 'G': 'Г',  # will be processed by special rules
            'h': '', 'H': '',    # Spanish h is silent
            'i': 'и', 'I': 'И',
            'j': 'х', 'J': 'Х',  # Spanish j = [x]
            'k': 'к', 'K': 'К',
            'l': 'л', 'L': 'Л',
            'm': 'м', 'M': 'М',
            'n': 'н', 'N': 'Н',
            'o': 'о', 'O': 'О',
            'p': 'п', 'P': 'П',
            'q': 'к', 'Q': 'К',  # always with u, will be processed specially
            'r': 'р', 'R': 'Р',  # will be processed by special rules
            's': 'с', 'S': 'С',
            't': 'т', 'T': 'Т',
            'u': 'у', 'U': 'У',
            'v': 'в', 'V': 'В',  # Spanish v = [b]
            'w': 'в', 'W': 'В',  # rare, in loanwords
            'x': 'кс', 'X': 'Кс',
            'y': 'й', 'Y': 'Й',  # Spanish y = [ʝ]
            'z': 'с', 'Z': 'С',  # Spanish z = [θ] or [s]
            
            # Diacritical marks
            'á': 'а', 'Á': 'А',
            'é': 'э', 'É': 'Э',
            'í': 'и', 'Í': 'И',
            'ó': 'о', 'Ó': 'О',
            'ú': 'у', 'Ú': 'У',
            'ñ': 'нь', 'Ñ': 'Нь',  # Spanish ñ = [ɲ]
            'ü': 'у', 'Ü': 'У',    # in Spanish ü indicates u pronunciation
            
            # Additional symbols
            "'": "", "’": "", "-": "-", " ": " "
        }
        
        # GEORGIAN (original alphabet) → Kabardian Cyrillic
        self.georgian_to_kabardian = {
            # Lowercase letters
            'ა': 'а', 'ბ': 'б', 'გ': 'г', 'დ': 'д', 'ე': 'э', 'ვ': 'в',
            'ზ': 'з', 'თ': 'т', 'ი': 'ы', 'კ': 'кӀ', 'ლ': 'л', 'მ': 'м',
            'ნ': 'н', 'ო': 'о', 'პ': 'пӀ', 'ჟ': 'ж', 'რ': 'р', 'ს': 'с',
            'ტ': 'тӀ', 'უ': 'у', 'ფ': 'п', 'ქ': 'к', 'ღ': 'гъ', 'ყ': 'кӀ',
            'შ': 'ш', 'ჩ': 'ч', 'ც': 'ц', 'ძ': 'дз', 'წ': 'цӀ', 'ჭ': 'чӀ',
            'ხ': 'хъ', 'ჯ': 'дж', 'ჰ': 'һ',
            
            # Uppercase letters  
            'Ⴀ': 'А', 'Ⴁ': 'Б', 'Ⴂ': 'Г', 'Ⴃ': 'Д', 'Ⴄ': 'Э', 'Ⴅ': 'В',
            'Ⴆ': 'З', 'Ⴇ': 'Т', 'Ⴈ': 'Ы', 'Ⴉ': 'КӀ', 'Ⴊ': 'Л', 'Ⴋ': 'М',
            'Ⴌ': 'Н', 'Ⴍ': 'О', 'Ⴎ': 'ПӀ', 'Ⴏ': 'Ж', 'Ⴐ': 'Р', 'Ⴑ': 'С',
            'Ⴒ': 'ТӀ', 'Ⴓ': 'У', 'Ⴔ': 'П', 'Ⴕ': 'К', 'Ⴖ': 'Гъ', 'Ⴗ': 'КӀ',
            'Ⴘ': 'Ш', 'Ⴙ': 'Ч', 'Ⴚ': 'Ц', 'Ⴛ': 'Дз', 'Ⴜ': 'ЦӀ', 'Ⴝ': 'ЧӀ',
            'Ⴞ': 'Хъ', 'Ⴟ': 'Дж', 'Ⴠ': 'Һ',
            
            # Modern uppercase (Mkhedruli)
            'Ა': 'А', 'Ბ': 'Б', 'Გ': 'Г', 'Დ': 'Д', 'Ე': 'Э', 'Ვ': 'В',
            'Ზ': 'З', 'Თ': 'Т', 'Ი': 'Ы', 'Კ': 'КӀ', 'Ლ': 'Л', 'Მ': 'М',
            'Ნ': 'Н', 'Ო': 'О', 'Პ': 'ПӀ', 'Ჟ': 'Ж', 'Რ': 'Р', 'Ს': 'С',
            'Ტ': 'ТӀ', 'Უ': 'У', 'Ფ': 'П', 'Ქ': 'К', 'Ღ': 'Гъ', 'Ყ': 'КӀ',
            'Შ': 'Ш', 'Ჩ': 'Ч', 'Ც': 'Ц', 'Ძ': 'Дз', 'Წ': 'ЦӀ', 'Ჭ': 'чӀ',
            'Ხ': 'хъ', 'Ჯ': 'дж', 'Ჰ': 'һ'
        }
        
        # ARMENIAN (original alphabet) → hybrid Kazakh + Kabardian
        self.armenian_to_hybrid = {
            # Lowercase letters
            'ա': 'а', 'բ': 'б', 'գ': 'г', 'դ': 'д', 'ե': 'е', 'զ': 'з',
            'է': 'е', 'ը': 'ы', 'թ': 'т', 'ժ': 'ж', 'ի': 'и', 'լ': 'л',
            'խ': 'хъ', 'ծ': 'ц', 'կ': 'к', 'հ': 'һ', 'ձ': 'дз', 'ղ': 'гъ',
            'ճ': 'дж', 'մ': 'м', 'յ': 'й', 'ն': 'н', 'շ': 'ш', 'ո': 'о',
            'չ': 'ч', 'պ': 'п', 'ջ': 'дж', 'ռ': 'р', 'ս': 'с', 'վ': 'в',
            'տ': 'т', 'ր': 'р', 'ց': 'ц', 'ւ': 'в', 'փ': 'п', 'ք': 'к',
            'օ': 'о', 'ֆ': 'ф', 'ու': 'у', 'և': 'ев',
            
            # Uppercase letters
            'Ա': 'А', 'Բ': 'Б', 'Գ': 'Г', 'Դ': 'Д', 'Ե': 'Е', 'Զ': 'З',
            'Է': 'Е', 'Ը': 'Ы', 'Թ': 'Т', 'Ժ': 'Ж', 'Ի': 'И', 'Լ': 'Л',
            'Խ': 'Хъ', 'Ծ': 'Ц', 'Կ': 'К', 'Հ': 'Һ', 'Ձ': 'Дз', 'Ղ': 'Гъ',
            'Ճ': 'Дж', 'Մ': 'М', 'Յ': 'Й', 'Ն': 'Н', 'Շ': 'Ш', 'Ո': 'О',
            'Չ': 'Ч', 'Պ': 'П', 'Ջ': 'Дж', 'Ռ': 'Р', 'Ս': 'С', 'Վ': 'В',
            'Տ': 'Т', 'Ր': 'Р', 'Ց': 'Ц', 'Ւ': 'В', 'Փ': 'П', 'Ք': 'К',
            'Օ': 'О', 'Ֆ': 'Ф', 'ՈՒ': 'У', 'ԵՎ': 'Ев',
            
            # Ligatures and special symbols
            'ւ': 'в', 'և': 'ев'
        }
        
        # SPECIAL RULES WITH WORD BOUNDARIES
        self.latvian_special_rules = [
            (r'ch', 'х'), (r'Ch', 'Х'), (r'CH', 'Х'),
            (r'dz', 'дз'), (r'Dz', 'Дз'), (r'DZ', 'Дз'),
            (r'dž', 'дж'), (r'Dž', 'Дж'), (r'DŽ', 'Дж'),
            (r'ie', 'ие'), (r'Ie', 'Ие'), (r'IE', 'Ие'),
        ]
        
        # GERMAN RULES WITH WORD BOUNDARIES
        self.german_special_rules = [
            # sp/st at word beginnings
            (r'sch', 'ш'), (r'Sch', 'Ш'), (r'SCH', 'Ш'),
            (r'ch', 'х'), (r'Ch', 'Х'), (r'CH', 'Х'),
            (r'tsch', 'ч'), (r'Tsch', 'Ч'), (r'TSCH', 'Ч'),
            (r'ck', 'к'), (r'Ck', 'К'), (r'CK', 'К'),
            (r'ph', 'ф'), (r'Ph', 'Ф'), (r'PH', 'Ф'),
            (r'th', 'т'), (r'Th', 'Т'), (r'TH', 'Т'),
            (r'äh', 'ә'), (r'Äh', 'Ә'), (r'ÄH', 'Ә'),
            (r'öh', 'ө'), (r'Öh', 'Ө'), (r'ÖH', 'Ө'),
            (r'üh', 'ү'), (r'Üh', 'Ү'), (r'ÜH', 'Ү'),
            (r'ie', 'и'), (r'Ie', 'И'), (r'IE', 'И'),
            (r'eu', 'ой'), (r'Eu', 'Ой'), (r'EU', 'Ой'),
            (r'äu', 'ой'), (r'Äu', 'Ой'), (r'ÄU', 'Ой'),
        ]
        
        # SPANISH RULES WITH WORD BOUNDARIES
        self.spanish_special_rules = [
            (r'ch', 'ч'), (r'Ch', 'Ч'), (r'CH', 'Ч'),
            (r'll', 'ль'), (r'Ll', 'Ль'), (r'LL', 'Ль'),
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
            (r'gü', 'гв'), (r'Gü', 'Гв'), (r'GÜ', 'Гв'),
            (r'ñ', 'нь'), (r'Ñ', 'Нь'),
        ]
        
        # ARMENIAN RULES
        self.armenian_special_rules = [
            (r'ու', 'у'), (r'և', 'ев'), (r'ո', 'во'), (r'Ո', 'Во'),
        ]
        
        # GEORGIAN RULES
        self.georgian_special_rules = [
            (r'ღ', 'гъ'), (r'ყ', 'кӀ'), (r'წ', 'цӀ'), (r'ჭ', 'чӀ'),
        ]
    
    def is_word_boundary(self, text, position):
        """Checks if position is at word boundary"""
        if position == 0 or position >= len(text):
            return True
        return not text[position-1].isalpha() or not text[position].isalpha()
    
    def transliterate_german_with_boundaries(self, text):
        """German transliteration with word boundary consideration"""
        result = []
        i = 0
        text_length = len(text)
        
        while i < text_length:
            char = text[i]
            matched = False
            
            # Process sp/st at word beginnings
            if self.is_word_boundary(text, i):
                if text[i:i+2].lower() == 'sp':
                    result.append('шп' if text[i:i+2].islower() else 'Шп')
                    i += 2
                    matched = True
                elif text[i:i+2].lower() == 'st':
                    result.append('шт' if text[i:i+2].islower() else 'Шт')
                    i += 2
                    matched = True
            
            if not matched:
                # Process er at word endings
                if i + 2 <= text_length and text[i:i+2].lower() == 'er' and self.is_word_boundary(text, i+2):
                    result.append('а' if text[i:i+2].islower() else 'А')
                    i += 2
                    matched = True
            
            if not matched:
                # Process r at word beginnings
                if char.lower() == 'r' and self.is_word_boundary(text, i):
                    result.append('гӀ' if char.islower() else 'Ғр')
                    i += 1
                    matched = True
            
            if not matched:
                # Regular special rules
                for pattern, replacement in self.german_special_rules:
                    if text[i:].startswith(pattern):
                        result.append(replacement)
                        i += len(pattern)
                        matched = True
                        break
            
            if not matched:
                # Regular character replacement
                if char in self.german_to_hybrid:
                    result.append(self.german_to_hybrid[char])
                else:
                    result.append(char)
                i += 1
        
        return ''.join(result)
    
    def transliterate_spanish_with_boundaries(self, text):
        """Spanish transliteration with word boundary consideration"""
        result = []
        i = 0
        text_length = len(text)
        
        while i < text_length:
            char = text[i]
            matched = False
            
            # Process r at word beginnings (strong pronunciation)
            if char.lower() == 'r' and self.is_word_boundary(text, i):
                result.append('рр' if char.islower() else 'Рр')
                i += 1
                matched = True
            
            if not matched:
                # Regular special rules
                for pattern, replacement in self.spanish_special_rules:
                    if text[i:].startswith(pattern):
                        result.append(replacement)
                        i += len(pattern)
                        matched = True
                        break
            
            if not matched:
                # Regular character replacement
                if char in self.spanish_to_hybrid:
                    result.append(self.spanish_to_hybrid[char])
                else:
                    result.append(char)
                i += 1
        
        return ''.join(result)
    
    def transliterate_latvian_with_boundaries(self, text):
        """Latvian transliteration with word boundary consideration"""
        result = []
        i = 0
        text_length = len(text)
        
        while i < text_length:
            char = text[i]
            matched = False
            
            # Process o at word beginnings/endings
            if char.lower() == 'o':
                if self.is_word_boundary(text, i):  # o at word beginning
                    result.append('уо' if char.islower() else 'Уо')
                    i += 1
                    matched = True
                elif i == text_length - 1 or self.is_word_boundary(text, i + 1):  # o at word ending
                    result.append('уо' if char.islower() else 'Уо')
                    i += 1
                    matched = True
            
            if not matched:
                # Regular special rules
                for pattern, replacement in self.latvian_special_rules:
                    if text[i:].startswith(pattern):
                        result.append(replacement)
                        i += len(pattern)
                        matched = True
                        break
            
            if not matched:
                # Regular character replacement
                if char in self.latvian_to_hybrid:
                    result.append(self.latvian_to_hybrid[char])
                else:
                    result.append(char)
                i += 1
        
        return ''.join(result)
    
    def transliterate_georgian_direct(self, text):
        """Direct Georgian alphabet transliteration"""
        result = []
        i = 0
        
        while i < len(text):
            char = text[i]
            matched = False
            
            # Check for special combinations
            for pattern, replacement in self.georgian_special_rules:
                if text[i:].startswith(pattern):
                    result.append(replacement)
                    i += len(pattern)
                    matched = True
                    break
            
            if not matched:
                # Regular character replacement
                if char in self.georgian_to_kabardian:
                    result.append(self.georgian_to_kabardian[char])
                else:
                    result.append(char)
                i += 1
        
        return ''.join(result)
    
    def transliterate_armenian_direct(self, text):
        """Direct Armenian alphabet transliteration"""
        # First process special combinations
        for pattern, replacement in self.armenian_special_rules:
            text = re.sub(pattern, replacement, text)
        
        # Then process single characters
        result = []
        for char in text:
            if char in self.armenian_to_hybrid:
                result.append(self.armenian_to_hybrid[char])
            else:
                result.append(char)
        
        return ''.join(result)
    
    def transliterate_turkish_direct(self, text):
        """Direct Turkish alphabet transliteration"""
        result = []
        for char in text:
            if char in self.turkish_to_kazakh:
                result.append(self.turkish_to_kazakh[char])
            else:
                result.append(char)
        return ''.join(result)
    
    def transliterate_azerbaijani_direct(self, text):
        """Direct Azerbaijani alphabet transliteration"""
        result = []
        for char in text:
            if char in self.azerbaijani_to_kazakh:
                result.append(self.azerbaijani_to_kazakh[char])
            else:
                result.append(char)
        return ''.join(result)
    
    def transliterate_for_tts(self, text, source_lang, target_script='kbd'):
        """
        Text transliteration for TTS with proper word boundary handling
        
        Args:
            text: source text
            source_lang: source language code
            target_script: 'kbd' (Kabardian) or 'kaz' (Kazakh)
        
        Returns:
            transliterated text
        """
        if not text.strip():
            return text
        
        original_text = text
        
        try:
            if source_lang == 'tur_Latn':
                transliterated = self.transliterate_turkish_direct(text)
                
            elif source_lang == 'azj_Latn':
                transliterated = self.transliterate_azerbaijani_direct(text)
                
            elif source_lang == 'lav_Latn':
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
            
            print(f"🔤 Transliteration {source_lang}→{target_script}: '{original_text[:30]}...' → '{transliterated[:30]}...'")
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
        return lang_code in ['tur_Latn', 'azj_Latn', 'kat_Geor', 'hye_Armn', 'lav_Latn', 'deu_Latn', 'spa_Latn']
    
    def get_target_speaker(self, lang_code):
        """
        Determines which speaker to use after transliteration
        """
        # Latvian, German and Spanish use Russian speaker after transliteration
        if lang_code in ['lav_Latn', 'deu_Latn', 'spa_Latn']:
            return 'ru_eduard'
        # Other transliterated languages use Kabardian speaker
        return 'kbd_eduard'
    
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

# Global instance
transliterator = Transliterator()

# Test functions
def test_transliteration():
    """Testing transliteration with word boundaries"""
    test_cases = [
        # German examples - should NOW work correctly!
        ('deu_Latn', 'sport', 'шпорт'),                    # Sport (sp at word beginning)
        ('deu_Latn', 'Student', 'Штудент'),                # Student (st at word beginning)
        ('deu_Latn', 'Hallo', 'Халло'),                    # Hello
        ('deu_Latn', 'tschüss', 'чюсс'),                   # Bye
        ('deu_Latn', 'schön', 'шөн'),                      # Beautiful
        ('deu_Latn', 'München', 'Мюнхен'),                 # Munich
        ('deu_Latn', 'Straße', 'Штрассе'),                 # Street (st at beginning!)
        ('deu_Latn', 'Sprache', 'Шпрахэ'),                 # Language (sp at beginning!)
        
        # Spanish examples
        ('spa_Latn', 'Hola', 'Ола'),                       # Hello
        ('spa_Latn', 'gracias', 'грасиас'),                # Thank you
        ('spa_Latn', 'mañana', 'маньана'),                 # Tomorrow
        ('spa_Latn', 'chico', 'чико'),                     # Boy
        ('spa_Latn', 'llamar', 'льямар'),                  # To call
        
        # Latvian examples
        ('lav_Latn', 'labdien', 'лабдиен'),                # Good day
        ('lav_Latn', 'paldies', 'палдиес'),                # Thank you
        ('lav_Latn', 'Rīga', 'Рийга'),                     # Riga
        
        # Georgian examples
        ('kat_Geor', 'გამარჯობა', 'гъамарджоба'),          # Hello
        ('kat_Geor', 'თბილისი', 'тӀбилисы'),               # Tbilisi
        
        # Armenian examples  
        ('hye_Armn', 'բարև', 'барев'),                     # Hello
        ('hye_Armn', 'երեկան', 'ерекан'),                  # Evening
        
        # Turkish examples
        ('tur_Latn', 'merhaba', 'мерһаба'),                # Hello
        
        # Azerbaijani examples
        ('azj_Latn', 'salam', 'салам'),                    # Hello
    ]
    
    print("🧪 Testing transliteration with word boundaries:")
    for lang, original, expected in test_cases:
        result = transliterator.transliterate_for_tts(original, lang)
        status = "✅" if result == expected else "❌"
        print(f"{status} {lang}: '{original}' → '{result}' (expected: '{expected}')")

if __name__ == "__main__":
    test_transliteration()