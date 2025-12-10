# Kabardian Translator Benchmarks

This directory contains reproducible benchmark scripts for testing translation quality of Russian↔Kabardian models.

## 📋 Contents

- `bench.py` - Main benchmark script comparing models
- `BENCHMARK_500.md` - Detailed results from 500-example test
- `requirements.txt` - Additional dependencies for benchmarking

## 🚀 Quick Start

### Installation

```bash
# Install benchmark dependencies (in addition to kabardian-translator)
pip install datasets evaluate pandas sacrebleu

# Or install from requirements.txt
pip install -r requirements.txt
```

### Running Benchmarks

```bash
# Run full benchmark (500 examples, ~10-15 minutes)
python bench.py

# The script will:
# 1. Load the circassian-parallel-corpus
# 2. Sample 500 test examples per direction
# 3. Test all available models
# 4. Generate detailed reports and markdown output
```

## 📊 What Gets Tested

### Models Compared

**Direction: Russian → Kabardian**
- Opus-MT RU→KBD (kubataba) - 80M params, specialized
- M2M100 RU→KBD (anzorq) - 1.2B params, baseline

**Direction: Kabardian → Russian**
- Opus-MT KBD→RU (kubataba) - 80M params, specialized
- M2M100 KBD→RU (anzorq) - 1.2B params, baseline

### Metrics Evaluated

- **BLEU** (SacreBLEU) - N-gram precision measure (0-100, higher is better)
- **chrF** - Character-level F-score (0-100, higher is better)
- **TER** - Translation Error Rate (0-100, lower is better)
- **Exact Match Rate** - Percentage of perfect translations
- **Speed** - Examples per second, average time per translation

### Test Dataset

- **Source**: [adiga-ai/circassian-parallel-corpus](https://huggingface.co/datasets/adiga-ai/circassian-parallel-corpus)
- **Sampling**: Every 50th sentence for uniform coverage
- **Size**: 500 examples per direction (1,000 total)
- **Reproducibility**: Fixed seed (42) for consistent results

## 📈 Current Results Summary

| Direction | Best Model | BLEU | Size | Speed |
|-----------|-----------|------|------|-------|
| RU→KBD | Opus-MT (kubataba) | **8.48** | 300MB | 4.7 ex/s |
| KBD→RU | Opus-MT (kubataba) | **12.75** | 300MB | 1.7 ex/s |

**Key Finding**: Specialized 80M parameter models outperform 1.2B parameter multilingual models by 39% BLEU for Russian→Kabardian translation, while being 8x smaller.

See [BENCHMARK_500.md](./BENCHMARK_500.md) for complete results with examples.

## ⚙️ Configuration

Edit `bench.py` to customize:

```python
# Test size
TEST_SIZE = 500  # Number of examples per direction

# Sampling strategy
SAMPLE_INTERVAL = 50  # Take every Nth sentence

# Reproducibility
SEED = 42  # Random seed

# Device
device = "mps"  # Or "cuda", "cpu"
```

## 📝 Output Files

After running, you'll get:

- `benchmark_results_TIMESTAMP.json` - Full results with all metrics
- `BENCHMARK_REPORT_TIMESTAMP.md` - Formatted markdown report
- Console output with detailed progress and examples

## 🔬 Methodology Notes

### Why BLEU Scores Are Low

The relatively low BLEU scores (8-13) for Kabardian models are due to **tokenization mismatch**, not translation quality:

1. **Digraph fragmentation**: Kabardian digraphs (кхъ, щӏ, лӏ, тӀ, цӀ) are split into separate tokens
2. **Morpheme boundaries**: Complex polysynthetic morphology isn't properly segmented
3. **N-gram artifacts**: Results in artificially reduced n-gram matches
4. **Semantic accuracy**: Despite low BLEU, translations are semantically correct and usable

**Read more**: [Tokenization as the Key to Language Models for Low-Resource Languages](https://habr.com/ru/articles/973324/)

### Comparison Context

For context, M2M100 418M benchmarks from Meta AI research:
- Low-resource pairs: BLEU 8.9-10.1
- Mid-resource pairs: BLEU 21.4-23.4
- High-resource pairs: BLEU 35.0-39.8

Our Kabardian models fall within expected ranges for ultra-low-resource languages.

## 🤝 Contributing

Want to improve the benchmark?

### Ideas for Enhancement

- [ ] Add more metrics (METEOR, BERTScore)
- [ ] Test on different corpus subsets
- [ ] Implement cross-validation
- [ ] Add human evaluation correlation
- [ ] Test with different generation parameters
- [ ] Benchmark memory usage more precisely

### How to Contribute

1. Fork the repository
2. Create a feature branch
3. Modify `bench.py` with improvements
4. Test thoroughly
5. Submit a Pull Request with updated results

## 📖 Citation

If you use these benchmarks in research, please cite:

```bibtex
@software{emkuzhev2025translator,
  title = {Kabardian Translator: Voice-Enabled Multilingual Translator for Caucasian Languages},
  author = {Eduard Emkuzhev},
  year = {2025},
  url = {https://github.com/kubataba/kabardian-translator},
  version = {1.0.3}
}

@dataset{qunash2025corpus,
  title = {Circassian-Russian Parallel Text Corpus},
  author = {Anzor Qunash},
  year = {2025},
  publisher = {Hugging Face},
  url = {https://huggingface.co/datasets/adiga-ai/circassian-parallel-corpus}
}
```

## 📞 Questions?

- **Technical issues**: [GitHub Issues](https://github.com/kubataba/kabardian-translator/issues)
- **Methodology discussion**: See [tokenization article](https://habr.com/ru/articles/973324/)
- **General questions**: info@copperline.info

---

**Note**: These benchmarks are designed for research and development purposes. They help track model improvements and provide reproducible baselines for the community.