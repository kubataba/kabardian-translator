"""Model packages: where they come from, how they are checked and where they live.

Every package is downloaded from the releases of github.com/kubataba/sayfable-models (the same files the SayFable
iOS app uses), verified by SHA-256 BEFORE it is unpacked, and kept in ~/.kabardian-translator/models/<name>/.
A local copy of the sayfable-models folder (KT_LOCAL_MODELS, or the default path on the author's Mac) is used
instead of the network when present — the checksum is verified all the same.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

RELEASES = "https://github.com/kubataba/sayfable-models/releases/download"
HOME = Path(os.environ.get("KT_HOME", Path.home() / ".kabardian-translator"))
MODELS = HOME / "models"
LOCAL_DEFAULT = Path("/Volumes/Shared/sayfable/data/projects/sayfable-models")


@dataclass(frozen=True)
class Asset:
    name: str            # file name in the release
    sha256: str
    local: str           # path inside a local sayfable-models folder
    unzip: bool = False  # a zip whose content becomes the package folder
    tag: str = ""        # release tag when it differs from the package's
    members: tuple = ()  # unzip only these files (empty: everything)


@dataclass(frozen=True)
class Package:
    key: str
    title: str
    tag: str             # release tag in kubataba/sayfable-models
    size_mb: int
    assets: tuple
    required: tuple      # files that must exist in the package folder
    licence: str
    note: str = ""
    extras: dict = field(default_factory=dict)
    marker: str = ""     # version file written after a successful install and required by installed(): a new
                         # release with the same file names must not pass for the old one (kbd v1 → v2)


PACKAGES = {
    "kbd": Package(
        key="kbd", title="Kabardian translator (Russian ↔ Kabardian)", tag="kbd-translate-v2", size_mb=83,
        assets=(Asset("kbd-translate-v2.zip", "1a93b8aece1123cfe64360f7b27ca4aadc4959b367eae933045f6e253fc125d6",
                      "translate-kbd/release-v2/kbd-translate-v2.zip", unzip=True),
                # Russian form dictionary for the colour-compound rule (language pack ru, Wiktionary/Kaikki)
                Asset("lang-ru.zip", "47fd7e8d0beb8fa36c5a2366ab80a3d9de58dcf77238726e77b64c0c0ad4c8db",
                      "lang-ru.zip", unzip=True, tag="lang-v13", members=("ru-morph.txt",))),
        required=("encoder_model.int8.onnx", "decoder_merged.int8.int32flag.onnx", "source.spm", "vocab.json",
                  "ru-morph.txt"),
        licence="SIA Copper Line, see the release LICENCE; source model kubataba/ru-kbd-bidirectional (CC BY-NC 4.0)",
        marker="kbd-translate-v2"),
    "madlad": Package(
        key="madlad", title="MADLAD-400 3B on the Neural Engine (every other language)", tag="translate-madlad-v1",
        size_mb=1335,
        assets=(Asset("madlad-sayfable-v1.zip", "7f48279ec6bf9694ac0342bb5d43ca62b0b290cef08eb35be1554ac03c1a2b80",
                      "translate-madlad/madlad-sayfable-v1.zip", unzip=True),),
        required=("spiece.model", "embed_int8.bin", "embed_scale_fp16.bin", ("decoder_24_32.mlpackage",
                                                                             "compiled/decoder_24_32.mlmodelc")),
        licence="Apache-2.0 (google/madlad400-3b-mt, modified: see ATTRIBUTION.md)"),
    "small100": Package(
        key="small100", title="SMaLL-100 (every other language; lighter and faster)", tag="translate-v1",
        size_mb=289,
        assets=(Asset("translate_small100.zip", "67835318ee6c10ad1dfb78225d49c8c0f22a360cafeca185cf2a2066b9126bcb",
                      "translate-small100/translate_small100.zip", unzip=True),),
        required=("encoder_model.int8.onnx", "decoder_merged.int8.int32flag.onnx", "bpe_vocab.tsv",
                  "token_ids.json"),
        licence="MIT (alirezamsh/small100, teacher facebook/m2m100_418M), ONNX int8 by SayFable"),
    "silero": Package(
        key="silero", title="Silero v5 speech (Russian, Kabardian and CIS languages)", tag="v5.1", size_mb=118,
        assets=(Asset("silero_v5_full.zip", "980324357a1fb4c07bb3c29f35d2879c5946a8330d05935897b849a265510c79",
                      "silero/dist/silero_v5_full.zip", unzip=True),
                # Russian stress without PyTorch: n-gram accentor + homograph BERT (silero-stress 1.5 export)
                Asset("silero_ru_stress.zip", "05c85b779cfed78e170fef744c58a695601c1e10b64512390f60662936657895",
                      "silero/dist/silero_ru_stress_v5.3.zip", unzip=True, tag="v5.3")),
        required=("dur_predictor.onnx", "pitch_predictor.onnx", "mel_encoder.onnx", "mel_decoder.onnx", "vocoder.onnx",
                  "accentor_ru_weights.bin", "ru_homosolver_bert.onnx"),
        licence="CC BY-NC-SA 4.0 (snakers4/silero-models), ONNX export by SayFable"),
    "baltic": Package(
        key="baltic", title="Baltic speech: Latvian, Lithuanian, Estonian (18 voices)", tag="baltic-sayfable-v1",
        size_mb=94,
        assets=(Asset("baltic-sayfable.onnx", "736e24458e70a5a64c304a37596c7bf38dca52b92906a9afb5970bb0ed433501",
                      "piper/piper-baltic/baltic-sayfable.onnx"),
                Asset("baltic-sayfable.onnx.json", "c12bf34888bb67e645eaddd8a6a7fed408b4737fa2ca4e3800d9e8b7f9fae722",
                      "piper/piper-baltic/baltic-sayfable.onnx.json"),
                Asset("lt.dict", "d3ddc2b4a1fe5532047ce3ea3266075e4a92d1eaf2b9b66ec6a78e73d75917ab",
                      "piper/piper-baltic/lt.dict"),
                Asset("et.dict", "4d94bbb6234ea669167fde6bc0b4435677b5230418a86f02f259a37d6407db07",
                      "piper/piper-baltic/et.dict"),
                # form dictionaries of the language packs (Wiktionary/Kaikki): a Roman letter in a heading
                # («X skyrius») and the case of an Estonian ordinal are decided by them, as in the app
                Asset("lang-lv.zip", "29960ddd2ca71936413e40be11580a635f9ea4cc0fbf9b3d588fb6079e41a9e2",
                      "lang-lv.zip", unzip=True, tag="lang-v2", members=("lv-morph.txt",)),
                Asset("lang-lt.zip", "90e6985f8569bf47f791dd7892d7f4dcbec87a73c596893cbbbb91fbc5af54f5",
                      "lang-lt.zip", unzip=True, tag="lang-v7", members=("lt-morph.txt",)),
                Asset("lang-et.zip", "a06a569943f34e3b962b07c25e5dcc2ec697306a7035fd2db1a80aa01e1653aa",
                      "lang-et.zip", unzip=True, tag="lang-v4", members=("et-morph.txt",))),
        required=("baltic-sayfable.onnx", "baltic-sayfable.onnx.json", "lt.dict", "et.dict", "lv-morph.txt",
                  "lt-morph.txt", "et-morph.txt"),
        licence="SIA Copper Line, see the release LICENCE"),
}


def available() -> list:
    """The packages this system uses: the chosen translator (MADLAD or SMaLL-100) and the rest."""
    from .system import translator
    return [k for k in PACKAGES if k not in ("madlad", "small100") or k == translator()]


def folder(key: str) -> Path:
    return MODELS / key


def _present(f: Path, r) -> bool:
    """A required file, or any of a tuple of alternatives (a package or its compiled form)."""
    return any((f / x).exists() for x in r) if isinstance(r, tuple) else (f / r).exists()


def _marker(pkg: Package) -> str:
    return f".{pkg.marker}" if pkg.marker else ""


def installed(key: str) -> bool:
    f, pkg = folder(key), PACKAGES[key]
    if pkg.marker and not (f / _marker(pkg)).exists():
        return False            # an older release of the same package (same file names): to be replaced
    return all(_present(f, r) for r in pkg.required)


def status() -> dict:
    return {k: {"installed": installed(k), "title": PACKAGES[k].title, "size_mb": PACKAGES[k].size_mb,
                "licence": PACKAGES[k].licence} for k in available()}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _local_root() -> Path | None:
    p = Path(os.environ.get("KT_LOCAL_MODELS", LOCAL_DEFAULT))
    return p if p.exists() else None


def _fetch(pkg: Package, asset: Asset, dest: Path, progress, local: bool = True) -> bool:
    """Copies the local file when there is one (→ True), else downloads the release asset (→ False)."""
    root = _local_root() if local else None
    if root and (root / asset.local).exists():
        progress(f"{asset.name}: local copy")
        shutil.copyfile(root / asset.local, dest)
        return True
    url = f"{RELEASES}/{asset.tag or pkg.tag}/{asset.name}"
    progress(f"{asset.name}: downloading {url}")
    with urllib.request.urlopen(url) as r, open(dest, "wb") as out:
        total = int(r.headers.get("Content-Length", 0)) or None
        done, last = 0, -1
        while True:
            block = r.read(1 << 20)
            if not block:
                break
            out.write(block)
            done += len(block)
            if total:
                pct = done * 100 // total
                if pct != last and pct % 5 == 0:
                    progress(f"{asset.name}: {pct}%")
                    last = pct
    return False


def _unzip(zip_path: Path, target: Path, members: tuple = ()) -> None:
    with zipfile.ZipFile(zip_path) as z:
        names = [n for n in z.namelist() if "/._" not in n and not n.startswith(("__MACOSX", "._"))]
        if members:
            names = [n for n in names if n.rsplit("/", 1)[-1] in members]
        tops = {n.split("/", 1)[0] for n in names}
        strip = len(tops) == 1 and all("/" in n for n in names if not n.endswith("/"))
        for n in names:
            rel = n.split("/", 1)[1] if strip else n
            if not rel or n.endswith("/"):
                continue
            out = target / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            with z.open(n) as src, open(out, "wb") as dst:
                shutil.copyfileobj(src, dst)


def _remove_orphan_stages(key: str, older_than_s: float = 3600) -> None:
    """A stage folder <key>-xxxx is removed by install() itself, except when the process dies mid-download (closed
    terminal, killed server): then a partial download stays in models/ for ever. Older than an hour = no live
    install owns it."""
    import time
    for d in MODELS.glob(f"{key}-*"):
        if d.is_dir() and time.time() - d.stat().st_mtime > older_than_s:
            shutil.rmtree(d, ignore_errors=True)


def install(key: str, progress=print, force: bool = False) -> Path:
    pkg = PACKAGES[key]
    target = folder(key)
    if installed(key) and not force:
        return target
    MODELS.mkdir(parents=True, exist_ok=True)
    _remove_orphan_stages(key)
    stage = Path(tempfile.mkdtemp(prefix=f"{key}-", dir=MODELS))
    try:
        unpacked = stage / "package"
        unpacked.mkdir()
        for asset in pkg.assets:
            tmp = stage / asset.name
            if _fetch(pkg, asset, tmp, progress) and _sha256(tmp) != asset.sha256:
                progress(f"{asset.name}: the local copy is a different file, downloading the release")
                _fetch(pkg, asset, tmp, progress, local=False)
            got = _sha256(tmp)
            if got != asset.sha256:
                raise RuntimeError(f"{asset.name}: checksum mismatch (expected {asset.sha256[:12]}…, got {got[:12]}…)")
            if asset.unzip:
                progress(f"{asset.name}: unpacking")
                _unzip(tmp, unpacked, asset.members)
                tmp.unlink()
            else:
                tmp.rename(unpacked / asset.name)
        missing = [r for r in pkg.required if not _present(unpacked, r)]
        if missing:
            raise RuntimeError(f"{key}: package is incomplete, missing {missing}")
        if pkg.marker:
            (unpacked / _marker(pkg)).write_text(pkg.tag + "\n", "utf-8")
        if target.exists():
            shutil.rmtree(target)
        unpacked.rename(target)
        progress(f"{key}: installed in {target}")
        return target
    finally:
        shutil.rmtree(stage, ignore_errors=True)


def remove(key: str) -> None:
    shutil.rmtree(folder(key), ignore_errors=True)


def switch_translator(engine: str, progress=print) -> None:
    """Mac with Apple Silicon: the chosen translator is installed (downloaded if it is not there), becomes the
    translator, and only then the other one is removed — a failed download changes nothing."""
    from . import system
    if not system.can_choose():
        raise RuntimeError("this computer has no choice of translator")
    if engine not in system.ENGINES:
        raise ValueError(f"unknown translator {engine!r}")
    install(engine, progress)
    system.set_translator(engine)
    for other in system.ENGINES:
        if other != engine and folder(other).exists():
            remove(other)
            progress(f"{other}: removed")


def main(argv=None) -> int:
    """kabardian-download-models [kbd madlad small100 silero baltic | all] [--force]; all = what this system uses;
    kabardian-download-models use madlad|small100 — switch the translator on a Mac with Apple Silicon"""
    args = argv if argv is not None else sys.argv[1:]
    force = "--force" in args
    args = [a for a in args if a != "--force"]
    if args[:1] == ["use"] and len(args) == 2:
        switch_translator(args[1])
        return 0
    keys = available() if not args or args == ["all"] else args
    for k in keys:
        if k not in PACKAGES:
            print(f"unknown package {k!r}; known: {', '.join(PACKAGES)}")
            return 2
        p = PACKAGES[k]
        print(f"== {p.title} ({p.size_mb} MB)")
        install(k, force=force)
    return 0


if __name__ == "__main__":
    sys.exit(main())
