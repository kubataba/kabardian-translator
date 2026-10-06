"""The web server as a browser uses it: a separate `kabardian-translator` process, requests answered on its worker
threads. The smoke test calls the code on the main thread only and so missed the crash of 06.10 (COM on a worker
thread on Windows, Python 3.14). On a crash the process's faulthandler dump is printed. Exit code 1 on failure."""
import json
import subprocess
import sys
import time
import urllib.request

PORT = 5511
BASE = f"http://127.0.0.1:{PORT}"
proc = subprocess.Popen([sys.executable, "-X", "faulthandler", "-c",
                         f"from kabardian_translator.cli import main; main(['--no-browser', '--port', '{PORT}'])"],
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace")


def fail(msg):
    proc.terminate()
    out = proc.communicate(timeout=30)[0]
    print("FAILED:", msg, "\n--- server output ---\n", out[-6000:])
    sys.exit(1)


def call(path, body=None, timeout=300):
    if proc.poll() is not None:
        fail(f"the server died before {path}")
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json"} if body is not None else {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read()
    except Exception as e:
        fail(f"{path}: {e}")
    return json.loads(data) if data[:1] in (b"{", b"[") else data


for _ in range(120):
    try:
        urllib.request.urlopen(BASE + "/", timeout=2)
        break
    except Exception:
        if proc.poll() is not None:
            fail("the server did not start")
        time.sleep(1)
else:
    fail("no answer from the server")

langs = call("/api/languages?ui=en")
print(f"languages: {len(langs['languages'])}, engine {langs['engine']}, can choose: {langs['can_choose']}")
for lang in ("ru", "lv", "en", "de"):
    voices = call(f"/api/voices?lang={lang}")["voices"]
    print(f"voices {lang}: {[v['label'] for v in voices][:4]}")
    if not voices:
        continue
    r = call("/api/speak_marked", {"text": "Hello. Labdien. Добрый день.", "lang": lang, "voice": voices[0]["id"]})
    if "error" in r:
        fail(f"speech {lang}: {r['error']}")
    audio = call(r["audio"])
    print(f"  speech {lang} via {voices[0]['label']}: {r['duration']} s, {len(audio)} bytes, "
          f"{len(r['sentences'])} sentences")
    assert r["duration"] > 0.5 and len(audio) > 10000, f"speech {lang} too short"

job = call("/api/translate", {"text": "The old castle stood on the hill.\n\nIt was cold.", "src": "en", "tgt": "kbd"})
for _ in range(600):
    j = call(f"/api/jobs/{job['job']}")
    if j["state"] in ("done", "error"):
        break
    time.sleep(1)
if j["state"] != "done":
    fail(f"translation: {j}")
print("translation en->kbd:", j["result"].replace("\n", " | "))
if proc.poll() is not None:
    fail("the server died at the end")
proc.terminate()
print("OK")
