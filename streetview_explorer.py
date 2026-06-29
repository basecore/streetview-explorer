#!/usr/bin/env python3
"""
streetview_explorer.py  -  StreetView Explorer v2.0
Selbst-installierend (pip + apt/dnf/pacman fuer python3-tk).
Linux-tauglich. Erfordert nur Python 3.9+.

Features:
  * Interaktive Karte (Leaflet/OpenStreetMap) - Punkt-Klick & Route zeichnen
  * Ganze Strasse per Name (Nominatim + dichtes Sampling + pano_id-Dedup)
  * Quota-Schutz (lokaler Zaehler, konfigurierbares Stop-Limit)
  * API-Key Tab mit Live-Test
  * Alle streetview-dl Optionen in der GUI
  * Vollstaendiges Debug-Logging (GUI + Datei)
  * Automatische Installation aller Abhaengigkeiten inkl. python3-tk
"""

# ==============================================================================
# SELF-INSTALL - laeuft vor allen anderen Imports
# ==============================================================================
import sys
import subprocess
import importlib
import shutil
import os


def _run(cmd: list, **kw):
    return subprocess.run(cmd, **kw)


def _pip(*pkgs):
    _run([sys.executable, "-m", "pip", "install", "--quiet", "--upgrade", *pkgs],
         check=True)


def _check_tkinter():
    """Prueft ob Tkinter verfuegbar ist; versucht es per Systempaketmanager zu installieren."""
    try:
        import tkinter  # noqa: F401
        return True
    except ModuleNotFoundError:
        pass

    print("[INSTALL] python3-tk (Tkinter) fehlt - versuche Systeminstallation ...")

    # apt (Ubuntu/Debian)
    if shutil.which("apt-get"):
        try:
            _run(["sudo", "apt-get", "install", "-y", "python3-tk"], check=True)
            print("[INSTALL] python3-tk via apt installiert.")
            return True
        except Exception as e:
            print(f"[INSTALL] apt fehlgeschlagen: {e}")

    # dnf (Fedora/RHEL)
    if shutil.which("dnf"):
        try:
            _run(["sudo", "dnf", "install", "-y", "python3-tkinter"], check=True)
            print("[INSTALL] python3-tkinter via dnf installiert.")
            return True
        except Exception as e:
            print(f"[INSTALL] dnf fehlgeschlagen: {e}")

    # pacman (Arch)
    if shutil.which("pacman"):
        try:
            _run(["sudo", "pacman", "-S", "--noconfirm", "tk"], check=True)
            print("[INSTALL] tk via pacman installiert.")
            return True
        except Exception as e:
            print(f"[INSTALL] pacman fehlgeschlagen: {e}")

    print(
        "\n[FEHLER] Tkinter konnte nicht automatisch installiert werden.\n"
        "Bitte manuell installieren:\n"
        "  Ubuntu/Debian:  sudo apt install python3-tk\n"
        "  Fedora:         sudo dnf install python3-tkinter\n"
        "  Arch:           sudo pacman -S tk\n"
    )
    return False


def _check_pip_packages():
    needed = {"requests": "requests", "PIL": "Pillow"}
    missing = []
    for imp, pkg in needed.items():
        try:
            importlib.import_module(imp)
        except ModuleNotFoundError:
            missing.append(pkg)
    if missing:
        print(f"[INSTALL] Installiere: {missing}")
        _pip(*missing)
        print("[INSTALL] pip-Pakete fertig.")


def _check_streetview_dl():
    try:
        r = _run(["streetview-dl", "--version"], capture_output=True, text=True)
        if r.returncode == 0:
            print(f"[INSTALL] streetview-dl vorhanden: {r.stdout.strip()}")
            return
    except FileNotFoundError:
        pass
    print("[INSTALL] Installiere streetview-dl ...")
    _pip("streetview-dl")
    print("[INSTALL] streetview-dl installiert.")


def _verify_all():
    """Vollstaendige Abhaengigkeitspruefung mit Ausgabe."""
    print("=" * 60)
    print("  StreetView Explorer - Abhaengigkeitspruefung")
    print("=" * 60)

    ok_tk = _check_tkinter()
    _check_pip_packages()
    _check_streetview_dl()

    results = {}
    for mod in ("tkinter", "requests", "PIL"):
        try:
            importlib.import_module(mod)
            results[mod] = "OK"
        except ModuleNotFoundError:
            results[mod] = "FEHLT"

    sv_ok = bool(shutil.which("streetview-dl"))
    results["streetview-dl"] = "OK" if sv_ok else "FEHLT"

    print("\n-- Pruefungsergebnis ------------------------------------------")
    for k, v in results.items():
        icon = "[OK]" if v == "OK" else "[!!]"
        print(f"  {icon}  {k}: {v}")
    print("--------------------------------------------------------------\n")

    if not ok_tk:
        sys.exit(1)


_verify_all()

# ==============================================================================
# IMPORTS (nach Self-Install)
# ==============================================================================
import json
import logging
import math
import queue
import re
import threading
import time
import traceback
from datetime import datetime
from pathlib import Path
from tkinter import (
    Tk, StringVar, IntVar, DoubleVar, BooleanVar,
    END, filedialog, messagebox, scrolledtext
)
from tkinter import ttk

import requests

# ==============================================================================
# LOGGING
# ==============================================================================
APP_DIR   = Path(__file__).resolve().parent
LOG_DIR   = APP_DIR / "logs"
STATE_DIR = APP_DIR / "state"
LOG_DIR.mkdir(exist_ok=True)
STATE_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / f"session_{datetime.now():%Y%m%d_%H%M%S}.log"
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s  [%(levelname)-7s]  %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("svex")
log.info("Session gestartet. Log: %s", LOG_FILE)

# ==============================================================================
# KONSTANTEN
# ==============================================================================
MONTH_KEY  = datetime.now().strftime("%Y-%m")
STATE_FILE = STATE_DIR / f"quota_usage_{MONTH_KEY}.json"

TILES = {"low": 32, "medium": 128, "high": 512}
QUERY_COST = 2

P = {
    "bg":       "#1c1b1a",
    "surface":  "#242321",
    "surface2": "#2b2a28",
    "border":   "#3a3835",
    "text":     "#e4e2de",
    "muted":    "#8f8d87",
    "primary":  "#4f98a3",
    "success":  "#6daa45",
    "warn":     "#c97b36",
    "error":    "#d15a5a",
    "ebg":      "#1e1d1b",
}

# ==============================================================================
# QUOTA TRACKER
# ==============================================================================
class QuotaTracker:
    def __init__(self):
        self.limit        = 100_000
        self.stop_percent = 80
        self.used         = 0
        self._lock        = threading.Lock()
        self._load()

    @property
    def stop_limit(self):  return int(self.limit * self.stop_percent / 100)
    @property
    def remaining(self):   return max(0, self.stop_limit - self.used)
    @property
    def pct(self):         return round(self.used / max(1, self.limit) * 100, 1)

    def can(self, n):
        with self._lock:
            return self.used + n <= self.stop_limit

    def add(self, n):
        with self._lock:
            self.used += n
        self._save()
        log.debug("Quota +%d -> %d/%d", n, self.used, self.stop_limit)

    def reset(self):
        with self._lock:
            self.used = 0
        self._save()
        log.info("Quota zurueckgesetzt.")

    def _load(self):
        if STATE_FILE.exists():
            try:
                d = json.loads(STATE_FILE.read_text())
                if d.get("month") == MONTH_KEY:
                    self.used         = int(d.get("used", 0))
                    self.limit        = int(d.get("limit", self.limit))
                    self.stop_percent = int(d.get("stop_percent", self.stop_percent))
                    log.info("Quota geladen: %d/%d (stop %d%%)", self.used, self.limit, self.stop_percent)
            except Exception as e:
                log.warning("Quota load: %s", e)

    def _save(self):
        try:
            STATE_FILE.write_text(json.dumps({
                "month": MONTH_KEY, "used": self.used,
                "limit": self.limit, "stop_percent": self.stop_percent,
                "updated": datetime.now().isoformat(timespec="seconds"),
            }, indent=2))
        except Exception as e:
            log.error("Quota save: %s", e)


# ==============================================================================
# GEO HELPERS
# ==============================================================================
def haversine(la1, lo1, la2, lo2):
    R = 6_371_000
    p1, p2 = math.radians(la1), math.radians(la2)
    a = (math.sin((p2 - p1) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lo2 - lo1) / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def interpolate(coords, every_m):
    if len(coords) < 2:
        return coords
    out, carry = [coords[0]], 0.0
    for i in range(1, len(coords)):
        la1, lo1 = coords[i - 1]
        la2, lo2 = coords[i]
        seg = haversine(la1, lo1, la2, lo2)
        if seg == 0:
            continue
        d = carry
        while d + every_m <= seg:
            d += every_m
            r = d / seg
            out.append((la1 + (la2 - la1) * r, lo1 + (lo2 - lo1) * r))
        carry = seg - d
    if out[-1] != coords[-1]:
        out.append(coords[-1])
    log.debug("Interpolate: %d Punkte / %.0f m Abstand", len(out), every_m)
    return out


def geocode_street(street, city):
    q = f"{street}, {city}"
    log.info("Geocode: %s", q)
    r = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"q": q, "format": "json", "polygon_geojson": 1, "limit": 1},
        headers={"User-Agent": "streetview-explorer/2.0"},
        timeout=20,
    )
    r.raise_for_status()
    data = r.json()
    if not data:
        raise RuntimeError(f"Nicht gefunden: {q}")
    geo = data[0].get("geojson", {})
    t, c = geo.get("type"), geo.get("coordinates", [])
    log.info("Geometrie: %s  Punkte: %d", t, len(c))
    if t == "LineString":
        return [(la, lo) for lo, la in c]
    if t == "MultiLineString":
        pts = []
        for ln in c:
            pts += [(la, lo) for lo, la in ln]
        return pts
    bb = data[0].get("boundingbox")
    if bb:
        return [((float(bb[0]) + float(bb[1])) / 2, (float(bb[2]) + float(bb[3])) / 2)]
    raise RuntimeError("Keine Geometrie verfuegbar.")


def test_api_key(key):
    log.info("API-Key Test (len=%d)", len(key))
    if len(key) < 20:
        return False, "Key zu kurz oder leer."
    url = f"https://tile.googleapis.com/v1/streetview/tiles/0/0/0?session=&key={key}"
    try:
        r = requests.get(url, timeout=12)
        body = r.text[:400]
        log.debug("API Test HTTP %d  body: %s", r.status_code, body[:120])
        if r.status_code == 200:
            return True, "[OK] Key gueltig - Map Tiles API erreichbar."
        if "API_KEY_INVALID" in body or "keyInvalid" in body:
            return False, "[FEHLER] Key ungueltig (keyInvalid)."
        if "accessNotConfigured" in body or "REQUEST_DENIED" in body:
            return False, "[FEHLER] Map Tiles API nicht aktiviert oder Billing fehlt."
        if r.status_code == 401:
            return False, "[FEHLER] HTTP 401 - nicht autorisiert."
        if r.status_code in (400, 403):
            return True, f"[WARN] HTTP {r.status_code} - Key erkannt. Billing pruefen."
        return False, f"[FEHLER] HTTP {r.status_code}"
    except Exception as exc:
        log.exception("API test Fehler")
        return False, f"[FEHLER] Netzwerkfehler: {exc}"


# ==============================================================================
# PANORAMA WORKER
# ==============================================================================
def query_point(lat, lng, radius, max_results):
    """Ruft streetview-dl query auf und gibt Liste von pano-dicts zurueck."""
    cmd = [
        "streetview-dl", "query",
        "--lat", str(lat), "--lng", str(lng),
        "--radius", str(radius),
        "--max-results", str(max_results),
        "--json",
    ]
    log.debug("CMD: %s", " ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True)
    log.debug("RC=%d  stderr=%s", r.returncode, r.stderr.strip()[:120])
    if r.returncode != 0:
        log.warning("query_point RC!=0: %s", r.stderr.strip()[:200])
        return []
    try:
        data = json.loads(r.stdout)
        return data.get("panoramas", [])
    except json.JSONDecodeError:
        log.warning("JSON parse err: %s", r.stdout[:200])
        return []


def build_download_cmd(url_file, outdir, opts):
    """Baut den streetview-dl Batch-Command aus den Optionen."""
    cmd = [
        "streetview-dl",
        "--batch",      str(url_file),
        "--output-dir", str(outdir),
        "--quality",    opts.get("quality", "medium"),
        "--verbose",
    ]
    for flag, key in [
        ("--fov",          "fov"),
        ("--clip",         "clip"),
        ("--filter",       "filter"),
        ("--brightness",   "brightness"),
        ("--contrast",     "contrast"),
        ("--saturation",   "saturation"),
        ("--jpeg-quality", "jpeg_quality"),
        ("--max-width",    "max_width"),
        ("--concurrency",  "concurrency"),
        ("--timeout",      "timeout"),
        ("--retries",      "retries"),
    ]:
        v = opts.get(key, "")
        if v and str(v).strip():
            cmd += [flag, str(v)]
    for flag, key in [
        ("--no-crop",             "no_crop"),
        ("--metadata",            "metadata"),
        ("--metadata-only",       "metadata_only"),
        ("--no-xmp",              "no_xmp"),
        ("--historical-download", "historical"),
    ]:
        if opts.get(key):
            cmd.append(flag)
    log.debug("Download CMD: %s", " ".join(cmd))
    return cmd


# ==============================================================================
# HAUPT-GUI
# ==============================================================================
class App:
    MAP_HTML = Path(__file__).resolve().parent / "map_viewer.html"

    def __init__(self, root: Tk):
        self.root     = root
        self.root.title("StreetView Explorer v2.0")
        self.root.geometry("1440x920")
        self.root.minsize(1100, 700)
        self.q         = queue.Queue()
        self.stop_flag = threading.Event()
        self.quota     = QuotaTracker()
        self.pano_ids  = set()
        self.panos     = []
        self.url_file  = None
        self._last_map_point = None
        self._last_map_route = None
        self._init_vars()
        self._theme()
        self._build()
        self._quota_refresh()
        self.root.after(100, self._poll)
        log.info("GUI bereit.")

    # -- VARS ------------------------------------------------------------------
    def _init_vars(self):
        self.v_street  = StringVar(value="Berger Strasse")
        self.v_city    = StringVar(value="Frankfurt am Main")
        self.v_output  = StringVar(value=str(APP_DIR / "downloads"))
        self.v_api_key = StringVar(value=os.environ.get("GOOGLE_MAPS_API_KEY", ""))
        self.v_sample  = IntVar(value=5)
        self.v_radius  = IntVar(value=8)
        self.v_max_res = IntVar(value=5)
        self.v_pause   = DoubleVar(value=0.2)
        self.v_status  = StringVar(value="Bereit")
        # Optionen
        self.v_quality  = StringVar(value="medium")
        self.v_fov      = StringVar(value="")
        self.v_clip     = StringVar(value="")
        self.v_filter   = StringVar(value="")
        self.v_bright   = StringVar(value="")
        self.v_contrast = StringVar(value="")
        self.v_saturat  = StringVar(value="")
        self.v_jpegq    = StringVar(value="")
        self.v_maxw     = StringVar(value="")
        self.v_concur   = StringVar(value="")
        self.v_timeout  = StringVar(value="")
        self.v_retries  = StringVar(value="")
        self.v_nocrop   = BooleanVar(value=False)
        self.v_metadata = BooleanVar(value=False)
        self.v_metaonly = BooleanVar(value=False)
        self.v_noxmp    = BooleanVar(value=False)
        self.v_hist     = BooleanVar(value=False)
        # Quota
        self.v_limit   = IntVar(value=self.quota.limit)
        self.v_stoppct = IntVar(value=self.quota.stop_percent)
        self.v_used    = IntVar(value=self.quota.used)
        # Map fallback
        self.v_map_lat = StringVar(value="50.1109")
        self.v_map_lng = StringVar(value="8.6821")

    # -- THEME -----------------------------------------------------------------
    def _theme(self):
        self.root.configure(bg=P["bg"])
        s = ttk.Style()
        try:    s.theme_use("clam")
        except Exception: pass
        s.configure(".",              background=P["bg"], foreground=P["text"], font=("Segoe UI", 10))
        s.configure("TFrame",         background=P["bg"])
        s.configure("TLabel",         background=P["bg"], foreground=P["text"])
        s.configure("TLabelframe",    background=P["bg"], foreground=P["primary"], relief="flat")
        s.configure("TLabelframe.Label", background=P["bg"], foreground=P["primary"], font=("Segoe UI", 10, "bold"))
        s.configure("TNotebook",      background=P["surface"], borderwidth=0)
        s.configure("TNotebook.Tab",  background=P["surface2"], foreground=P["muted"],
                    padding=(15, 9), font=("Segoe UI", 10))
        s.map("TNotebook.Tab",
              background=[("selected", P["primary"])],
              foreground=[("selected", "#fff")])
        s.configure("TEntry",    fieldbackground=P["ebg"], foreground=P["text"],
                    insertcolor=P["text"], borderwidth=1, relief="flat")
        s.configure("TCombobox", fieldbackground=P["ebg"], foreground=P["text"],
                    selectbackground=P["primary"], borderwidth=1, relief="flat")
        s.map("TCombobox",       fieldbackground=[("readonly", P["ebg"])])
        s.configure("TSpinbox",  fieldbackground=P["ebg"], foreground=P["text"],
                    arrowcolor=P["primary"], borderwidth=1, relief="flat")
        s.configure("TCheckbutton", background=P["bg"], foreground=P["text"])
        s.configure("TButton",   background=P["surface2"], foreground=P["text"],
                    padding=(11, 7), relief="flat", borderwidth=0)
        s.map("TButton",         background=[("active", P["border"])])
        for name, bg, hover in [
            ("Primary", P["primary"],  "#3a7f8a"),
            ("Success", P["success"],  "#598c36"),
            ("Danger",  P["error"],    "#b04040"),
            ("Warn",    P["warn"],     "#a05a20"),
        ]:
            s.configure(f"{name}.TButton", background=bg, foreground="#fff")
            s.map(f"{name}.TButton",        background=[("active", hover)])
        s.configure("TProgressbar", troughcolor=P["surface2"], background=P["primary"],
                    borderwidth=0, thickness=9)
        for name, fg, fnt in [
            ("Muted",  P["muted"],   ("Segoe UI", 9)),
            ("OK",     P["success"], ("Segoe UI", 10)),
            ("Warn",   P["warn"],    ("Segoe UI", 10)),
            ("Err",    P["error"],   ("Segoe UI", 10)),
            ("Head",   P["text"],    ("Segoe UI", 17, "bold")),
            ("Status", P["primary"], ("Segoe UI", 10, "bold")),
            ("Sub",    P["muted"],   ("Segoe UI", 10)),
        ]:
            s.configure(f"{name}.TLabel", background=P["bg"], foreground=fg, font=fnt)

    # -- BUILD -----------------------------------------------------------------
    def _build(self):
        outer = ttk.Frame(self.root, padding=16)
        outer.pack(fill="both", expand=True)

        h = ttk.Frame(outer)
        h.pack(fill="x", pady=(0, 12))
        ttk.Label(h, text="StreetView Explorer", style="Head.TLabel").pack(anchor="w")
        ttk.Label(h,
                  text="Karte  *  Strasse/Route/Punkt  *  pano_id-Dedup  *  Quota-Schutz  *  Debug-Log",
                  style="Sub.TLabel").pack(anchor="w", pady=(2, 0))

        qb = ttk.Frame(outer)
        qb.pack(fill="x", pady=(0, 10))
        self.l_used   = ttk.Label(qb, text="Verbraucht: 0", style="Muted.TLabel")
        self.l_stop   = ttk.Label(qb, text="Stop bei: 0",   style="Muted.TLabel")
        self.l_rem    = ttk.Label(qb, text="Verfuegbar: 0", style="Muted.TLabel")
        self.l_status = ttk.Label(qb, textvariable=self.v_status, style="Status.TLabel")
        for w in (self.l_used, self.l_stop, self.l_rem, self.l_status):
            w.pack(side="left", padx=(0, 20))
        self.progress = ttk.Progressbar(qb, length=200, mode="determinate")
        self.progress.pack(side="left", padx=(0, 6))
        self.l_pct = ttk.Label(qb, text="0 %", style="Muted.TLabel")
        self.l_pct.pack(side="left")

        nb = ttk.Notebook(outer)
        nb.pack(fill="both", expand=True)
        self._tab_map(nb)
        self._tab_street(nb)
        self._tab_options(nb)
        self._tab_quota(nb)
        self._tab_api(nb)
        self._tab_log(nb)

    # -- TAB: Karte ------------------------------------------------------------
    def _tab_map(self, nb):
        frm = ttk.Frame(nb, padding=0)
        nb.add(frm, text="  Karte  ")
        frm.rowconfigure(1, weight=1)
        frm.columnconfigure(0, weight=1)

        toolbar = ttk.Frame(frm, padding=(10, 8))
        toolbar.grid(row=0, column=0, sticky="ew")
        ttk.Button(toolbar, text="Einzelpunkt herunterladen",
                   style="Primary.TButton", command=self._map_download_point).pack(side="left", padx=(0, 8))
        ttk.Button(toolbar, text="Route-Panoramen entdecken",
                   style="Success.TButton", command=self._map_discover_route).pack(side="left", padx=(0, 8))
        ttk.Button(toolbar, text="Alle gefundenen herunterladen",
                   command=self._start_download).pack(side="left", padx=(0, 8))
        ttk.Button(toolbar, text="Stopp",
                   style="Danger.TButton", command=self._stop).pack(side="left", padx=(0, 16))
        self.l_map_info = ttk.Label(toolbar, text="Klicke auf die Karte.", style="Muted.TLabel")
        self.l_map_info.pack(side="left")

        map_frame = ttk.Frame(frm)
        map_frame.grid(row=1, column=0, sticky="nsew")
        map_frame.rowconfigure(0, weight=1)
        map_frame.columnconfigure(0, weight=1)

        if self.MAP_HTML.exists():
            try:
                import tkinterweb  # noqa
                self._embed_map_tkinterweb(map_frame)
                return
            except ImportError:
                pass
            self._embed_map_fallback(map_frame)
        else:
            ttk.Label(map_frame,
                      text="map_viewer.html nicht gefunden.\nBitte im selben Ordner ablegen.",
                      style="Muted.TLabel").grid(row=0, column=0)

    def _embed_map_fallback(self, parent):
        info = ttk.Frame(parent, padding=20)
        info.grid(row=0, column=0, sticky="nsew")
        info.columnconfigure(1, weight=1)
        ttk.Label(info,
                  text="Karte (tkinterweb nicht installiert)\nKoordinaten manuell eingeben:",
                  style="Muted.TLabel").grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 14))
        for r, lbl, var in [(1, "Latitude", self.v_map_lat), (2, "Longitude", self.v_map_lng)]:
            ttk.Label(info, text=lbl).grid(row=r, column=0, sticky="w", padx=(0, 10), pady=4)
            ttk.Entry(info, textvariable=var, width=18).grid(row=r, column=1, sticky="w")
        bf = ttk.Frame(info)
        bf.grid(row=3, column=0, columnspan=3, sticky="w", pady=(12, 0))
        ttk.Button(bf, text="OSM im Browser oeffnen",
                   command=lambda: subprocess.Popen(
                       ["xdg-open",
                        f"https://www.openstreetmap.org/?mlat={self.v_map_lat.get()}&mlon={self.v_map_lng.get()}"])
                   ).pack(side="left", padx=(0, 8))
        ttk.Button(bf, text="Punkt abfragen",
                   style="Primary.TButton",
                   command=self._map_query_manual).pack(side="left")
        ttk.Label(info,
                  text="\nTipp: pip install tkinterweb  -> Karte direkt in der App anzeigen.",
                  style="Muted.TLabel").grid(row=4, column=0, columnspan=3, sticky="w")

    def _embed_map_tkinterweb(self, parent):
        import tkinterweb
        self._webview = tkinterweb.HtmlFrame(parent, messages_enabled=False)
        self._webview.grid(row=0, column=0, sticky="nsew")
        self._webview.load_file(str(self.MAP_HTML))
        self.root.after(800, self._map_poll_js)

    def _map_poll_js(self):
        try:
            msg = self._webview.run_javascript("window._svex_msg || ''", _timeout=0.3)
            if msg:
                self._webview.run_javascript("window._svex_msg=''")
                self._handle_map_msg(msg)
        except Exception:
            pass
        self.root.after(600, self._map_poll_js)

    def _handle_map_msg(self, msg):
        try:
            d = json.loads(msg)
            if d.get("type") == "point":
                lat, lng = float(d["lat"]), float(d["lng"])
                self._last_map_point = (lat, lng)
                self.l_map_info.config(text=f"Punkt: {lat:.5f}, {lng:.5f}")
                log.debug("Karte Punkt: %f, %f", lat, lng)
            elif d.get("type") == "route":
                pts = [(p[0], p[1]) for p in d.get("points", [])]
                self._last_map_route = pts
                self.l_map_info.config(text=f"Route: {len(pts)} Wegpunkte")
                log.debug("Karte Route: %d Wegpunkte", len(pts))
        except Exception as e:
            log.warning("Map msg parse: %s", e)

    def _map_download_point(self):
        pt = self._last_map_point
        if pt is None:
            try:
                pt = (float(self.v_map_lat.get()), float(self.v_map_lng.get()))
            except Exception:
                messagebox.showwarning("Hinweis", "Bitte zuerst auf die Karte klicken oder Koordinaten eingeben.")
                return
        self.stop_flag.clear()
        threading.Thread(target=self._single_point_worker, args=(pt,), daemon=True).start()

    def _map_query_manual(self):
        try:
            lat = float(self.v_map_lat.get())
            lng = float(self.v_map_lng.get())
        except ValueError:
            messagebox.showerror("Fehler", "Ungueltige Koordinaten.")
            return
        self.stop_flag.clear()
        threading.Thread(target=self._single_point_worker, args=((lat, lng),), daemon=True).start()

    def _map_discover_route(self):
        pts = self._last_map_route
        if not pts or len(pts) < 2:
            messagebox.showwarning("Hinweis", "Bitte zuerst eine Route auf der Karte zeichnen.")
            return
        self.stop_flag.clear()
        self.pano_ids.clear()
        self.panos.clear()
        threading.Thread(target=self._route_worker, args=(pts,), daemon=True).start()

    def _single_point_worker(self, pt):
        lat, lng = pt
        self.q.put(("status", f"Suche Panorama bei {lat:.5f}, {lng:.5f} ..."))
        self.q.put(("log",    f"[Punkt] lat={lat:.6f}  lng={lng:.6f}"))
        if not self.quota.can(QUERY_COST):
            self.q.put(("log",   "[Quota] Stopp-Limit erreicht."))
            self.q.put(("status", "Quota-Stopp"))
            return
        self.quota.add(QUERY_COST)
        self.q.put(("quota",))
        results = query_point(lat, lng, int(self.v_radius.get()), 3)
        if not results:
            self.q.put(("log",   "  -> Kein Panorama gefunden."))
            self.q.put(("status", "Kein Treffer"))
            return
        for p in results:
            pid = p.get("pano_id")
            if pid and pid not in self.pano_ids:
                self.pano_ids.add(pid)
                e = {"pano_id": pid, "lat": p.get("lat", lat),
                     "lng": p.get("lng", lng), "date": p.get("date", "?")}
                self.panos.append(e)
                self.q.put(("tree_add", e))
                self.q.put(("log", f"  -> pano_id: {pid}"))
        self._write_url_file()
        self.q.put(("status", f"{len(self.pano_ids)} Panorama(s) bereit"))

    def _route_worker(self, pts):
        self.q.put(("status", "Route wird abgetastet ..."))
        sample = int(self.v_sample.get())
        radius = int(self.v_radius.get())
        pause  = float(self.v_pause.get())
        points = interpolate(pts, sample)
        total  = len(points)
        self.q.put(("log", f"[Route] {total} Sample-Punkte alle {sample} m"))
        for idx, (lat, lng) in enumerate(points, 1):
            if self.stop_flag.is_set():
                self.q.put(("status", "Abgebrochen")); break
            if not self.quota.can(QUERY_COST):
                self.q.put(("log", "[Quota] Stopp.")); break
            self.quota.add(QUERY_COST)
            self.q.put(("quota",))
            self.q.put(("status", f"Route Punkt {idx}/{total}"))
            results = query_point(lat, lng, radius, int(self.v_max_res.get()))
            new = 0
            for p in results:
                pid = p.get("pano_id")
                if pid and pid not in self.pano_ids:
                    self.pano_ids.add(pid)
                    e = {"pano_id": pid, "lat": p.get("lat", lat),
                         "lng": p.get("lng", lng), "date": p.get("date", "?")}
                    self.panos.append(e)
                    new += 1
                    self.q.put(("tree_add", e))
            self.q.put(("log", f"[{idx:>4}/{total}]  neu:{new}  gesamt:{len(self.pano_ids)}"))
            time.sleep(pause)
        self._write_url_file()
        self.q.put(("status", f"Route fertig - {len(self.pano_ids)} Panoramen"))
        self.q.put(("done",   f"Route-Entdeckung fertig: {len(self.panos)} Panoramen."))

    # -- TAB: Strasse ----------------------------------------------------------
    def _tab_street(self, nb):
        frm = ttk.Frame(nb, padding=20)
        nb.add(frm, text="  Strasse  ")
        frm.columnconfigure(1, weight=1)
        frm.rowconfigure(7, weight=1)

        self._row(frm, 0, "Strasse",       self.v_street, "z. B.  Berger Strasse")
        self._row(frm, 1, "Ort / Stadt",   self.v_city,   "z. B.  Frankfurt am Main")
        self._row(frm, 2, "Ausgabeordner", self.v_output, "Bilder und URL-Datei")
        ttk.Button(frm, text="Ordner ...", command=self._choose_out).grid(
            row=2, column=2, padx=(8, 0), sticky="w")
        self._spin(frm, 3, "Sampling-Abstand (m)", self.v_sample, 1, 200,
                   "5 m = vollstaendig  |  15 m = schneller")

        acts = ttk.Frame(frm)
        acts.grid(row=5, column=0, columnspan=3, sticky="w", pady=(14, 0))
        ttk.Button(acts, text="Strasse analysieren",
                   style="Primary.TButton", command=self._start_street_scan).pack(side="left", padx=(0, 8))
        ttk.Button(acts, text="Download starten",
                   style="Success.TButton", command=self._start_download).pack(side="left", padx=(0, 8))
        ttk.Button(acts, text="Stopp",
                   style="Danger.TButton", command=self._stop).pack(side="left")

        self.l_summary = ttk.Label(frm, text="Noch kein Lauf.",
                                   style="Muted.TLabel", wraplength=1200)
        self.l_summary.grid(row=6, column=0, columnspan=3, sticky="w", pady=(12, 0))

        tf = ttk.LabelFrame(frm, text="Gefundene Panoramen", padding=8)
        tf.grid(row=7, column=0, columnspan=3, sticky="nsew", pady=(14, 0))
        tf.columnconfigure(0, weight=1)
        tf.rowconfigure(0, weight=1)
        cols = ("pano_id", "lat", "lng", "date")
        self.tree = ttk.Treeview(tf, columns=cols, show="headings", height=12)
        for col, w, h in zip(cols, (300, 110, 110, 100),
                             ("Pano-ID", "Lat", "Lng", "Datum")):
            self.tree.heading(col, text=h)
            self.tree.column(col, width=w, anchor="w")
        sb = ttk.Scrollbar(tf, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        sb.grid(row=0, column=1, sticky="ns")

    # -- TAB: Optionen ---------------------------------------------------------
    def _tab_options(self, nb):
        frm = ttk.Frame(nb, padding=20)
        nb.add(frm, text="  Optionen  ")
        frm.columnconfigure(1, weight=1)

        ttk.Label(frm, text="Bildqualitaet").grid(row=0, column=0, sticky="w", pady=7, padx=(0, 10))
        ttk.Combobox(frm, textvariable=self.v_quality,
                     values=["low", "medium", "high"],
                     state="readonly", width=14).grid(row=0, column=1, sticky="w")
        ttk.Label(frm, text="low=32  medium=128  high=512 Tiles/Pano",
                  style="Muted.TLabel").grid(row=0, column=2, sticky="w", padx=(10, 0))

        for r, lbl, var, hint in [
            (1,  "FOV (Grad)",        self.v_fov,      "leer = Standard"),
            (2,  "Clip",              self.v_clip,     "leer = kein Clip"),
            (3,  "Filter",            self.v_filter,   "z. B. grayscale"),
            (4,  "Helligkeit",        self.v_bright,   "1.0 = Standard"),
            (5,  "Kontrast",          self.v_contrast, "1.0 = Standard"),
            (6,  "Saettigung",        self.v_saturat,  "1.0 = Standard"),
            (7,  "JPEG-Qualitaet",    self.v_jpegq,    "1-95"),
            (8,  "Max. Breite (px)",  self.v_maxw,     "leer = unbegrenzt"),
            (9,  "Parallelitaet",     self.v_concur,   "Standard: 3"),
            (10, "Timeout (s)",       self.v_timeout,  ""),
            (11, "Retries",           self.v_retries,  ""),
        ]:
            self._row(frm, r, lbl, var, hint)

        self._spin(frm, 12, "Suchradius/Punkt (m)",  self.v_radius,  1, 100,  "8 m = wenige Duplikate")
        self._spin(frm, 13, "Max. Treffer/Punkt",    self.v_max_res, 1, 20,   "")
        self._spin(frm, 14, "Pause zw. Queries (s)", self.v_pause,   0.05, 5.0, "", incr=0.05)

        chk = ttk.Frame(frm)
        chk.grid(row=15, column=0, columnspan=3, sticky="w", pady=(14, 0))
        for txt, var in [
            ("Kein Crop (--no-crop)",              self.v_nocrop),
            ("Metadaten speichern (--metadata)",   self.v_metadata),
            ("Nur Metadaten (--metadata-only)",    self.v_metaonly),
            ("Kein XMP (--no-xmp)",                self.v_noxmp),
            ("Historische Bilder (--historical-download)", self.v_hist),
        ]:
            ttk.Checkbutton(chk, text=txt, variable=var).pack(anchor="w", pady=2)

    # -- TAB: Quota ------------------------------------------------------------
    def _tab_quota(self, nb):
        frm = ttk.Frame(nb, padding=20)
        nb.add(frm, text="  Quota  ")
        frm.columnconfigure(1, weight=1)

        self._spin(frm, 0, "Monatliches Limit (Tiles)", self.v_limit,   1000, 1_000_000,
                   "Google: 100.000/Monat kostenlos", incr=1000)
        self._spin(frm, 1, "Stopp bei Prozent (%)",     self.v_stoppct, 1, 100,
                   "Empfohlen: 80 %")
        self._spin(frm, 2, "Bereits verbraucht",        self.v_used,    0, 1_000_000,
                   "Auf echten Cloud-Stand setzen", incr=100)

        bf = ttk.Frame(frm)
        bf.grid(row=3, column=0, columnspan=3, sticky="w", pady=(14, 0))
        ttk.Button(bf, text="Speichern & anwenden",
                   style="Primary.TButton", command=self._save_quota).pack(side="left", padx=(0, 10))
        ttk.Button(bf, text="Auf 0 zuruecksetzen",
                   style="Danger.TButton", command=self._reset_quota).pack(side="left")

        note = ttk.LabelFrame(frm, text="Messgenauigkeit", padding=12)
        note.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(20, 0))
        ttk.Label(note, style="Muted.TLabel", justify="left", wraplength=900, text=(
            "Dieser Zaehler ist eine konservative lokale Schaetzung - keine Live-Abfrage der "
            "Google Cloud Billing API. Queries: ~2 Tiles. Downloads: low=32  medium=128  high=512 Tiles/Pano. "
            "Falls du den echten Stand aus der Cloud Console kennst, trage ihn oben ein."
        )).pack(anchor="w")

    # -- TAB: API-Key ----------------------------------------------------------
    def _tab_api(self, nb):
        frm = ttk.Frame(nb, padding=20)
        nb.add(frm, text="  API-Key  ")
        frm.columnconfigure(1, weight=1)

        ttk.Label(frm, text="Google Maps API-Key").grid(row=0, column=0, sticky="w", pady=8, padx=(0, 10))
        self.entry_key = ttk.Entry(frm, textvariable=self.v_api_key, width=62, show="*")
        self.entry_key.grid(row=0, column=1, sticky="ew")
        ttk.Checkbutton(frm, text="Anzeigen",
                        command=lambda: self.entry_key.config(
                            show="" if self.entry_key.cget("show") == "*" else "*")
                        ).grid(row=0, column=2, padx=(8, 0))

        bf = ttk.Frame(frm)
        bf.grid(row=1, column=0, columnspan=3, sticky="w", pady=(10, 0))
        ttk.Button(bf, text="Speichern (Env-Variable setzen)",
                   style="Primary.TButton", command=self._save_api).pack(side="left", padx=(0, 10))
        ttk.Button(bf, text="Key testen",
                   command=self._test_api).pack(side="left")

        self.l_api = ttk.Label(frm, text="", wraplength=950)
        self.l_api.grid(row=2, column=0, columnspan=3, sticky="w", pady=(12, 0))

        guide = ttk.LabelFrame(frm, text="Schritt-fuer-Schritt: Google API-Key einrichten", padding=14)
        guide.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(20, 0))
        for i, step in enumerate([
            "1.  https://console.cloud.google.com oeffnen.",
            "2.  Projekt erstellen oder auswaehlen.",
            "3.  APIs & Dienste -> Bibliothek -> 'Map Tiles API' suchen -> Aktivieren.",
            "4.  APIs & Dienste -> Anmeldedaten -> '+ Anmeldedaten' -> API-Schluessel.",
            "5.  Abrechnung aktivieren (Kreditkarte; unter 100.000 Tiles/Monat kostenlos).",
            "6.  Optional: Key auf 'Map Tiles API' einschraenken.",
            "7.  Key oben eintragen -> Speichern -> Key testen.",
        ]):
            ttk.Label(guide, text=step, style="Muted.TLabel").grid(row=i, column=0, sticky="w", pady=2)

    # -- TAB: Debug-Log --------------------------------------------------------
    def _tab_log(self, nb):
        frm = ttk.Frame(nb, padding=12)
        nb.add(frm, text="  Log  ")
        frm.rowconfigure(0, weight=1)
        frm.columnconfigure(0, weight=1)
        self.log_w = scrolledtext.ScrolledText(
            frm, wrap="word", bg="#111110", fg="#b0afa9",
            insertbackground="#b0afa9", font=("Monospace", 9), relief="flat")
        self.log_w.grid(row=0, column=0, sticky="nsew")
        bf = ttk.Frame(frm)
        bf.grid(row=1, column=0, sticky="w", pady=(7, 0))
        ttk.Button(bf, text="Log leeren",
                   command=lambda: self.log_w.delete("1.0", END)).pack(side="left", padx=(0, 8))
        ttk.Button(bf, text="Log-Datei oeffnen",
                   command=lambda: subprocess.Popen(["xdg-open", str(LOG_FILE)])).pack(side="left", padx=(0, 8))
        ttk.Label(bf, text=str(LOG_FILE), style="Muted.TLabel").pack(side="left")

    # -- HELPERS ---------------------------------------------------------------
    def _row(self, p, r, lbl, var, hint=""):
        ttk.Label(p, text=lbl).grid(row=r, column=0, sticky="w", pady=5, padx=(0, 10))
        ttk.Entry(p, textvariable=var).grid(row=r, column=1, sticky="ew")
        if hint:
            ttk.Label(p, text=hint, style="Muted.TLabel").grid(row=r, column=2, sticky="w", padx=(10, 0))

    def _spin(self, p, r, lbl, var, lo, hi, hint="", incr=1):
        ttk.Label(p, text=lbl).grid(row=r, column=0, sticky="w", pady=6, padx=(0, 10))
        ttk.Spinbox(p, from_=lo, to=hi, textvariable=var,
                    increment=incr, width=14).grid(row=r, column=1, sticky="w")
        if hint:
            ttk.Label(p, text=hint, style="Muted.TLabel").grid(row=r, column=2, sticky="w", padx=(10, 0))

    def _choose_out(self):
        d = filedialog.askdirectory(initialdir=self.v_output.get())
        if d:
            self.v_output.set(d)

    def _gui_log(self, txt):
        try:
            ts = datetime.now().strftime("%H:%M:%S")
            self.log_w.insert(END, f"{ts}  {txt}\n")
            self.log_w.see(END)
        except Exception:
            pass

    def _quota_refresh(self):
        q = self.quota
        self.l_used.config(text=f"Verbraucht: {q.used:,}")
        self.l_stop.config(text=f"Stop bei: {q.stop_limit:,}")
        self.l_rem.config(text=f"Verfuegbar: {q.remaining:,}")
        pct = q.pct
        self.progress["value"] = min(100, pct)
        stl = "OK.TLabel" if pct < 60 else ("Warn.TLabel" if pct < q.stop_percent else "Err.TLabel")
        self.l_pct.config(text=f"{pct} %", style=stl)

    def _poll(self):
        try:
            while True:
                msg = self.q.get_nowait()
                k = msg[0]
                if k == "log":
                    self._gui_log(msg[1])
                elif k == "status":
                    self.v_status.set(msg[1])
                elif k == "summary":
                    try: self.l_summary.config(text=msg[1])
                    except Exception: pass
                    try: self.l_map_info.config(text=msg[1])
                    except Exception: pass
                elif k == "quota":
                    self._quota_refresh()
                elif k == "tree_add":
                    p = msg[1]
                    self.tree.insert("", "end", values=(
                        p["pano_id"], f"{p['lat']:.6f}",
                        f"{p['lng']:.6f}", p.get("date", "?")))
                elif k == "done":
                    messagebox.showinfo("Fertig", msg[1])
                elif k == "error":
                    messagebox.showerror("Fehler", msg[1])
        except queue.Empty:
            pass
        self.root.after(100, self._poll)

    def _write_url_file(self):
        if not self.panos:
            return
        outdir = Path(self.v_output.get())
        outdir.mkdir(parents=True, exist_ok=True)
        safe = re.sub(r"[^\w]", "_",
                      f"{self.v_street.get()}_{self.v_city.get()}").lower()
        self.url_file = outdir / f"streetview_urls_{safe}.txt"
        with self.url_file.open("w") as fh:
            for p in self.panos:
                fh.write(
                    f"https://www.google.com/maps/@{p['lat']},{p['lng']},"
                    f"3a,75y,0h,90t/data=!3m7!1e1!3m5!1s{p['pano_id']}!\n"
                )
        log.info("URL-Datei: %s (%d Eintraege)", self.url_file, len(self.panos))

    def _stop(self):
        self.stop_flag.set()
        self.v_status.set("Stopp ...")
        self._gui_log("[Stopp] Signal gesendet.")

    # -- QUOTA / API -----------------------------------------------------------
    def _save_quota(self):
        self.quota.limit        = int(self.v_limit.get())
        self.quota.stop_percent = int(self.v_stoppct.get())
        self.quota.used         = int(self.v_used.get())
        self.quota._save()
        self._quota_refresh()
        self._gui_log("[Quota] Gespeichert.")

    def _reset_quota(self):
        if messagebox.askyesno("Reset?", "Monatszaehler auf 0 setzen?"):
            self.quota.reset()
            self.v_used.set(0)
            self._quota_refresh()
            self._gui_log("[Quota] Zurueckgesetzt.")

    def _save_api(self):
        key = self.v_api_key.get().strip()
        os.environ["GOOGLE_MAPS_API_KEY"] = key
        self._gui_log(f"[API] Key gesetzt (Laenge: {len(key)}).")
        messagebox.showinfo("Gespeichert",
                            "Key als Umgebungsvariable gesetzt.\n\n"
                            "Dauerhaft in ~/.bashrc:\n"
                            f'export GOOGLE_MAPS_API_KEY="{key}"')

    def _test_api(self):
        key = self.v_api_key.get().strip()
        os.environ["GOOGLE_MAPS_API_KEY"] = key
        self.l_api.config(text="Teste ...", style="Muted.TLabel")
        self._gui_log(f"[API] Teste Key (len={len(key)}) ...")
        def _run_test():
            ok, msg = test_api_key(key)
            self.l_api.config(text=msg, style="OK.TLabel" if ok else "Err.TLabel")
            self._gui_log(f"[API] {'OK' if ok else 'FEHLER'}: {msg}")
        threading.Thread(target=_run_test, daemon=True).start()

    # -- STREET SCAN -----------------------------------------------------------
    def _start_street_scan(self):
        self.stop_flag.clear()
        self.pano_ids.clear()
        self.panos.clear()
        self.url_file = None
        for i in self.tree.get_children():
            self.tree.delete(i)
        self._gui_log("[Scan] Gestartet.")
        threading.Thread(target=self._street_worker, daemon=True).start()

    def _street_worker(self):
        try:
            street = self.v_street.get().strip()
            city   = self.v_city.get().strip()
            sample = int(self.v_sample.get())
            radius = int(self.v_radius.get())
            maxres = int(self.v_max_res.get())
            pause  = float(self.v_pause.get())

            self.q.put(("status", "Geokodiere Strasse ..."))
            self.q.put(("log",    f"[Scan] {street}, {city}  |  {sample}m  |  r={radius}m"))

            coords = geocode_street(street, city)
            self.q.put(("log", f"[Scan] Geometrie: {len(coords)} Punkte"))

            points = interpolate(coords, sample)
            total  = len(points)
            self.q.put(("log",     f"[Scan] Sample-Punkte: {total}"))
            self.q.put(("summary", f"Suche auf {total} Punkten ..."))

            dup = 0
            for idx, (lat, lng) in enumerate(points, 1):
                if self.stop_flag.is_set():
                    self.q.put(("status", "Abgebrochen")); break
                if not self.quota.can(QUERY_COST):
                    self.q.put(("log", f"[Quota] Stopp: {self.quota.used:,}/{self.quota.stop_limit:,}"))
                    self.q.put(("status", "Quota-Stopp")); break
                self.quota.add(QUERY_COST)
                self.q.put(("quota",))
                self.q.put(("status", f"Punkt {idx}/{total}"))

                results = query_point(lat, lng, radius, maxres)
                new = 0
                for p in results:
                    pid = p.get("pano_id")
                    if pid and pid not in self.pano_ids:
                        self.pano_ids.add(pid)
                        e = {"pano_id": pid, "lat": p.get("lat", lat),
                             "lng": p.get("lng", lng), "date": p.get("date", "?")}
                        self.panos.append(e)
                        new += 1
                        self.q.put(("tree_add", e))

                dup = (dup + 1) if new == 0 else 0
                self.q.put(("log",
                    f"[{idx:>5}/{total}]  neu:{new:2}  gesamt:{len(self.pano_ids):4}  dup-streak:{dup}"))
                if dup >= 6:
                    self.q.put(("log", "  -> 6x keine neuen pano_ids. Abschnitt abgedeckt."))
                    dup = 0
                time.sleep(pause)

            self._write_url_file()
            q_str = self.v_quality.get()
            est = len(self.panos) * TILES.get(q_str, 128)
            summary = (f"Fertig: {len(self.panos)} Panoramen  |  "
                       f"~{est:,} Tiles  |  Datei: {self.url_file.name if self.url_file else '-'}")
            self.q.put(("summary", summary))
            self.q.put(("status",  "Analyse fertig - Download starten!"))
            self.q.put(("done",    summary))

        except Exception:
            tb = traceback.format_exc()
            log.error("Street worker:\n%s", tb)
            self.q.put(("log",   f"[FEHLER]\n{tb}"))
            self.q.put(("error", tb))
            self.q.put(("status", "Fehler"))

    # -- DOWNLOAD --------------------------------------------------------------
    def _start_download(self):
        if not self.url_file or not Path(self.url_file).exists():
            messagebox.showwarning("Hinweis",
                                   "Bitte zuerst Strasse analysieren oder Punkte/Route entdecken.")
            return
        self.stop_flag.clear()
        threading.Thread(target=self._download_worker, daemon=True).start()

    def _download_worker(self):
        try:
            opts = {
                "quality":       self.v_quality.get(),
                "fov":           self.v_fov.get(),
                "clip":          self.v_clip.get(),
                "filter":        self.v_filter.get(),
                "brightness":    self.v_bright.get(),
                "contrast":      self.v_contrast.get(),
                "saturation":    self.v_saturat.get(),
                "jpeg_quality":  self.v_jpegq.get(),
                "max_width":     self.v_maxw.get(),
                "concurrency":   self.v_concur.get(),
                "timeout":       self.v_timeout.get(),
                "retries":       self.v_retries.get(),
                "no_crop":       self.v_nocrop.get(),
                "metadata":      self.v_metadata.get(),
                "metadata_only": self.v_metaonly.get(),
                "no_xmp":        self.v_noxmp.get(),
                "historical":    self.v_hist.get(),
            }
            tiles_each  = TILES.get(opts["quality"], 128)
            tiles_total = len(self.panos) * tiles_each
            if opts["historical"]:
                tiles_total = int(tiles_total * 2.5)

            self.q.put(("log", f"[Download] {len(self.panos)} Panos  |  "
                                f"~{tiles_total:,} Tiles  |  Qualitaet: {opts['quality']}"))

            if not self.quota.can(tiles_total):
                raise RuntimeError(
                    f"Quota wuerde ueberschritten.\n"
                    f"Bedarf: {tiles_total:,}  Verfuegbar: {self.quota.remaining:,}")

            outdir = Path(self.v_output.get())
            outdir.mkdir(parents=True, exist_ok=True)
            cmd = build_download_cmd(self.url_file, outdir, opts)

            self.q.put(("status", "Download laeuft ..."))
            self.q.put(("log",   f"[Download] CMD: {' '.join(cmd)}"))
            log.info("Download CMD: %s", " ".join(cmd))

            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True)
            for line in proc.stdout:
                line = line.rstrip()
                if line:
                    self.q.put(("log", f"  {line}"))
                    log.debug("sv-dl: %s", line)
                if self.stop_flag.is_set():
                    proc.terminate()
                    self.q.put(("status", "Abgebrochen")); return
            proc.wait()
            log.info("sv-dl exit %d", proc.returncode)

            self.quota.add(tiles_total)
            self.q.put(("quota",))
            done = f"Download fertig! {len(self.panos)} Panoramen -> {outdir}"
            self.q.put(("summary", done))
            self.q.put(("status",  "Download fertig"))
            self.q.put(("done",    done))

        except Exception:
            tb = traceback.format_exc()
            log.error("Download worker:\n%s", tb)
            self.q.put(("log",   f"[FEHLER]\n{tb}"))
            self.q.put(("error", tb))
            self.q.put(("status", "Fehler"))


# ==============================================================================
# ENTRY POINT
# ==============================================================================
if __nam