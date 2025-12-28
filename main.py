# -*- coding: utf-8 -*-

# Einfache GUI im Stil der Vorlesung, aber mit Profil-Anlage.

import tkinter as tk
from tkinter import ttk
import os
import csv

# Globale Profilvariablen
profil_name = ""
profil_alter = 0
profil_geschlecht = "m"
profil_groesse_cm = 0.0
profil_gewicht_kg = 0.0
profil_aktivitaet = "Sitzend"
profil_ziel = "Gewicht halten"

# Übungen und Log (nur im Speicher)
uebungsliste = ["Bankdrücken", "Kniebeuge", "Kreuzheben", "Schulterdrücken"]
log = []  # jedes Element: [datum, uebung, gewicht, reps, sets]

window = tk.Tk()
window.title("Trainings-Log (einfach)")

def datenordner():
    pfad = os.path.join(os.path.dirname(__file__), "logbuch_profile")
    try:
        os.makedirs(pfad, exist_ok=True)
    except Exception:
        pass
    return pfad

def profil_datei(name):
    return os.path.join(datenordner(), name + "_profile.csv")

def eintraege_datei(name):
    return os.path.join(datenordner(), name + ".csv")

def kalorien_datei(name):
    return os.path.join(datenordner(), name + "_kalorien.csv")

def speichere_profil():
    # schreibt Profil als eine Zeile in eine CSV
    pfad = profil_datei(profil_name)
    try:
        with open(pfad, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["name", "alter", "geschlecht", "groesse_cm", "gewicht_kg", "aktivitaet", "ziel"])
            w.writerow([profil_name, profil_alter, profil_geschlecht, profil_groesse_cm, profil_gewicht_kg, profil_aktivitaet, profil_ziel])
    except Exception:
        # still einfach: keine Fehlermeldung im Fenster
        pass

def schreibe_eintrag_csv(datum, uebung, gewicht, reps, sets):
    pfad = eintraege_datei(profil_name)
    header_noch_nicht = not os.path.exists(pfad)
    try:
        with open(pfad, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if header_noch_nicht:
                w.writerow(["date", "exercise", "weight", "reps", "sets"])
            w.writerow([datum, uebung, gewicht, reps, sets])
    except Exception:
        pass

def schreibe_kalorien_csv(datum, kcal, ziel, status):
    pfad = kalorien_datei(profil_name)
    header_noch_nicht = not os.path.exists(pfad)
    try:
        with open(pfad, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if header_noch_nicht:
                w.writerow(["date", "kcal", "ziel_kcal", "status"])
            w.writerow([datum, kcal, ziel, status])
    except Exception:
        pass

def finde_existierendes_profil():
    ordner = datenordner()
    dateien = os.listdir(ordner)
    i = 0
    while i < len(dateien):
        name = dateien[i]
        if name.endswith("_profile.csv"):
            return name[:-12]
        i = i + 1
    return ""

def lade_profil(name):
    pfad = profil_datei(name)
    if not os.path.exists(pfad):
        return False
    with open(pfad, "r", encoding="utf-8") as f:
        r = csv.reader(f)
        next(r, None)
        zeile = next(r, None)
        if zeile is None:
            return False
        global profil_name, profil_alter, profil_geschlecht, profil_groesse_cm, profil_gewicht_kg, profil_aktivitaet, profil_ziel
        profil_name = str(zeile[0])
        profil_alter = int(zeile[1])
        profil_geschlecht = str(zeile[2])
        profil_groesse_cm = float(zeile[3])
        profil_gewicht_kg = float(zeile[4])
        profil_aktivitaet = str(zeile[5])
        profil_ziel = str(zeile[6])
        return True

def lade_eintraege(name):
    pfad = eintraege_datei(name)
    eintraege = []
    if not os.path.exists(pfad):
        return eintraege
    with open(pfad, "r", encoding="utf-8") as f:
        r = csv.reader(f)
        next(r, None)
        for zeile in r:
            if len(zeile) >= 5:
                datum = str(zeile[0])
                uebung = str(zeile[1])
                gewicht = float(zeile[2])
                reps = int(zeile[3])
                sets = int(zeile[4])
                eintraege.append([datum, uebung, gewicht, reps, sets])
    return eintraege

def aktualisiere_eintraege_label():
    text = "Letzte Einträge:\n"
    start = len(log) - 5
    if start < 0:
        start = 0
    i = start
    while i < len(log):
        e = log[i]
        text = text + e[0] + " – " + e[1] + ": " + str(e[2]) + " kg, " + str(e[3]) + " Wdh, " + str(e[4]) + " Sätze\n"
        i = i + 1
    eintraege_label.config(text=text)

def berechne_kcal(alter, geschlecht, groesse_cm, gewicht_kg, aktivitaet, ziel):
    if geschlecht == "w":
        bmr = 10 * gewicht_kg + 6.25 * groesse_cm - 5 * alter - 161
    else:
        bmr = 10 * gewicht_kg + 6.25 * groesse_cm - 5 * alter + 5

    if aktivitaet == "Sitzend":
        faktor = 1.2
    elif aktivitaet == "Leicht aktiv":
        faktor = 1.375
    elif aktivitaet == "Mäßig aktiv":
        faktor = 1.55
    elif aktivitaet == "Sehr aktiv":
        faktor = 1.725
    else:
        faktor = 1.9

    if ziel == "Abnehmen -0.5 kg/Woche":
        delta = -500
    elif ziel == "Abnehmen -0.25 kg/Woche":
        delta = -250
    elif ziel == "Zunehmen +0.25 kg/Woche":
        delta = 250
    elif ziel == "Zunehmen +0.5 kg/Woche":
        delta = 500
    else:
        delta = 0

    tdee = bmr * faktor
    ziel_kcal = tdee + delta
    return round(bmr), round(tdee), round(ziel_kcal)

def dialog_zeigen(text):
    dialog = tk.Toplevel(window)
    dialog.grab_set()
    label = ttk.Label(dialog, text=text)
    label.pack()
    button = ttk.Button(dialog, text="Schließen", command=dialog.destroy)
    button.pack()
    window.wait_window(dialog)

def profil_anlegen():
    dialog = tk.Toplevel(window)
    dialog.grab_set()

    name_label = ttk.Label(dialog, text="Profilname:")
    name_entry = ttk.Entry(dialog)
    alter_label = ttk.Label(dialog, text="Alter (Jahre):")
    alter_entry = ttk.Entry(dialog)
    geschlecht_label = ttk.Label(dialog, text="Geschlecht:")
    geschlecht_box = ttk.Combobox(dialog)
    geschlecht_box['values'] = ["m", "w"]
    geschlecht_box.set("m")
    groesse_label = ttk.Label(dialog, text="Größe (cm):")
    groesse_entry = ttk.Entry(dialog)
    gewicht_label = ttk.Label(dialog, text="Gewicht (kg):")
    gewicht_entry = ttk.Entry(dialog)
    aktiv_label = ttk.Label(dialog, text="Aktivität:")
    aktiv_box = ttk.Combobox(dialog)
    aktiv_box['values'] = ["Sitzend", "Leicht aktiv", "Mäßig aktiv", "Sehr aktiv", "Extrem aktiv"]
    aktiv_box.set("Sitzend")
    ziel_label = ttk.Label(dialog, text="Ziel:")
    ziel_box = ttk.Combobox(dialog)
    ziel_box['values'] = ["Abnehmen -0.5 kg/Woche", "Abnehmen -0.25 kg/Woche", "Gewicht halten", "Zunehmen +0.25 kg/Woche", "Zunehmen +0.5 kg/Woche"]
    ziel_box.set("Gewicht halten")

    def speichern():
        global profil_name, profil_alter, profil_geschlecht, profil_groesse_cm, profil_gewicht_kg, profil_aktivitaet, profil_ziel
        name = name_entry.get().strip()
        if name == "":
            name = "Standard"
        profil_name = name
        try:
            profil_alter = int(alter_entry.get())
            profil_geschlecht = geschlecht_box.get()
            profil_groesse_cm = float(groesse_entry.get())
            profil_gewicht_kg = float(gewicht_entry.get())
            profil_aktivitaet = aktiv_box.get()
            profil_ziel = ziel_box.get()
        except Exception:
            dialog_zeigen("Bitte gültige Zahlen für Alter, Größe und Gewicht eingeben.")
            return
        speichere_profil()
        dialog.destroy()

    name_label.pack()
    name_entry.pack()
    alter_label.pack()
    alter_entry.pack()
    geschlecht_label.pack()
    geschlecht_box.pack()
    groesse_label.pack()
    groesse_entry.pack()
    gewicht_label.pack()
    gewicht_entry.pack()
    aktiv_label.pack()
    aktiv_box.pack()
    ziel_label.pack()
    ziel_box.pack()
    ttk.Button(dialog, text="Speichern", command=speichern).pack()

    window.wait_window(dialog)

# Profil laden, falls vorhanden; sonst anlegen
gel_name = finde_existierendes_profil()
if gel_name != "":
    ok = lade_profil(gel_name)
    if not ok:
        profil_anlegen()
else:
    profil_anlegen()

# Nach der Anlage: Anzeige der Profilinfos und Kalorienziel
bmr, tdee, ziel_kcal = berechne_kcal(profil_alter, profil_geschlecht, profil_groesse_cm, profil_gewicht_kg, profil_aktivitaet, profil_ziel)
profil_label = ttk.Label(text="Profil: " + profil_name)
kcal_label = ttk.Label(text="Kalorienziel: " + str(ziel_kcal) + " kcal (BMR " + str(bmr) + " | TDEE " + str(tdee) + ")")
eintraege_label = ttk.Label(text="Letzte Einträge:\n")

# Einträge laden
log = lade_eintraege(profil_name)
aktualisiere_eintraege_label()

# Eingabe-Widgets für Trainingslog
info_label = ttk.Label(text="Bitte Trainingsdaten eingeben:")
datum_frame = ttk.Frame()
datum_label = ttk.Label(master=datum_frame, text="Datum (YYYY-MM-DD): ")
datum_entry = ttk.Entry(master=datum_frame)

uebung_frame = ttk.Frame()
uebung_label = ttk.Label(master=uebung_frame, text="Übung: ")
uebung_combobox = ttk.Combobox(master=uebung_frame)
uebung_combobox['values'] = uebungsliste

gewicht_frame = ttk.Frame()
gewicht_label = ttk.Label(master=gewicht_frame, text="Gewicht (kg): ")
gewicht_entry = ttk.Entry(master=gewicht_frame)

reps_frame = ttk.Frame()
reps_label = ttk.Label(master=reps_frame, text="Wiederholungen: ")
reps_entry = ttk.Entry(master=reps_frame)

sets_frame = ttk.Frame()
sets_label = ttk.Label(master=sets_frame, text="Sätze: ")
sets_entry = ttk.Entry(master=sets_frame)

# Kalorien-Eingabe (einfach)
kalorien_frame = ttk.Frame()
kalorien_label = ttk.Label(master=kalorien_frame, text="Kalorien heute (kcal): ")
kalorien_entry = ttk.Entry(master=kalorien_frame)

def eintrag_speichern():
    datum = datum_entry.get()
    uebung = uebung_combobox.get()
    try:
        gewicht = float(gewicht_entry.get())
        reps = int(reps_entry.get())
        sets = int(sets_entry.get())
    except Exception:
        dialog_zeigen("Bitte gültige Zahlen eingeben (Gewicht, Wiederholungen, Sätze).")
        return
    if datum.strip() == "" or uebung.strip() == "":
        dialog_zeigen("Bitte Datum und Übung ausfüllen.")
        return
    log.append([datum, uebung, gewicht, reps, sets])
    schreibe_eintrag_csv(datum, uebung, gewicht, reps, sets)
    aktualisiere_eintraege_label()
    lv = gewicht * reps
    dialog_zeigen(datum + " – " + uebung + ": " + str(gewicht) + " kg, " + str(reps) + " Wdh, " + str(sets) + " Sätze\nLeistungswert: " + str(round(lv, 2)))

def kalorien_speichern():
    datum = datum_entry.get()
    try:
        kcal = int(kalorien_entry.get())
    except Exception:
        dialog_zeigen("Bitte gültige Zahl für Kalorien eingeben.")
        return
    if datum.strip() == "":
        dialog_zeigen("Bitte Datum für Kalorien eingeben.")
        return
    status = "drüber" if kcal > ziel_kcal else "ok"
    if status == "drüber":
        dialog_zeigen("Kalorien heute: " + str(kcal) + " — Du bist drüber.")
    else:
        dialog_zeigen("Kalorien heute: " + str(kcal) + " — Im Rahmen.")
    schreibe_kalorien_csv(datum, kcal, ziel_kcal, status)

def fortschritt_anzeigen():
    uebung = uebung_combobox.get()
    if uebung == "":
        dialog_zeigen("Bitte zuerst eine Übung auswählen.")
        return

    # Filtere Einträge der gewählten Übung
    eintraege = []
    i = 0
    while i < len(log):
        if log[i][1] == uebung:
            eintraege.append(log[i])
        i = i + 1

    if len(eintraege) < 2:
        dialog_zeigen("Zu wenig Einträge für diese Übung.")
        return

    alt = eintraege[-2]
    neu = eintraege[-1]
    lv_alt = alt[2] * alt[3]
    lv_neu = neu[2] * neu[3]

    if lv_neu > lv_alt:
        dialog_zeigen(
            "Verbesserung: " + str(round(lv_neu - lv_alt, 2)) +
            "\nAlt (" + alt[0] + "): " + str(round(lv_alt, 2)) +
            "\nNeu (" + neu[0] + "): " + str(round(lv_neu, 2)) +
            "\nEinheit: kg × Wiederholungen"
        )
    elif lv_neu < lv_alt:
        dialog_zeigen(
            "Verschlechterung: " + str(round(lv_alt - lv_neu, 2)) +
            "\nAlt (" + alt[0] + "): " + str(round(lv_alt, 2)) +
            "\nNeu (" + neu[0] + "): " + str(round(lv_neu, 2)) +
            "\nEinheit: kg × Wiederholungen"
        )
    else:
        dialog_zeigen(
            "Keine Veränderung." +
            "\nAlt (" + alt[0] + "): " + str(round(lv_alt, 2)) +
            "\nNeu (" + neu[0] + "): " + str(round(lv_neu, 2)) +
            "\nEinheit: kg × Wiederholungen"
        )

def schliessen():
    window.destroy()

speichern_button = ttk.Button(text="Speichern", command=eintrag_speichern)
fortschritt_button = ttk.Button(text="Fortschritt", command=fortschritt_anzeigen)
kalorien_button = ttk.Button(text="Kalorien speichern", command=kalorien_speichern)
abbrechen_button = ttk.Button(text="Abbrechen", command=schliessen)

# Layout per pack()
profil_label.pack()
kcal_label.pack()
info_label.pack()
eintraege_label.pack()

datum_label.pack()
datum_entry.pack()
datum_frame.pack()

uebung_label.pack()
uebung_combobox.pack()
uebung_frame.pack()

gewicht_label.pack()
gewicht_entry.pack()
gewicht_frame.pack()

reps_label.pack()
reps_entry.pack()
reps_frame.pack()

sets_label.pack()
sets_entry.pack()
sets_frame.pack()

kalorien_label.pack()
kalorien_entry.pack()
kalorien_frame.pack()

speichern_button.pack()
kalorien_button.pack()
fortschritt_button.pack()
abbrechen_button.pack()

window.mainloop()