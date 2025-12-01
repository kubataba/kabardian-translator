# setup.py - измените version
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="kabardian-translator",
    version="1.0.2",
    author="Kubataba",
    author_email="info@copperline.info",
    description="Multilingual translator for Kabardian and Caucasian languages with speech synthesis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kubataba/kabardian-translator",
    packages=find_packages(include=['kabardian_translator']),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Education",
        "Intended Audience :: Science/Research",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.11",
    install_requires=[
        # Web framework
        "flask>=3.0.0",
        
        # Machine learning core
        "torch>=2.1.0",
        "transformers>=4.37.0,<5.0.0",
        "sentencepiece>=0.1.99",
        
        # Optimization for Apple Silicon
        "accelerate>=0.24.1",
        
        # Hugging Face integration
        "huggingface-hub>=0.20.3,<1.0.0",
        
        # Audio processing
        "soundfile>=0.12.1",
        "numpy>=1.24.3",
        "scipy>=1.11.0",  # ДОБАВЛЕНО: необходимо для Silero TTS
        "torchaudio>=2.1.0",
        "omegaconf>=2.3.0",
        
        # Optional: advanced audio processing
        "librosa>=0.10.0; extra == 'audio'",
    ],
    entry_points={
        "console_scripts": [
            "kabardian-translator=kabardian_translator.cli:main",
            "kabardian-download-models=kabardian_translator.download_models:main",
        ],
    },
    include_package_data=True,
    package_data={
        'kabardian_translator': [
            'templates/*.html',
            '*.py',
        ],
    },
    extras_require={
        'audio': ['librosa>=0.10.0'],
        'dev': [
            'pytest>=7.0.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
        ],
    },
)