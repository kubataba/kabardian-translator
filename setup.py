from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="kabardian-translator",
    version="1.0.0",
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
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "kabardian-translator=kabardian_translator.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        '': ['templates/*.html'],  # Включаем шаблоны
    },
)