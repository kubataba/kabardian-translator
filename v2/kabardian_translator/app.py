"""The web interface: one page (templates/index.html) and a small JSON API. Runs on 127.0.0.1 only."""
from __future__ import annotations

import io
import threading
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file

from . import __version__, documents, languages, models, system
from .translator import Jobs, Translator
from .tts import Speech

app = Flask(__name__, template_folder=str(Path(__file__).parent / "templates"))
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024 * 1024           # 64 MB documents
app.json.sort_keys = False                                      # groups and languages keep their order
translator = Translator()
jobs = Jobs(translator)
speech = Speech()
installs = {}                                                   # model key → {"state", "log"}
audio_cache = {}                                                # id → wav bytes, the last 40 spoken paragraphs


@app.get("/")
def index():
    return render_template("index.html", version=__version__)


@app.get("/api/languages")
def api_languages():
    ui = request.args.get("ui", "en")
    rows = languages.describe(ui)
    for r in rows:
        r["voices"] = [o["engine"] for o in speech.options(r["code"])][:1]
    groups = {g: dict(zip(("ru", "en", "lv"), names)).get(ui) for g, names in languages.GROUPS.items()}
    return jsonify({"languages": rows, "groups": groups, "engine": languages.engine_name(),
                    "engine_key": system.translator(), "can_choose": system.can_choose(),
                    "madlad_python": system.madlad_blocked_by_python()})


switching = {}                                                  # the translator switch in progress: state, log


@app.get("/api/translator")
def api_translator():
    return jsonify({"engine": system.translator(), "name": languages.engine_name(), "can_choose": system.can_choose(),
                    "switch": switching or None})


@app.post("/api/translator")
def api_translator_switch():
    """Mac with Apple Silicon: install the chosen translator, switch to it, remove the other one."""
    engine = (request.get_json(force=True) or {}).get("engine")
    if not system.can_choose():
        return jsonify({"error": "no choice of translator on this computer"}), 400
    if engine not in system.ENGINES:
        return jsonify({"error": "unknown translator"}), 400
    if switching.get("state") == "running":
        return jsonify({"state": "running"})
    if any(i.get("state") in ("queued", "running") for i in installs.values()) or \
            any(j["state"] in ("queued", "running") for j in jobs.jobs.values()):
        return jsonify({"error": "busy"}), 409
    if engine == system.translator() and models.installed(engine):
        return jsonify({"state": "done"})
    switching.clear()
    switching.update(state="running", engine=engine, log=[])

    def run():
        try:
            with jobs.run_lock:                                 # no translation starts while the model changes
                models.switch_translator(engine, progress=lambda m: switching["log"].append(m))
                translator.unload()
            switching["state"] = "done"
        except Exception as e:
            switching.update(state="error", error=str(e))
    threading.Thread(target=run, daemon=True).start()
    return jsonify({"state": "running"})


@app.get("/api/models")
def api_models():
    st = models.status()
    for k in st:
        st[k]["install"] = installs.get(k)
    return jsonify({"models": st, "loaded": translator.loaded()})


@app.post("/api/models/<key>/install")
def api_install(key):
    if key not in models.PACKAGES:
        return jsonify({"error": "unknown model"}), 404
    if installs.get(key, {}).get("state") == "running":
        return jsonify({"state": "running"})
    threading.Thread(target=_install_now, args=(key,), daemon=True).start()
    return jsonify({"state": "running"})


_install_lock = threading.Lock()
AUTO_ORDER = ("kbd", "madlad", "small100", "silero", "baltic")     # translation first, then the voices


def _install_now(key: str) -> None:
    """One package, with its progress in `installs` (the Models tab and the download banner read it)."""
    with _install_lock:
        if installs.get(key, {}).get("state") == "running":
            return
        rec = {"state": "running", "log": []}
        installs[key] = rec
    try:
        models.install(key, progress=lambda m: rec["log"].append(m))
        rec["state"] = "done"
    except Exception as e:
        rec["state"], rec["error"] = "error", str(e)


def auto_install() -> list:
    """Downloads the missing models of this system one by one in the background; returns their keys."""
    keys = [k for k in AUTO_ORDER if k in models.available() and not models.installed(k)]
    for k in keys:
        installs[k] = {"state": "queued", "log": []}

    def run():
        for k in keys:
            if not models.installed(k):
                _install_now(k)
    if keys:
        threading.Thread(target=run, daemon=True).start()
    return keys


@app.post("/api/translate")
def api_translate():
    d = request.get_json(force=True)
    text = (d.get("text") or "").strip("\n")
    src, tgt = d.get("src", "ru"), d.get("tgt", "kbd")
    if not text.strip():
        return jsonify({"error": "empty"}), 400
    if src not in languages.available() or tgt not in languages.available():
        return jsonify({"error": "unknown language"}), 400
    jid = jobs.start(text, src, tgt, beams=1 if d.get("fast") else 4)
    return jsonify({"job": jid})


@app.post("/api/document")
def api_document():
    f = request.files.get("file")
    src, tgt = request.form.get("src", "ru"), request.form.get("tgt", "kbd")
    if not f:
        return jsonify({"error": "no file"}), 400
    if src not in languages.available() or tgt not in languages.available():
        return jsonify({"error": "unknown language"}), 400
    try:
        text = documents.read(f.filename, f.read())
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    jid = jobs.start(text, src, tgt, beams=1 if request.form.get("fast") == "1" else 4, name=f.filename)
    return jsonify({"job": jid, "chars": len(text), "text": text if len(text) <= 2_000_000 else text[:2_000_000]})


@app.get("/api/jobs/<jid>")
def api_job(jid):
    j = jobs.get(jid)
    if not j:
        return jsonify({"error": "unknown job"}), 404
    return jsonify({k: j[k] for k in ("id", "state", "done", "total", "partial", "result", "error", "seconds", "name")})


@app.get("/api/jobs/<jid>/download")
def api_download(jid):
    j = jobs.get(jid)
    if not j or j["state"] != "done":
        return jsonify({"error": "not ready"}), 404
    fmt = request.args.get("format", "txt")
    fmt = fmt if fmt in ("txt", "docx") else "txt"
    both = request.args.get("mode") == "bilingual"
    ui = request.args.get("ui", "en")
    title = Path(j["name"]).stem if j.get("name") else None
    if both:
        data = documents.write_bilingual(j["pairs"], languages.name(j["src"], ui), languages.name(j["tgt"], ui),
                                         j["src"], j["tgt"], fmt, title)
    else:
        data = documents.write(j["result"], fmt, title=title)
    stem = Path(j.get("name") or "translation").stem
    name = f"{stem}.{j['src']}-{j['tgt']}.{fmt}" if both else f"{stem}.{j['tgt']}.{fmt}"
    mime = "text/plain" if fmt == "txt" else \
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    return send_file(io.BytesIO(data), mimetype=mime, as_attachment=True, download_name=name)


@app.get("/api/voices")
def api_voices():
    return jsonify({"voices": speech.options(request.args.get("lang", "ru"))})


@app.post("/api/speak_marked")
def api_speak_marked():
    """One reading unit (a paragraph or a few sentences) → its audio (by URL) and the sentence/word timings for highlighting."""
    import uuid
    d = request.get_json(force=True)
    text, lang = d.get("text") or "", d.get("lang", "ru")
    if not text.strip():
        return jsonify({"error": "empty"}), 400
    try:
        samples, rate, sentences, words = speech.synthesize_marked(text, lang, d.get("voice") or None,
                                                                    float(d.get("speed", 1.0)))
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    aid = uuid.uuid4().hex[:12]
    audio_cache[aid] = Speech.wav_bytes(samples, rate)
    while len(audio_cache) > 40:
        audio_cache.pop(next(iter(audio_cache)))
    return jsonify({"audio": f"/api/audio/{aid}", "duration": round(len(samples) / rate, 3),
                    "sentences": sentences, "words": words})


@app.get("/api/audio/<aid>")
def api_audio(aid):
    data = audio_cache.get(aid)
    if data is None:
        return jsonify({"error": "expired"}), 404
    return send_file(io.BytesIO(data), mimetype="audio/wav")


def run(host="127.0.0.1", port=5500, download=True):
    # native libraries are loaded on the main thread, before requests come on worker threads
    import numpy  # noqa: F401
    import onnxruntime  # noqa: F401
    import soundfile  # noqa: F401
    if download:
        keys = auto_install()
        if keys:
            print(f"downloading the missing models in the background: {', '.join(keys)} — progress on the page")
    app.run(host=host, port=port, debug=False, threaded=True)
