#!/usr/bin/env python3
"""
Сравнительное тестирование моделей перевода RU↔KBD
Сравнивает ваши Opus-MT модели с M2M100 моделями на одинаковых примерах

Метрики:
- BLEU (SacreBLEU)
- chrF/chrF++
- TER (Translation Error Rate)
- Скорость перевода
- Примеры переводов

License: CC BY-NC 4.0
Author: [Ваше имя]
"""

import torch
from transformers import (
    AutoTokenizer, AutoModelForSeq2SeqLM,
    MarianTokenizer, MarianMTModel
)
from datasets import load_from_disk
import evaluate
from pathlib import Path
import time
import json
import pandas as pd
from datetime import datetime
import random
import numpy as np

print("=" * 80)
print("🏆 СРАВНИТЕЛЬНОЕ ТЕСТИРОВАНИЕ МОДЕЛЕЙ ПЕРЕВОДА RU↔KBD")
print("=" * 80)

# ============================================================================
# КОНФИГУРАЦИЯ
# ============================================================================

# Устройство
device = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"
print(f"💻 Устройство: {device}")

# Параметры теста
TEST_SIZE = 1000  # 1000 одинаковых предложений для каждого направления
SEED = 42
SAMPLE_INTERVAL = 50  # Берем каждое 50-е предложение

# Устанавливаем seed для воспроизводимости
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)

# ============================================================================
# КОНФИГУРАЦИЯ МОДЕЛЕЙ (ГРУППИРОВКА ПО НАПРАВЛЕНИЯМ)
# ============================================================================

MODELS = {
    "ru_kbd": {
        "opus_ru_kbd": {
            "name": "Opus-MT RU→KBD (kubataba)",
            "type": "opus",
            "path": "models/opus-mt-ru-kbd",
            "base_model": "Helsinki-NLP/opus-mt-ru-uk",
            "author": "kubataba",
            "direction": "ru_kbd"
        }   
    },
    "kbd_ru": {
        "opus_kbd_ru": {
            "name": "Opus-MT KBD→RU (kubataba)",
            "type": "opus",
            "path": "models/opus-mt-kbd-ru",
            "base_model": "Helsinki-NLP/opus-mt-en-ru",
            "author": "kubataba",
            "direction": "kbd_ru"
        }
    }
}

# ============================================================================
# ФУНКЦИИ ПРЕПРОЦЕССИНГА
# ============================================================================

def preprocess_kbd_for_opus(text):
    """Замена Ӏ → I для Opus-MT"""
    return text.replace('Ӏ', 'I').replace('ӏ', 'I') if isinstance(text, str) else text

def postprocess_kbd_from_opus(text):
    """Восстановление I → Ӏ из Opus-MT"""
    return text.replace('I', 'Ӏ') if isinstance(text, str) else text

def preprocess_kbd_for_m2m100(text):
    """Замена Ӏ → I для M2M100"""
    return text.replace('Ӏ', 'I').replace('ӏ', 'I') if isinstance(text, str) else text

def postprocess_kbd_from_m2m100(text):
    """Восстановление I → Ӏ из M2M100"""
    return text.replace('I', 'Ӏ') if isinstance(text, str) else text

# ============================================================================
# ЗАГРУЗКА ТЕСТОВЫХ ДАННЫХ ИЗ КОРПУСА
# ============================================================================

def load_test_samples_from_corpus():
    """
    Загружает тестовые примеры напрямую из корпуса.
    Берет одинаковые 100 примеров для каждого направления.
    """
    print("\n" + "="*80)
    print("📥 ЗАГРУЗКА ТЕСТОВЫХ ДАННЫХ ИЗ КОРПУСА")
    print("="*80)
    
    corpus_path = Path("data/circassian_corpus")
    
    if not corpus_path.exists():
        raise FileNotFoundError(f"Корпус не найден: {corpus_path}")
    
    print(f"📂 Структура корпуса:")
    for item in corpus_path.iterdir():
        if item.is_dir():
            print(f"   📁 {item.name}")
    
    # Функция извлечения пар из конкретного датасета
    def extract_pairs_from_dataset(dataset_path, source_key='ru', target_key='kbd'):
        """Извлекает пары из датасета по пути"""
        try:
            dataset = load_from_disk(dataset_path)
            pairs = []
            
            for item in dataset:
                try:
                    if isinstance(item, dict) and 'translation' in item:
                        translation = item['translation']
                    else:
                        translation = item
                    
                    if isinstance(translation, str):
                        try:
                            parsed = json.loads(translation)
                        except:
                            continue
                    else:
                        parsed = translation
                    
                    if isinstance(parsed, dict) and source_key in parsed and target_key in parsed:
                        source_text = str(parsed[source_key]).strip()
                        target_text = str(parsed[target_key]).strip()
                        
                        if source_text and target_text and source_text != 'None' and target_text != 'None':
                            pairs.append({
                                'source': source_text,
                                'target': target_text
                            })
                except Exception as e:
                    continue
            
            return pairs
            
        except Exception as e:
            print(f"   ❌ Ошибка загрузки {dataset_path}: {e}")
            return []
    
    # Загружаем данные из соответствующих папок
    print("\n🔄 Загрузка данных RU→KBD...")
    ru_kbd_path = corpus_path / "ru_kbd"
    ru_kbd_pairs = extract_pairs_from_dataset(ru_kbd_path, source_key='ru', target_key='kbd')
    
    print("🔄 Загрузка данных KBD→RU...")
    kbd_ru_path = corpus_path / "kbd_ru"
    kbd_ru_pairs = extract_pairs_from_dataset(kbd_ru_path, source_key='kbd', target_key='ru')
    
    print(f"✅ Извлечено пар:")
    print(f"   RU→KBD: {len(ru_kbd_pairs):,}")
    print(f"   KBD→RU: {len(kbd_ru_pairs):,}")
    
    if len(ru_kbd_pairs) == 0 or len(kbd_ru_pairs) == 0:
        print("⚠️  Внимание: один из датасетов пуст!")
    
    # Выбираем 100 случайных примеров с интервалом
    def select_samples(pairs, n=TEST_SIZE, interval=SAMPLE_INTERVAL):
        """Выбирает N примеров с заданным интервалом"""
        if not pairs:
            return []
            
        if len(pairs) < n * interval:
            # Если данных мало, берем случайные
            indices = random.sample(range(len(pairs)), min(n, len(pairs)))
        else:
            # Берем с интервалом для равномерного покрытия
            indices = [i * interval for i in range(n) if i * interval < len(pairs)]
            # Дополняем случайными если не хватает
            if len(indices) < n:
                remaining = n - len(indices)
                extra_indices = random.sample(
                    [i for i in range(len(pairs)) if i not in indices],
                    remaining
                )
                indices.extend(extra_indices)
        
        return [pairs[i] for i in sorted(indices)]
    
    ru_kbd_test = select_samples(ru_kbd_pairs)
    kbd_ru_test = select_samples(kbd_ru_pairs)
    
    print(f"\n✅ Выбрано тестовых примеров:")
    print(f"   RU→KBD: {len(ru_kbd_test)}")
    print(f"   KBD→RU: {len(kbd_ru_test)}")
    
    # Примеры
    if ru_kbd_test:
        print(f"\n📝 Примеры RU→KBD:")
        for i in range(min(3, len(ru_kbd_test))):
            print(f"   {i+1}. RU:  {ru_kbd_test[i]['source'][:60]}...")
            print(f"      KBD: {ru_kbd_test[i]['target'][:60]}...")
    
    if kbd_ru_test:
        print(f"\n📝 Примеры KBD→RU:")
        for i in range(min(3, len(kbd_ru_test))):
            print(f"   {i+1}. KBD: {kbd_ru_test[i]['source'][:60]}...")
            print(f"      RU:  {kbd_ru_test[i]['target'][:60]}...")
    
    return {
        'ru_kbd': ru_kbd_test,
        'kbd_ru': kbd_ru_test
    }

# ============================================================================
# ЗАГРУЗКА МОДЕЛЕЙ
# ============================================================================

def load_model_and_tokenizer(model_key, model_config):
    """Загружает модель и токенизатор"""
    model_path = Path(model_config['path'])
    
    if not model_path.exists():
        print(f"   ⚠️  Модель не найдена: {model_path}")
        return None, None
    
    try:
        if model_config['type'] == 'opus':
            tokenizer = MarianTokenizer.from_pretrained(model_path)
            model = MarianMTModel.from_pretrained(
                model_path,
                torch_dtype=torch.float32
            ).to(device)
        else:  # m2m100
            tokenizer = AutoTokenizer.from_pretrained(model_path)
            model = AutoModelForSeq2SeqLM.from_pretrained(
                model_path,
                torch_dtype=torch.float32
            ).to(device)
        
        model.eval()
        print(f"   ✅ Загружено: {model_config['name']}")
        return model, tokenizer
    
    except Exception as e:
        print(f"   ❌ Ошибка загрузки {model_key}: {e}")
        return None, None

# ============================================================================
# ФУНКЦИИ ПЕРЕВОДА
# ============================================================================

def translate_opus_ru_kbd(model, tokenizer, text):
    """Перевод RU→KBD для Opus-MT"""
    inputs = tokenizer(text, return_tensors="pt", max_length=128, truncation=True).to(device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_length=128,
            num_beams=4,
            early_stopping=True,
            repetition_penalty=1.2
        )
    
    translation = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return postprocess_kbd_from_opus(translation)

def translate_opus_kbd_ru(model, tokenizer, text):
    """Перевод KBD→RU для Opus-MT"""
    processed_text = preprocess_kbd_for_opus(text)
    inputs = tokenizer(processed_text, return_tensors="pt", max_length=128, truncation=True).to(device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_length=128,
            num_beams=4,
            early_stopping=True,
            repetition_penalty=1.2
        )
    
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

def translate_m2m100_ru_kbd(model, tokenizer, text):
    """Перевод RU→KBD для M2M100"""
    formatted_input = f"__zu__ {text}"
    inputs = tokenizer(formatted_input, return_tensors="pt", max_length=128, truncation=True).to(device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_length=128,
            num_beams=4,
            early_stopping=True,
            repetition_penalty=1.2
        )
    
    translation = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return postprocess_kbd_from_m2m100(translation)

def translate_m2m100_kbd_ru(model, tokenizer, text):
    """Перевод KBD→RU для M2M100"""
    processed_text = preprocess_kbd_for_m2m100(text)
    formatted_input = f"__ru__ {processed_text}"
    inputs = tokenizer(formatted_input, return_tensors="pt", max_length=128, truncation=True).to(device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_length=128,
            num_beams=4,
            early_stopping=True,
            repetition_penalty=1.2
        )
    
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

# Словарь функций перевода
TRANSLATE_FUNCS = {
    "opus_ru_kbd": translate_opus_ru_kbd,
    "opus_kbd_ru": translate_opus_kbd_ru,
    "m2m100_ru_kbd": translate_m2m100_ru_kbd,
    "m2m100_kbd_ru": translate_m2m100_kbd_ru
}

# ============================================================================
# ТЕСТИРОВАНИЕ МОДЕЛИ
# ============================================================================

def test_model(model_key, model_config, test_data):
    """Тестирует одну модель"""
    print(f"\n{'='*80}")
    print(f"🔍 ТЕСТИРОВАНИЕ: {model_config['name']}")
    print(f"{'='*80}")
    
    # Загрузка модели
    print("📥 Загрузка модели и токенизатора...")
    model, tokenizer = load_model_and_tokenizer(model_key, model_config)
    
    if model is None or tokenizer is None:
        print(f"   ❌ Пропуск {model_key}")
        return None
    
    # Получаем тестовые данные по направлению
    direction = model_config['direction']
    test_examples = test_data[direction]
    
    if not test_examples:
        print(f"   ❌ Нет тестовых данных для направления: {direction}")
        return None
    
    print(f"📊 Тестовых примеров: {len(test_examples)}")
    
    # Функция перевода
    translate_func = TRANSLATE_FUNCS[model_key]
    
    # Метрики
    sacrebleu = evaluate.load("sacrebleu")
    chrf = evaluate.load("chrf")
    ter = evaluate.load("ter")
    
    predictions = []
    references = []
    translation_times = []
    
    print("🔄 Генерация переводов...")
    start_time = time.time()
    
    for i, example in enumerate(test_examples):
        try:
            source_text = example['source']
            target_text = example['target']
            
            # Засекаем время перевода
            trans_start = time.time()
            prediction = translate_func(model, tokenizer, source_text)
            trans_time = time.time() - trans_start
            
            predictions.append(prediction)
            references.append([target_text])
            translation_times.append(trans_time)
            
            if (i + 1) % 20 == 0:
                speed = (i + 1) / (time.time() - start_time)
                print(f"   {i+1}/{len(test_examples)} ({speed:.1f} ex/s)")
        
        except Exception as e:
            print(f"   ❌ Ошибка в примере {i}: {e}")
            continue
    
    total_time = time.time() - start_time
    
    if not predictions:
        print("   ❌ Нет валидных предсказаний")
        return None
    
    # Вычисление метрик
    print("\n📊 Вычисление метрик...")
    
    bleu_result = sacrebleu.compute(predictions=predictions, references=references)
    chrf_result = chrf.compute(predictions=predictions, references=references)
    ter_result = ter.compute(predictions=predictions, references=references)
    
    # Дополнительные метрики
    exact_matches = sum(1 for p, r in zip(predictions, references) if p == r[0])
    exact_match_rate = (exact_matches / len(predictions)) * 100
    
    avg_trans_time = np.mean(translation_times)
    std_trans_time = np.std(translation_times)
    
    # Вывод результатов
    print(f"\n✅ РЕЗУЛЬТАТЫ:")
    print(f"   BLEU:              {bleu_result['score']:.2f}")
    print(f"   chrF:              {chrf_result['score']:.2f}")
    print(f"   chrF++:            {chrf_result.get('score', 0):.2f}")
    print(f"   TER:               {ter_result['score']:.2f}")
    print(f"   Точные совпадения: {exact_match_rate:.1f}%")
    print(f"   Время на пример:   {avg_trans_time*1000:.1f} ± {std_trans_time*1000:.1f} мс")
    print(f"   Общее время:       {total_time:.1f}с")
    print(f"   Скорость:          {len(predictions)/total_time:.1f} ex/s")
    
    # Примеры переводов
    print(f"\n📝 ПРИМЕРЫ ПЕРЕВОДОВ:")
    for i in range(min(5, len(predictions))):
        example = test_examples[i]
        match = "✅" if predictions[i] == references[i][0] else "❌"
        
        print(f"\n   {i+1}. {match}")
        print(f"      Источник:  {example['source'][:70]}")
        print(f"      Ожидалось: {references[i][0][:70]}")
        print(f"      Получено:  {predictions[i][:70]}")
    
    return {
        "model": model_config['name'],
        "author": model_config['author'],
        "base_model": model_config['base_model'],
        "direction": direction,
        "bleu": round(bleu_result['score'], 2),
        "chrf": round(chrf_result['score'], 2),
        "ter": round(ter_result['score'], 2),
        "exact_match_rate": round(exact_match_rate, 1),
        "avg_time_ms": round(avg_trans_time * 1000, 1),
        "std_time_ms": round(std_trans_time * 1000, 1),
        "total_time": round(total_time, 1),
        "speed": round(len(predictions) / total_time, 1),
        "examples": len(predictions),
        "predictions": predictions[:10],  # Первые 10 для отчета
        "references": [r[0] for r in references[:10]]
    }

# ============================================================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================================================

def main():
    """Главная функция бенчмарка"""
    
    print(f"\n📋 КОНФИГУРАЦИЯ ТЕСТА:")
    print(f"   Тестовых примеров: {TEST_SIZE} на направление")
    print(f"   Интервал выборки:  каждое {SAMPLE_INTERVAL}-е предложение")
    print(f"   Seed:              {SEED}")
    print(f"   Устройство:        {device}")
    
    # Загрузка тестовых данных
    try:
        test_data = load_test_samples_from_corpus()
    except Exception as e:
        print(f"\n❌ Ошибка загрузки данных: {e}")
        return
    
    # Тестирование всех моделей
    all_results = {}
    
    # Тестируем модели для каждого направления отдельно
    for direction, models_in_direction in MODELS.items():
        print(f"\n{'='*80}")
        print(f"🔍 НАПРАВЛЕНИЕ: {direction.upper()}")
        print(f"{'='*80}")
        
        for model_key, model_config in models_in_direction.items():
            try:
                result = test_model(model_key, model_config, test_data)
                if result:
                    all_results[model_key] = result
            except Exception as e:
                print(f"\n❌ Ошибка тестирования {model_key}: {e}")
                continue
    
    # Сохранение результатов
    if not all_results:
        print("\n❌ Нет результатов для сохранения")
        return
        
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # JSON с полными результатами
    results_file = f"benchmark_results_{timestamp}.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Результаты сохранены: {results_file}")
    
    # Создание итоговых таблиц и отчета
    create_comparison_report(all_results, test_data)

# ============================================================================
# СОЗДАНИЕ ОТЧЕТА
# ============================================================================

def create_comparison_report(all_results, test_data):
    """Создает подробный отчет сравнения"""
    
    print(f"\n{'='*80}")
    print(f"🏆 СРАВНИТЕЛЬНЫЙ ОТЧЕТ")
    print(f"{'='*80}")
    
    if not all_results:
        print("❌ Нет результатов для сравнения")
        return
    
    # Таблица сравнения для RU→KBD
    ru_kbd_results = {k: v for k, v in all_results.items() if k in ['opus_ru_kbd', 'm2m100_ru_kbd']}
    
    if ru_kbd_results:
        print(f"\n🔹 РУССКИЙ → КАБАРДИНСКИЙ ({len(test_data['ru_kbd'])} примеров)")
        print("="*80)
        
        df_ru_kbd = pd.DataFrame([
            {
                "Модель": r['model'],
                "Автор": r['author'],
                "BLEU": r['bleu'],
                "chrF": r['chrf'],
                "TER": r['ter'],
                "Точные %": r['exact_match_rate'],
                "Время (мс)": f"{r['avg_time_ms']:.1f}±{r['std_time_ms']:.1f}",
                "Скорость": f"{r['speed']:.1f} ex/s"
            }
            for r in sorted(ru_kbd_results.values(), key=lambda x: x['bleu'], reverse=True)
        ])
        
        print(df_ru_kbd.to_string(index=False))
        
        # Победитель
        if ru_kbd_results:
            best_ru_kbd = max(ru_kbd_results.values(), key=lambda x: x['bleu'])
            print(f"\n🥇 Лучшая модель: {best_ru_kbd['model']} (BLEU: {best_ru_kbd['bleu']})")
    
    # Таблица сравнения для KBD→RU
    kbd_ru_results = {k: v for k, v in all_results.items() if k in ['opus_kbd_ru', 'm2m100_kbd_ru']}
    
    if kbd_ru_results:
        print(f"\n🔹 КАБАРДИНСКИЙ → РУССКИЙ ({len(test_data['kbd_ru'])} примеров)")
        print("="*80)
        
        df_kbd_ru = pd.DataFrame([
            {
                "Модель": r['model'],
                "Автор": r['author'],
                "BLEU": r['bleu'],
                "chrF": r['chrf'],
                "TER": r['ter'],
                "Точные %": r['exact_match_rate'],
                "Время (мс)": f"{r['avg_time_ms']:.1f}±{r['std_time_ms']:.1f}",
                "Скорость": f"{r['speed']:.1f} ex/s"
            }
            for r in sorted(kbd_ru_results.values(), key=lambda x: x['bleu'], reverse=True)
        ])
        
        print(df_kbd_ru.to_string(index=False))
        
        # Победитель
        if kbd_ru_results:
            best_kbd_ru = max(kbd_ru_results.values(), key=lambda x: x['bleu'])
            print(f"\n🥇 Лучшая модель: {best_kbd_ru['model']} (BLEU: {best_kbd_ru['bleu']})")
    

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Создание Markdown отчета для публикации
    create_markdown_report(all_results, test_data, timestamp)

def create_markdown_report(all_results, test_data, timestamp):
    """Создает Markdown отчет для публикации на HuggingFace"""
    
    report = f"""# Benchmark Results - Russian↔Kabardian Translation Models

**Date:** {datetime.now().strftime("%Y-%m-%d %H:%M")}
**Test Size:** {TEST_SIZE} examples per direction
**Dataset:** [adiga-ai/circassian-parallel-corpus](https://huggingface.co/datasets/adiga-ai/circassian-parallel-corpus)
**Device:** {device}

## Methodology

- **Test Set:** {TEST_SIZE} randomly sampled sentences from the corpus (every {SAMPLE_INTERVAL}th sentence)
- **Metrics:** BLEU (SacreBLEU), chrF, TER, Exact Match Rate
- **Generation Parameters:** beam_search (num_beams=4), max_length=128
- **Reproducibility:** seed={SEED}

## Results

### Russian → Kabardian

"""
    
    # Таблица RU→KBD
    ru_kbd_results = {k: v for k, v in all_results.items() if k in ['opus_ru_kbd', 'm2m100_ru_kbd']}
    
    if ru_kbd_results:
        report += "| Model | Author | BLEU | chrF | TER | Exact Match | Avg Time (ms) | Speed (ex/s) |\n"
        report += "|-------|--------|------|------|-----|-------------|---------------|---------------|\n"
        
        for r in sorted(ru_kbd_results.values(), key=lambda x: x['bleu'], reverse=True):
            report += f"| {r['model']} | {r['author']} | **{r['bleu']}** | {r['chrf']} | {r['ter']} | {r['exact_match_rate']}% | {r['avg_time_ms']:.1f} | {r['speed']:.1f} |\n"
        
        # Лучшая модель
        if ru_kbd_results:
            best = max(ru_kbd_results.values(), key=lambda x: x['bleu'])
            report += f"\n**Winner:** {best['model']} with BLEU {best['bleu']}\n"
    
    report += "\n### Kabardian → Russian\n\n"
    
    # Таблица KBD→RU
    kbd_ru_results = {k: v for k, v in all_results.items() if k in ['opus_kbd_ru', 'm2m100_kbd_ru']}
    
    if kbd_ru_results:
        report += "| Model | Author | BLEU | chrF | TER | Exact Match | Avg Time (ms) | Speed (ex/s) |\n"
        report += "|-------|--------|------|------|-----|-------------|---------------|---------------|\n"
        
        for r in sorted(kbd_ru_results.values(), key=lambda x: x['bleu'], reverse=True):
            report += f"| {r['model']} | {r['author']} | **{r['bleu']}** | {r['chrf']} | {r['ter']} | {r['exact_match_rate']}% | {r['avg_time_ms']:.1f} | {r['speed']:.1f} |\n"
        
        # Лучшая модель
        if kbd_ru_results:
            best = max(kbd_ru_results.values(), key=lambda x: x['bleu'])
            report += f"\n**Winner:** {best['model']} with BLEU {best['bleu']}\n"
    
    # Примеры переводов
    report += "\n## Translation Examples\n\n"
    
    for model_key, result in all_results.items():
        report += f"\n### {result['model']}\n\n"
        report += "| Source | Reference | Translation |\n"
        report += "|--------|-----------|-------------|\n"
        
        for i in range(min(5, len(result['predictions']))):
            source = test_data[result['direction']][i]['source'][:50]
            ref = result['references'][i][:50]
            pred = result['predictions'][i][:50]
            report += f"| {source}... | {ref}... | {pred}... |\n"
    
    # Интерпретация результатов
    report += "\n## Interpretation\n\n"
    report += "### Metrics Explained\n\n"
    report += "- **BLEU**: Measures n-gram overlap (0-100, higher is better)\n"
    report += "- **chrF**: Character-level F-score (0-100, higher is better)\n"
    report += "- **TER**: Translation Error Rate (0-100, lower is better)\n"
    report += "- **Exact Match**: Percentage of perfect translations\n\n"
    
    report += "### Quality Assessment\n\n"
    
    # Оценка качества
    all_bleu = [r['bleu'] for r in all_results.values()]
    avg_bleu = sum(all_bleu) / len(all_bleu) if all_bleu else 0
    
    if avg_bleu > 30:
        quality = "Excellent - suitable for production use"
    elif avg_bleu > 25:
        quality = "Good - suitable for most applications"
    elif avg_bleu > 20:
        quality = "Acceptable - suitable for basic translation tasks"
    else:
        quality = "Needs improvement - requires additional training"
    
    report += f"Average BLEU across all models: **{avg_bleu:.2f}**\n\n"
    report += f"Quality Assessment: **{quality}**\n\n"
    
    report += "## Technical Details\n\n"
    report += f"- Test conducted on: {device.upper()}\n"
    report += f"- Framework: PyTorch + Transformers\n"
    report += f"- Reproducible with seed: {SEED}\n"
    report += f"- Dataset splits: Sampled every {SAMPLE_INTERVAL}th example\n"
    
    # Сохранение отчета
    report_file = f"BENCHMARK_REPORT_{timestamp}.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"💾 Markdown отчет сохранен: {report_file}")
    print(f"   Используйте его для публикации на HuggingFace!")

if __name__ == "__main__":
    main()
    
    print(f"\n{'='*80}")
    print("✅ БЕНЧМАРК ЗАВЕРШЕН!")
    print("="*80)
    print("\n📁 Созданные файлы:")
    print("   • benchmark_results_*.json - полные результаты")
    print("   • benchmark_ru_kbd_*.csv - таблица RU→KBD")
    print("   • benchmark_kbd_ru_*.csv - таблица KBD→RU")
    print("   • BENCHMARK_REPORT_*.md - отчет для публикации")
    print("\n🚀 Следующие шаги:")
    print("   1. Добавьте BENCHMARK_REPORT_*.md в Model Card на HuggingFace")
    print("   2. Разместите таблицы CSV в репозитории")
    print("   3. Используйте результаты для сравнения с baseline")
    print("\n💡 Для повторного запуска: python benchmark_models.py")
    print("="*80)