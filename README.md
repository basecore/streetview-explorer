# streetview-explorer

[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://python.org)
[![Platform](https://img.shields.io/badge/platform-Linux-orange.svg)]()
[![Requires](https://img.shields.io/badge/requires-streetview--dl-teal.svg)](https://github.com/stiles/streetview-dl)

**Eine moderne Linux-Desktop-GUI fuer [streetview-dl](https://github.com/stiles/streetview-dl)** — Panoramen entdecken, erkunden und batch-downloaden mit interaktiver OpenStreetMap-Karte, Strassen-Crawling, Einzelpunkt-Klick-Download, pano_id-Deduplizierung und eingebautem Quota-Schutz.

> **v2.0**: Das Skript installiert sich vollstaendig selbst — kein manuelles `pip install` noetig.

---

## Schnellstart

```bash
# 1. Einmalig: python3 und python3-tk sicherstellen
sudo apt install python3 python3-pip python3-tk   # Ubuntu/Debian
# sudo dnf install python3 python3-tkinter          # Fedora
# sudo pacman -S python tk                          # Arch

# 2. Repo klonen
git clone https://github.com/basecore/streetview-explorer.git
cd streetview-explorer

# 3. Starten – alle Python-Pakete werden automatisch installiert
python3 streetview_explorer.py
```

Beim ersten Start prueft das Skript alle Abhaengigkeiten und installiert fehlende Pakete automatisch per `pip` (und versucht `python3-tk` per Systempaketmanager).

---

## Features

| Feature | Detail |
|---|---|
| Auto-Install | Alle pip-Pakete + streetview-dl werden beim Start automatisch installiert |
| Abhaengigkeitspruefung | Beim Start: vollstaendige Pruefung mit OK/FEHLT Ausgabe |
| Interaktive Karte | Leaflet/OpenStreetMap — Punkt klicken oder Route zeichnen |
| Route zeichnen | Mehrere Wegpunkte -> Panoramen entlang der Route entdecken |
| Strasse per Name | Nominatim-Geocode + dichtes Sampling + pano_id-Deduplizierung |
| Einzelpunkt | Koordinaten eingeben oder auf Karte klicken |
| pano_id-Dedup | Jedes Panorama genau einmal, egal wie viele Punkte es treffen |
| Quota-Schutz | Konservativer lokaler Tile-Zaehler stoppt vor dem Monatslimit |
| Historische Bilder | Alle historischen Aufnahmen eines Panoramas laden |
| Alle streetview-dl Optionen | Qualitaet, FOV, Clip, Filter, Helligkeit/Kontrast/Saettigung, Crop, Format, Metadaten |
| Debug-Log Tab | Live-Ausgabe jeder Aktion, CMD-Strings, HTTP-Codes, pano_id-Liste |
| Log-Datei | Jede Sitzung in logs/session_DATUM_UHRZEIT.log gespeichert |
| Session-State | Quota-Zaehler ueber Neustarts hinweg (JSON, editierbar) |
| API-Key Test | Key direkt in der GUI testen mit Fehlermeldung |

---

## Systemvoraussetzungen

- Linux (Ubuntu 20.04+, Debian 11+, Fedora 36+, Arch)
- Python 3.9+
- `python3-tk` (Tkinter) — einzige Systemabhaengigkeit
- Google Maps API-Key mit **Map Tiles API** und aktivierter Abrechnung

---

## Installation (Details)

### Schritt 1: python3-tk installieren

```bash
# Ubuntu / Debian
sudo apt install python3-tk

# Fedora
sudo dnf install python3-tkinter

# Arch Linux
sudo pacman -S tk
```

### Schritt 2: Repo klonen & starten

```bash
git clone https://github.com/basecore/streetview-explorer.git
cd streetview-explorer
python3 streetview_explorer.py
```

Das Skript installiert beim ersten Start automatisch:
- `requests`
- `Pillow`
- `streetview-dl`

### Optional: Karte direkt in der App (tkinterweb)

```bash
pip install tkinterweb
```

Ohne tkinterweb: Koordinaten manuell eingeben, Karte im Browser oeffnen.

---

## API-Key einrichten

1. [https://console.cloud.google.com](https://console.cloud.google.com) oeffnen
2. Projekt erstellen oder auswaehlen
3. **APIs & Dienste → Bibliothek → "Map Tiles API"** aktivieren
4. **APIs & Dienste → Anmeldedaten → API-Schluessel** erstellen
5. Abrechnung aktivieren (kostenlos bis 100.000 Tiles/Monat)
6. Key im **API-Key**-Tab der App eintragen → **Key testen**

---

## Tabs uebersicht

| Tab | Zweck |
|---|---|
| **Karte** | OpenStreetMap — Punkt klicken oder Route zeichnen |
| **Strasse** | Strassenname + Stadt eingeben -> Vollstaendige Abdeckung |
| **Optionen** | Alle streetview-dl Bildoptionen (Qualitaet, FOV, Filter, Crop ...) |
| **Quota** | Monatlicher Tile-Zaehler, Stopp-Schwelle, manueller Override |
| **API-Key** | Key eingeben, anzeigen/verstecken, testen, Schritt-fuer-Schritt-Anleitung |
| **Log** | Echtzeit-Ausgabe aller Schritte inkl. CMD-Strings und Fehler |

---

## Workflow

### Einzelner Panorama-Punkt
1. **Karte**-Tab → Koordinaten eingeben (oder tkinterweb: Karte klicken)
2. **Einzelpunkt herunterladen** druecken
3. Naechstes Panorama wird gefunden → direkt downloaden

### Route / Polyline
1. **Karte**-Tab → tkinterweb: Route zeichnen → **Route fertig**
2. **Route-Panoramen entdecken** druecken
3. Alle eindeutigen pano_ids entlang der Route erscheinen in der Tabelle
4. **Alle gefundenen herunterladen**

### Ganze Strasse per Name
1. **Strasse**-Tab → Strassenname + Stadt eingeben
2. Sampling-Abstand waehlen (5 m = vollstaendig, 15 m = schneller)
3. **Strasse analysieren** → Geometrie von OSM, Panoramen entdecken
4. **Download starten**

---

## Quota-Schutz

| Qualitaet | Tiles / Panorama |
|---|---|
| low | 32 |
| medium | 128 |
| high | 512 |

Standard-Stopp: **80 % von 100.000 Tiles/Monat**. Zaehler in `state/quota_usage_YYYY-MM.json`.

---

## Alle streetview-dl Optionen in der GUI

`--quality` · `--fov` · `--clip` · `--filter` · `--brightness` · `--contrast` · `--saturation` · `--crop-bottom` · `--no-crop` · `--format` · `--jpeg-quality` · `--max-width` · `--metadata` · `--metadata-only` · `--historical-download` · `--no-xmp` · `--concurrency` · `--timeout` · `--retries` · `--verbose`

---

## Projektstruktur

```
streetview-explorer/
├── streetview_explorer.py   # Haupt-GUI (selbst-installierend)
├── map_viewer.html          # Leaflet-Karte (in App eingebettet via tkinterweb)
├── state/                   # Auto-erstellt; Quota-JSON-Dateien
├── logs/                    # Auto-erstellt; Session-Log-Dateien
├── downloads/               # Standard-Ausgabeordner
├── requirements.txt
└── README.md
```

---

## Fehlerbehebung

| Problem | Loesung |
|---|---|
| `ModuleNotFoundError: tkinter` | `sudo apt install python3-tk` |
| `streetview-dl: command not found` | Skript neu starten (installiert es automatisch) |
| `keyInvalid` beim API-Test | Key pruefen, Map Tiles API aktivieren |
| `accessNotConfigured` | Billing in Google Cloud aktivieren |
| Karte nicht sichtbar | `pip install tkinterweb` oder Koordinaten manuell eingeben |
| Quota-Stopp zu frueh | Im Quota-Tab: Stop-% erhoehen oder echten Stand eintragen |

---

## Lizenz

MIT — siehe [LICENSE](LICENSE).

## Verwandt

- [stiles/streetview-dl](https://github.com/stiles/streetview-dl)
- [OpenStreetMap / Nominatim](https://nominatim.org)
- [Leaflet](https://leafletjs.com)
- [tkinterweb](https://github.com/Andereoo/TkinterWeb)
