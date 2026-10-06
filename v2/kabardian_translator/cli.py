"""Command-line entry points.

  kabardian-translator [--port 5500] [--no-browser]     the web interface on http://127.0.0.1:5500
  kabardian-translate -s ru -t kbd "text"               translate a string
  kabardian-translate -s en -t kbd -i book.docx -o book.kbd.docx [--fast] [--both]
  kabardian-download-models [kbd madlad silero baltic | all]
"""
from __future__ import annotations

import argparse
import platform
import sys
import threading
import time
import webbrowser
from pathlib import Path

from . import __version__, documents, languages, models


def _check_platform():
    if sys.platform != "darwin" or platform.machine() != "arm64":
        print("Kabardian Translator 3 needs macOS on Apple Silicon (MADLAD runs on the Apple Neural Engine).\n"
              "On Windows and Linux use version 2.0: pip install 'kabardian-translator<3'", file=sys.stderr)
        sys.exit(1)


def main(argv=None):
    """kabardian-translator — the web interface."""
    ap = argparse.ArgumentParser(prog="kabardian-translator", description=f"Kabardian Translator {__version__}")
    ap.add_argument("--port", type=int, default=5500)
    ap.add_argument("--no-browser", action="store_true")
    a = ap.parse_args(argv)
    _check_platform()
    missing = [k for k in models.PACKAGES if not models.installed(k)]
    url = f"http://127.0.0.1:{a.port}"
    print(f"Kabardian Translator {__version__} — {url}")
    if missing:
        print(f"models not installed yet: {', '.join(missing)} — install them on the Models tab "
              f"or with: kabardian-download-models all")
    if not a.no_browser:
        threading.Timer(1.2, lambda: webbrowser.open(url)).start()
    from .app import run
    run(port=a.port)


def translate_cli(argv=None):
    """kabardian-translate — a string or a document from the terminal."""
    ap = argparse.ArgumentParser(prog="kabardian-translate")
    ap.add_argument("text", nargs="?", help="text to translate (or use -i)")
    ap.add_argument("-s", "--src", required=True, choices=sorted(languages.LANGS))
    ap.add_argument("-t", "--tgt", required=True, choices=sorted(languages.LANGS))
    ap.add_argument("-i", "--input", help=".txt, .md or .docx")
    ap.add_argument("-o", "--output", help=".txt or .docx (default: stdout)")
    ap.add_argument("--fast", action="store_true", help="greedy search for Kabardian (about 2× faster)")
    ap.add_argument("--both", action="store_true", help="write the original and the translation together")
    a = ap.parse_args(argv)
    _check_platform()
    if a.input:
        p = Path(a.input)
        text = documents.read(p.name, p.read_bytes())
    elif a.text:
        text = a.text
    else:
        text = sys.stdin.read()
    from .translator import Translator
    tr = Translator()
    t0 = time.time()

    def progress(done, total, _):
        print(f"\r{done}/{total} paragraphs  {time.time() - t0:.0f} s", end="", file=sys.stderr, flush=True)
    out = tr.text(text, a.src, a.tgt, beams=1 if a.fast else 4, progress=progress if a.input else None)
    if a.input:
        print(file=sys.stderr)
    if a.output:
        fmt = "docx" if a.output.lower().endswith(".docx") else "txt"
        Path(a.output).write_bytes(documents.write(out, fmt, text if a.both else None))
        print(f"written {a.output}", file=sys.stderr)
    else:
        print(out)


def download_models(argv=None):
    sys.exit(models.main(argv))
