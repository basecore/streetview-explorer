#!/usr/bin/env python3
"""
streetview_server.py  -  Lokaler Mini-Server fuer die HTML5 Web-App
Laeuft auf http://localhost:5000
Streamt den Log per SSE (Server-Sent Events) live in den Browser.

Start:
  python streetview_server.py        (Windows)
  python3 streetview_server.py       (Linux/macOS)

Stoppen:
  Ctrl+C
"""

import json
import logging
import os
import queue
import re
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path


def _ensure(pkg, import_as=None):
    try:
        __import__(import_as or pkg)
    except ImportError:
        print(f"[AUTO-INSTALL] {pkg}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])

_ensure("flask")
_ensure("flask_cors", "flask_cors")

from flask import Flask, Response, jsonify, request, stream_with_context
from flask_cors import CORS

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s  [%(levelname)-7s]  %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("svex-server")

app = Flask(__name__)
CORS(app)

BASE     = Path(__file__).parent
HEADLESS = BASE / "streetview_headless.py"

_jobs: dict = {}
_jobs_lock  = threading.Lock()


# ---------------------------------------------------------------------------
# Hilfsfunktion: CMD bauen
# ---------------------------------------------------------------------------

def _build_cmd(params: dict, pano_ids_file: str = None) -> list:
    """Baut den streetview_headless.py Aufruf aus params zusammen."""
    street = params.get("street", "").strip()
    city   = params.get("city",   "").strip()

    cmd = [
        sys.executable, str(HEADLESS),
        "--street",        street or "unbekannt",
        "--city",          city,
        "--quality",       params.get("quality",       "medium"),
        "--sampling",      str(params.get("sampling",   10)),
        "--radius",        str(params.get("radius",     8)),
        "--historical",    str(params.get("historical", "false")),
        "--output",        params.get("output", str(BASE / "downloads")),
        "--heading",       str(params.get("heading",    0)),
        "--pitch",         str(params.get("pitch",      0)),
        "--fov",           str(params.get("fov",        90)),
        "--zoom",          str(params.get("zoom",       2)),
        "--output-format", params.get("output_format",  "jpg"),
        "--jpg-quality",   str(params.get("jpg_quality", 85)),
    ]

    # Optionale Parameter nur wenn nicht leer
    for flag, key in [
        ("--date-from",  "date_from"),
        ("--date-to",    "date_to"),
        ("--source",     "source"),
        ("--outdoor",    "outdoor"),
    ]:
        val = str(params.get(key, "")).strip()
        if val:
            cmd += [flag, val]

    max_age = str(params.get("max_age_months", "")).strip()
    if max_age:
        cmd += ["--max-age-months", max_age]

    if pano_ids_file:
        cmd += ["--pano-ids-file", pano_ids_file]

    return cmd


# ---------------------------------------------------------------------------
# Job Runner
# ---------------------------------------------------------------------------

def _run_job(job_id: str, params: dict):
    """streetview_headless.py in einem Thread ausfuehren."""
    q        = _jobs[job_id]["queue"]
    street   = params.get("street", "").strip()
    pano_ids = params.get("pano_ids", [])

    coord_mode = bool(re.match(r'^-?\d+\.?\d*,\s*-?\d+\.?\d*$', street))
    INVALID    = {"", "karte", "map", "unknown", "unbekannt"}

    if not pano_ids and not coord_mode and street.lower() in INVALID:
        q.put({"type": "error", "data": (
            f"Ungültiger Strassenname: \"{street}\"\n"
            f"Bitte einen echten Strassennamen eingeben (z.B. 'Berger Strasse')."
        )})
        _jobs[job_id]["status"]     = "error"
        _jobs[job_id]["returncode"] = 1
        q.put({"type": "done", "data": "Abgebrochen (ungültiger Strassenname)", "rc": 1})
        return

    # pano_ids als temporaere JSON-Datei
    tmp_file = None
    if pano_ids:
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(pano_ids, tmp)
        tmp.close()
        tmp_file = tmp.name

    cmd = _build_cmd(params, pano_ids_file=tmp_file)
    env = os.environ.copy()
    env["GOOGLE_MAPS_API_KEY"] = params.get("api_key", "")

    q.put({"type": "cmd", "data": " ".join(cmd)})
    log.info("Job %s start: %s", job_id, " ".join(cmd))
    _jobs[job_id]["status"] = "running"

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
        )
        _jobs[job_id]["process"] = proc

        for line in proc.stdout:
            line = line.rstrip()
            if line:
                q.put({"type": "log", "data": line})

        proc.wait()
        rc = proc.returncode
        _jobs[job_id]["status"]     = "success" if rc == 0 else "error"
        _jobs[job_id]["returncode"] = rc
        q.put({"type": "done", "data": f"Prozess beendet (exit={rc})", "rc": rc})
        log.info("Job %s done rc=%d", job_id, rc)
    except Exception as e:
        _jobs[job_id]["status"] = "error"
        q.put({"type": "error", "data": str(e)})
        log.exception("Job %s exception", job_id)
    finally:
        if tmp_file:
            try:
                os.unlink(tmp_file)
            except OSError:
                pass


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/api/status")
def api_status():
    return jsonify({"status": "ok", "version": "3.5"})


# ── Einzelpunkt-Abfrage ────────────────────────────────────────────────────

@app.route("/api/query", methods=["POST"])
def api_query():
    """lat, lng, radius, api_key → panoramas[]"""
    params  = request.get_json(force=True)
    lat     = params.get("lat")
    lng     = params.get("lng")
    radius  = params.get("radius", 8)
    api_key = params.get("api_key", "")

    if lat is None or lng is None:
        return jsonify({"error": "lat und lng erforderlich"}), 400

    try:
        r = subprocess.run(
            ["streetview-dl", "query",
             "--lat",         str(lat),
             "--lng",         str(lng),
             "--radius",      str(radius),
             "--max-results", "5",
             "--json"],
            capture_output=True, text=True, timeout=15,
            env={**os.environ, "GOOGLE_MAPS_API_KEY": api_key}
        )
        if r.returncode == 0:
            return jsonify(json.loads(r.stdout))
    except Exception as e:
        log.warning("streetview-dl query fehlgeschlagen: %s", e)

    fid = f"pos_{str(lat).replace('.','_')}_{str(lng).replace('.','_')}"
    return jsonify({"panoramas": [{"pano_id": fid, "lat": lat, "lng": lng, "date": "?"}]})


# ── Historical Discovery ───────────────────────────────────────────────────

@app.route("/api/discover", methods=["POST"])
def api_discover():
    """
    Historische Zeitraeume fuer eine Position entdecken.
    Body: { pano_id, lat, lng, api_key, historical_max_depth, historical_max_panoramas }
    Returns: { ok, panoramas: [{pano_id, date, lat, lng, source}], maps_url }
    """
    params    = request.get_json(force=True)
    lat       = params.get("lat")
    lng       = params.get("lng")
    pano_id   = params.get("pano_id", "")
    api_key   = params.get("api_key", "")
    max_depth = int(params.get("historical_max_depth",    7))
    max_panos = int(params.get("historical_max_panoramas", 200))

    if not api_key:
        return jsonify({"ok": False, "error": "api_key erforderlich"}), 400
    if not pano_id and (lat is None or lng is None):
        return jsonify({"ok": False, "error": "pano_id oder lat+lng erforderlich"}), 400

    # Google Maps URL bauen
    if pano_id and not pano_id.startswith("pos_"):
        lat_f = float(lat) if lat is not None else 0
        lng_f = float(lng) if lng is not None else 0
        maps_url = (
            f"https://www.google.com/maps/@{lat_f},{lng_f},3a,75y,0h,90t"
            f"/data=!3m6!1e1!3m4!1s{pano_id}!2e0!7i16384!8i8192"
        )
    else:
        maps_url = f"https://www.google.com/maps/@{lat},{lng},3a,75y,0h,90t"

    log.info("Historical Discovery: pano=%s lat=%s lng=%s depth=%d maxpanos=%d",
             pano_id, lat, lng, max_depth, max_panos)

    env = {**os.environ, "GOOGLE_MAPS_API_KEY": api_key}

    try:
        r = subprocess.run(
            [
                "streetview-dl",
                "--historical",
                "--historical-max-depth",     str(max_depth),
                "--historical-max-panoramas", str(max_panos),
                "--json",
                maps_url,
            ],
            capture_output=True, text=True, timeout=180,
            env=env
        )
        log.info("discover rc=%d stdout_len=%d", r.returncode, len(r.stdout))
        log.debug("discover stdout: %s", r.stdout[:500])

        if r.returncode == 0 and r.stdout.strip():
            try:
                data      = json.loads(r.stdout)
                panoramas = data.get("panoramas", data if isinstance(data, list) else [])
                return jsonify({"ok": True, "panoramas": panoramas, "maps_url": maps_url})
            except json.JSONDecodeError:
                # Fallback: Datum-Pattern aus Textausgabe parsen
                dates     = sorted(set(re.findall(r'\d{4}-\d{2}(?:-\d{2})?', r.stdout)), reverse=True)
                panoramas = [{"date": d, "pano_id": "", "lat": lat, "lng": lng, "source": "parsed"} for d in dates]
                if panoramas:
                    return jsonify({"ok": True, "panoramas": panoramas, "maps_url": maps_url,
                                    "note": "Datum aus Textausgabe geparst (kein JSON)"})
                return jsonify({"ok": False,
                                "error": "Keine JSON-Ausgabe und keine Datumsmuster gefunden",
                                "raw":   r.stdout[:300],
                                "maps_url": maps_url})

        err_msg = (r.stderr or r.stdout or "Keine Ausgabe").strip()[:300]
        return jsonify({"ok": False, "error": err_msg, "maps_url": maps_url})

    except subprocess.TimeoutExpired:
        return jsonify({"ok": False,
                        "error": "Timeout (180s) — Tiefe reduzieren oder Max-Panoramen verringern",
                        "maps_url": maps_url})
    except FileNotFoundError:
        return jsonify({"ok": False,
                        "error": "streetview-dl nicht gefunden — bitte 'pip install streetview-dl' ausfuehren",
                        "maps_url": maps_url})
    except Exception as e:
        log.exception("discover Fehler")
        return jsonify({"ok": False, "error": str(e), "maps_url": maps_url})


# ── Download starten ───────────────────────────────────────────────────────

@app.route("/api/start", methods=["POST"])
def api_start():
    params   = request.get_json(force=True)
    pano_ids = params.get("pano_ids", [])

    required = ["api_key"] if pano_ids else ["street", "city", "api_key"]
    missing  = [k for k in required if not params.get(k)]
    if missing:
        return jsonify({"error": f"Fehlende Parameter: {', '.join(missing)}"}), 400

    if not params.get("street"):
        params["street"] = "unbekannt"
    if not params.get("city"):
        params["city"] = ""

    job_id = f"job_{int(time.time()*1000)}"
    with _jobs_lock:
        _jobs[job_id] = {
            "queue":      queue.Queue(),
            "status":     "queued",
            "process":    None,
            "params":     params,
            "returncode": None,
        }

    threading.Thread(target=_run_job, args=(job_id, params), daemon=True).start()
    log.info("Job %s queued: street=%s city=%s pano_count=%d",
             job_id, params.get("street"), params.get("city"), len(pano_ids))
    return jsonify({"job_id": job_id})


# ── SSE Log-Stream ─────────────────────────────────────────────────────────

@app.route("/api/log/<job_id>")
def api_log(job_id):
    """Server-Sent Events: Live-Log eines Jobs."""
    if job_id not in _jobs:
        return jsonify({"error": "Job nicht gefunden"}), 404

    def generate():
        q = _jobs[job_id]["queue"]
        while True:
            try:
                msg = q.get(timeout=30)
                yield f"data: {json.dumps(msg)}\n\n"
                if msg["type"] in ("done", "error"):
                    break
            except queue.Empty:
                yield "data: {\"type\": \"ping\"}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── Job stoppen ────────────────────────────────────────────────────────────

@app.route("/api/stop/<job_id>", methods=["POST"])
def api_stop(job_id):
    if job_id not in _jobs:
        return jsonify({"error": "Job nicht gefunden"}), 404
    proc = _jobs[job_id].get("process")
    if proc and proc.poll() is None:
        proc.terminate()
        _jobs[job_id]["status"] = "stopped"
        log.info("Job %s gestoppt", job_id)
        return jsonify({"ok": True})
    return jsonify({"ok": False, "reason": "Prozess laeuft nicht"})


# ── Jobs auflisten ─────────────────────────────────────────────────────────

@app.route("/api/jobs")
def api_jobs():
    with _jobs_lock:
        result = [
            {
                "job_id":     jid,
                "status":     j["status"],
                "returncode": j["returncode"],
                "street":     j["params"].get("street", ""),
                "city":       j["params"].get("city", ""),
                "quality":    j["params"].get("quality", ""),
                "pano_count": len(j["params"].get("pano_ids", [])),
            }
            for jid, j in _jobs.items()
        ]
    return jsonify(result)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("SVEX_PORT", 5000))
    log.info("StreetView Explorer Server v3.5 auf http://localhost:%d", port)
    log.info("Stoppen mit Ctrl+C")
    app.run(host="127.0.0.1", port=port, debug=False, threaded=True)
