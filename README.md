# streetview-explorer

[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://python.org)
[![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-CI%2FCD-2088FF?logo=github-actions&logoColor=white)](.github/workflows/download.yml)
[![GitHub Pages](https://img.shields.io/badge/Web_App-GitHub_Pages-222?logo=github&logoColor=white)](https://basecore.github.io/streetview-explorer/)
[![streetview-dl](https://img.shields.io/badge/powered_by-streetview--dl-007acc)](https://github.com/stiles/streetview-dl)

**Eine moderne Web-App zum Entdecken, Auswählen und Batch-Downloaden von Google Street View Panoramen** —
powered by [streetview-dl](https://github.com/stiles/streetview-dl), interaktiver OpenStreetMap-Karte,
Google Map Tiles API, GPS-Ortung, Punkt-/Linien-/Flächen-Suche, GitHub Actions Cloud-Modus,
lokalem Download-Modus und eingebautem Quota-Schutz.

> **v3.8** — Cloud-first StreetView Explorer mit echter Browser-Panorama-Discovery über die
> **Google Map Tiles API** (`createSession`, `streetview/panoIds`, `streetview/metadata`),
> interaktiver Marker↔Tabelle-Synchronisierung, direktem StreetView-Linking und neuer Flächen-Suche.

---

## 🌐 Web-App starten

**[➜ Web-App öffnen](https://basecore.github.io/streetview-explorer/)**

Die HTML5-App läuft direkt im Browser.

- Kein lokaler Python-Server nötig für die normale Suche.
- Cloud-Modus ist der Standard.
- Der lokale Server wird nur benötigt, wenn du Downloads direkt auf deine eigene Festplatte ausführen möchtest.

---

## 🚀 Schnellstart Cloud-Modus

Der **Cloud-Modus ist ab v3.8 der Default**.

1. **Web-App öffnen**
2. Im **API-Keys-Tab**:
   - Google Maps API-Key eintragen
   - GitHub PAT eintragen
   - optional: **„Keys speichern“** klicken
3. Im **Karten-Tab**:
   - per GPS suchen,
   - Punkt setzen,
   - Linie zeichnen,
   - Fläche zeichnen,
   - oder Straße suchen
4. **„🔍 Panoramen suchen“** drücken
5. Gefundene Panoramen erscheinen:
   - als Marker auf der OpenStreetMap-Karte
   - in der Panorama-Tabelle
6. Panoramen auswählen:
   - per Tabellen-Checkbox
   - oder direkt durch Klick auf den Panorama-Marker
7. **„▶ Request“** drücken
8. Im **Jobs-Tab** den GitHub Actions Job verfolgen
9. Fertige Panoramen als **ZIP-Artifact** herunterladen

```text
Browser / GitHub Pages
    └─► Punkt / GPS / Linie / Fläche / Straßensuche
        └─► Google Map Tiles API
            ├─► createSession
            ├─► streetview/panoIds
            └─► streetview/metadata
                └─► echte pano_ids in Tabelle + Karte
                    └─► GitHub Actions Workflow Dispatch
                        └─► streetview_headless.py
                            └─► Panoramen als ZIP-Artifact
```

---

## 🖥 Schnellstart Local-Modus

Der Local-Modus ist weiterhin vorhanden, aber nicht mehr der Standard.

```bash
# Lokalen Python-Server starten
python3 streetview_server.py
```

Danach in der Web-App:

1. Karten-Tab öffnen
2. Modus auf **„Lokal“** stellen
3. Panoramen suchen
4. Auswählen
5. **„▶ Lokal laden“** drücken

Der lokale Modus speichert Downloads direkt auf deine Festplatte.

---

## ✨ Features v3.8

### 🗺 Karte & Navigation

| Feature | Beschreibung |
|---|---|
| Interaktive OpenStreetMap-Karte | Leaflet + OSM-Tiles mit Live-Koordinatenanzeige |
| Cloud-first UI | App startet standardmäßig im Cloud-Modus |
| GPS-Ortung | Standort per Browser-Geolocation |
| GPS-Auto-Suchpunkt | Nach Klick auf GPS wird der Standort automatisch als Suchpunkt gesetzt |
| Kein Zusatzklick bei GPS nötig | Der Button **„🔍 Panoramen suchen“** erscheint direkt nach erfolgreicher GPS-Ermittlung |
| Punkt-Modus | Einzelnen Suchpunkt per Klick auf die Karte setzen |
| Linien-Modus | Mehrere Punkte setzen und Linie abschließen |
| Flächen-Modus | Polygonfläche aufspannen und Panoramen innerhalb der Fläche suchen |
| Straßensuche | Straße/Stadt per Nominatim suchen und als Linie oder Fläche übernehmen |
| Karte leeren | Marker, Linien, Flächen, GPS-Punkt und Panorama-Ergebnisse zurücksetzen |

---

## 🧭 Suchmodi

### 📍 Punkt-Suche

Ein Klick auf die Karte setzt einen Suchpunkt.

Geeignet für:

- einzelne Gebäude
- Kreuzungen
- POIs
- manuelle Kontrolle eines Standorts

Workflow:

```text
Punkt-Modus → Karte anklicken → Panoramen suchen
```

---

### 📷 GPS-Suche

Der GPS-Button fragt den Browser-Standort ab.

Ab v3.8 gilt:

- GPS-Punkt wird automatisch als Suchpunkt gesetzt
- **„🔍 Panoramen suchen“** erscheint sofort
- kein zusätzlicher Klick auf **„📌 Als Punkt“** nötig

Workflow:

```text
GPS klicken → Standort gefunden → Panoramen suchen
```

---

### ✏ Linien-Suche

Im Linien-Modus können mehrere Punkte gesetzt werden.

Die App interpoliert entlang der Linie Sampling-Punkte gemäß dem eingestellten Sampling-Abstand.

Beispiel:

```text
Sampling-Abstand = 10 m
Linie = 250 m
≈ 25 Suchpunkte
```

Workflow:

```text
Linie wählen → Punkte setzen → Linie abschließen → Panoramen suchen
```

---

### ⬜ Flächen-Suche

Neu in v3.8: Du kannst eine Fläche als Polygon zeichnen.

Die App erzeugt innerhalb der Fläche ein Raster aus Sampling-Punkten und sucht an diesen Punkten nach Panoramen.

Geeignet für:

- Parkplätze
- Werksgelände
- Wohnblöcke
- Kreuzungsbereiche
- Plätze
- frei definierbare Suchbereiche

Workflow:

```text
Fläche wählen → mindestens 3 Eckpunkte setzen → Fläche abschließen → Panoramen suchen
```

Technische Details:

| Eigenschaft | Beschreibung |
|---|---|
| Mindestpunkte | 3 Eckpunkte |
| Sampling | Raster innerhalb der Polygonfläche |
| Rasterabstand | Einstellung **Sampling-Abstand (m)** |
| Begrenzung | Maximal ca. 500 Sampling-Punkte pro Fläche |
| Fallback | Bei sehr kleinen Flächen wird mindestens der Mittelpunkt verwendet |

Hinweis:

> Bei großen Flächen sollte der Sampling-Abstand erhöht werden, um API-Last und Quota-Verbrauch zu begrenzen.

---

## 🔎 Panorama-Discovery

Ab v3.8 nutzt der Browser selbst die **Google Map Tiles API** zur Panorama-Suche.

Die bisherige reine Fallback-Logik wurde erweitert: Auch ohne lokalen Server können echte `pano_id`s gefunden werden.

### Verwendete Google APIs

| API | Zweck |
|---|---|
| `createSession` | Erstellt eine Map Tiles StreetView Session |
| `streetview/panoIds` | Sucht Panorama-IDs in der Nähe von Koordinaten |
| `streetview/metadata` | Lädt Metadaten zu einer `pano_id`, z. B. Datum, Koordinate, Links |

---

### Ergebnis-Typen

| Typ | Beschreibung |
|---|---|
| echte `pano_id` | Von Google Map Tiles API gefundenes Panorama |
| `pos_...` Fallback | Koordinaten-Fallback, falls keine echte `pano_id` gefunden wurde |

Beispiel echte Panorama-ID:

```text
yAMdSx48qhlR64YUwB8Bgg
```

Beispiel Fallback-ID:

```text
pos_49_03792_12_12779
```

---

## 🧩 Marker ↔ Tabelle Synchronisierung

Ab v3.8 sind Karte und Tabelle interaktiv gekoppelt.

| Aktion | Ergebnis |
|---|---|
| Checkbox in Tabelle deaktivieren | Marker wird grau |
| Checkbox in Tabelle aktivieren | Marker wird wieder farbig |
| Panorama-Marker anklicken | Zugehörige Tabellen-Checkbox wird umgeschaltet |
| Marker erneut anklicken | Auswahl wird wieder zurückgeschaltet |
| „Alle“ | Alle Panoramen auswählen |
| „Invertieren“ | Auswahl invertieren |
| CSV Export | Exportiert nur ausgewählte Panoramen |
| Cloud Request | Sendet nur ausgewählte Panoramen |

Markerfarben:

| Zustand | Farbe |
|---|---|
| echte `pano_id`, ausgewählt | Blau im Cloud-/Browser-Modus |
| echte `pano_id`, lokal/serverbasiert | Grün |
| Fallback `pos_...` | Orange |
| deaktiviert | Grau |

---

## 🔗 Direkte Google Street View Links

Alle Kartenlinks wurden in v3.8 auf direkte StreetView-URLs umgestellt.

Die App nutzt dafür intern:

```js
gmapsPanoUrl(lat, lng, panoId, heading, pitch, fov)
```

Für echte `pano_id`s wird der Link mit `pano=` erzeugt:

```text
https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=LAT,LNG&heading=0&pitch=0&fov=90&pano=PANO_ID
```

Für Fallback-Positionen wird nur die Koordinate als Viewpoint verwendet:

```text
https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=LAT,LNG&heading=0&pitch=0&fov=90
```

Diese Links werden verwendet in:

- Panorama-Tabelle
- Marker-Popup
- CSV Export

---

## 📋 Panorama-Tabelle

Nach der Suche erscheinen alle gefundenen Panoramen in einer Tabelle.

| Spalte | Beschreibung |
|---|---|
| Checkbox | Auswahl für Download/Export |
| `#` | Laufende Nummer |
| `pano_id` | Google StreetView Panorama-ID oder Fallback-ID |
| Datum | Aufnahmedatum, sofern von Google verfügbar |
| Lat | Latitude |
| Lng | Longitude |
| Karte | StreetView-Link + Marker-Fokus |

Zusätzliche Badges:

| Badge | Bedeutung |
|---|---|
| `✓ angefragt` | Panorama wurde bereits per Cloud Request dispatcht |
| `fallback` | Kein echtes Panorama, sondern Koordinaten-Fallback |

---

## ⭳ CSV Export

Der CSV Export enthält alle ausgewählten Panoramen.

Spalten:

```csv
#,pano_id,datum,lat,lng,maps_url
```

`maps_url` ist ein direkter Google StreetView-Link.

---

## ☁ Cloud-Modus

Der Cloud-Modus ist ab v3.8 der Standardmodus.

| Feature | Beschreibung |
|---|---|
| Kein lokaler Server nötig | Browser findet Panoramen via Map Tiles API |
| GitHub Actions Dispatch | Download läuft in GitHub Actions |
| ZIP Artifact | Ergebnisse werden als ZIP bereitgestellt |
| PAT-authentifizierter Download | Artifact kann direkt aus der App geladen werden |
| Jobs-Tab Default | Jobs-Tab startet ebenfalls im Cloud/GitHub Actions Modus |
| Kein localhost Polling | `localhost:5000` wird im Cloud-Modus nicht mehr ständig geprüft |

---

## 🖥 Local-Modus

Der Local-Modus bleibt erhalten.

Er ist sinnvoll, wenn:

- Downloads direkt lokal gespeichert werden sollen
- ein lokaler Python-Prozess verwendet werden soll
- die GitHub Actions Cloud nicht genutzt werden soll

```bash
python3 streetview_server.py
```

Danach in der Web-App auf **„Lokal“** umschalten.

---

## 📦 Download-Modi

| Modus | Beschreibung |
|---|---|
| Cloud Request | Startet GitHub Actions Workflow |
| Lokal laden | Startet lokalen Download über `streetview_server.py` |
| CSV Export | Exportiert Auswahl als CSV ohne Download |

Dispatch-Modi im Cloud-Modus:

| Dispatch-Typ | Beschreibung |
|---|---|
| `pano_ids` | Echte Panorama-IDs werden direkt an den Workflow übergeben |
| Koordinaten | Fallback bei `pos_...` oder GPS/Punkt |
| Straße/Stadt | Fallback, wenn keine `pano_id`s vorhanden sind |

---

## ⚙ Einstellungen

### Basis

| Einstellung | Beschreibung |
|---|---|
| Qualität | `low`, `medium`, `high` |
| Sampling-Abstand | Abstand zwischen Suchpunkten in Metern |
| Suchradius | Radius pro Suchpunkt |
| Max. Ergebnisse/Punkt | Begrenzung pro Sampling-Punkt |
| Ausgabeordner | Lokaler Zielordner |
| Pause zwischen Anfragen | Rate-Limit-Schutz |

---

### Historische Aufnahmen

| Einstellung | Beschreibung |
|---|---|
| Historische Suche | Aktiviert historische Epochen |
| Datum von | Startdatum `YYYY-MM` |
| Datum bis | Enddatum `YYYY-MM` |
| Max. Alter | Maximales Alter in Monaten |

---

### Field of View

| Einstellung | Beschreibung |
|---|---|
| Heading | Blickrichtung 0–360° |
| Pitch | Neigung −90–90° |
| FOV | Field of View 10–120° |
| Zoom-Level | Zoom 0–5 |
| Bildbreite | Ausgabe-Breite |
| Bildhöhe | Ausgabe-Höhe |

---

### Filter

| Einstellung | Beschreibung |
|---|---|
| Nur Outdoor | Indoor/Outdoor Filter |
| Quelle | Google/User/Alle |
| Min. Qualitätswert | Mindestqualität |
| Max. Distanz | Distanzfilter |

---

### Output

| Einstellung | Beschreibung |
|---|---|
| Format | JPG, PNG, WebP |
| JPEG-Qualität | Qualität in Prozent |
| Cropping | Links, rechts, oben, unten |

---

### GitHub Actions

| Einstellung | Beschreibung |
|---|---|
| Owner | GitHub Owner |
| Repository | GitHub Repository |
| Branch | Branch für Workflow Dispatch |
| Workflow | Workflow-Datei, z. B. `download.yml` |

---

## 📊 Tile-Verbrauch & Kosten

| Qualität | Tiles/Panorama | Kostenloses Limit/Monat | Panoramen im Freikontingent |
|---|---:|---:|---:|
| low | 32 | 100.000 | ca. 3.125 |
| medium | 128 | 100.000 | ca. 781 |
| high | 512 | 100.000 | ca. 195 |

Historische Suche erhöht den Verbrauch ungefähr um Faktor `2,5`.

Die App warnt automatisch, wenn ein Request voraussichtlich mehr als `10.000` Tiles verbraucht.

---

## 🧮 Quota-Tracking

| Feature | Beschreibung |
|---|---|
| Lokaler Zähler | Tile-Verbrauch wird monatlich im Browser-localStorage getrackt |
| GitHub Sync | Verbrauch aus abgeschlossenen GitHub Actions Runs ableiten |
| Stopp-Schwelle | Standard: 80 % |
| Manuelle Korrektur | Verbrauch kann im Quota-Tab angepasst werden |
| Verbrauchsschätzung | Vor jedem Request im Debug-Log sichtbar |

---

## 🔑 Google Maps API-Key erstellen

1. [console.cloud.google.com](https://console.cloud.google.com) öffnen
2. Neues Projekt erstellen
3. **APIs & Dienste → Bibliothek → Map Tiles API → Aktivieren**
4. **APIs & Dienste → Anmeldedaten → API-Schlüssel erstellen**
5. Abrechnung aktivieren
6. Optional: Key auf **Map Tiles API** beschränken
7. Key in der Web-App im **API-Keys-Tab** eintragen
8. Optional: **„Keys speichern“** klicken

Wichtig:

> Für v3.8 ist die **Map Tiles API** entscheidend. Die Browser-Discovery nutzt nicht die alte StreetView Static Metadata API.

---

## 🔑 GitHub PAT erstellen

Für den Cloud-Modus wird ein GitHub Personal Access Token benötigt.

1. [github.com/settings/tokens?type=beta](https://github.com/settings/tokens?type=beta) öffnen
2. **Generate new token**
3. Fine-grained token wählen
4. Repository-Zugriff auf `streetview-explorer` beschränken
5. Permission setzen:
   - **Actions: Read and write**
6. Token generieren
7. Token in der Web-App eintragen
8. Optional: **„Keys speichern“**

Empfohlene Rechte:

| Bereich | Recht |
|---|---|
| Repository | Nur dieses Repository |
| Actions | Read and write |
| Code | No access |
| Secrets | No access |
| Issues | No access |
| Pull Requests | No access |

---

## 🔐 API-Keys & Sicherheit

| Feature | Beschreibung |
|---|---|
| AES-256-GCM | Keys werden verschlüsselt im Browser gespeichert |
| Gerätebindung | Verschlüsselung basiert auf Browser/UserAgent/Sprache |
| PBKDF2 | 100.000 Iterationen |
| Kein Server | Keys verlassen den Browser nur für Google/GitHub API Requests |
| Auto-Laden | Gespeicherte Keys werden beim App-Start geladen |
| Key-Test | Google Key und GitHub PAT können getestet werden |
| Sichtbarkeit | Passwortfelder können temporär angezeigt werden |

Hinweis:

> Die Speicherung im Browser ist komfortabel, aber nicht mit einem professionellen Secret Manager gleichzusetzen. Für produktive Umgebungen sollten API-Keys möglichst eingeschränkt werden.

---

## 🐍 Local-Modus: Python-Server

Der lokale Server läuft standardmäßig auf:

```text
http://localhost:5000
```

Er wird nur im Local-Modus benötigt.

### Installation

```bash
pip install flask flask-cors requests streetview-dl
```

### Start

```bash
python3 streetview_server.py
```

### Stoppen

```bash
Ctrl + C
```

Linux/macOS:

```bash
pkill -f streetview_server.py
```

Oder per Port:

```bash
lsof -ti:5000 | xargs kill -9
```

Windows:

```bat
for /f "tokens=5" %a in ('netstat -aon ^| findstr :5000') do taskkill /F /PID %a
```

### Port ändern

Windows:

```bat
set SVEX_PORT=8080 && python streetview_server.py
```

Linux/macOS:

```bash
SVEX_PORT=8080 python3 streetview_server.py
```

---

## 🔌 Lokale API-Endpunkte

| Endpunkt | Methode | Beschreibung |
|---|---|---|
| `/api/status` | GET | Serverstatus |
| `/api/query` | POST | Panorama-Abfrage pro Punkt |
| `/api/start` | POST | Download-Job starten |
| `/api/log/<job_id>` | GET | Live-Log via SSE |
| `/api/stop/<job_id>` | POST | Job abbrechen |
| `/api/jobs` | GET | Lokale Jobs auflisten |

---

## ⚙ GitHub Actions Workflow-Inputs

| Input | Beschreibung | Standard |
|---|---|---|
| `street` | Straßenname oder Fallback-Label | — |
| `city` | Stadt | — |
| `lat` | Latitude bei Koordinatenmodus | — |
| `lng` | Longitude bei Koordinatenmodus | — |
| `pano_ids` | Kommagetrennte echte Panorama-IDs | — |
| `quality` | `low`, `medium`, `high` | `medium` |
| `sampling` | Sampling-Abstand in Metern | `10` |
| `radius` | Suchradius in Metern | `8` |
| `historical` | Historische Aufnahmen | `false` |
| `date_from` | Datum von `YYYY-MM` | — |
| `date_to` | Datum bis `YYYY-MM` | — |
| `max_age_months` | Max. Alter in Monaten | — |
| `heading` | Blickrichtung | `0` |
| `pitch` | Neigung | `0` |
| `fov` | Field of View | `90` |
| `zoom` | Zoom-Level | `2` |
| `source` | Quelle `google`, `user`, leer | — |
| `outdoor` | Outdoor-Filter | — |
| `output_format` | `jpg`, `png`, `webp` | `jpg` |
| `jpg_quality` | JPEG Qualität | `85` |
| `api_key` | Google Maps API-Key | — |

---

## 🗂 Projektstruktur

```text
streetview-explorer/
├── docs/
│   └── index.html              # Web-App v3.8 für GitHub Pages
├── streetview_headless.py      # Headless Runner für GitHub Actions / CLI
├── streetview_server.py        # Lokaler API-Server für Local-Modus
├── .github/
│   └── workflows/
│       └── download.yml        # GitHub Actions Workflow
├── downloads/                  # Standard-Ausgabeordner lokal
├── requirements.txt
├── LICENSE
└── README.md
```

---

## 🧪 Validierung v3.8

Die v3.8 Web-App sollte folgende Eigenschaften erfüllen:

| Check | Erwartung |
|---|---|
| App-Version | `v3.8` |
| Default-Modus | Cloud |
| Jobs-Default | GitHub Actions |
| Browser-Discovery | Map Tiles API |
| `createSession` | vorhanden |
| `streetview/panoIds` | vorhanden |
| `streetview/metadata` | vorhanden |
| `.startswith(` | darf nicht vorkommen |
| `.startsWith(` | korrekt verwendet |
| Google Maps Links | direkte StreetView-Links |
| Marker-Klick | toggelt Tabellen-Auswahl |
| Tabellen-Checkbox | ändert Marker-Farbe |
| GPS | zeigt direkt „Panoramen suchen“ |
| Fläche | Polygon-Suche verfügbar |
| Cloud-Modus | kein dauerhaftes localhost-Polling |

---

## 🐛 Fehlerbehebung

| Problem | Lösung |
|---|---|
| `keyInvalid` beim API-Test | API-Key prüfen |
| `accessNotConfigured` | Map Tiles API aktivieren |
| Billing-Fehler | Google Cloud Billing aktivieren |
| Keine Panoramen gefunden | Suchradius erhöhen oder Sampling anpassen |
| Nur `pos_...` Fallbacks | In der Umgebung wurden keine echten `pano_id`s gefunden |
| Alte Google-Maps-Links sichtbar | Browser Hard Reload ausführen |
| `.startswith is not a function` | Alte gecachte Version geladen → Hard Reload |
| `localhost:5000 ERR_CONNECTION_REFUSED` im Cloud-Modus | Alte gecachte Version geladen oder Local-Modus aktiv |
| Tabelle verschwindet beim Marker-Klick | Alte Version geladen → v3.8 neu deployen und Hard Reload |
| GPS zeigt keinen Suchbutton | Browser-Geolocation erlauben und v3.8 verwenden |
| Fläche erzeugt sehr viele Punkte | Sampling-Abstand erhöhen |
| HTTP 401 bei GitHub | PAT ungültig oder abgelaufen |
| HTTP 404 bei GitHub | Repo, Owner oder Workflow falsch |
| HTTP 422 bei GitHub | Workflow Inputs passen nicht zur `download.yml` |
| Artifact fehlt | GitHub Actions Run prüfen |
| Artifact abgelaufen | GitHub Artifacts sind nur begrenzt verfügbar |
| Quota ungenau | Im Quota-Tab **„☁ GitHub sync“** ausführen |

---

## 🔄 Browser Cache / Hard Reload

Wenn nach einem Update noch alte Fehler auftreten, lädt der Browser vermutlich eine gecachte Version.

Hard Reload:

| System | Tastenkombination |
|---|---|
| Windows/Linux | `Ctrl + F5` |
| macOS Chrome/Edge | `Cmd + Shift + R` |
| macOS Safari | `Cmd + Option + R` |

Bei GitHub Pages kann zusätzlich etwas Wartezeit nötig sein, bis die neue `index.html` ausgeliefert wird.

---

## 🔗 Verwandte Projekte

- [stiles/streetview-dl](https://github.com/stiles/streetview-dl) — zugrundeliegender Downloader
- [Google Map Tiles API](https://developers.google.com/maps/documentation/tile) — Panorama Discovery
- [OpenStreetMap](https://www.openstreetmap.org) — Kartenbasis
- [Nominatim](https://nominatim.org) — Geocoding & Reverse-Geocoding
- [Leaflet](https://leafletjs.com) — interaktive Karte
- [GitHub Actions](https://docs.github.com/en/actions) — Cloud Runner

---

## 📄 Lizenz

MIT — siehe [LICENSE](LICENSE).
