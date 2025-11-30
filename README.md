<<<<<<< HEAD
# Einfaches Fitness CLI & Web UI

Dieses Projekt ist eine sehr einfache Python-App mit:
- CLI-Menü in `app.py`
- Flask Web-UI in `web.py` (Templates unter `templates/`)

Trackt:
- Benutzerprofil & Kalorienziel
- Mahlzeiten (Kalorien & Makros)
- Tägliches Dashboard
- Trainings-Logbuch

Alle Daten werden lokal in JSON-Dateien gespeichert:
- `user.json`
- `meals.json`
- `training.json`

## Start (CLI)
Python 3.10+ empfohlen.

```bash
python app.py
```

## Start (Web-UI)
```bash
python web.py
```
Dann im Browser `http://127.0.0.1:5010` öffnen.

## Funktionen kurz
1. Profil: Berechnet Grundumsatz (Mifflin St. Jeor) und Tagesbedarf (Aktivität & Ziel).
2. Mahlzeit hinzufügen: Natürliche Eingabe wie "2 Eier und ein Apfel" -> einfache interne Tabelle.
3. Dashboard: Zeigt Zielkalorien, konsumierte Kalorien, verbleibende Kalorien.
4. Training: Speichert Übung, Gewicht, Wdh, Sätze. Fortschritt: Vergleich letzte 7 vs vorherige 7 Einträge.

## Vereinfachungen
- Kein echter API Call; stattdessen kleine interne Lebensmittel-Datenbank.
- Kein komplexes Error-Handling, damit der Code leicht lesbar bleibt.

## Beispiel Lebensmittel-Datenbank
- ei: 78 kcal, 6g Protein
- apfel: 95 kcal, 0g Fett

## Lizenz
Frei verwendbar zu Lernzwecken.
=======
# FitnessTrackerHM
>>>>>>> dbe52fefa8453d9fc091a33c2eaf7182e89b0d4d
