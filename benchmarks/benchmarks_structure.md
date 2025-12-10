# Benchmarks Folder Structure Guide

## 📁 Recommended Structure

```
kabardian-translator/
├── benchmarks/                    # NEW FOLDER
│   ├── README.md                  # Instructions (from artifact)
│   ├── requirements.txt           # Benchmark dependencies
│   ├── bench.py                   # Your benchmark script
│   ├── BENCHMARK_500.md           # Your static results (reference)
│   └── .gitignore                 # Optional: ignore generated files
│
├── kabardian_translator/          # Main package (unchanged)
├── setup.py                       # Package config (unchanged)
├── README.md                      # Updated main README
└── .gitignore                     # Add benchmark ignore rules
```

## ✅ What to Commit to Git

**DO commit these files:**
- ✅ `benchmarks/README.md` - Instructions for running benchmarks
- ✅ `benchmarks/requirements.txt` - Dependencies
- ✅ `benchmarks/bench.py` - The benchmark script
- ✅ `benchmarks/BENCHMARK_500.md` - Reference results (static snapshot)

**DON'T commit these (add to .gitignore):**
- ❌ `benchmarks/benchmark_results_*.json` - Generated results
- ❌ `benchmarks/benchmark_ru_kbd_*.csv` - Generated CSV files
- ❌ `benchmarks/benchmark_kbd_ru_*.csv` - Generated CSV files
- ❌ `benchmarks/BENCHMARK_REPORT_*.md` - Generated reports (except reference)

## 🔧 Setup Instructions

### Step 1: Create benchmarks folder

```bash
cd kabardian-translator
mkdir benchmarks
```

### Step 2: Add files to benchmarks/

Copy these files from the artifacts:
1. `README.md` → `benchmarks/README.md`
2. `requirements.txt` → `benchmarks/requirements.txt`
3. `bench.py` → `benchmarks/bench.py` (your existing script)
4. `BENCHMARK_500.md` → `benchmarks/BENCHMARK_500.md` (your existing results)

### Step 3: Update .gitignore

Add to your root `.gitignore`:

```gitignore
# Benchmark generated files
benchmarks/benchmark_results_*.json
benchmarks/benchmark_ru_kbd_*.csv
benchmarks/benchmark_kbd_ru_*.csv
benchmarks/BENCHMARK_REPORT_*.md

# Keep static reference
!benchmarks/BENCHMARK_500.md
```

### Step 4: Update setup.py

Make sure benchmarks folder is NOT included in package:

```python
# In setup.py, explicitly exclude benchmarks
setup(
    name="kabardian-translator",
    # ... other config ...
    packages=find_packages(exclude=["benchmarks", "benchmarks.*", "tests", "tests.*"]),
    # ... rest of config ...
)
```

### Step 5: Commit changes

```bash
git add benchmarks/README.md
git add benchmarks/requirements.txt
git add benchmarks/bench.py
git add benchmarks/BENCHMARK_500.md
git add .gitignore
git commit -m "Add reproducible benchmark suite for model evaluation"
git push
```

## 📦 Verification

Test that benchmarks aren't included in package:

```bash
# Build package
python setup.py sdist bdist_wheel

# Check contents (should NOT include benchmarks/)
tar -tzf dist/kabardian-translator-*.tar.gz | grep benchmarks
# Should return nothing if properly excluded
```

## 🎯 Usage for Contributors

After cloning the repo:

```bash
# Clone repo
git clone https://github.com/kubataba/kabardian-translator.git
cd kabardian-translator

# Install main package
pip install -e .

# Install benchmark dependencies
pip install -r benchmarks/requirements.txt

# Download models
kabardian-download-models

# Run benchmarks
cd benchmarks
python bench.py
```

## 💡 Benefits of This Structure

1. **Separation of concerns**: Benchmarks separate from main package
2. **No bloat**: Users installing via PyPI don't get benchmark scripts
3. **Reproducibility**: Developers can run identical tests
4. **Transparency**: Community can verify quality claims
5. **Contribution-friendly**: Clear structure for improvements

## ❓ FAQ

**Q: Will benchmarks be installed with `pip install kabardian-translator`?**  
A: No, they're excluded from the package. Only available via GitHub.

**Q: How do users access benchmarks?**  
A: Clone the repo from GitHub, then follow benchmarks/README.md

**Q: Should I update BENCHMARK_500.md?**  
A: Only when making significant changes. Keep it as a stable reference.

**Q: Can I add more benchmark scripts?**  
A: Yes! Add them to benchmarks/ folder with descriptive names (e.g., `bench_speed.py`, `bench_memory.py`)

---

This structure follows best practices from major ML projects like PyTorch, Transformers, and TensorFlow.be