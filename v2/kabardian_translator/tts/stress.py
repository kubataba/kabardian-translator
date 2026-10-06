"""Stress marks for Silero without PyTorch.

The logic is silero-stress 1.5 (MIT, (c) 2020-present Silero Team) — `AccentorNgram`, `AccentorNgramSimple`,
`HomoSolver` and its BERT tokenizer — kept as in the original; only the two networks are replaced by the files the
SayFable app runs (exported by `scripts/export_ru_stress.py`, release packs v5.1 and v5.3):

  * the n-gram accentor (FastText-style EmbeddingBag + MLP, ru with the ё head) — numpy over `accentor_*_weights.bin`;
  * the homograph BERT — ONNX Runtime over `ru_homosolver_bert.onnx` (int8 embedding restored inside the graph).

Russian: homograph solver (built-in phrases, then BERT) → accentor (exceptions, then the network, ё head).
Ukrainian and Belarusian: the simple accentor (Belarusian exceptions exported from the original package).
Only these three languages get stress marks: the Silero model is the no-stress v5, the rest read without them.
"""
from __future__ import annotations

import collections
import json
import re
import struct
import unicodedata
from importlib import resources
from pathlib import Path

import numpy as np


# ------------------------------------------------------------------------------------------ the n-gram network
def _word_ngrams(text: str, min_len: int, max_len: int) -> list:
    """TorchScript `models.modules.word_ngrams` of the original."""
    out = []
    b = "<" + text + ">"
    for n in range(min_len, max_len + 1):
        out.extend(b[i:i + n] for i in range(len(b) - n + 1))
    if len(text) < min_len:
        out.append(text)
    return out


class NgramMLP:
    """`accentor_<lang>_dict.json` (n-gram → row) + `accentor_<lang>_weights.bin` (format 1: little-endian u32
    header length, JSON header, then float32 embedding, stress layers and optional ё-head layers)."""

    def __init__(self, dict_path: Path, bin_path: Path):
        self.ngrams = json.loads(Path(dict_path).read_text("utf-8"))
        blob = Path(bin_path).read_bytes()
        hl = struct.unpack("<I", blob[:4])[0]
        header = json.loads(blob[4:4 + hl])
        off = 4 + hl

        def take(*shape):
            nonlocal off
            n = int(np.prod(shape))
            a = np.frombuffer(blob, dtype="<f4", count=n, offset=off).reshape(shape)
            off += 4 * n
            return a
        self.E = take(*header["embedding"])
        self.layers = [(take(*l["w"]), take(*l["b"])) for l in header["layers"]]
        self.yo_layers = [(take(*l["w"]), take(*l["b"])) for l in header.get("yo_layers") or []]
        self.unk = header["unk"]

    def _embed(self, words):
        out = np.zeros((len(words), self.E.shape[1]), np.float32)
        for i, w in enumerate(words):
            ids = [self.ngrams[g] for g in _word_ngrams(w, 1, len(w) + 3) if g in self.ngrams] or [self.unk]
            out[i] = self.E[ids].mean(0)
        return out

    @staticmethod
    def _mlp(x, layers):
        for i, (w, b) in enumerate(layers):
            x = x @ w.T + b
            if i < len(layers) - 1:
                x = np.maximum(x, 0)
        return x

    def __call__(self, words):
        x = self._embed(words)
        return self._mlp(x, self.layers), (self._mlp(x, self.yo_layers) if self.yo_layers else None)


def _softmax(x):
    e = np.exp(x - x.max(1, keepdims=True))
    return e / e.sum(1, keepdims=True)


# ------------------------------------------------------------------------------------------ Russian accentor
class AccentorNgram:
    """silero-stress 1.5 `models/accentor.py`, the network swapped for `NgramMLP`."""

    def __init__(self, model: NgramMLP, exceptions: dict, stress_token="+"):
        self.model = model
        self.exceptions = {w: (int(v[0]), int(v[1])) for w, v in exceptions.items()}
        self.stress_token = stress_token
        self.re_cond = r'[^А-Яа-яёЁ]'
        self.vowels = 'аоуыэиеяёю'

    def __call__(self, sentence, put_stress=True, put_yo=True, stress_single_vowel=True, skip_stress_words=None,
                 skip_yo_words=None, words_to_ignore=None):
        skip_stress_words = skip_stress_words if skip_stress_words is not None else []
        skip_yo_words = skip_yo_words if skip_yo_words is not None else []
        if not (put_stress or put_yo):
            return sentence
        raw_tokens, clean_tokens, prediction_mask = self._tokenize(sentence, words_to_ignore)
        stress_probs, stress_preds, yo_probs, yo_preds = self._get_model_preds(clean_tokens)
        accented_sentence = []
        for word_idx, (raw_word, clean_word, need_processing) in enumerate(zip(raw_tokens, clean_tokens, prediction_mask)):
            raw_word_lower = raw_word.lower()
            if not need_processing:
                accented_sentence.append(raw_word)
                continue
            have_stress = self.stress_token in raw_word_lower
            have_yo = 'ё' in raw_word_lower
            if have_stress is True and have_yo is True:
                accented_sentence.append(raw_word)
                continue
            if have_stress is False and have_yo is True and put_stress:
                if (sum(c in self.vowels for c in raw_word_lower) == 1 and not stress_single_vowel) or \
                        clean_word.replace('ё', 'е') in skip_stress_words:
                    accented_sentence.append(raw_word)
                    continue
                user_yo_positions = [i for i, x in enumerate(raw_word_lower) if x == 'ё']
                for i, yo_pos in enumerate(user_yo_positions):
                    raw_word = raw_word[:(yo_pos + i)] + self.stress_token + raw_word[(yo_pos + i):]
                accented_sentence.append(raw_word)
                continue
            if clean_word in self.exceptions:
                accented_sentence.append(self._accentuate_exception(clean_word, raw_word, have_stress))
                continue
            stressed_vowel_ids = [stress_preds[word_idx]]
            passed_stress_trs = stress_probs[word_idx][stressed_vowel_ids[0]] > (0.5 if put_stress else 1)
            set_stress = passed_stress_trs and not have_stress and (clean_word.replace('ё', 'е') not in skip_stress_words)
            yo_vowel_ids = [yo_preds[word_idx]] if yo_preds is not None else [-10]
            passed_yo_trs = yo_preds is not None and yo_probs[word_idx][yo_vowel_ids[0]] > (0.5 if put_yo else 1)
            set_yo = passed_yo_trs and (clean_word.replace('ё', 'е') not in skip_yo_words)
            if have_stress:
                stressed_vowel_ids = [sum(map(part.count, self.vowels)) for part in raw_word_lower.split(self.stress_token)]
            stress_positions, yo_positions, num_vowels, first_vowel_pos = self._get_positions(
                raw_word_lower, stressed_vowel_ids, yo_vowel_ids)
            if num_vowels == 0:
                accented_sentence.append(raw_word)
                continue
            for yo_pos in yo_positions:
                if yo_pos in stress_positions and set_yo:
                    if raw_word_lower[yo_pos] == 'е':
                        raw_word = raw_word[:yo_pos] + ('ё' if raw_word[yo_pos].islower() else 'Ё') + raw_word[(yo_pos + 1):]
            if num_vowels == 1:
                stress_positions = [first_vowel_pos]
                set_stress = stress_single_vowel and put_stress
            if not have_stress and set_stress:
                for i, stress_pos in enumerate(stress_positions):
                    raw_word = raw_word[:(stress_pos + i)] + self.stress_token + raw_word[(stress_pos + i):]
            accented_sentence.append(raw_word)
        return ''.join(accented_sentence)

    def _get_positions(self, word, stressed_vowel_ids, yo_vowel_ids):
        vowel_ids = [i for i, c in enumerate(word) if c in self.vowels]
        ye_ids = [i for i, c in enumerate(word) if c == 'е']
        stress_positions = [vowel_ids[idx] for idx in stressed_vowel_ids if (idx < len(vowel_ids)) and (len(vowel_ids) > 0)]
        yo_positions = [ye_ids[idx - 1] for idx in yo_vowel_ids
                        if (idx > 0) and (idx - 1 < len(ye_ids)) and (len(ye_ids) > 0)]
        return stress_positions, yo_positions, len(vowel_ids), (vowel_ids[0] if vowel_ids else -1)

    def _get_model_preds(self, words):
        if not words:
            return [], [], None, None
        stress_logits, yo_logits = self.model(words)
        stress_probs = _softmax(stress_logits)
        stress_preds = stress_probs.argmax(1)
        if yo_logits is None:
            return stress_probs, stress_preds, None, None
        yo_probs = _softmax(yo_logits)
        return stress_probs, stress_preds, yo_probs, yo_probs.argmax(1)

    def _accentuate_exception(self, clean_word, raw_word, have_stress):
        exc_stress, exc_yo = self.exceptions[clean_word]
        if have_stress:
            user_positions = [i for i, c in enumerate(raw_word) if c == self.stress_token]
            word = raw_word.replace(self.stress_token, '')
            if exc_yo != -1 and (exc_yo + 1 in user_positions):
                word = word[:exc_yo] + ('ё' if word[exc_yo].islower() else 'Ё') + word[(exc_yo + 1):]
            for pos in user_positions:
                word = word[:pos] + self.stress_token + word[pos:]
            return word
        if exc_yo != -1:
            raw_word = raw_word[:exc_yo] + ('ё' if raw_word[exc_yo].islower() else 'Ё') + raw_word[(exc_yo + 1):]
        return raw_word[:exc_stress] + self.stress_token + raw_word[exc_stress:]

    def _tokenize(self, sentence, words_to_ignore=None):
        words_to_ignore = words_to_ignore if words_to_ignore is not None else []
        tokens, model_inputs, prediction_mask = [], [], []
        for word in re.split(r'([\s.,!?;:<>=()/\\]+)', sentence):
            parts = word.split('-')
            if len(parts) == 1:
                cur_tokens, cur_mask = parts, [True]
            else:
                cur_tokens = [part + '-' for part in parts[:-1]] + [parts[-1]]
                cur_mask = [True for _ in parts[:-1]] + [parts[-1] != 'то']
            cur_inputs = [re.sub(self.re_cond, '', token.lower()) for token in cur_tokens]
            cur_mask = [((len(x) > 0) and (x not in words_to_ignore)) & m for x, m in zip(cur_inputs, cur_mask)]
            tokens.extend(cur_tokens)
            model_inputs.extend(cur_inputs)
            prediction_mask.extend(cur_mask)
        # the network is asked about every word; the original filters empty ones the same way (mask)
        return tokens, model_inputs, prediction_mask


class AccentorNgramSimple:
    """silero-stress `models/accentor_simple.py` (ukr/bel): tokenization (split at spaces and . , ! ? ; : < > = ( ) / \\,
    every hyphen part stressed on its own), the bel exception dictionary, the 0.5 confidence threshold — all as in the
    original. One correction: the original builds its cleaning regex from a Python LIST (fr'[^{list}]'), so quotes stay
    glued to the word («тепер, дыябету") and the network, trained without them, guesses wrong; here a word's leading and
    quotes and brackets are set aside before the network sees the word and put back after. Nothing else is removed:
    the original's regex removes nothing in practice, so the network sees the word as written (hyphen, apostrophe,
    letters of another alphabet) — exactly as in the original."""

    QUOTE = "\"«»“”„‟[]{}"

    def __init__(self, model: NgramMLP, exceptions: dict, lang: str, stress_token="+"):
        self.model = model
        self.exceptions = {w: (int(v[0]), int(v[1])) for w, v in exceptions.items()}
        self.stress_token = stress_token
        if lang == 'bel':
            alpha = 'абвгдежзйклмнопрстуфхцчшыьэюяёіў’'
            self.vowels = 'аоуіэыяеёю'
        else:
            alpha = 'абвгґдеєжзиіїйклмнопрстуфхцчшщьюя'
            self.vowels = 'аеєиіїоуюя'

    def _tokenize(self, sentence, words_to_ignore=None):
        words_to_ignore = words_to_ignore or []
        tokens, inputs, mask = [], [], []
        for word in re.split(r'([\s.,!?;:<>=()/\\]+)', sentence):
            parts = word.split('-')
            cur = parts if len(parts) == 1 else [p + '-' for p in parts[:-1]] + [parts[-1]]
            for tok in cur:
                core = tok.lstrip(self.QUOTE)
                lead = tok[:len(tok) - len(core)]
                stripped = core.rstrip(self.QUOTE)
                trail, core = core[len(stripped):], stripped
                clean = core.lower()
                tokens.append((lead, core, trail))
                inputs.append(clean)
                mask.append(len(clean) > 0 and clean not in words_to_ignore)
        return tokens, inputs, mask

    def __call__(self, sentence, stress_single_vowel=True, words_to_ignore=None):
        tokens, clean_tokens, prediction_mask = self._tokenize(sentence, words_to_ignore)
        todo = [w for w, m in zip(clean_tokens, prediction_mask) if m]
        probs = preds = None
        if todo:
            stress_logits, _ = self.model(todo)
            probs = _softmax(stress_logits)
            preds = probs.argmax(1)
        out, k = [], 0
        for (lead, raw_word, trail), clean_word, need in zip(tokens, clean_tokens, prediction_mask):
            if not need:
                out.append(lead + raw_word + trail)
                continue
            p, idx = probs[k], preds[k]
            k += 1
            low = raw_word.lower()
            if self.stress_token in low:
                out.append(lead + raw_word + trail)
                continue
            if clean_word in self.exceptions:
                exc_stress, exc_yo = self.exceptions[clean_word]
                if exc_yo != -1:
                    raw_word = raw_word[:exc_yo] + ('ё' if raw_word[exc_yo].islower() else 'Ё') + raw_word[(exc_yo + 1):]
                out.append(lead + raw_word[:exc_stress] + self.stress_token + raw_word[exc_stress:] + trail)
                continue
            set_stress = p[idx] > 0.5
            vowel_ids = [i for i, c in enumerate(low) if c in self.vowels]
            if not vowel_ids:
                out.append(lead + raw_word + trail)
                continue
            positions = [vowel_ids[idx]] if idx < len(vowel_ids) else []
            if len(vowel_ids) == 1:
                positions, set_stress = [vowel_ids[0]], stress_single_vowel
            if set_stress:
                for i, pos in enumerate(positions):
                    raw_word = raw_word[:(pos + i)] + self.stress_token + raw_word[(pos + i):]
            out.append(lead + raw_word + trail)
        return ''.join(out)


# ------------------------------------------------------------------------------------------ homograph solver
class _BasicTokenizer:
    """silero-stress `custom_tokenizers/bert_tokenizer.py`, BasicTokenizer (unchanged)."""

    def __init__(self, never_split=None):
        self.never_split = set(never_split or ())

    def tokenize(self, text):
        out = []
        text = "".join(" " if self._ws(c) else c for c in text
                       if not (ord(c) in (0, 0xfffd) or self._control(c)))
        text = "".join(f" {c} " if self._chinese(ord(c)) else c for c in text)
        for token in text.strip().split():
            out.extend([token] if token in self.never_split else self._split_punc(token))
        return " ".join(out).split()

    @staticmethod
    def _control(c):
        return c not in "\t\n\r" and unicodedata.category(c).startswith("C")

    @staticmethod
    def _ws(c):
        return c in " \t\n\r" or unicodedata.category(c) == "Zs"

    @staticmethod
    def _chinese(cp):
        return (0x4E00 <= cp <= 0x9FFF or 0x3400 <= cp <= 0x4DBF or 0x20000 <= cp <= 0x2A6DF or
                0x2A700 <= cp <= 0x2B73F or 0x2B740 <= cp <= 0x2B81F or 0x2B820 <= cp <= 0x2CEAF or
                0xF900 <= cp <= 0xFAFF or 0x2F800 <= cp <= 0x2FA1F)

    @staticmethod
    def _punc(c):
        cp = ord(c)
        return 33 <= cp <= 47 or 58 <= cp <= 64 or 91 <= cp <= 96 or 123 <= cp <= 126 or \
            unicodedata.category(c).startswith("P")

    def _split_punc(self, token):
        out, new = [], True
        for c in token:
            if self._punc(c):
                out.append([c])
                new = True
            else:
                if new:
                    out.append([])
                new = False
                out[-1].append(c)
        return ["".join(x) for x in out]


class _BertTokenizer:
    def __init__(self, vocab_json: dict):
        self.vocab = vocab_json["vocab"]
        self.unk_id, self.cls_id, self.sep_id = vocab_json["unk_token_id"], vocab_json["cls_token_id"], vocab_json["sep_token_id"]
        self.homo_start_id, self.homo_end_id = vocab_json["homo_start_id"], vocab_json["homo_end_id"]
        self.basic = _BasicTokenizer(never_split={"[HOMO]", "[/HOMO]"})

    def _wordpiece(self, text):
        out = []
        for token in text.split():
            if len(token) > 100:
                out.append("[UNK]")
                continue
            start, subs, bad = 0, [], False
            while start < len(token):
                end, cur = len(token), None
                while start < end:
                    sub = ("##" if start > 0 else "") + token[start:end]
                    if sub in self.vocab:
                        cur = sub
                        break
                    end -= 1
                if cur is None:
                    bad = True
                    break
                subs.append(cur)
                start = end
            out.extend(["[UNK]"] if bad else subs)
        return out

    def __call__(self, text):
        tokens = self._wordpiece(" ".join(self.basic.tokenize(text)))
        return [self.cls_id] + [self.vocab.get(t, self.unk_id) for t in tokens] + [self.sep_id]


def _capitalize_stress(w):
    i = w.index('+')
    return w[:i] + w[i + 1].capitalize() + w[i + 2:]


def _decapitalize_stress(w):
    for i, c in enumerate(w):
        if c.isupper():
            return w[:i] + "+" + w[i:].lower()


class HomoSolver:
    """silero-stress 1.5 `models/homosolver.py`, BERT on ONNX Runtime (batch of one)."""

    LOOKBEHIND = r"(?<![а-яА-ЯёЁ\-])"
    LOOKAHEAD = r"(?![а-яА-ЯёЁ\-])"

    def __init__(self, folder: Path):
        import onnxruntime as ort
        folder = Path(folder)
        o = ort.SessionOptions()
        o.log_severity_level = 3
        o.intra_op_num_threads = 2
        self.session = ort.InferenceSession(str(folder / "ru_homosolver_bert.onnx"), o, providers=["CPUExecutionProvider"])
        self.tokenizer = _BertTokenizer(json.loads((folder / "ru_bert_vocab.json").read_text("utf-8")))
        self.homodict = json.loads((folder / "ru_homodict.json").read_text("utf-8"))
        self.yohomodict = {w: v for w, v in self.homodict.items() if any('ё' in x for x in v)}
        self.pattern = re.compile(r'(?=.*[а-яё])[а-яё+]+', re.IGNORECASE)
        self.vowels = 'аоуыэиеяёю'
        self.compiled_phrases = {}
        for word, variants in json.loads((folder / "ru_homophrases.json").read_text("utf-8")).items():
            pat = "|".join(f"(?P<{_capitalize_stress(v)}>{self.LOOKBEHIND}(?:{'|'.join(map(re.escape, ps))}){self.LOOKAHEAD})"
                           for v, ps in variants)
            self.compiled_phrases[word] = re.compile(pat, re.IGNORECASE | re.UNICODE)
        self._re_remove_extra = re.compile(r'[^a-zA-Zа-яА-ЯёЁ0-9\s.!?,\-]')
        self._re_spaces = re.compile(r'\s+')
        self._re_double_dash = re.compile(r'-{2,}')
        self._re_repeat_punct = re.compile(r'([.!?])\1+')
        self._re_repeat_comma = re.compile(r',{2,}')
        self._re_space_before_punct = re.compile(r'\s+([.,!?])')
        self._re_punct_add_space = re.compile(r'([.,!?])(?=\S)')
        self.window_size = 300

    def __call__(self, sentence, put_stress=True, put_yo=True, stress_single_vowel=True, words_to_ignore=None):
        if not (put_stress or put_yo):
            return sentence
        starts, ends, words, preds = [], [], [], []
        for start, end, word, word_lower, raw_mark, _ in self._find_and_tag_homos(sentence, words_to_ignore):
            if raw_mark is None:
                continue
            pred = None
            if word_lower in self.compiled_phrases:
                m = self.compiled_phrases[word_lower].search(raw_mark)
                if m:
                    pred = next(_decapitalize_stress(g) for g, t in m.groupdict().items() if t is not None)
            if pred is None:
                if word_lower not in self.homodict:
                    continue
                ids = self.tokenizer(raw_mark)
                s, e = ids.index(self.tokenizer.homo_start_id), ids.index(self.tokenizer.homo_end_id)
                logit = self.session.run(None, {"ids": np.array([ids], np.int64), "starts": np.array([s], np.int64),
                                               "ends": np.array([e], np.int64)})[0].reshape(-1)[0]
                pred = sorted(self.homodict[word_lower])[1 if logit > 0 else 0]
            starts.append(start)
            ends.append(end)
            words.append(word)
            preds.append(pred)
        out, offset = sentence, 0
        for start, end, word, word_pred in zip(starts, ends, words, preds):
            start, end = start + offset, end + offset
            word_pred = word_pred if put_yo else word_pred.replace('ё', 'е')
            n_vowels = sum(c.lower() in self.vowels for c in word_pred)
            stress_idx = word_pred.index('+')
            word_pred = word_pred.replace('+', '')
            word_pred = ''.join(c2.lower() if c1.islower() else c2.upper() for c1, c2 in zip(word, word_pred))
            if (n_vowels > 1 or stress_single_vowel) and put_stress:
                word_pred = word_pred[:stress_idx] + '+' + word_pred[stress_idx:]
                offset += 1
            out = out[:start] + word_pred + out[end:]
        return out

    def _find_and_tag_homos(self, sentence, words_to_ignore=None):
        words_to_ignore = words_to_ignore or []
        res = []
        for m in self.pattern.finditer(sentence):
            start, end = m.span()
            word = m.group()
            low = word.lower()
            if (low in self.homodict or low in self.compiled_phrases) and low not in words_to_ignore:
                a = self._clean_text(sentence[:start], True)[-(self.window_size // 2):]
                b = self._clean_text(sentence[end:], False)[:(self.window_size // 2)]
                res.append((start, end, word, low, (a + ' [HOMO] ' + low + ' [/HOMO] ' + b).strip(), (a + ' ' + low + ' ' + b).strip()))
            else:
                res.append((start, end, word, low, None, None))
        return res

    def _clean_text(self, text, is_start=True):
        if not text:
            return ""
        text = self._re_remove_extra.sub('', text)
        text = self._re_spaces.sub(' ', text)
        text = self._re_double_dash.sub(' - ', text)
        text = self._re_repeat_punct.sub(r'\1', text)
        text = self._re_repeat_comma.sub(',', text)
        text = self._re_space_before_punct.sub(r'\1', text)
        text = self._re_repeat_punct.sub(r'\1', text)
        text = self._re_repeat_comma.sub(',', text)
        text = self._re_punct_add_space.sub(r'\1 ', text)
        text = self._re_spaces.sub(' ', text).strip()
        if is_start:
            text = text.lstrip(' .,!?-')
            if text:
                text = text[0].upper() + text[1:].lower()
        else:
            if text:
                text = text[0] + text[1:].lower()
            if text and text[-1] not in '.!?':
                text += '.'
        return text


class RussianStress:
    """silero-stress 1.5 `SileroStress`: homograph solver first, then the accentor."""

    def __init__(self, folder: Path):
        folder = Path(folder)
        self.homosolver = HomoSolver(folder)
        self.accentor = AccentorNgram(
            NgramMLP(folder / "accentor_ru_dict.json", folder / "accentor_ru_weights.bin"),
            json.loads((folder / "accentor_ru_exceptions.json").read_text("utf-8")))

    def __call__(self, sentence, put_stress=True, put_stress_homo=True, put_yo=True, put_yo_homo=True,
                 stress_single_vowel=True, words_to_ignore=None):
        return self.accentor(
            self.homosolver(sentence, put_stress=put_stress_homo, put_yo=put_yo_homo,
                            stress_single_vowel=stress_single_vowel, words_to_ignore=words_to_ignore),
            put_stress=put_stress, put_yo=put_yo, stress_single_vowel=stress_single_vowel,
            skip_stress_words=(self.homosolver.homodict if not put_stress_homo else None),
            skip_yo_words=(self.homosolver.yohomodict if not put_yo_homo else None),
            words_to_ignore=words_to_ignore)


def load_accentor(code: str, folder: Path):
    """code: ru | ukr | bel. None for anything else (no stress marks needed)."""
    folder = Path(folder)
    if code == "ru":
        return RussianStress(folder) if (folder / "accentor_ru_weights.bin").exists() else None
    if code in ("ukr", "bel"):
        model = NgramMLP(folder / f"accentor_{code}_dict.json", folder / f"accentor_{code}_weights.bin")
        exc = {}
        if code == "bel":
            exc = json.loads(resources.files("kabardian_translator").joinpath(
                "data/stress/accentor_bel_exceptions.json").read_text("utf-8"))
        return AccentorNgramSimple(model, exc, code)
    return None
