# streetview-explorer

[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://python.org)
[![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-CI%2FCD-2088FF?logo=github-actions&logoColor=white)](.github/workflows/download.yml)
[![GitHub Pages](https://img.shields.io/badge/Web_App-GitHub_Pages-222?logo=github&logoColor=white)](https://basecore.github.io/streetview-explorer/)
[![streetview-dl](https://img.shields.io/badge/powered_by-streetview--dl-007acc)](https://github.com/stiles/streetview-dl)

**Eine moderne Web-App zum Entdecken und Batch-Downloaden von Google Street View Panoramen** —
powered by [streetview-dl](https://github.com/stiles/streetview-dl), interaktiver OpenStreetMap-Karte,
GPS-Ortung, Strassen-Crawling, GitHub Actions Cloud-Modus und eingebautem Quota-Schutz.

> **v3.5** — Zwei Nutzungsmodi: **Cloud-Modus** (GitHub Pages + GitHub Actions, kein lokales Python noetig)
> und **Local-Modus** (lokaler Python-Server fuer echte pano_id-Discovery direkt ueber die Google API).

---

## 🌐 Web-App starten

**[➜ Web-App oeffnen](https://basecore.github.io/streetview-explorer/)**

Die HTML5-App laeuft direkt im Browser — keine Installation, kein Python lokal noetig.

### Schnellstart (Cloud-Modus)

1. Web-App oeffnen
2. Im **Keys-Tab**: Google API-Key + GitHub PAT eingeben → **„Keys speichern"** (AES-256-GCM verschluesselt)
3. Im **Karten-Tab**: Modus auf **„Cloud"** stellen
4. Standort per GPS ermitteln, Punkt per Klick setzen oder Strasse im Suchfeld eingeben
5. **„Panoramen suchen"** druecken → gefundene Panoramen erscheinen in der Tabelle
6. Gewuenschte Panoramen auswaehlen → **„▶ Request"**
7. Im **Jobs-Tab** den Fortschritt live verfolgen
8. Fertige Panoramas als **ZIP-Artifact herunterladen**


```
Browser (Web-App)
    └─► GPS / Klick / Strassensuche (Nominatim)
        └─► POST api.github.com/.../workflows/download.yml/dispatches
            └─► GitHub Actions Runner (ubuntu-latest)
                └─► streetview_headless.py
                    └─► Panoramas als ZIP-Artifact (7 Tage verfuegbar)
```

---

### Schnellstart (Local-Modus)

```bash
# Python-Server starten (einmalig)
python3 streetview_server.py

# Web-App oeffnen → Modus "Local" → echte pano_ids per Google API abfragen
```

---

## ✨ Features

### Karte & Navigation
| Feature | Beschreibung |
|---|---|
| Interaktive OpenStreetMap-Karte | Leaflet, OSM-Tiles, Live-Koordinaten-Anzeige |
| GPS-Ortung | Standort per Browser-Geolocation, Adresse per Nominatim Reverse-Geocode |
| Punkt-Modus | Einzelnen Punkt per Klick auf Karte setzen |
| Linien-Modus | Polyline zeichnen (Doppeltippen zum Abschliessen) |
| Strassen-Suche | Strassenname + Stadt → Geometrie von OpenStreetMap via Nominatim |
| Sampling | Punkte entlang der Linie alle N Meter (einstellbar, Standard 10 m) |
| Karte leeren | Alle Marker, Linien und Panoramen auf einmal zuruecksetzen |

### Panorama-Discovery
| Feature | Beschreibung |
|---|---|
| Echte pano_ids | Mit lokalem Python-Server: tatsaechliche Google StreetView pano_ids |
| Browser-Fallback | Ohne Server: Koordinaten-basierte Positionen (pos_...) |
| Deduplizierung | Jede pano_id erscheint nur einmal, egal wie viele Sample-Punkte sie treffen |
| Ergebnis-Tabelle | Alle Panoramen mit pano_id, Datum, Lat/Lng, Maps-Link und Karte-Pin-Button |
| Status-Badges | `✓ angefragt` (bereits dispatched) und `fallback` (Browser-Fallback) |
| CSV-Export | Alle ausgewaehlten Panoramen als CSV-Datei exportieren |
| Auswahl-Steuerung | Alle auswaehlen, keine auswaehlen, invertieren, Einzel-Toggle |

### Download-Modi
| Feature | Beschreibung |
|---|---|
| **Local-Modus** | `streetview_headless.py` lokal ausfuehren, direkt auf eigene Festplatte |
| **Cloud-Modus** | GitHub Actions Job dispatchen, Panoramas als ZIP-Artifact herunterladen |
| Dispatch-Modi | pano_ids direkt · Koordinaten (lat/lng) · Strassenname/Stadt |
| Duplikat-Schutz | Bereits angefragte pano_ids werden erkannt, Benutzer wird vor erneutem Dispatch gefragt |
| Tile-Warnung | Automatische Warnung + Bestaetigung bei geschaetztem Verbrauch > 10.000 Tiles |
| Tile-Schaetzung | Vor jedem Dispatch: Anzahl Tiles + geschaetzte Kosten werden im Debug-Log angezeigt |

### Jobs & Artifacts
| Feature | Beschreibung |
|---|---|
| Auto-Refresh | Jobs-Tab aktualisiert sich automatisch alle 8 Sekunden solange Jobs laufen |
| Sofort-Platzhalter | Neuer Job erscheint unmittelbar nach Dispatch ohne auf Refresh warten zu muessen |
| Job abbrechen | Laufende GitHub Actions Jobs direkt aus der App heraus abbrechen |
| Artifact-Links | Name, Groesse (MB) und Ablaufdatum pro Artifact |
| Artifact-Download | Direkter ZIP-Download per PAT-Token ohne Browser-Umweg |
| GitHub Actions Summary | Jeder Run erzeugt eine Parametertabelle direkt in der GitHub Actions UI |
| Modus-Sync | Karten-Tab Cloud/Local schaltet Jobs-Tab automatisch mit um |

### Einstellungen (vollstaendige streetview-dl Parameter)
| Kategorie | Parameter |
|---|---|
| **Basis** | Qualitaet (low/medium/high), Sampling-Abstand (m), Suchradius (m), Max. Ergebnisse pro Punkt, Ausgabeordner, Pause zwischen Anfragen (s) |
| **Historisch** | Historische Suche an/aus, Datum von (YYYY-MM), Datum bis (YYYY-MM), Max. Alter in Monaten |
| **Field of View** | Heading 0–360°, Pitch −90–90°, FOV 10–120°, Zoom-Level 0–5 |
| **Bildgroesse** | Breite (px), Hoehe (px) |
| **Filter** | Nur Outdoor, Quelle (Google/User/alle), Min. Qualitaetswert (0–1), Max. Distanz vom Punkt (m) |
| **Cropping** | Crop links/rechts/oben/unten (px) |
| **Output** | Format (JPG/PNG/WebP), JPEG-Qualitaet (%) |
| **GitHub Actions** | Owner, Repository, Branch, Workflow-Datei |

### Quota-Tracking
| Feature | Beschreibung |
|---|---|
| Lokaler Zaehler | Tile-Verbrauch wird pro Monat im Browser-localStorage getrackt |
| GitHub-Sync | Quota aus abgeschlossenen GitHub Actions Runs des aktuellen Monats neu berechnen |
| Stopp-Schwelle | Konfigurierbarer Stopp-Prozentsatz (Standard 80 %) |
| Tile-Referenz | low = 32 · medium = 128 · high = 512 Tiles pro Panorama |
| Historisch-Faktor | Historische Aufnahmen verbrauchen ca. 2,5× mehr Tiles |

### API-Keys & Sicherheit
| Feature | Beschreibung |
|---|---|
| AES-256-GCM Verschluesselung | Keys werden geraetegebunden verschluesselt im localStorage gespeichert |
| Geraete-Fingerprint | PBKDF2 (100.000 Iterationen) + UserAgent + Sprache als Schluessel — kein Server noetig |
| Auto-Laden | Gespeicherte Keys werden beim App-Start automatisch entschluesselt geladen |
| Key-Test | Google API-Key und GitHub PAT live testen mit Statusanzeige |
| Anzeigen/Verstecken | Passwort-Toggle fuer beide Keys |

---

## 📊 Tile-Verbrauch & Kosten

| Qualitaet | Tiles/Panorama | Kostenloses Limit/Monat | Panoramen im Freikontigent |
|---|---|---|---|
| low | 32 | 100.000 | ~3.125 |
| medium | 128 | 100.000 | ~781 |
| high | 512 | 100.000 | ~195 |

> Historische Aufnahmen (`historical: true`) erhoehen den Verbrauch um Faktor ~2,5.
> Die App warnt automatisch und fragt nach Bestaetigung wenn ein Request voraussichtlich > 10.000 Tiles verbraucht.

---

## 🔑 Google Maps API-Key erstellen

1. **[console.cloud.google.com](https://console.cloud.google.com)** oeffnen (Google-Account benoetigt)
2. Neues Projekt erstellen (z.B. `streetview-explorer`)
3. **APIs & Dienste → Bibliothek → Map Tiles API → Aktivieren**
4. **APIs & Dienste → Anmeldedaten → + API-Schluessel erstellen** → kopieren
5. **Abrechnung aktivieren** (Pflicht, auch fuer kostenlosen Tier — Kreditkarte erforderlich)
6. Optional empfohlen: Key auf `Map Tiles API` einschraenken
7. Key in Web-App → Keys-Tab eingeben → **„Keys speichern"**

---

## 🔑 GitHub PAT erstellen (fuer Cloud-Modus)

1. **[github.com/settings/tokens?type=beta](https://github.com/settings/tokens?type=beta)** oeffnen
2. **„Generate new token" → „Fine-grained token"**
3. Repository-Zugriff: nur `streetview-explorer` auswaehlen
4. Permissions: ausschliesslich **Actions → Read and write** setzen
5. Token generieren → kopieren → in Web-App → Keys-Tab eingeben → **„Keys speichern"**

> Alle anderen Permissions bleiben auf `No access`. Der Token kann damit ausschliesslich
> Actions in diesem einen Repo starten — kein Code-Zugriff, keine Secrets, keine anderen Repos.

### Token verloren oder abgelaufen?

Neuen Token erstellen (Schritte 1–5 wiederholen). Alte Tokens unter
[github.com/settings/tokens](https://github.com/settings/tokens) widerrufen.

---

## 🐍 Local-Modus: Python-Server

Der lokale Server laeuft auf `http://localhost:5000` und ermoeglichst echte pano_id-Discovery
direkt ueber die Google Street View API — ohne GitHub Actions, direkt auf die eigene Festplatte.

### Installation & Start

```bash
# Einmalig: Abhaengigkeiten installieren
pip install flask flask-cors requests streetview-dl

# Server starten
python3 streetview_server.py
```

> `flask` und `flask-cors` werden beim ersten Start automatisch per pip installiert falls sie fehlen.

### Stoppen

```bash
# Im Terminal wo der Server laeuft:
Ctrl + C

# Falls im Hintergrund gestartet — per Prozess-Name:
pkill -f streetview_server.py

# Oder per Port:
lsof -ti:5000 | xargs kill -9
```

### Port aendern

```bash
SVEX_PORT=8080 python3 streetview_server.py
```

### Deinstallieren

```bash
# Nur Python-Pakete entfernen:
pip uninstall flask flask-cors -y

# Repo komplett loeschen:
rm -rf streetview-explorer/
```

> Der Server bindet **ausschliesslich auf `127.0.0.1`** (localhost) — er ist nicht aus dem
> Netzwerk erreichbar. Kein Daemon, kein Autostart, kein Systemdienst.

### API-Endpunkte

| Endpunkt | Methode | Beschreibung |
|---|---|---|
| `/api/status` | GET | Serverversion und Health-Check |
| `/api/query` | POST | Einzelpunkt-Abfrage: lat/lng → pano_ids |
| `/api/start` | POST | Download-Job starten → job_id |
| `/api/log/<job_id>` | GET | SSE-Stream: Live-Log des Jobs im Browser |
| `/api/stop/<job_id>` | POST | Laufenden Job abbrechen |
| `/api/jobs` | GET | Alle Jobs der aktuellen Session auflisten |

---

## ⚙️ GitHub Actions Workflow-Inputs

Alle Parameter sind direkt aus der Web-App (Einstellungen-Tab) steuerbar:

| Input | Beschreibung | Standard |
|---|---|---|
| `street` | Strassenname ODER `lat,lng` Koordinaten | — |
| `city` | Stadt (leer lassen bei Koordinaten-Modus) | — |
| `lat` / `lng` | Direkte Koordinaten als Alternative zu street/city | — |
| `pano_ids` | Kommagetrennte pano_ids (ueberspringt Discovery komplett) | — |
| `quality` | low / medium / high | medium |
| `sampling` | Sampling-Abstand in Metern | 10 |
| `radius` | Suchradius pro Punkt in Metern | 8 |
| `historical` | Historische Aufnahmen an/aus | false |
| `date_from` | Historisch: Datum von (YYYY-MM) | — |
| `date_to` | Historisch: Datum bis (YYYY-MM) | — |
| `max_age_months` | Max. Alter der Aufnahmen in Monaten | — |
| `heading` | Blickrichtung 0–360° | 0 |
| `pitch` | Neigung −90–90° | 0 |
| `fov` | Field of View 10–120° | 90 |
| `zoom` | Zoom-Level 0–5 | 2 |
| `source` | Quelle filtern: google / user / leer = alle | — |
| `outdoor` | Nur Outdoor: true / false / leer = alle | — |
| `output_format` | Ausgabeformat: jpg / png / webp | jpg |
| `jpg_quality` | JPEG-Qualitaet 10–100 % | 85 |
| `api_key` | Google Maps API Key (wird nicht gespeichert) | — |

---

## 🗂 Projektstruktur

```
streetview-explorer/
├── docs/
│ └── index.html # Web-App v3.5 (GitHub Pages)
├── streetview_headless.py # Headless Runner (GitHub Actions / CLI)
├── streetview_server.py # Lokaler API-Server v3.5 (Flask, Local-Modus)
├── .github/
│ └── workflows/
│ └── download.yml # GitHub Actions Workflow (alle Parameter)
├── downloads/ # Standard-Ausgabeordner (lokal)
├── requirements.txt
└── README.md
```

---

## 🐛 Fehlerbehebung

| Problem | Loesung |
|---|---|
| `keyInvalid` beim API-Test | Key pruefen, Map Tiles API in Google Cloud aktivieren |
| `accessNotConfigured` | Billing in Google Cloud aktivieren (Kreditkarte) |
| Web-App HTTP 401 | PAT ungueltig oder abgelaufen → neuen erstellen |
| Web-App HTTP 404 | Workflow-Datei fehlt oder falscher Token-Scope (Actions R+W benoetigt) |
| Web-App HTTP 422 | Unbekannte Workflow-Inputs → `download.yml` auf aktuelle Version aktualisieren |
| Nur `pos_...` pano_ids | `streetview_server.py` lokal starten fuer echte pano_id-Discovery |
| `street="unbekannt"` | Im Karten-Tab erst Strasse suchen oder GPS nutzen, dann Request starten |
| Artifact fehlt nach Erfolg | API-Key pruefen, pano_id manuell in Google Maps validieren |
| Keys nach Reload weg | Im Keys-Tab: **„Keys speichern"** druecken (werden AES-256-GCM verschluesselt) |
| Quota-Wert ungenau | Im Quota-Tab: **„☁ GitHub sync"** druecken fuer Berechnung aus echten Job-Daten |
| Doppelter Dispatch | App erkennt bereits angefragte pano_ids automatisch und fragt vor erneutem Request |
| Server nicht erreichbar | `python3 streetview_server.py` starten, Port 5000 pruefen (`lsof -i:5000`) |
| Server laesst sich nicht stoppen | `pkill -f streetview_server.py` oder `lsof -ti:5000 \| xargs kill -9` |

---

## 🔗 Verwandte Projekte

- [stiles/streetview-dl](https://github.com/stiles/streetview-dl) — der zugrundeliegende Downloader
- [OpenStreetMap / Nominatim](https://nominatim.org) — Geocoding & Reverse-Geocoding
- [Leaflet](https://leafletjs.com) — interaktive Karte in der Web-App
- [GitHub Actions](https://docs.github.com/en/actions) — Cloud-Runner fuer den Download

---

## 📄 Lizenz

MIT — siehe [LICENSE](LICENSE).
- [tkinterweb](https://github.com/Andereoo/TkinterWeb) — Webkit in Tkinter
