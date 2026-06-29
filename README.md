# streetview-explorer

[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://python.org)
[![Platform](https://img.shields.io/badge/platform-Linux-orange.svg)]()
[![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-CI%2FCD-2088FF?logo=github-actions&logoColor=white)](.github/workflows/download.yml)
[![GitHub Pages](https://img.shields.io/badge/Web_App-GitHub_Pages-222?logo=github&logoColor=white)](https://basecore.github.io/streetview-explorer/)
[![Requires](https://img.shields.io/badge/requires-streetview--dl-teal.svg)](https://github.com/stiles/streetview-dl)
[![streetview-dl](https://img.shields.io/badge/powered_by-streetview--dl-007acc)](https://github.com/stiles/streetview-dl)

**Eine moderne Linux-Desktop-GUI und Web-App fuer [streetview-dl](https://github.com/stiles/streetview-dl)** —
Panoramen entdecken, erkunden und batch-downloaden mit interaktiver OpenStreetMap-Karte,
Strassen-Crawling, Einzelpunkt-Download, pano_id-Deduplizierung und eingebautem Quota-Schutz.

> **v2.0** — Zwei Nutzungsmodi: **Desktop-GUI** (Linux, selbst-installierend) und **Web-App** (GitHub Pages + GitHub Actions, kein lokales Python noetig).

---

## 🌐 Web-App (kein Python noetig)

**[➜ Web-App oeffnen](https://basecore.github.io/streetview-explorer/)**

Die HTML5-App laeuft direkt im Browser und startet einen **GitHub Actions Job** — ohne lokale Installation:

1. Web-App oeffnen
2. PAT-Token + Google API-Key eingeben
3. Strasse, Stadt, Qualitaet waehlen
4. **„Panoramas herunterladen"** klicken
5. Job laeuft auf GitHub Actions (~5–30 Min)
6. Fertige Panoramas als **ZIP-Artifact** herunterladen

```
Browser (Web-App)
    └─► POST api.github.com/repos/.../actions/workflows/download.yml/dispatches
            └─► GitHub Actions Runner (ubuntu-latest)
                    └─► streetview_headless.py
                            └─► Panoramas als Artifact (7 Tage verfuegbar)
```

---

## 🔑 PAT-Token erstellen (GitHub Personal Access Token)

Der PAT-Token wird benoetigt, damit die Web-App den GitHub Actions Workflow starten kann.
Er wird **nur im RAM des Browsers** gehalten — nie gespeichert, nie weitergegeben.

### Schritt-fuer-Schritt

1. **[github.com/settings/tokens?type=beta](https://github.com/settings/tokens?type=beta)** oeffnen
   *(eingeloggt als `basecore` oder dein eigener Account)*

2. Klicke **„Generate new token" → „Fine-grained token"**

3. Felder ausfullen:

   | Feld | Wert |
   |---|---|
   | Token name | `streetview-explorer` |
   | Expiration | `30 days` (oder laenger) |
   | Repository access | **Only select repositories** → `streetview-explorer` auswaehlen |

4. Unter **Permissions** nur eine Berechtigung setzen:

   | Permission | Level |
   |---|---|
   | **Actions** | **Read and write** |

   > Alle anderen Permissions bleiben auf `No access`. Der Token kann damit
   > ausschliesslich Actions in diesem einen Repo starten — kein Code-Zugriff,
   > keine Secrets, keine anderen Repos.

5. Klicke **„Generate token"** → Token erscheint einmalig → **kopieren**

6. Token in die Web-App einfuegen → fertig.

### Token verloren oder abgelaufen?

Einfach einen neuen erstellen (Schritt 1–5 wiederholen). Alte Tokens koennen unter
[github.com/settings/tokens](https://github.com/settings/tokens) widerrufen werden.

---

## 🔑 Google Maps API-Key erstellen

Der Google Maps API-Key wird benoetigt, damit `streetview-dl` die Panorama-Tiles
von Googles Map Tiles API laden kann. **Kostenlos bis 100.000 Tiles/Monat.**

### Schritt-fuer-Schritt

1. **[console.cloud.google.com](https://console.cloud.google.com)** oeffnen
   (Google-Account benoetigt)

2. **Neues Projekt erstellen** (oder bestehendes auswaehlen):
   - Oben links: Projekt-Dropdown → **„Neues Projekt"**
   - Name z.B. `streetview-explorer` → **Erstellen**

3. **Map Tiles API aktivieren:**
   - Linkes Menue → **„APIs & Dienste"** → **„Bibliothek"**
   - Suche nach `Map Tiles API`
   - Klicke auf **„Map Tiles API"** → **„Aktivieren"**

4. **API-Schluessel erstellen:**
   - Linkes Menue → **„APIs & Dienste"** → **„Anmeldedaten"**
   - Klicke **„+ Anmeldedaten erstellen"** → **„API-Schluessel"**
   - Schluessel wird angezeigt → **kopieren**

5. **Abrechnung aktivieren** *(Pflicht, auch fuer kostenlosen Tier):*
   - Linkes Menue → **„Abrechnung"**
   - Rechnungskonto erstellen oder verknuepfen (Kreditkarte)
   - **Keine Kosten bis 100.000 Tiles/Monat** (Stand 2024)

6. **Optional: Key einschraenken** (empfohlen):
   - Anmeldedaten → Key anklicken → **„API-Einschraenkungen"**
   - Waehle **„Map Tiles API"** → Speichern

7. Key in die Desktop-GUI (API-Key Tab) oder Web-App eingeben → **„Key testen"**

### Kosten & Limits

| Qualitaet | Tiles / Panorama | Kostenloses Monatslimit |
|---|---|---|
| low | 32 | ~3.125 Panoramen/Monat |
| medium | 128 | ~781 Panoramen/Monat |
| high | 512 | ~195 Panoramen/Monat |

> Der eingebaute **Quota-Schutz** stoppt automatisch bei 80 % des Limits.

---

## 🖥 Desktop-GUI (Linux)

### Schnellstart

```bash
# 1. Einmalig: python3-tk sicherstellen
sudo apt install python3 python3-pip python3-tk   # Ubuntu/Debian
# sudo dnf install python3 python3-tkinter         # Fedora
# sudo pacman -S python tk                         # Arch

# 2. Repo klonen
git clone https://github.com/basecore/streetview-explorer.git
cd streetview-explorer

# 3. Starten – alle Python-Pakete werden automatisch installiert
python3 streetview_explorer.py
```

Beim ersten Start prueft das Skript alle Abhaengigkeiten und installiert
`requests`, `Pillow` und `streetview-dl` automatisch per `pip`.

### Optional: Karte direkt in der App

```bash
pip install tkinterweb
```

Ohne tkinterweb: Koordinaten manuell eingeben, Karte im Browser oeffnen.

---

## ✨ Features

| Feature | Desktop-GUI | Web-App |
|---|---|---|
| Strasse per Name (Nominatim + Sampling) | ✓ | ✓ |
| Interaktive OpenStreetMap-Karte | ✓ (tkinterweb) | — |
| Route / Polyline zeichnen | ✓ (tkinterweb) | — |
| Einzelpunkt per Koordinate | ✓ | — |
| pano_id-Deduplizierung | ✓ | ✓ |
| Quota-Schutz (lokaler Zaehler) | ✓ | ✓ |
| Historische Aufnahmen | ✓ | ✓ |
| Alle streetview-dl Bildoptionen | ✓ | — |
| API-Key Test (Live) | ✓ | — |
| Debug-Log Tab + Log-Datei | ✓ | GitHub Actions Log |
| Auto-Install aller Abhaengigkeiten | ✓ | ✓ (Actions) |
| Kein lokales Python noetig | — | ✓ |
| Artifact-Download (ZIP) | — | ✓ |

---

## 🗂 Tabs (Desktop-GUI)

| Tab | Zweck |
|---|---|
| **Karte** | OpenStreetMap — Punkt klicken oder Route zeichnen |
| **Strasse** | Strassenname + Stadt → vollstaendige Abdeckung |
| **Optionen** | Alle streetview-dl Bildoptionen (Qualitaet, FOV, Filter, Crop …) |
| **Quota** | Monatlicher Tile-Zaehler, Stopp-Schwelle, manueller Override |
| **API-Key** | Key eingeben, anzeigen/verstecken, testen, Schritt-fuer-Schritt |
| **Log** | Echtzeit-Ausgabe aller Schritte inkl. CMD-Strings und Fehler |

---

## 📋 Workflow (Desktop-GUI)

### Einzelner Panorama-Punkt
1. **Karte**-Tab → Koordinaten eingeben (oder tkinterweb: Karte klicken)
2. **Einzelpunkt herunterladen** druecken
3. Naechstes Panorama wird gefunden → direkt downloaden

### Route / Polyline
1. **Karte**-Tab → Route zeichnen → **Route fertig**
2. **Route-Panoramen entdecken** druecken
3. Alle eindeutigen pano_ids erscheinen in der Tabelle
4. **Alle gefundenen herunterladen**

### Ganze Strasse per Name
1. **Strasse**-Tab → Strassenname + Stadt eingeben
2. Sampling-Abstand waehlen (5 m = vollstaendig, 15 m = schneller)
3. **Strasse analysieren** → Geometrie von OSM, Panoramen entdecken
4. **Download starten**

---

## ⚙ Alle streetview-dl Optionen in der GUI

`--quality` · `--fov` · `--clip` · `--filter` · `--brightness` · `--contrast` ·
`--saturation` · `--crop-bottom` · `--no-crop` · `--format` · `--jpeg-quality` ·
`--max-width` · `--metadata` · `--metadata-only` · `--historical-download` ·
`--no-xmp` · `--concurrency` · `--timeout` · `--retries` · `--verbose`

---

## 🗂 Projektstruktur

```
streetview-explorer/
├── streetview_explorer.py      # Desktop-GUI (selbst-installierend, Tkinter)
├── streetview_headless.py      # Headless Runner (GitHub Actions / CLI)
├── map_viewer.html             # Leaflet-Karte (eingebettet via tkinterweb)
├── docs/
│   └── index.html              # Web-App (GitHub Pages)
├── .github/
│   └── workflows/
│       └── download.yml        # GitHub Actions Workflow
├── state/                      # Auto-erstellt: Quota-JSON-Dateien
├── logs/                       # Auto-erstellt: Session-Log-Dateien
├── downloads/                  # Standard-Ausgabeordner
├── requirements.txt
└── README.md
```

---

## 🐛 Fehlerbehebung

| Problem | Loesung |
|---|---|
| `ModuleNotFoundError: tkinter` | `sudo apt install python3-tk` |
| `streetview-dl: command not found` | Skript neu starten (installiert automatisch) |
| `keyInvalid` beim API-Test | Key pruefen, Map Tiles API aktivieren |
| `accessNotConfigured` | Billing in Google Cloud aktivieren |
| Karte nicht sichtbar | `pip install tkinterweb` oder Koordinaten manuell eingeben |
| Quota-Stopp zu frueh | Im Quota-Tab: Stop-% erhoehen oder echten Stand eintragen |
| Web-App HTTP 401 | PAT-Token ungueltig oder abgelaufen → neuen erstellen |
| Web-App HTTP 404 | Workflow-Datei fehlt oder falscher Token-Scope (Actions: R&W benoetigt) |
| Web-App HTTP 422 | Branch `main` existiert nicht oder Inputs ungueltig |
| Actions Job schlaegt fehl | Actions-Log ansehen → Link in Web-App unter „Letzte Jobs" |

---

## 📄 Lizenz

MIT — siehe [LICENSE](LICENSE).

---

## 🔗 Verwandte Projekte

- [stiles/streetview-dl](https://github.com/stiles/streetview-dl) — der zugrundeliegende Downloader
- [OpenStreetMap / Nominatim](https://nominatim.org) — Geocoding
- [Leaflet](https://leafletjs.com) — interaktive Karte
- [tkinterweb](https://github.com/Andereoo/TkinterWeb) — Webkit in Tkinter
