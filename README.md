# streetview-explorer

[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://python.org)
[![Platform](https://img.shields.io/badge/platform-Linux-orange.svg)]()
[![Requires](https://img.shields.io/badge/requires-streetview--dl-teal.svg)](https://github.com/stiles/streetview-dl)

**A modern Linux desktop GUI for [streetview-dl](https://github.com/stiles/streetview-dl)** — discover, explore and batch-download Google Street View panoramas with an interactive OpenStreetMap, street-line crawling, single-point click-download, pano_id deduplication and a built-in quota guard.

---

## Features

| Feature | Detail |
|---|---|
| 🗺 Interactive map | Click any point on OpenStreetMap to instantly queue a single panorama |
| 〰 Draw a route | Draw a polyline on the map → all panoramas along the line discovered automatically |
| 🏘 Street by name | Enter a street name + city → geocode via Nominatim → dense sampling + deduplication |
| 🔑 pano_id deduplication | Every panorama downloaded exactly once regardless of how many query points hit it |
| 🛡 Quota guard | Conservative local tile counter stops the run before your monthly limit |
| 📅 Historical download | Optionally download all historical captures for found panoramas |
| 🎨 All streetview-dl options | Quality, FOV, clip, filters, brightness/contrast/saturation, crop, format, metadata |
| 📋 Full log tab | Real-time log of every query, found pano_id, tile estimate and download result |
| 💾 Session state | Quota counter persists across sessions (JSON file, editable in Quota tab) |

---

## Requirements

- Linux (Ubuntu 20.04+, Debian 11+, Fedora 36+)
- Python 3.9+
- `python3-tk` (Tkinter)
- [streetview-dl](https://github.com/stiles/streetview-dl)
- `requests`
- A **Google Maps API key** with **Map Tiles API** and Billing enabled

---

## Installation

```bash
# 1. System dependencies
sudo apt update && sudo apt install -y python3 python3-pip python3-tk python3-venv git

# 2. Clone
git clone https://github.com/basecore/streetview-explorer.git
cd streetview-explorer

# 3. Virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 4. Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 5. API key
export GOOGLE_MAPS_API_KEY="YOUR_KEY_HERE"
```

---

## Quick start

```bash
source .venv/bin/activate
python3 streetview_explorer.py
```

---

## Tabs overview

| Tab | Purpose |
|---|---|
| **Map** | Interactive OpenStreetMap — click a point or draw a route |
| **Street** | Enter a street name and city to crawl the whole street |
| **Options** | All streetview-dl image options (quality, FOV, filters, crop …) |
| **Quota** | Monthly tile counter, stop threshold, manual override |
| **Log** | Real-time output of every step |

---

## Workflow

### Single panorama (click on map)
1. Open **Map** tab → click anywhere on the map
2. Nearest panorama found via `streetview-dl query`
3. Marker placed, pano_id shown
4. Press **Download selected panorama**

### Route / polyline
1. Open **Map** tab → click **Draw route**
2. Click multiple waypoints on the map
3. Click **Finish route** — blue polyline appears
4. Press **Discover panoramas on route**
5. All unique pano_ids along the route shown as markers
6. Press **Download all found panoramas**

### Whole street by name
1. Open **Street** tab → enter street name + city
2. Choose sampling distance (5 m = maximum, 15 m = faster)
3. Press **Analyse street** → geometry fetched from OpenStreetMap
4. All panoramas discovered and deduplicated
5. Press **Download**

---

## Quota protection

| Quality | Tiles / panorama |
|---|---|
| low | 32 |
| medium | 128 |
| high | 512 |

Default stop: **80 % of 100 000 tiles/month**. Counter saved in `state/quota_usage_YYYY-MM.json`.

---

## All streetview-dl options exposed in GUI

`--quality` · `--fov` · `--clip` · `--filter` · `--brightness` · `--contrast` · `--saturation` · `--crop-bottom` · `--no-crop` · `--format` · `--jpeg-quality` · `--max-width` · `--metadata` · `--metadata-only` · `--historical-download` · `--no-xmp` · `--concurrency` · `--timeout` · `--retries` · `--verbose`

---

## Project structure

```
streetview-explorer/
├── streetview_explorer.py   # Main GUI (Tkinter + embedded Leaflet)
├── map_viewer.html          # Leaflet map loaded inside the app
├── state/                   # Auto-created; quota JSON files
├── downloads/               # Default output directory
├── requirements.txt
└── README.md
```

---

## License

MIT — see [LICENSE](LICENSE).

## Related

- [stiles/streetview-dl](https://github.com/stiles/streetview-dl)
- [OpenStreetMap / Nominatim](https://nominatim.org)
- [Leaflet](https://leafletjs.com)
