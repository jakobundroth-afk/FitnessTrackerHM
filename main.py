"""
Einfaches Studienprojekt: Profil + Dashboard + Trainings-Logbuch
---------------------------------------------------------------
Dieses Programm ist bewusst sehr simpel gehalten und verwendet NUR die
Python-Standardbibliothek. Es nutzt KEINE externen Pakete und KEINE
objektorientierte Programmierung. Alles basiert auf einfachen Funktionen
und klaren Datenstrukturen.

KERNELEMENTE:
1. Benutzerprofil anlegen und speichern (JSON-Datei: user_profile.json)
2. Dashboard zeigt die Profilbasisdaten + berechneten Grund- und Gesamtumsatz
3. Trainings-Logbuch (CSV-Datei: training_log.csv) für einfache Einträge
   + sehr einfache Fortschrittsanalyse (letzte 7 vs vorherige 7 Einträge)

Dateien werden lokal im selben Ordner wie dieses Skript abgelegt.

VERWENDETE FORMELN (Mifflin-St-Jeor):
BMR (Grundumsatz)
  Männer:    10*Gewicht(kg) + 6.25*Größe(cm) - 5*Alter + 5
  Frauen:    10*Gewicht(kg) + 6.25*Größe(cm) - 5*Alter - 161
TDEE (Gesamtumsatz) = BMR * Aktivitätsfaktor

Aktivitätsfaktoren (vereinfachtes Modell):
  1 = 1.2   (Sitzend)
  2 = 1.375 (Leicht aktiv)
  3 = 1.55  (Moderat aktiv)
  4 = 1.725 (Sehr aktiv)

ZIELE (nur informativ – keine Kalorienanpassung im Code außer Anzeige):
  halten = TDEE
  zunehmen = TDEE + 300 (optionale Infoausgabe)
  abnehmen = TDEE - 500 (optionale Infoausgabe)

Das Programm passt NICHT automatisch Kalorien an. Es zeigt nur mögliche
Ziel-Kalorien zur Orientierung (kann im Studienprojekt erläutert werden).
"""

import json          # Für JSON Profil-Datei
import csv           # Für Trainings-Log CSV
import os            # Prüfen ob Dateien existieren
import datetime      # Für Datum und Kalenderwoche

# Dateinamen als Konstanten (können leicht angepasst werden)
PROFILE_FILE = 'user_profile.json'
TRAINING_FILE = 'training_log.csv'

# ------------------------------------------------------------
# Hilfsfunktionen für Datei-Operationen
# ------------------------------------------------------------

def load_profile():
    """Lädt das Benutzerprofil aus der JSON-Datei.
    Gibt ein Dictionary zurück oder None, falls die Datei fehlt.
    """
    if not os.path.exists(PROFILE_FILE):
        return None  # Noch kein Profil angelegt
    try:
        with open(PROFILE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        # Falls Datei kaputt ist oder kein gültiges JSON enthalten ist
        return None


def save_profile(profile_dict):
    """Speichert das Profil (Dictionary) in die JSON-Datei.
    Überschreibt vorhandene Daten vollständig.
    """
    with open(PROFILE_FILE, 'w', encoding='utf-8') as f:
        json.dump(profile_dict, f, ensure_ascii=False, indent=2)


def load_training_log():
    """Lädt das Trainings-Log aus der CSV-Datei.
    Gibt eine Liste von Dictionaries zurück. Falls die Datei fehlt,
    wird eine leere Liste geliefert.
    """
    entries = []
    if not os.path.exists(TRAINING_FILE):
        return entries  # Keine Datei -> keine Einträge
    try:
        with open(TRAINING_FILE, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Konvertiere numerische Felder zurück in Zahlen
                # Falls das fehlschlägt, bleibt der Wert ein String
                try:
                    row['weight'] = float(row['weight'])
                except Exception:
                    row['weight'] = 0.0
                try:
                    row['reps'] = int(row['reps'])
                except Exception:
                    row['reps'] = 0
                try:
                    row['sets'] = int(row['sets'])
                except Exception:
                    row['sets'] = 0
                entries.append(row)
    except Exception:
        # Fehler beim Lesen -> leere Liste
        pass
    return entries


def append_training_entry(entry_dict):
    """Fügt einen einzelnen Trainings-Eintrag zur CSV-Datei hinzu.
    Falls die Datei noch nicht existiert, wird sie mit Header erstellt.

    Erwartete Keys im entry_dict:
      date (ISO Datum), week (Kalenderwoche), exercise, weight, reps, sets
    """
    file_exists = os.path.exists(TRAINING_FILE)
    fieldnames = ['date', 'week', 'exercise', 'weight', 'reps', 'sets']
    with open(TRAINING_FILE, 'a', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        # Wenn Datei neu angelegt -> zuerst Header schreiben
        if not file_exists:
            writer.writeheader()
        # Zeile schreiben
        writer.writerow(entry_dict)

# ------------------------------------------------------------
# Profil-Funktionen
# ------------------------------------------------------------

def setup_profile():
    """Fragt den Benutzer nach Basisdaten und legt ein Profil an.
    Berechnet BMR und TDEE und speichert alles in user_profile.json.
    """
    print("\n--- Profil Einrichtung ---")
    # Eingaben: Alle mit einfacher Validierung (Fehler -> erneute Eingabe)
    age = ask_int("Alter (Jahre): ")
    sex = ask_choice("Geschlecht (m/f): ", ['m', 'f'])
    height = ask_float("Größe (cm): ")
    weight = ask_float("Gewicht (kg): ")

    print("Aktivität: 1=Sitzend 2=Leicht 3=Moderat 4=Sehr Aktiv")
    activity_choice = ask_choice("Wahl (1-4): ", ['1','2','3','4'])
    activity_factor_map = {'1':1.2, '2':1.375, '3':1.55, '4':1.725}
    activity_factor = activity_factor_map[activity_choice]

    print("Ziel: halten / zunehmen / abnehmen")
    goal = ask_choice("Ziel eingeben: ", ['halten','zunehmen','abnehmen'])

    # BMR nach Mifflin-St-Jeor
    if sex == 'm':
        bmr = 10*weight + 6.25*height - 5*age + 5
    else:
        bmr = 10*weight + 6.25*height - 5*age - 161

    # Gesamtumsatz (TDEE)
    tdee = bmr * activity_factor

    # Optional mögliche Zielkalorien (nur Orientierung)
    if goal == 'abnehmen':
        daily_target = tdee - 500
    elif goal == 'zunehmen':
        daily_target = tdee + 300
    else:  # halten
        daily_target = tdee

    profile = {
        'age': age,
        'sex': sex,
        'height_cm': height,
        'weight_kg': weight,
        'activity_factor': activity_factor,
        'goal': goal,
        'bmr': round(bmr, 1),
        'tdee': round(tdee, 1),
        'suggested_daily_calories': round(daily_target, 1)
    }
    save_profile(profile)
    print("Profil gespeichert.")


def show_dashboard():
    """Zeigt eine einfache Übersicht über das Profil.
    Falls kein Profil existiert, Hinweis ausgeben.
    """
    print("\n--- Dashboard ---")
    profile = load_profile()
    if profile is None:
        print("Kein Profil gefunden. Bitte zuerst anlegen.")
        return
    # Ausgabe der Profilinfos
    print(f"Alter: {profile['age']} Jahre")
    print(f"Geschlecht: {profile['sex']}")
    print(f"Größe: {profile['height_cm']} cm")
    print(f"Gewicht: {profile['weight_kg']} kg")
    print(f"Aktivitätsfaktor: {profile['activity_factor']}")
    print(f"Ziel: {profile['goal']}")
    print(f"BMR (Grundumsatz): {profile['bmr']} kcal/Tag")
    print(f"TDEE (Gesamtumsatz): {profile['tdee']} kcal/Tag")
    print(f"Empfohlene Ziel-Kalorien: {profile['suggested_daily_calories']} kcal/Tag")

# ------------------------------------------------------------
# Trainings-Logbuch
# ------------------------------------------------------------

def add_training_entry():
    """Fragt Trainingsdaten ab und speichert sie in der CSV-Datei.
    Felder: Übung, Gewicht, Wdh, Sätze, Datum (heute), Kalenderwoche.
    """
    print("\n--- Training hinzufügen ---")
    exercise = input("Übung: ").strip()
    if not exercise:
        print("Keine Übung eingegeben – Abbruch.")
        return
    weight = ask_float("Gewicht (kg): ")
    reps = ask_int("Wiederholungen: ")
    sets = ask_int("Sätze: ")

    today = datetime.date.today()            # aktuelles Datum
    iso_date = today.isoformat()             # z.B. 2025-11-30
    week = today.isocalendar().week          # Kalenderwoche

    entry = {
        'date': iso_date,
        'week': week,
        'exercise': exercise,
        'weight': weight,
        'reps': reps,
        'sets': sets
    }
    append_training_entry(entry)
    print("Trainingseintrag gespeichert.")


def show_training_progress():
    """Vergleicht die letzten 7 Einträge mit den vorherigen 7.
    Berechnet Durchschnittsgewicht und Durchschnitts-Wiederholungen.
    Zeigt eine ganz einfache Veränderung an.
    """
    print("\n--- Trainings Fortschritt ---")
    data = load_training_log()
    if len(data) < 2:
        print("Nicht genug Einträge für einen Vergleich.")
        return

    # Wir nehmen die letzten 14 Einträge und splitten in zwei Blöcke à 7
    last14 = data[-14:]           # Falls weniger als 14 vorhanden, kommt eben weniger
    last7 = last14[-7:]           # Letzte 7
    prev7 = last14[:-7]           # Die 7 davor (kann <7 sein, wenn insgesamt <14)

    # Hilfsfunktionen für Durchschnitt
    def avg_weight(entries):
        if not entries:
            return 0.0
        total = 0.0
        count = 0
        for e in entries:
            total += e.get('weight', 0.0)
            count += 1
        return total / count if count else 0.0

    def avg_reps(entries):
        if not entries:
            return 0.0
        total = 0
        count = 0
        for e in entries:
            total += e.get('reps', 0)
            count += 1
        return total / count if count else 0.0

    w_last = avg_weight(last7)
    w_prev = avg_weight(prev7)
    r_last = avg_reps(last7)
    r_prev = avg_reps(prev7)

    print(f"Durchschnittliches Gewicht (letzte 7): {w_last:.1f} kg | vorher: {w_prev:.1f} kg")
    print(f"Durchschnittliche Wdh    (letzte 7): {r_last:.1f}    | vorher: {r_prev:.1f}")

def list_training_entries():
    """Zeigt alle Trainings-Einträge in einfacher Listenform.
    Falls keine vorhanden sind, wird ein Hinweis ausgegeben.
    """
    print("\n--- Alle Trainings Einträge ---")
    data = load_training_log()
    if not data:
        print("Keine Einträge vorhanden.")
        return
    # Jede Zeile einfach ausgeben (Datum | Übung | Gewichtkg x Wdh (Sätze))
    for e in data:
        date = e.get('date','?')
        exercise = e.get('exercise','?')
        weight = e.get('weight',0)
        reps = e.get('reps',0)
        sets = e.get('sets',0)
        print(f"{date} | {exercise} | {weight}kg x {reps} ({sets} Sätze)")

def delete_last_training_entry():
    """Löscht den letzten Trainings-Eintrag (falls vorhanden).
    Implementiert durch Neu-Schreiben der CSV ohne den letzten Eintrag.
    """
    print("\n--- Letzten Trainings-Eintrag löschen ---")
    data = load_training_log()
    if not data:
        print("Keine Einträge zum Löschen.")
        return
    # Entferne den letzten Eintrag aus der Liste
    removed = data.pop()  # letztes Element
    # Nun Datei komplett neu schreiben
    fieldnames = ['date','week','exercise','weight','reps','sets']
    with open(TRAINING_FILE, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow(row)
    print("Letzter Eintrag gelöscht:")
    print(removed)

# ------------------------------------------------------------
# Einfache Eingabe-Helfer (um Wiederholungen zu vermeiden)
# ------------------------------------------------------------

def ask_int(prompt):
    """Fragt eine ganze Zahl ab. Wiederholt bei ungültiger Eingabe."""
    while True:
        text = input(prompt).strip()
        try:
            return int(text)
        except ValueError:
            print("Bitte eine ganze Zahl eingeben.")


def ask_float(prompt):
    """Fragt eine Kommazahl ab. Wiederholt bei ungültiger Eingabe."""
    while True:
        text = input(prompt).strip()
        try:
            return float(text)
        except ValueError:
            print("Bitte eine Zahl (z.B. 72.5) eingeben.")


def ask_choice(prompt, options):
    """Fragt eine Auswahl ab. 'options' ist eine Liste erlaubter Strings.
    Gibt den gültigen String zurück.
    """
    opts_display = "/".join(options)
    while True:
        val = input(prompt).strip().lower()
        if val in options:
            return val
        print(f"Ungültig. Erlaubt: {opts_display}")

# ------------------------------------------------------------
# Hauptmenü
# ------------------------------------------------------------

def main_menu():
    """Zeigt das Hauptmenü in einer Schleife, bis der Benutzer beendet."""
    while True:
        print("\n=== Haupte Menü ===")
        print("1 Profil einrichten/neu")
        print("2 Dashboard anzeigen")
        print("3 Training hinzufügen")
        print("4 Trainings Fortschritt")
        print("5 Alle Trainings anzeigen")
        print("6 Letzten Trainingseintrag löschen")
        print("7 Automatisch Profil erstellen (Demo)")
        print("0 Ende")
        choice = input("Wahl: ").strip()

        if choice == '1':
            setup_profile()
        elif choice == '2':
            show_dashboard()
        elif choice == '3':
            add_training_entry()
        elif choice == '4':
            show_training_progress()
        elif choice == '5':
            list_training_entries()
        elif choice == '6':
            delete_last_training_entry()
        elif choice == '7':
            auto_create_demo_profile()
        elif choice == '0':
            print("Beende Programm. Tschüss!")
            break
        else:
            print("Ungültige Eingabe.")

# ------------------------------------------------------------
# Einstiegspunkt
# ------------------------------------------------------------
if __name__ == '__main__':
    print("Willkommen zum einfachen Fitness-Studienprojekt!")
    # Hinweis, falls noch kein Profil existiert
    if load_profile() is None:
        print("Noch kein Profil vorhanden. Bitte unter Menüpunkt 1 anlegen.")
    main_menu()

def auto_create_demo_profile():
    """Erstellt ein sehr einfaches Demo-Profil mit festen Werten.
    Nur als Abkürzung, falls man zum Testen schnell Daten braucht.
    """
    if load_profile() is not None:
        print("Profil existiert bereits – Demo nicht nötig.")
        return
    age = 25
    sex = 'm'
    height = 180
    weight = 80
    activity_factor = 1.55
    goal = 'halten'
    if sex == 'm':
        bmr = 10*weight + 6.25*height - 5*age + 5
    else:
        bmr = 10*weight + 6.25*height - 5*age - 161
    tdee = bmr * activity_factor
    daily_target = tdee
    profile = {
        'age': age,
        'sex': sex,
        'height_cm': height,
        'weight_kg': weight,
        'activity_factor': activity_factor,
        'goal': goal,
        'bmr': round(bmr,1),
        'tdee': round(tdee,1),
        'suggested_daily_calories': round(daily_target,1)
    }
    save_profile(profile)
    print("Demo-Profil erstellt.")
