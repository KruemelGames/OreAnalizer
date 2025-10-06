# EasyPeasyScanny – Feature-Slicing light

## Struktur
```
easypeasyscanny/
  scans/  # Scan-spezifische Modelle, Store, Analyzer
  rocks/  # Rocks-Modelle und Store
  ui/     # pywebview-UI (optional)
main.py
rocks.json
```

## Start
```bash
python3 -m pip install pywebview  # optional für Fenster-UI
python3 main.py
```

Ohne pywebview läuft ein CLI-Fallback und führt einen Beispielscan aus.

## Nächste Schritte
- Eure echte Scoring-/Analyse-Logik in `easypeasyscanny/scans/analyzer.py` einfügen.
- Datenformat von `rocks.json` anpassen (oder Lader erweitern).
- UI ersetzen/erweitern (HTML, JS-Bridge) in `easypeasyscanny/ui/webapp.py`.
