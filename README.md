# Einfaches Fitness CLI Tool

Dieses Projekt ist eine sehr einfache Python-Kommandozeilen-App zum Tracken von:
- Benutzerprofil & Kalorienziel
- Mahlzeiten (Kalorien & Makros)
- Tägliches Dashboard
- Trainings-Logbuch

Alle Daten werden lokal in JSON-Dateien gespeichert:
- `user.json`
- `meals.json`
- `training.json`

## Start
Python 3.10+ empfohlen.

```bash
python app.py
```

Beim ersten Start wirst du nach deinen Daten gefragt.

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
