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


PACKAGES = {
    "kbd": Package(
        key="kbd", title="Kabardian translator (Russian ↔ Kabardian)", tag="kbd-translate-v1", size_mb=84,
        assets=(Asset("kbd-translate-v1.zip", "b25ce9cd50d3b0f103eb68f9de068bad41fa899522ecf011e0dd2985ab7bf292",
                      "translate-kbd/kbd-translate-v1.zip", unzip=True),
                # Russian form dictionary for the colour-compound rule (language pack ru, Wiktionary/Kaikki)
                Asset("lang-ru.zip", "47fd7e8d0beb8fa36c5a2366ab80a3d9de58dcf77238726e77b64c0c0ad4c8db",
                      "lang-ru.zip", unzip=True, tag="lang-v13", members=("ru-morph.txt",))),
        required=("encoder_model.int8.onnx", "decoder_merged.int8.int32flag.onnx", "source.spm", "vocab.json",
                  "ru-morph.txt"),
        licence="SIA Copper Line, see the release LICENCE; source model kubataba/ru-kbd-bidirectional (CC BY-NC 4.0)"),
    "madlad": Package(
        key="madlad", title="MADLAD-400 3B on the Neural Engine (every other language)", tag="translate-madlad-v1",
        size_mb=1335,
        assets=(Asset("madlad-sayfable-v1.zip", "7f48279ec6bf9694ac0342bb5d43ca62b0b290cef08eb35be1554ac03c1a2b80",
                      "translate-madlad/madlad-sayfable-v1.zip", unzip=True),),
        required=("spiece.model", "embed_int8.bin", "embed_scale_fp16.bin", ("decoder_24_32.mlpackage",
                                                                             "compiled/decoder_24_32.mlmodelc")),
        licence="Apache-2.0 (google/madlad400-3b-mt, modified: see ATTRIBUTION.md)"),
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
                      "piper/piper-baltic/et.dict")),
        required=("baltic-sayfable.onnx", "baltic-sayfable.onnx.json", "lt.dict", "et.dict"),
        licence="SIA Copper Line, see the release LICENCE"),
}


def folder(key: str) -> Path:
    return MODELS / key


def _present(f: Path, r) -> bool:
    """A required file, or any of a tuple of alternatives (a package or its compiled form)."""
    return any((f / x).exists() for x in r) if isinstance(r, tuple) else (f / r).exists()


def installed(key: str) -> bool:
    f = folder(key)
    return all(_present(f, r) for r in PACKAGES[key].required)


def status() -> dict:
    return {k: {"installed": installed(k), "title": p.title, "size_mb": p.size_mb, "licence": p.licence}
            for k, p in PACKAGES.items()}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _local_root() -> Path | None:
    p = Path(os.environ.get("KT_LOCAL_MODELS", LOCAL_DEFAULT))
    return p if p.exists() else None


def _fetch(pkg: Package, asset: Asset, dest: Path, progress) -> None:
    root = _local_root()
    if root and (root / asset.local).exists():
        progress(f"{asset.name}: local copy")
        shutil.copyfile(root / asset.local, dest)
        return
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


def install(key: str, progress=print, force: bool = False) -> Path:
    pkg = PACKAGES[key]
    target = folder(key)
    if installed(key) and not force:
        return target
    MODELS.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f"{key}-", dir=MODELS))
    try:
        unpacked = stage / "package"
        unpacked.mkdir()
        for asset in pkg.assets:
            tmp = stage / asset.name
            _fetch(pkg, asset, tmp, progress)
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
        if target.exists():
            shutil.rmtree(target)
        unpacked.rename(target)
        progress(f"{key}: installed in {target}")
        return target
    finally:
        shutil.rmtree(stage, ignore_errors=True)


def remove(key: str) -> None:
    shutil.rmtree(folder(key), ignore_errors=True)


def main(argv=None) -> int:
    """kabardian-download-models [kbd madlad silero baltic | all] [--force]"""
    args = argv if argv is not None else sys.argv[1:]
    force = "--force" in args
    args = [a for a in args if a != "--force"]
    keys = list(PACKAGES) if not args or args == ["all"] else args
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
