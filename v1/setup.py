# setup.py - v2.0.0 (NLLB-200 Edition)
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="kabardian-translator",
    version="2.0.0",
    author="Kubataba",
    author_email="info@copperline.info",
    description="Advanced multilingual translator for Kabardian and Caucasian languages with NLLB-200 model, speech synthesis and accentuation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kubataba/kabardian-translator",
    packages=find_packages(
        include=['kabardian_translator'], 
        exclude=['benchmarks', 'benchmarks.*', 'tests', 'tests.*']
    ),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Text Processing :: Linguistic",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Natural Language :: Russian",
        "Natural Language :: English",
        "Natural Language :: Turkish",
        "Natural Language :: Georgian",
        "Natural Language :: Armenian",
        "Natural Language :: Azerbaijani",
        "Natural Language :: Kabardian",
        "Natural Language :: Kazakh",
        "Natural Language :: Ukrainian",
        "Natural Language :: Belarusian",
        "Natural Language :: German",
        "Natural Language :: French",
        "Natural Language :: Spanish",
    ],
    keywords=[
        "machine-translation",
        "nllb-200",
        "marianmt",
        "kabardian",
        "caucasian-languages",
        "multilingual",
        "speech-synthesis",
        "tts",
        "transliteration",
        "accentuation",
        "silero",
        "huggingface",
    ],
    python_requires=">=3.11",
    install_requires=[
        # Web framework
        "flask>=3.0.0",
        
        # Machine learning core
        "torch>=2.1.0",
        "transformers>=4.37.0,<5.0.0",
        "sentencepiece>=0.1.99",
        
        # Optimization for Apple Silicon / CUDA
        "accelerate>=0.24.1",
        
        # Hugging Face integration
        "huggingface-hub>=0.20.3,<1.0.0",
        
        # Audio processing for speech synthesis
        "soundfile>=0.12.1",
        "numpy>=1.24.3",
        "scipy>=1.11.0",
        "torchaudio>=2.1.0",
        "omegaconf>=2.3.0",
        
        # Accentuation and stress marks for Slavic languages
        "silero-stress>=0.1.0",
        
        # Text processing utilities
        "regex>=2023.10.3",
    ],
    entry_points={
        "console_scripts": [
            "kabardian-translator=kabardian_translator.cli:main",
            "kabardian-download-models=kabardian_translator.download_models:main",
            "kabardian-translate=kabardian_translator.cli:translate_cli",
        ],
    },
    include_package_data=True,
    package_data={
        'kabardian_translator': [
            'templates/*.html',
            'static/*.css',
            'static/*.js',
            'static/*.png',
            'static/*.ico',
            'models/*',
            '*.py',
        ],
    },
    data_files=[
        ('share/kabardian-translator', [
            'README.md',
            'LICENSE',
        ]),
    ],
    extras_require={
        'audio': [
            'librosa>=0.10.0',
        ],
        'accentuation': [
            'silero-stress>=0.1.0',
        ],
        'dev': [
            'pytest>=7.0.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
            'mypy>=1.7.0',
            'pytest-cov>=4.1.0',
        ],
        'gui': [
            'gradio>=4.0.0',
            'ipywidgets>=8.0.0',
        ],
        'full': [
            'librosa>=0.10.0',
            'silero-stress>=0.1.0',
            'gradio>=4.0.0',
            'pytest>=7.0.0',
        ],
    },
    project_urls={
        "Documentation": "https://github.com/kubataba/kabardian-translator/wiki",
        "Source Code": "https://github.com/kubataba/kabardian-translator",
        "Bug Tracker": "https://github.com/kubataba/kabardian-translator/issues",
        "Changelog": "https://github.com/kubataba/kabardian-translator/releases",
    },
    license_files=('LICENSE',),
    platforms=["macOS", "Linux", "Windows"],
    provides=["kabardian_translator"],
)