# FitnessTrackerHM kurzer Guide 

Servus! Das ist unsere kleine Desktop-App zum Loggen von Workouts und einem einfachen Kalorien-Check. Hier findet ihr eine schnelle Einführung und eine verständliche Code-Erklärung, so könnt ihr das Projekt easy verstehen und weitestgehend die Fragen beantworten.

## Schnellstart
- Starten: einfach `main.py` ausführen. Es öffnet sich ein Fenster.
- Beim ersten Start wirst du nach einem Profil gefragt (Name, Alter, etc.).
- Neue Einträge: Datum, Übung, Gewicht, Wdh, Sätze ausfüllen und speichern.
- CSV öffnen: Button „CSV öffnen“ öffnet die Datei vom aktuellen Profil.
- Kalorien: Tageskcal eintragen und speichern. Ziel/Status wird oben angezeigt.

Ordnerstruktur:
- `main.py` – die gesamte App (UI + Logik)
- `logbuch_profile/` – hier landen CSV und JSON-Dateien deiner Profile

## Wie speichert die App Daten?
- Trainingseinträge: CSV pro Profil (`<Profilname>.csv`), Spalten: date, exercise, weight, reps, sets
- Profil-Infos (Alter, Größe, Ziel…): JSON pro Profil (`<Profilname>.json`)
- Tageskalorien: JSON pro Profil (`<Profilname>_kcal.json`), Map: `{ "YYYY-MM-DD": kcal }`

## Code-Walkthrough
Wir gehen die wichtigsten Teile von `main.py` durch, dass du es erklären kannst.

### Kopfbereich: Imports, Konstanten, Pfade
- `tkinter`, `ttk`, `messagebox`: bauen das Fenster und die Widgets.
- `csv`, `json`, `pathlib.Path`: Speichern/Laden der Daten.
- `HEADERS`: CSV-Spaltennamen (einheitlich für alle Profile).
- `DATEN_ORDNER`: Ordner `logbuch_profile` neben der `main.py`.
- `STANDARD_PROFIL` und `aktuelles_profil`: Standardname und aktives Profil.

Warum das wichtig ist: Einheitliche Struktur, überall derselbe Speicherort, CSV kompatibel mit Excel.

### Hilfsfunktionen rund um Dateien/Profilnamen
- `_bereinige_profilname(name)`: erlaubt nur sichere Zeichen (Vermeidung von Pfadproblemen), fällt sonst auf „Standard“ zurück.
- `_profil_datei(profil)`: Pfad zur CSV.
- `_profil_info_datei(profil)`: Pfad zur Profil-Info-JSON.
- `_kcal_datei(profil)`: Pfad zur Kalorien-JSON.

### `_init_datenspeicher()`
- Legt den Ordner `logbuch_profile` an (falls nicht da).
- Wenn noch keine CSV existiert: erstellt eine Standard-CSV mit Headern. So kann man direkt loslegen.

### `profil_liste()`
- Listet alle vorhandenen Profile (CSV-Dateien) auf.

### `lade_log(profil=None)`
- Lädt die CSV des Profile und gibt eine Liste von Einträgen zurück.
- Detail: erkennt automatisch den Trenner (Komma, Semikolon, Tab), damit Import/Öffnen in Excel/Numbers nicht kaputt geht.
- Normalisiert Werte (z. B. Dezimal-Komma), skippt kaputte Zeilen, damit die App nicht abstürzt.

### `schreibe_eintrag_csv(entry, profil=None)`
- Hängt einen neuen Eintrag unten an die CSV an. Falls die Datei neu ist, wird der Header geschrieben.

### Profil-Info und Kalorien
- `lade_profil_info(profil)`: liest die Profil-JSON.
- `speichere_profil_info(info, profil)`: speichert Alter, Geschlecht, Größe, Gewicht, Aktivität, Ziel.
- `berechne_kcal(info)`: nutzt Mifflin-St Jeor Formel (BMR), Aktivitätsfaktor (TDEE) und Ziel (+/- Kalorien) → gibt BMR, TDEE, Ziel-Kcal zurück.
- `lade_kcal_map(profil)`, `speichere_kcal_map(map)`: Tageskalorien als Map `Datum → kcal`.
- `add_kcal_heute(kcal)`: addiert Kcal auf das aktuelle Datum.

Merksatz: CSV = Workouts, JSON = Profil & Tageskcal.

### Fortschritt-Funktion
- `fortschritt(uebung=None)` → `_fortschritt_lv(uebung)`
- Idee: simple Metrik „Gewicht × Wiederholungen“ (pro Eintrag).
- Vergleicht den letzten mit dem vorherigen Eintrag (optional gefiltert nach Übung). Liefert Datum, Werte und Delta.
- Absichtlich simpel gehalten, damit’s nachvollziehbar ist.

### In-Memory Log
- `log: List[Dict]`: wird beim Start mit der CSV synchronisiert und nach jedem Speichern aktualisiert. Praktisch für die UI-Anzeige.

### Die GUI-Klasse: `LogbuchApp`
Wichtigste Bausteine:
- Titel/Container Rahmen fürs Layout.
- Profil-Bereich: zeigt den aktuellen Profilnamen und Button „Profil bearbeiten“.
- Formular „Neuer Eintrag“: Felder für Datum, Übung, Gewicht, Wdh, Sätze + Buttons „Eintrag speichern“, „CSV öffnen“, „Fortschritt“.
- Kalorien-Leiste: zeigt Ziel (BMR/TDEE/Ziel-Kcal) und lässt Tageskcal eintragen. Anzeige wird farbig: unter Ziel (grün), leicht drüber (gelb), drüber (rot).
- Tabelle: zeigt die Einträge (neueste zuerst). Scrollbar ist dran.

Wichtige Methoden:
- `_onboarding_if_needed()`: falls noch kein Profil existiert, öffnet einmalig ein Setup-Fenster (Name + Basisdaten). Legt Dateien an und setzt das Profil.
- `_update_kcal_label()`: berechnet BMR/TDEE/Ziel und zeigt Status zu heutigen Kcal.
- `aktion_kcal_speichern()`: nimmt Eingabe, validiert, speichert in die Kalorien-Map, aktualisiert Anzeige.
- `_on_profil_bearbeiten()`: Dialog zum Editieren der Profilwerte, speichert und aktualisiert.
- `datum_vorbelegen()`: setzt das Datum-Feld auf heute (Convenience).
- `aktion_speichern()`: validiert Eingaben, schreibt in CSV, leert Felder (außer Datum), aktualisiert Tabelle.
- `tabelle_aktualisieren()`: lädt CSV neu und zeigt die letzten 50 Einträge (Performance + Übersicht).
- `aktion_fortschritt()`: optional nach Übungsnamen fragen, Fortschritt berechnen und in einem Dialog hübsch anzeigen.
- `aktion_csv_oeffnen()`: öffnet die CSV im OS (Windows/macOS/Linux spezifisch).

### Programmstart
- `if __name__ == "__main__":` startet die Tkinter-App.
- Setzt ggf. ein freundliches Theme (Windows) und ruft `mainloop()`.

## FAQ (wenn ihr wollt könnt ihr wichtige fragen ergänzen!)
- Warum CSV statt DB? Einfach, portabel, direkt mit Excel nutzbar.
- Was, wenn Semikolons statt Kommas? Der Loader erkennt den Trenner automatisch.
- Kann man mehrere Profile haben? Ja, jede CSV/JSON gehört zu einem Profil.
- Kann ich nur eine Übung vergleichen? Ja, Fortschritt fragt optional nach Übungsnamen.

## Tipps für’s Team
- Benennungen/Kommentare einheitlich halten.
- Beim Vorstellen kurz die Dateiarten erklären (CSV vs. JSON) 
- Für Demos 2–3 Einträge eintragen, dann Fortschritt zeigen.

Ich hoffe alles war verständlich. Bei Rückfragen bitte an Luca oder Adrian wenden!