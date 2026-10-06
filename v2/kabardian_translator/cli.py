"""Command-line entry points.

  kabardian-translator [--port 5500] [--no-browser]     the web interface on http://127.0.0.1:5500
  kabardian-translate -s ru -t kbd "text"               translate a string
  kabardian-translate -s en -t kbd -i book.docx -o book.kbd.docx [--fast] [--both]
  kabardian-download-models [kbd madlad small100 silero baltic | all]   (all = what this system uses)
"""
from __future__ import annotations

import argparse
import sys
import threading
import time
import webbrowser
from pathlib import Path

from . import __version__, documents, languages, models


def main(argv=None):
    """kabardian-translator — the web interface."""
    ap = argparse.ArgumentParser(prog="kabardian-translator", description=f"Kabardian Translator {__version__}")
    ap.add_argument("--port", type=int, default=5500)
    ap.add_argument("--no-browser", action="store_true")
    a = ap.parse_args(argv)
    missing = [k for k in models.available() if not models.installed(k)]
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
    ap.add_argument("-s", "--src", required=True, choices=sorted(languages.available()))
    ap.add_argument("-t", "--tgt", required=True, choices=sorted(languages.available()))
    ap.add_argument("-i", "--input", help=".txt, .md or .docx")
    ap.add_argument("-o", "--output", help=".txt or .docx (default: stdout)")
    ap.add_argument("--fast", action="store_true", help="greedy search for Kabardian (about 2× faster)")
    ap.add_argument("--both", action="store_true", help="original and translation sentence by sentence, both languages named")
    a = ap.parse_args(argv)
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
    pairs = []
    out = tr.text(text, a.src, a.tgt, beams=1 if a.fast else 4, progress=progress if a.input else None, pairs=pairs)
    if a.input:
        print(file=sys.stderr)
    if a.output:
        fmt = "docx" if a.output.lower().endswith(".docx") else "txt"
        title = Path(a.input).stem if a.input else None
        data = documents.write_bilingual(pairs, languages.name(a.src), languages.name(a.tgt), a.src, a.tgt, fmt, title) \
            if a.both else documents.write(out, fmt, title=title)
        Path(a.output).write_bytes(data)
        print(f"written {a.output}", file=sys.stderr)
    elif a.both:
        sys.stdout.write(documents.write_bilingual(pairs, languages.name(a.src), languages.name(a.tgt), a.src, a.tgt)
                         .decode("utf-8"))
    else:
        print(out)


def download_models(argv=None):
    sys.exit(models.main(argv))
