"""Einfache Tkinter-App zum Trainings- und Kalorientracking mit CSV/JSON-Dateien."""

# -*- coding: utf-8 -*-
from typing import List, Dict
from pathlib import Path
import csv
import os
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import json

# CSV-Konfiguration (Excel-kompatibel) und Profile
HEADERS = ["date", "exercise", "weight", "reps", "sets"]
DATEN_ORDNER = Path(__file__).with_name("logbuch_profile")
STANDARD_PROFIL = "Standard"
aktuelles_profil = STANDARD_PROFIL


def _bereinige_profilname(name: str) -> str:
    """Lässt nur einfache Zeichen zu und fällt auf STANDARD_PROFIL zurück."""
    erlaubte = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-"
    cleaned = "".join(ch for ch in name if ch in erlaubte).strip()
    return cleaned or STANDARD_PROFIL


def _profil_datei(profil: str) -> Path:
    """Pfad zur CSV des Profils."""
    return DATEN_ORDNER / f"{profil}.csv"


def _profil_info_datei(profil: str) -> Path:
    """Pfad zur Profil-Info (JSON)."""
    return DATEN_ORDNER / f"{profil}.json"


def _kcal_datei(profil: str) -> Path:
    """Pfad zur Kalorien-Tageswerte-Datei (JSON-Map)."""
    return DATEN_ORDNER / f"{profil}_kcal.json"


def _init_datenspeicher() -> None:
    """Stellt den Datenordner sicher und legt bei Bedarf ein Standard-Profil an."""
    DATEN_ORDNER.mkdir(parents=True, exist_ok=True)
    # Falls keine Profile existieren, Standard anlegen
    if not any(DATEN_ORDNER.glob("*.csv")):
        datei = _profil_datei(STANDARD_PROFIL)
        with datei.open("w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=HEADERS)
            writer.writeheader()

"""--- Ende Duplikatbereich: Imports/Konstanten/Helfer mehrfach vorhanden gewesen ---"""


def profil_liste() -> List[str]:
    _init_datenspeicher()
    return sorted([p.stem for p in DATEN_ORDNER.glob("*.csv")])


def lade_log(profil: str | None = None) -> List[Dict]:
    """Lädt alle Einträge eines Profils aus der CSV-Datei."""
    _init_datenspeicher()
    p = profil or aktuelles_profil
    datei = _profil_datei(p)
    if not datei.exists():
        return []
    try:
        # Lese Inhalt zur Delimiter-Erkennung
        content = datei.read_text(encoding="utf-8-sig")
        sample = "\n".join(content.splitlines()[:10])
        delimiter = ","
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=[",", ";", "\t"])
            delimiter = dialect.delimiter
        except Exception:
            # Fallback: wenn Semikolon häufiger ist, nutze es
            if sample.count(";") > sample.count(","):
                delimiter = ";"
            elif sample.count("\t") > max(sample.count(","), sample.count(";")):
                delimiter = "\t"

        # Jetzt mit erkanntem Delimiter parsen
        import io as _io
        f = _io.StringIO(content)
        reader = csv.DictReader(f, delimiter=delimiter)
        norm = []
        for r in reader:
            try:
                # Spalten-Aliasse unterstützen (DE/EN)
                def col(rdict, *names, default=""):
                    for n in names:
                        if n in rdict:
                            return rdict.get(n, default)
                    # Suche auch case-insensitive
                    lower = {k.lower(): v for k, v in rdict.items()}
                    for n in names:
                        if n.lower() in lower:
                            return lower[n.lower()]
                    return default
                # Rohwerte
                d_raw = col(r, "date", "datum", default="")
                ex_raw = col(r, "exercise", "übung", "uebung", default="")
                w_raw = col(r, "weight", "gewicht", default=0)
                reps_raw = col(r, "reps", "wiederholungen", default=0)
                sets_raw = col(r, "sets", "sätze", "saetze", default=0)
                # Normalisieren
                d = str(d_raw or "").strip()
                ex = str(ex_raw or "").strip()
                # Zahl-Konvertierung robust (unterstützt Dezimal-Komma)
                def to_float(val):
                    s = str(val or 0).strip().replace(".", ".").replace(",", ".")
                    try:
                        return float(s)
                    except Exception:
                        return 0.0
                def to_int(val):
                    s = str(val or 0).strip()
                    try:
                        return int(float(s.replace(",", ".")))
                    except Exception:
                        return 0
                w = to_float(w_raw)
                rp = to_int(reps_raw)
                st = to_int(sets_raw)
                if not d:
                    # Überspringe Einträge ohne Datum
                    continue
                norm.append({
                    "date": d,
                    "exercise": ex,
                    "weight": w,
                    "reps": rp,
                    "sets": st,
                })
            except Exception:
                # Überspringe fehlerhafte Zeilen
                pass
        return norm
    except Exception:
        return []


"""--- Entfernt: ältere, aggregierende _fortschritt_lv-Variante (Duplikat) ---"""

def schreibe_eintrag_csv(entry: Dict, profil: str | None = None) -> None:
    _init_datenspeicher()
    p = profil or aktuelles_profil
    file = _profil_datei(p)
    file_exists = file.exists()
    file.parent.mkdir(parents=True, exist_ok=True)
    with file.open("a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "date": entry.get("date", ""),
            "exercise": entry.get("exercise", ""),
            "weight": entry.get("weight", 0),
            "reps": entry.get("reps", 0),
            "sets": entry.get("sets", 0),
        })


# ---------------- Profil-Info (JSON) + Kalorien-Berechnung ----------------

def lade_profil_info(profil: str | None = None) -> Dict | None:
    p = profil or aktuelles_profil
    datei = _profil_info_datei(p)
    if not datei.exists():
        return None
    try:
        with datei.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def speichere_profil_info(info: Dict, profil: str | None = None) -> None:
    p = profil or aktuelles_profil
    datei = _profil_info_datei(p)
    datei.parent.mkdir(parents=True, exist_ok=True)
    with datei.open("w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)


def _aktivitaetsfaktor(level: str) -> float:
    mapping = {
        "Sitzend": 1.2,
        "Leicht aktiv": 1.375,
        "Mäßig aktiv": 1.55,
        "Sehr aktiv": 1.725,
        "Extrem aktiv": 1.9,
    }
    return mapping.get(level, 1.2)


def _ziel_delta_kcal(ziel: str) -> int:
    mapping = {
        "Abnehmen -0.5 kg/Woche": -500,
        "Abnehmen -0.25 kg/Woche": -250,
        "Gewicht halten": 0,
        "Zunehmen +0.25 kg/Woche": 250,
        "Zunehmen +0.5 kg/Woche": 500,
    }
    return mapping.get(ziel, 0)


def berechne_kcal(info: Dict) -> Dict:
    alter = int(info.get("alter", 0) or 0)
    geschlecht = str(info.get("geschlecht", "m")).lower()
    groesse_cm = float(info.get("groesse_cm", 0) or 0.0)
    gewicht_kg = float(info.get("gewicht_kg", 0) or 0.0)
    aktivitaet = str(info.get("aktivitaet", "Sitzend"))
    ziel = str(info.get("ziel", "Gewicht halten"))

    if geschlecht.startswith("w"):
        bmr = 10 * gewicht_kg + 6.25 * groesse_cm - 5 * alter - 161
    else:
        bmr = 10 * gewicht_kg + 6.25 * groesse_cm - 5 * alter + 5
    faktor = _aktivitaetsfaktor(aktivitaet)
    tdee = bmr * faktor
    delta = _ziel_delta_kcal(ziel)
    ziel_kcal = tdee + delta
    return {
        "bmr": round(bmr),
        "tdee": round(tdee),
        "ziel_kcal": round(ziel_kcal),
        "ziel_delta": delta,
    }


def lade_kcal_map(profil: str | None = None) -> Dict[str, int]:
    p = profil or aktuelles_profil
    datei = _kcal_datei(p)
    if not datei.exists():
        return {}
    try:
        with datei.open("r", encoding="utf-8") as f:
            data = json.load(f)
            return {str(k): int(v) for k, v in data.items()}
    except Exception:
        return {}


def speichere_kcal_map(d: Dict[str, int], profil: str | None = None) -> None:
    p = profil or aktuelles_profil
    datei = _kcal_datei(p)
    datei.parent.mkdir(parents=True, exist_ok=True)
    with datei.open("w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)


def _heute_str() -> str:
    try:
        from datetime import date as _date
        return str(_date.today())
    except Exception:
        return ""


def add_kcal_heute(kcal: int, profil: str | None = None) -> None:
    if kcal <= 0:
        return
    d = lade_kcal_map(profil)
    key = _heute_str()
    d[key] = int(d.get(key, 0)) + int(kcal)
    speichere_kcal_map(d, profil)

def _fortschritt_lv(uebung: str | None = None) -> dict:
    """Vergleicht den neuesten Eintrag mit dem vorherigen (einfaches Modell).

    Leistungswert pro Eintrag: gewicht * wiederholungen.
    Optional: Nur Einträge einer bestimmten Übung berücksichtigen.
    """
    eintraege = lade_log(aktuelles_profil)
    if not eintraege:
        return {"hinweis": "Keine Einträge vorhanden."}

    # Reihenfolge beibehalten wie in CSV; optional nach Übung filtern
    seq = []
    for e in eintraege:
        if uebung:
            ex = str(e.get("exercise", "") or "").strip().lower()
            if ex != uebung.strip().lower():
                continue
        try:
            gewicht = float(e.get("weight", 0) or 0)
            reps = int(e.get("reps", 0) or 0)
        except Exception:
            gewicht = 0.0
            reps = 0
        lv = gewicht * reps
        datum = str(e.get("date") or "").strip()
        seq.append((datum, lv))

    if len(seq) < 2:
        return {"hinweis": "Zu wenig historische Einträge für Vergleich."}

    # Neuesten und vorherigen Eintrag: wir nehmen die letzten zwei aus der Sequenz
    aktuelles_datum, aktueller_lv = seq[-1]
    vorheriges_datum, vorheriger_lv = seq[-2]
    delta = aktueller_lv - vorheriger_lv

    return {
        "aktuelles_datum": aktuelles_datum,
        "aktueller_lv": aktueller_lv,
        "vorheriges_datum": vorheriges_datum,
        "avg_vor3": vorheriger_lv,  # Für Anzeige nutzen wir den direkten vorherigen Wert
        "delta": delta,
        "anzahl_vergleich": 1,
    }


#Liste von Einträgen
log: List[Dict] = []  # alle Trainingseinträge solange Programm läuft


def eintrag_hinzufuegen(date: str, exercise: str, weight_kg: float, reps: int, sets: int) -> None:
    #Fügt einen Trainingseintrag in die Liste
    #Felder: Datum, Übung, Gewicht, Wiederholungen, Sätze
    entry = {
        "date": date,                # Datum als String
        "exercise": exercise,        # Name der Übung
        "weight": float(weight_kg),  # Gewicht als float
        "reps": int(reps),           # Wiederholungen als int
        "sets": int(sets),           # Sätze als int
    }
    log.append(entry)
    schreibe_eintrag_csv(entry)


def letzter_eintrag(n: int = 10) -> List[Dict]:
    #gibt die letzten n Einträge zurück
    #schneidet die letzten n Elemente und kehren sie um damit neueste zuerst
    return log[-n:][::-1]


def fortschritt(uebung: str | None = None) -> Dict:
    # Delegiert auf neue Leistungswert-basierte Fortschrittsberechnung
    return _fortschritt_lv(uebung)


# ---------------------- Tkinter GUI ----------------------

class LogbuchApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Trainings-Logbuch (CSV)")

        # Haupt-Container
        container = ttk.Frame(root, padding=10)
        container.grid(row=0, column=0, sticky="nsew")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        # Profil-Bereich (nur ein Profil; Name fest, Bearbeiten erlaubt)
        profil_frame = ttk.LabelFrame(container, text="Profil", padding=10)
        profil_frame.grid(row=0, column=0, sticky="ew")
        profil_frame.columnconfigure(1, weight=1)
        ttk.Label(profil_frame, text="Name:").grid(row=0, column=0, sticky="w")
        self.var_profil_name = tk.StringVar(value=aktuelles_profil)
        self.lbl_profil_name = ttk.Label(profil_frame, textvariable=self.var_profil_name)
        self.lbl_profil_name.grid(row=0, column=1, sticky="w")
        ttk.Button(profil_frame, text="Profil bearbeiten", command=self._on_profil_bearbeiten).grid(row=0, column=2, sticky="e")

        # Formular
        form = ttk.LabelFrame(container, text="Neuer Eintrag", padding=10)
        form.grid(row=1, column=0, sticky="ew")
        for i in range(8):
            form.columnconfigure(i, weight=1)

        ttk.Label(form, text="Datum (YYYY-MM-DD)").grid(row=0, column=0, sticky="w")
        self.var_date = tk.StringVar()
        self.entry_date = ttk.Entry(form, textvariable=self.var_date, width=18)
        self.entry_date.grid(row=1, column=0, sticky="ew", padx=(0, 8))

        ttk.Label(form, text="Übung").grid(row=0, column=1, sticky="w")
        self.var_exercise = tk.StringVar()
        self.entry_exercise = ttk.Entry(form, textvariable=self.var_exercise)
        self.entry_exercise.grid(row=1, column=1, sticky="ew", padx=(0, 8))

        ttk.Label(form, text="Gewicht (kg)").grid(row=0, column=2, sticky="w")
        self.var_weight = tk.StringVar()
        self.entry_weight = ttk.Entry(form, textvariable=self.var_weight, width=10)
        self.entry_weight.grid(row=1, column=2, sticky="ew", padx=(0, 8))

        ttk.Label(form, text="Wdh").grid(row=0, column=3, sticky="w")
        self.var_reps = tk.StringVar()
        self.entry_reps = ttk.Entry(form, textvariable=self.var_reps, width=8)
        self.entry_reps.grid(row=1, column=3, sticky="ew", padx=(0, 8))

        ttk.Label(form, text="Sätze").grid(row=0, column=4, sticky="w")
        self.var_sets = tk.StringVar()
        self.entry_sets = ttk.Entry(form, textvariable=self.var_sets, width=8)
        self.entry_sets.grid(row=1, column=4, sticky="ew", padx=(0, 8))

        btn_save = ttk.Button(form, text="Eintrag speichern", command=self.aktion_speichern)
        btn_save.grid(row=1, column=5, sticky="ew", padx=(8, 0))

        btn_csv = ttk.Button(form, text="CSV öffnen", command=self.aktion_csv_oeffnen)
        btn_csv.grid(row=1, column=6, sticky="ew", padx=(8, 0))

        btn_progress = ttk.Button(form, text="Fortschritt", command=self.aktion_fortschritt)
        btn_progress.grid(row=1, column=7, sticky="ew", padx=(8, 0))

        # Kalorien-Ziel Anzeige
        ziel_frame = ttk.Frame(container, padding=(0, 6, 0, 0))
        ziel_frame.grid(row=2, column=0, sticky="ew")
        self.lbl_kcal = ttk.Label(ziel_frame, text="Kalorienziel: — (BMR — | TDEE —)")
        self.lbl_kcal.grid(row=0, column=0, sticky="w")
        # Eingabe für heutige Kalorien + Status
        ttk.Label(ziel_frame, text="Kcal heute:").grid(row=0, column=1, padx=(12, 4), sticky="e")
        self.var_kcal = tk.StringVar()
        ttk.Entry(ziel_frame, textvariable=self.var_kcal, width=8).grid(row=0, column=2, sticky="w")
        ttk.Button(ziel_frame, text="Speichern", command=self.aktion_kcal_speichern).grid(row=0, column=3, padx=(6, 0))
        self.lbl_kcal_status = ttk.Label(ziel_frame, text="—")
        self.lbl_kcal_status.grid(row=0, column=4, padx=(12, 0), sticky="w")

        # Tabelle
        table_frame = ttk.LabelFrame(container, text="Einträge (neueste zuerst)", padding=10)
        table_frame.grid(row=3, column=0, sticky="nsew", pady=(10, 0))
        container.rowconfigure(3, weight=1)

        columns = ("date", "exercise", "weight", "reps", "sets")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=12)
        self.tree.heading("date", text="Datum")
        self.tree.heading("exercise", text="Übung")
        self.tree.heading("weight", text="Gewicht (kg)")
        self.tree.heading("reps", text="Wdh")
        self.tree.heading("sets", text="Sätze")
        self.tree.column("date", width=120)
        self.tree.column("exercise", width=160)
        self.tree.column("weight", width=100, anchor="e")
        self.tree.column("reps", width=60, anchor="e")
        self.tree.column("sets", width=60, anchor="e")
        self.tree.grid(row=0, column=0, sticky="nsew")

        # Scrollbar
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.grid(row=0, column=1, sticky="ns")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        # Initiale Werte
        self.datum_vorbelegen()
        # Onboarding beim ersten Start (wenn keine Profile existieren)
        self._onboarding_if_needed()
        self.var_profil_name.set(aktuelles_profil)
        self.tabelle_aktualisieren()
        self._update_kcal_label()

    def _onboarding_if_needed(self) -> None:
        # Wenn keine Profile existieren: einmaliger Dialog inkl. Name + Daten
        vorhandene = profil_liste()
        if vorhandene:
            # Wähle erstes Profil als aktiv
            global aktuelles_profil
            aktuelles_profil = vorhandene[0]
            return

        win = tk.Toplevel(self.root)
        win.title("Profil anlegen")
        win.transient(self.root)
        win.grab_set()

        pad = dict(padx=8, pady=4, sticky="ew")
        frm = ttk.Frame(win, padding=10)
        frm.grid(row=0, column=0, sticky="nsew")
        for i in range(2):
            frm.columnconfigure(i, weight=1)

        ttk.Label(frm, text="Profilname").grid(row=0, column=0, **pad)
        var_name = tk.StringVar()
        ttk.Entry(frm, textvariable=var_name).grid(row=0, column=1, **pad)

        # Reuse Felder aus Profil bearbeiten
        ttk.Label(frm, text="Alter (Jahre)").grid(row=1, column=0, **pad)
        var_alter = tk.StringVar()
        ttk.Entry(frm, textvariable=var_alter).grid(row=1, column=1, **pad)

        ttk.Label(frm, text="Geschlecht").grid(row=2, column=0, **pad)
        var_geschl = tk.StringVar(value="m")
        ttk.Combobox(frm, textvariable=var_geschl, values=["m", "w"], state="readonly").grid(row=2, column=1, **pad)

        ttk.Label(frm, text="Größe (cm)").grid(row=3, column=0, **pad)
        var_groesse = tk.StringVar()
        ttk.Entry(frm, textvariable=var_groesse).grid(row=3, column=1, **pad)

        ttk.Label(frm, text="Gewicht (kg)").grid(row=4, column=0, **pad)
        var_gewicht = tk.StringVar()
        ttk.Entry(frm, textvariable=var_gewicht).grid(row=4, column=1, **pad)

        ttk.Label(frm, text="Aktivität").grid(row=5, column=0, **pad)
        var_akt = tk.StringVar(value="Sitzend")
        ttk.Combobox(frm, textvariable=var_akt, values=["Sitzend", "Leicht aktiv", "Mäßig aktiv", "Sehr aktiv", "Extrem aktiv"], state="readonly").grid(row=5, column=1, **pad)

        ttk.Label(frm, text="Ziel").grid(row=6, column=0, **pad)
        var_ziel = tk.StringVar(value="Gewicht halten")
        ttk.Combobox(frm, textvariable=var_ziel, values=["Abnehmen -0.5 kg/Woche", "Abnehmen -0.25 kg/Woche", "Gewicht halten", "Zunehmen +0.25 kg/Woche", "Zunehmen +0.5 kg/Woche"], state="readonly").grid(row=6, column=1, **pad)

        def speichern():
            name = _bereinige_profilname(var_name.get())
            if not name:
                messagebox.showerror("Fehler", "Profilname darf nicht leer sein.")
                return
            if name in set(profil_liste()):
                messagebox.showerror("Fehler", "Profil existiert bereits.")
                return
            try:
                info = {
                    "alter": int(var_alter.get().strip()),
                    "geschlecht": var_geschl.get().strip().lower() or "m",
                    "groesse_cm": float(var_groesse.get().strip()),
                    "gewicht_kg": float(var_gewicht.get().strip()),
                    "aktivitaet": var_akt.get().strip(),
                    "ziel": var_ziel.get().strip(),
                }
            except Exception:
                messagebox.showerror("Fehler", "Bitte gültige Zahlen für Alter, Größe und Gewicht eingeben.")
                return
            # Dateien anlegen
            csv_datei = _profil_datei(name)
            csv_datei.parent.mkdir(parents=True, exist_ok=True)
            with csv_datei.open("w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=HEADERS)
                writer.writeheader()
            speichere_profil_info(info, profil=name)

            # aktiv setzen und UI aktualisieren
            global aktuelles_profil
            aktuelles_profil = name
            self.var_profil_name.set(name)
            self.tabelle_aktualisieren()
            self._update_kcal_label()
            win.destroy()

        btns = ttk.Frame(win, padding=(10, 0, 10, 10))
        btns.grid(row=1, column=0, sticky="e")
        ttk.Button(btns, text="Speichern", command=speichern).grid(row=0, column=1)

    def _update_kcal_label(self) -> None:
        info = lade_profil_info()
        if not info:
            self.lbl_kcal.config(text="Kalorienziel: — (BMR — | TDEE —)")
            self.lbl_kcal_status.config(text="—")
            return
        daten = berechne_kcal(info)
        self.lbl_kcal.config(text=f"Kalorienziel: {daten['ziel_kcal']} kcal (BMR {daten['bmr']} | TDEE {daten['tdee']})")
        # Status berechnen
        try:
            ziel = int(daten.get("ziel_kcal", 0))
        except Exception:
            ziel = 0
        kcal_map = lade_kcal_map()
        heute = _heute_str()
        gegessen = int(kcal_map.get(heute, 0))
        diff = ziel - gegessen
        if ziel <= 0:
            self.lbl_kcal_status.config(text="—")
        else:
            if diff >= 0:
                self.lbl_kcal_status.config(text=f"Unter Ziel (frei {diff} kcal)", foreground="#0a7d00")
            elif -diff <= 200:
                self.lbl_kcal_status.config(text=f"Leicht drüber (+{-diff} kcal)", foreground="#ca8a04")
            else:
                self.lbl_kcal_status.config(text=f"Drüber (+{-diff} kcal)", foreground="#b91c1c")

    def aktion_kcal_speichern(self) -> None:
        val = self.var_kcal.get().strip()
        try:
            kcal = int(float(val))
        except Exception:
            messagebox.showerror("Fehler", "Bitte eine gültige Zahl für Kalorien eingeben.")
            return
        if kcal <= 0:
            messagebox.showerror("Fehler", "Der Wert muss größer als 0 sein.")
            return
        add_kcal_heute(kcal)
        self.var_kcal.set("")
        self._update_kcal_label()

    def _on_profil_bearbeiten(self) -> None:
        # Einfacher Dialog als Toplevel mit Formularfeldern
        win = tk.Toplevel(self.root)
        win.title("Profil bearbeiten")
        win.transient(self.root)
        win.grab_set()

        pad = dict(padx=8, pady=4, sticky="ew")
        frm = ttk.Frame(win, padding=10)
        frm.grid(row=0, column=0, sticky="nsew")
        for i in range(2):
            frm.columnconfigure(i, weight=1)

        info_alt = lade_profil_info() or {}

        ttk.Label(frm, text="Alter (Jahre)").grid(row=0, column=0, **pad)
        var_alter = tk.StringVar(value=str(info_alt.get("alter", "")))
        ttk.Entry(frm, textvariable=var_alter).grid(row=0, column=1, **pad)

        ttk.Label(frm, text="Geschlecht").grid(row=1, column=0, **pad)
        var_geschl = tk.StringVar(value=str(info_alt.get("geschlecht", "m")).lower())
        cb_geschl = ttk.Combobox(frm, textvariable=var_geschl, values=["m", "w"], state="readonly")
        cb_geschl.grid(row=1, column=1, **pad)

        ttk.Label(frm, text="Größe (cm)").grid(row=2, column=0, **pad)
        var_groesse = tk.StringVar(value=str(info_alt.get("groesse_cm", "")))
        ttk.Entry(frm, textvariable=var_groesse).grid(row=2, column=1, **pad)

        ttk.Label(frm, text="Gewicht (kg)").grid(row=3, column=0, **pad)
        var_gewicht = tk.StringVar(value=str(info_alt.get("gewicht_kg", "")))
        ttk.Entry(frm, textvariable=var_gewicht).grid(row=3, column=1, **pad)

        ttk.Label(frm, text="Aktivität").grid(row=4, column=0, **pad)
        var_akt = tk.StringVar(value=str(info_alt.get("aktivitaet", "Sitzend")))
        cb_akt = ttk.Combobox(frm, textvariable=var_akt, values=["Sitzend", "Leicht aktiv", "Mäßig aktiv", "Sehr aktiv", "Extrem aktiv"], state="readonly")
        cb_akt.grid(row=4, column=1, **pad)

        ttk.Label(frm, text="Ziel").grid(row=5, column=0, **pad)
        var_ziel = tk.StringVar(value=str(info_alt.get("ziel", "Gewicht halten")))
        cb_ziel = ttk.Combobox(frm, textvariable=var_ziel, values=["Abnehmen -0.5 kg/Woche", "Abnehmen -0.25 kg/Woche", "Gewicht halten", "Zunehmen +0.25 kg/Woche", "Zunehmen +0.5 kg/Woche"], state="readonly")
        cb_ziel.grid(row=5, column=1, **pad)

        def speichern():
            try:
                info = {
                    "alter": int(var_alter.get().strip()),
                    "geschlecht": var_geschl.get().strip().lower() or "m",
                    "groesse_cm": float(var_groesse.get().strip()),
                    "gewicht_kg": float(var_gewicht.get().strip()),
                    "aktivitaet": var_akt.get().strip(),
                    "ziel": var_ziel.get().strip(),
                }
            except Exception:
                messagebox.showerror("Fehler", "Bitte gültige Zahlen für Alter, Größe und Gewicht eingeben.")
                return
            speichere_profil_info(info)
            self._update_kcal_label()
            win.destroy()

        btns = ttk.Frame(win, padding=(10, 0, 10, 10))
        btns.grid(row=1, column=0, sticky="e")
        ttk.Button(btns, text="Abbrechen", command=win.destroy).grid(row=0, column=0, padx=6)
        ttk.Button(btns, text="Speichern", command=speichern).grid(row=0, column=1)

    def datum_vorbelegen(self) -> None:
        try:
            from datetime import date as _date
            self.var_date.set(str(_date.today()))
        except Exception:
            self.var_date.set("")

    def aktion_speichern(self) -> None:
        date = self.var_date.get().strip()
        exercise = self.var_exercise.get().strip()
        try:
            weight = float(self.var_weight.get().strip())
            reps = int(self.var_reps.get().strip())
            sets = int(self.var_sets.get().strip())
        except Exception:
            messagebox.showerror("Fehler", "Ungültige Zahl bei Gewicht/Wdh/Sätze.")
            return

        if not date or not exercise:
            messagebox.showerror("Fehler", "Datum oder Übung darf nicht leer sein.")
            return

        eintrag_hinzufuegen(date=date, exercise=exercise, weight_kg=weight, reps=reps, sets=sets)
        self.tabelle_aktualisieren()
        # Felder (außer Datum) leeren
        self.var_exercise.set("")
        self.var_weight.set("")
        self.var_reps.set("")
        self.var_sets.set("")
        self.entry_exercise.focus_set()

    def tabelle_aktualisieren(self) -> None:
        # Einträge neu laden (aus CSV), neueste zuerst anzeigen
        all_entries = lade_log()
        log[:] = all_entries  # in-memory synchron halten
        for i in self.tree.get_children():
            self.tree.delete(i)
        # zeige die letzten 50
        for e in reversed(all_entries[-50:]):
            self.tree.insert("", "end", values=(
                e.get("date", ""),
                e.get("exercise", ""),
                e.get("weight", 0),
                e.get("reps", 0),
                e.get("sets", 0),
            ))

    def aktion_fortschritt(self):
        # Optional: Übungsname abfragen und danach filtern
        try:
            import tkinter.simpledialog as sd
            uebung = sd.askstring("Fortschritt filtern", "Übungsname (leer = alle):", parent=self.root)
        except Exception:
            uebung = None
        info = fortschritt(uebung if (uebung and uebung.strip()) else None)
        msg = []
        if "hinweis" in info:
            msg.append(info["hinweis"])
        else:
            msg.append("Leistungswert (Gewicht × Wiederholungen)")
            title_line = f"Aktuelles Training ({info['aktuelles_datum']})"
            if uebung and uebung.strip():
                title_line += f" – Übung: {uebung.strip()}"
            msg.append(f"{title_line}: {info['aktueller_lv']:.1f}")
            if info["anzahl_vergleich"] > 0:
                avg_line = "Vergleich mit vorherigem Training"
                if info.get("vorheriges_datum"):
                    avg_line += f" ({info['vorheriges_datum']})"
                if uebung and uebung.strip():
                    avg_line += f" – Übung: {uebung.strip()}"
                avg_line += f": {info['avg_vor3']:.1f}"
                msg.append(avg_line)
                diff = info["delta"]
                betrag = abs(diff)
                if diff > 0:
                    msg.append(f"Steigerung: {betrag:.1f}")
                elif diff < 0:
                    msg.append(f"Verschlechterung: {betrag:.1f}")
                else:
                    msg.append("Keine Veränderung gegenüber dem Durchschnitt.")
            else:
                msg.append("Zu wenig historische Trainings für Vergleich.")

        # Kalorienziel-Info
        info_profil = lade_profil_info(aktuelles_profil)
        kcal_text = ""
        if info_profil:
            kcal_info = berechne_kcal(info_profil)
            kcal_text = (
                f"\n\nKalorien: BMR {kcal_info['bmr']:.0f}, TDEE {kcal_info['tdee']:.0f}, Ziel {kcal_info['ziel_kcal']:.0f} kcal"
            )
        messagebox.showinfo("Fortschritt", "\n".join(msg) + kcal_text)

    def aktion_csv_oeffnen(self) -> None:
        try:
            datei = _profil_datei(aktuelles_profil)
            if not datei.exists():
                with datei.open("w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.DictWriter(f, fieldnames=HEADERS)
                    writer.writeheader()
            if sys.platform.startswith("win"):
                os.startfile(str(datei))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(datei)])
            else:
                subprocess.Popen(["xdg-open", str(datei)])
        except Exception as e:
            messagebox.showerror("Fehler", f"Konnte CSV nicht öffnen: {e}")


# starte die GUI, wenn Datei direkt ausgeführt wird
if __name__ == "__main__":
    # Datenordner sicherstellen
    _init_datenspeicher()
    # Noch kein Profil? GUI-Onboarding übernimmt die Anlage beim Start.
    # Falls Profile vorhanden sind, wird das erste im GUI gesetzt.
    log[:] = []
    root = tk.Tk()
    # Windows: etwas freundlichere Standard-Theme, falls verfügbar
    try:
        style = ttk.Style()
        if "vista" in style.theme_names():
            style.theme_use("vista")
    except Exception:
        pass
    app = LogbuchApp(root)
    root.mainloop()

# Kompatibilitäts-Aliasse für ältere Namen
def load_log(profil: str | None = None):
    return lade_log(profil)

def append_entry_csv(entry: Dict, profil: str | None = None):
    return schreibe_eintrag_csv(entry, profil)

def eintrag(date: str, exercise: str, weight_kg: float, reps: int, sets: int):
    return eintrag_hinzufuegen(date, exercise, weight_kg, reps, sets)