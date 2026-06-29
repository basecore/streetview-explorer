#!/usr/bin/env python3
"""
streetview_headless.py  -  StreetView Explorer v2.0 (Headless / CI Mode)
Kein GUI - laeuft direkt in GitHub Actions oder per CLI.

Usage:
  python streetview_headless.py \
    --street "Berger Strasse" --city "Frankfurt am Main" \
    --quality medium --sampling 10 --radius 8 \
    --output ./panoramas
"""

import argparse
import json
import logging
import math
import os
import subprocess
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s  [%(levelname)-7s]  %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("svex-headless")

# ---------------------------------------------------------------------------
# Geo helpers
# ---------------------------------------------------------------------------
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
    log.debug("Interpolate: %d Punkte / %.0f m", len(out), every_m)
    return out


def geocode_street(street, city):
    import requests
    q = f"{street}, {city}"
    log.info("Geocode: %s", q)
    r = requests.get(
        "https://nominatim.openstreetmap.org/search",
        params={"q": q, "format": "json", "polygon_geojson": 1, "limit": 1},
        headers={"User-Agent": "streetview-explorer/2.0-headless"},
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
        return [((float(bb[0]) + float(bb[1])) / 2,
                 (float(bb[2]) + float(bb[3])) / 2)]
    raise RuntimeError("Keine Geometrie verfuegbar.")


def query_point(lat, lng, radius, max_results):
    cmd = [
        "streetview-dl", "query",
        "--lat", str(lat), "--lng", str(lng),
        "--radius", str(radius),
        "--max-results", str(max_results),
        "--json",
    ]
    log.debug("CMD: %s", " ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        log.warning("query RC=%d  stderr=%s", r.returncode, r.stderr.strip()[:200])
        return []
    try:
        data = json.loads(r.stdout)
        return data.get("panoramas", [])
    except json.JSONDecodeError:
        log.warning("JSON parse err: %s", r.stdout[:200])
        return []


def build_download_cmd(url_file, outdir, quality, historical):
    cmd = [
        "streetview-dl",
        "--batch",      str(url_file),
        "--output-dir", str(outdir),
        "--quality",    quality,
        "--verbose",
    ]
    if historical:
        cmd.append("--historical-download")
    log.debug("Download CMD: %s", " ".join(cmd))
    return cmd


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="StreetView Explorer Headless")
    parser.add_argument("--street",    required=True)
    parser.add_argument("--city",      required=True)
    parser.add_argument("--quality",   default="medium", choices=["low", "medium", "high"])
    parser.add_argument("--sampling",  type=int,   default=10)
    parser.add_argument("--radius",    type=int,   default=8)
    parser.add_argument("--max-results", type=int, default=5)
    parser.add_argument("--pause",     type=float, default=0.3)
    parser.add_argument("--historical", default="false")
    parser.add_argument("--output",    default="./panoramas")
    args = parser.parse_args()

    historical = args.historical.lower() == "true"
    outdir = Path(args.output)
    outdir.mkdir(parents=True, exist_ok=True)

    api_key = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    if not api_key:
        log.error("GOOGLE_MAPS_API_KEY ist nicht gesetzt!")
        sys.exit(1)
    log.info("API Key: gesetzt (len=%d)", len(api_key))

    log.info("=" * 60)
    log.info("  StreetView Explorer Headless v2.0")
    log.info("  Strasse  : %s, %s", args.street, args.city)
    log.info("  Qualitaet: %s", args.quality)
    log.info("  Sampling : %d m  Radius: %d m", args.sampling, args.radius)
    log.info("  Historisch: %s", historical)
    log.info("  Output   : %s", outdir)
    log.info("=" * 60)

    # 1. Geocode
    try:
        coords = geocode_street(args.street, args.city)
    except Exception as e:
        log.error("Geocode fehlgeschlagen: %s", e)
        sys.exit(1)

    # 2. Interpolate
    points = interpolate(coords, args.sampling)
    total  = len(points)
    log.info("Sample-Punkte: %d", total)

    # 3. Query panoramas
    pano_ids = set()
    panos    = []
    dup_streak = 0

    for idx, (lat, lng) in enumerate(points, 1):
        log.info("[%d/%d] Query lat=%.6f lng=%.6f", idx, total, lat, lng)
        results = query_point(lat, lng, args.radius, args.max_results)
        new = 0
        for p in results:
            pid = p.get("pano_id")
            if pid and pid not in pano_ids:
                pano_ids.add(pid)
                panos.append({
                    "pano_id": pid,
                    "lat": p.get("lat", lat),
                    "lng": p.get("lng", lng),
                    "date": p.get("date", "?"),
                })
                new += 1
                log.info("  [NEU] pano_id=%s  date=%s", pid, p.get("date", "?"))
        dup_streak = (dup_streak + 1) if new == 0 else 0
        log.debug("  neu=%d  gesamt=%d  dup_streak=%d", new, len(pano_ids), dup_streak)
        if dup_streak >= 8:
            log.info("  8x keine neuen pano_ids - Abschnitt vollstaendig.")
            dup_streak = 0
        time.sleep(args.pause)

    log.info("=" * 60)
    log.info("Gefundene Panoramen: %d", len(panos))

    if not panos:
        log.warning("Keine Panoramen gefunden. Pruefe API-Key und Strassenname.")
        sys.exit(0)

    # 4. Write URL file
    import re
    safe = re.sub(r"[^\w]", "_", f"{args.street}_{args.city}").lower()
    url_file = outdir / f"streetview_urls_{safe}.txt"
    with url_file.open("w") as fh:
        for p in panos:
            fh.write(
                f"https://www.google.com/maps/@{p['lat']},{p['lng']},"
                f"3a,75y,0h,90t/data=!3m7!1e1!3m5!1s{p['pano_id']}!\n"
            )
    log.info("URL-Datei geschrieben: %s (%d Eintraege)", url_file, len(panos))

    # 5. Write metadata JSON
    meta_file = outdir / f"metadata_{safe}.json"
    meta_file.write_text(json.dumps({
        "street": args.street,
        "city": args.city,
        "quality": args.quality,
        "sampling_m": args.sampling,
        "radius_m": args.radius,
        "historical": historical,
        "panoramas_found": len(panos),
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "panoramas": panos,
    }, indent=2, ensure_ascii=False))
    log.info("Metadaten geschrieben: %s", meta_file)

    # 6. Download
    TILES = {"low": 32, "medium": 128, "high": 512}
    est_tiles = len(panos) * TILES.get(args.quality, 128)
    if historical:
        est_tiles = int(est_tiles * 2.5)
    log.info("Starte Download: ~%d Tiles geschaetzt", est_tiles)

    cmd = build_download_cmd(url_file, outdir, args.quality, historical)
    log.info("CMD: %s", " ".join(cmd))

    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True)
    for line in proc.stdout:
        line = line.rstrip()
        if line:
            log.info("sv-dl: %s", line)
    proc.wait()

    if proc.returncode != 0:
        log.error("streetview-dl exit code %d", proc.returncode)
        sys.exit(proc.returncode)

    downloaded = list(outdir.glob("**/*.jpg")) + list(outdir.glob("**/*.png"))
    log.info("=" * 60)
    log.info("FERTIG: %d Bilder heruntergeladen -> %s", len(downloaded), outdir)
    log.info("=" * 60)


if __name__ == "__main__":
    main()
