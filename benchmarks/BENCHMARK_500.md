# Benchmark Results - Russian↔Kabardian Translation Models

**Date:** 2025-12-06 11:47
**Test Size:** 500 examples per direction
**Dataset:** [adiga-ai/circassian-parallel-corpus](https://huggingface.co/datasets/adiga-ai/circassian-parallel-corpus)
**Device:** mps

## Methodology

- **Test Set:** 500 randomly sampled sentences from the corpus (every 200th sentence)
- **Metrics:** BLEU (SacreBLEU), chrF, TER, Exact Match Rate
- **Generation Parameters:** beam_search (num_beams=4), max_length=128
- **Reproducibility:** seed=42

## Results

### Russian → Kabardian

| Model | Author | BLEU | chrF | TER | Exact Match | Avg Time (ms) | Speed (ex/s) |
|-------|--------|------|------|-----|-------------|---------------|---------------|
| Opus-MT RU→KBD | kubataba | **8.48** | 32.7 | 86.09 | 6.6% | 210.6 | 4.7 |
| M2M100 RU→KBD | anzorq | **6.09** | 33.89 | 84.35 | 9.6% | 1287.6 | 0.8 |

**Winner:** Opus-MT RU→KBD (kubataba) with BLEU 8.48

### Kabardian → Russian

| Model | Author | BLEU | chrF | TER | Exact Match | Avg Time (ms) | Speed (ex/s) |
|-------|--------|------|------|-----|-------------|---------------|---------------|
| Opus-MT KBD→RU| kubataba | **12.75** | 32.48 | 81.35 | 7.8% | 592.0 | 1.7 |
| M2M100 KBD→RU | anzorq | **7.44** | 28.15 | 89.98 | 9.0% | 1658.0 | 0.6 |

**Winner:** Opus-MT KBD→RU (kubataba) with BLEU 12.75

## Translation Examples


### Opus-MT RU→KBD (kubataba)

| Source | Reference | Translation |
|--------|-----------|-------------|
| затиснуть... | дэкуэн... | щхьэщытхъун... |
| вырыть погреб... | щӀыунэ къэтӀын... | щӀапӀэр къэтӀэтӀыкӀын... |
| первенство... | пашэныгъэ... | нэхъыщхьэ... |
| Ты уже доел завтрак?... | Пщэдджыжьышхэр нэбгъэсакӀэ?... | Пщэдджыжьышхэ пщэдджыжь хъуакъэ?... |
| вообще... | дапщэщи... | нэгъуэщӀми... |

### M2M100 RU→KBD

| Source | Reference | Translation |
|--------|-----------|-------------|
| затиснуть... | дэкуэн... | уфӀыцӀын... |
| вырыть погреб... | щӀыунэ къэтӀын... | щӀыунэр къыщӀэхун... |
| первенство... | пашэныгъэ... | пашэ... |
| Ты уже доел завтрак?... | Пщэдджыжьышхэр нэбгъэсакӀэ?... | пщэдджыжьышхэр пшхакӀэ?... |
| вообще... | дапщэщи... | сыт щыгъуи... |

### Opus-MT KBD→RU (kubataba)

| Source | Reference | Translation |
|--------|-----------|-------------|
| ублэрэкӀын... | переворачивать... | перевалиться... |
| Ерагъпсэрагъщ зэрызрагъэкӀужар.... | С трудом их помирили.... | Это единственность, которую они вернули.... |
| нэщӀащэ... | глазница... | пустыня... |
| лэжьыгъэр мытэмэму гъэзэщӀащ... | упражнение выполнено неверно... | работа выполнена неправильно... |
| гъэдыргъ... | скрежет... | крупный... |

### M2M100 KBD→RU

| Source | Reference | Translation |
|--------|-----------|-------------|
| ублэрэкӀын... | переворачивать... | перевернуться... |
| Ерагъпсэрагъщ зэрызрагъэкӀужар.... | С трудом их помирили.... | едный сорт пищи.... |
| нэщӀащэ... | глазница... | глазная мазь... |
| лэжьыгъэр мытэмэму гъэзэщӀащ... | упражнение выполнено неверно... | упражнение выполнено неверно... |
| гъэдыргъ... | скрежет... | то, что он вместе с ним отдает ему... |

## Interpretation

### Metrics Explained

- **BLEU**: Measures n-gram overlap (0-100, higher is better)
- **chrF**: Character-level F-score (0-100, higher is better)
- **TER**: Translation Error Rate (0-100, lower is better)
- **Exact Match**: Percentage of perfect translations

### Quality Assessment

Average BLEU across all models: **8.69**

Quality Assessment: **Needs improvement - requires additional training**

## Technical Details

- Test conducted on: MPS
- Framework: PyTorch + Transformers
- Reproducible with seed: 42
- Dataset splits: Sampled every 200th example
