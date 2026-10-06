"""Documents in and out: .txt / .md / .docx are read as paragraphs; the translation is written back as .txt or
.docx (paragraph for paragraph), optionally side by side with the original."""
from __future__ import annotations

import io
from pathlib import Path

READABLE = (".txt", ".md", ".docx")


def read(name: str, data: bytes) -> str:
    ext = Path(name).suffix.lower()
    if ext == ".docx":
        import docx
        d = docx.Document(io.BytesIO(data))
        return "\n\n".join(p.text for p in d.paragraphs if p.text.strip())
    if ext not in (".txt", ".md", ""):
        raise ValueError(f"unsupported file type {ext!r}: use .txt, .md or .docx")
    for enc in ("utf-8-sig", "utf-16", "cp1251", "latin-1"):
        try:
            text = data.decode(enc)
            if enc == "utf-16" and "\x00" in text:
                continue
            return text.replace("\r\n", "\n")
        except UnicodeDecodeError:
            continue
    raise ValueError("cannot decode the file")


def _pairs(original: str, translation: str):
    a = [p for p in original.split("\n") if p.strip()]
    b = [p for p in translation.split("\n") if p.strip()]
    return list(zip(a, b)) if len(a) == len(b) else None


def write(translation: str, fmt: str = "txt", original: str | None = None, title: str | None = None) -> bytes:
    """fmt: txt | docx; with `original` the file holds both texts, paragraph by paragraph."""
    pairs = _pairs(original, translation) if original else None
    if fmt == "docx":
        import docx
        d = docx.Document()
        if title:
            d.add_heading(title, level=1)
        if pairs:
            for src, tgt in pairs:
                d.add_paragraph(src).runs[0].italic = True
                d.add_paragraph(tgt)
        else:
            for p in translation.split("\n"):
                if p.strip():
                    d.add_paragraph(p)
        buf = io.BytesIO()
        d.save(buf)
        return buf.getvalue()
    if pairs:
        text = "\n\n".join(f"{s}\n{t}" for s, t in pairs)
    else:
        text = translation
    return (text.rstrip() + "\n").encode("utf-8")
