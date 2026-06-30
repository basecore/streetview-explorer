#!/usr/bin/env python3
"""
streetview_server.py  -  Lokaler Mini-Server fuer die HTML5 Web-App
Laeuft auf http://localhost:5000
Streamt den Log per SSE (Server-Sent Events) live in den Browser.

Start:
  python3 streetview_server.py
"""

import json
import logging
import os
import queue
import subprocess
import sys
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

BASE = Path(__file__).parent
HEADLESS = BASE / "streetview_headless.py"

_jobs: dict = {}
_jobs_lock = threading.Lock()


def _run_job(job_id: str, params: dict):
    """Run streetview_headless.py in a thread, feed output into a queue."""
    q = _jobs[job_id]["queue"]

    street = params.get("street", "").strip()
    city   = params.get("city",   "").strip()
    pano_ids = params.get("pano_ids", [])

    # Koordinaten-Modus: street kann "lat,lng" sein
    import re
    coord_mode = bool(re.match(r'^-?\d+\.?\d*,\s*-?\d+\.?\d*$', street))

    # Sicherheitspruefung nur wenn kein Koordinaten-Modus und keine pano_ids
    INVALID = {"", "karte", "map", "unknown", "unbekannt"}
    if not pano_ids and not coord_mode and street.lower() in INVALID:
        q.put({"type": "error", "data": (
            f"Ungültiger Strassenname: \"{street}\"\n"
            f"Bitte im Suchfeld einen echten Strassennamen eingeben\n"
            f"(z.B. 'Berger Strasse') und dann 'Suchen' drücken."
        )})
        _jobs[job_id]["status"] = "error"
        _jobs[job_id]["returncode"] = 1
        q.put({"type": "done", "data": "Abgebrochen (ungültiger Strassenname)", "rc": 1})
        return

    cmd = [
        sys.executable, str(HEADLESS),
        "--street",     street,
        "--city",       city,
        "--quality",    params.get("quality",    "medium"),
        "--sampling",   str(params.get("sampling",  10)),
        "--radius",     str(params.get("radius",    8)),
        "--historical", str(params.get("historical","false")),
        "--output",     params.get("output", str(BASE / "downloads")),
        # FOV & Framing
        "--heading",    str(params.get("heading",   0)),
        "--pitch",      str(params.get("pitch",     0)),
        "--fov",        str(params.get("fov",       90)),
        "--zoom",       str(params.get("zoom",      2)),
        # Output
        "--output-format", params.get("output_format", "jpg"),
        "--jpg-quality",   str(params.get("jpg_quality", 85)),
    ]

    # Optionale Parameter nur hinzufuegen wenn nicht leer
    for flag, key in [
        ("--date-from",       "date_from"),
        ("--date-to",         "date_to"),
        ("--source",          "source"),
        ("--outdoor",         "outdoor"),
    ]:
        val = str(params.get(key, "")).strip()
        if val:
            cmd += [flag, val]

    max_age = params.get("max_age_months", "")
    if max_age and str(max_age).strip():
        cmd += ["--max-age-months", str(max_age)]

    # pano_ids als JSON-Datei uebergeben (kein erneutes Geocoding noetig)
    if pano_ids:
        import tempfile
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(pano_ids, tmp)
        tmp.close()
        cmd += ["--pano-ids-file", tmp.name]

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
        _jobs[job_id]["status"] = "success" if rc == 0 else "error"
        _jobs[job_id]["returncode"] = rc
        q.put({"type": "done", "data": f"Prozess beendet (exit={rc})", "rc": rc})
        log.info("Job %s done rc=%d", job_id, rc)
    except Exception as e:
        _jobs[job_id]["status"] = "error"
        q.put({"type": "error", "data": str(e)})
        log.exception("Job %s exception", job_id)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/api/status")
def api_status():
    return jsonify({"status": "ok", "version": "3.5"})


@app.route("/api/query", methods=["POST"])
def api_query():
    """Einzelpunkt-Abfrage: lat, lng, radius, api_key -> panoramas[]"""
    params = request.get_json(force=True)
    lat = params.get("lat")
    lng = params.get("lng")
    radius = params.get("radius", 8)
    api_key = params.get("api_key", "")
    if lat is None or lng is None:
        return jsonify({"error": "lat und lng erforderlich"}), 400
    # Stub: In Produktion hier streetview-dl query aufrufen
    # Gibt Browser-Fallback-Pano zurueck wenn kein streetview-dl verfuegbar
    try:
        import subprocess as sp
        r = sp.run(
            ["streetview-dl", "query",
             "--lat", str(lat), "--lng", str(lng),
             "--radius", str(radius),
             "--max-results", "5",
             "--json"],
            capture_output=True, text=True, timeout=15,
            env={**os.environ, "GOOGLE_MAPS_API_KEY": api_key}
        )
        if r.returncode == 0:
            data = json.loads(r.stdout)
            return jsonify(data)
    except Exception as e:
        log.warning("streetview-dl query fehlgeschlagen: %s", e)
    fid = f"pos_{str(lat).replace('.','_')}_{str(lng).replace('.','_')}"
    return jsonify({"panoramas": [{"pano_id": fid, "lat": lat, "lng": lng, "date": "?"}]})


@app.route("/api/start", methods=["POST"])
def api_start():
    params = request.get_json(force=True)

    # city darf leer sein wenn pano_ids direkt uebergeben werden
    pano_ids = params.get("pano_ids", [])
    if pano_ids:
        required = ["api_key"]
    else:
        required = ["street", "city", "api_key"]

    missing = [k for k in required if not params.get(k)]
    if missing:
        return jsonify({"error": f"Fehlende Parameter: {', '.join(missing)}"}), 400

    # Pflichtfeld street trotzdem setzen wenn nicht vorhanden
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

    t = threading.Thread(target=_run_job, args=(job_id, params), daemon=True)
    t.start()
    log.info("Job %s queued: %s, %s", job_id, params.get("street"), params.get("city"))
    return jsonify({"job_id": job_id})


@app.route("/api/log/<job_id>")
def api_log(job_id):
    """SSE stream: text/event-stream"""
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
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


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
    log.info("StreetView Explorer Server v2.1 auf http://localhost:%d", port)
    log.info("Stoppen mit Ctrl+C")
    app.run(host="127.0.0.1", port=port, debug=False, threaded=True)
