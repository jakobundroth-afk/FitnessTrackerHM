import tkinter as tk
from tkinter import ttk, messagebox
import datetime
from app import USER_FILE, MEALS_FILE, TRAINING_FILE, load_json, save_json

# Lokale kcal/100g Tabelle (rein Python)
KCAL_PER_100G = {
    'apfel': 52,
    'banane': 89,
    'haferflocken': 379,
    'brot': 265,
    'ei': 155,
    'hähnchenbrust gekocht': 165,
    'reis gekocht': 130,
    'nudeln gekocht': 131,
}


def kcal_for_grams(name: str, grams: float):
    n = name.strip().lower()
    per100 = KCAL_PER_100G.get(n)
    if per100 is None:
        return None
    return round(per100 * grams / 100.0, 1)


class FitnessAppGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FitnessTrackerHM GUI")
        self.geometry("700x520")

        nb = ttk.Notebook(self)
        nb.pack(fill=tk.BOTH, expand=True)

        self.tab_dashboard = ttk.Frame(nb)
        self.tab_profile = ttk.Frame(nb)
        self.tab_meal = ttk.Frame(nb)
        self.tab_training = ttk.Frame(nb)
        self.tab_progress = ttk.Frame(nb)

        nb.add(self.tab_dashboard, text="Dashboard")
        nb.add(self.tab_profile, text="Profil")
        nb.add(self.tab_meal, text="Mahlzeit")
        nb.add(self.tab_training, text="Training")
        nb.add(self.tab_progress, text="Fortschritt")

        self.build_dashboard()
        self.build_profile()
        self.build_meal()
        self.build_training()
        self.build_progress()

        self.refresh_dashboard()
        self.refresh_training_list()
        self.refresh_progress()

    # ---------- Dashboard ----------
    def build_dashboard(self):
        frm = self.tab_dashboard
        self.lbl_target = ttk.Label(frm, text="Ziel Kalorien: -")
        self.lbl_target.pack(anchor=tk.W, padx=12, pady=8)
        self.lbl_consumed = ttk.Label(frm, text="Konsumiert heute: -")
        self.lbl_consumed.pack(anchor=tk.W, padx=12, pady=8)
        self.lbl_remaining = ttk.Label(frm, text="Verbleibend: -")
        self.lbl_remaining.pack(anchor=tk.W, padx=12, pady=8)

        btn = ttk.Button(frm, text="Aktualisieren", command=self.refresh_dashboard)
        btn.pack(anchor=tk.W, padx=12, pady=12)

    def refresh_dashboard(self):
        profile = load_json(USER_FILE, None)
        meals = load_json(MEALS_FILE, [])
        today = datetime.date.today().isoformat()
        consumed = sum(e['totals']['kcal'] for e in meals if e.get('time','').startswith(today))
        target = profile['daily_calorie_target'] if profile else 0
        remaining = round(target - consumed, 1)
        self.lbl_target.config(text=f"Ziel Kalorien: {target}")
        self.lbl_consumed.config(text=f"Konsumiert heute: {consumed}")
        self.lbl_remaining.config(text=f"Verbleibend: {remaining}")

    # ---------- Profil ----------
    def build_profile(self):
        frm = self.tab_profile
        grid = ttk.Frame(frm)
        grid.pack(fill=tk.X, padx=12, pady=12)

        def add_row(row, label):
            ttk.Label(grid, text=label).grid(row=row, column=0, sticky=tk.W, padx=6, pady=6)

        add_row(0, "Alter")
        add_row(1, "Geschlecht (m/f)")
        add_row(2, "Größe (cm)")
        add_row(3, "Gewicht (kg)")
        add_row(4, "Aktivität (1.2-1.725)")
        add_row(5, "Ziel (lose/halten/gain)")

        self.var_age = tk.StringVar()
        self.var_sex = tk.StringVar()
        self.var_height = tk.StringVar()
        self.var_weight = tk.StringVar()
        self.var_activity = tk.StringVar()
        self.var_goal = tk.StringVar()

        ttk.Entry(grid, textvariable=self.var_age).grid(row=0, column=1, padx=6, pady=6)
        ttk.Entry(grid, textvariable=self.var_sex).grid(row=1, column=1, padx=6, pady=6)
        ttk.Entry(grid, textvariable=self.var_height).grid(row=2, column=1, padx=6, pady=6)
        ttk.Entry(grid, textvariable=self.var_weight).grid(row=3, column=1, padx=6, pady=6)
        ttk.Entry(grid, textvariable=self.var_activity).grid(row=4, column=1, padx=6, pady=6)
        ttk.Entry(grid, textvariable=self.var_goal).grid(row=5, column=1, padx=6, pady=6)

        ttk.Button(frm, text="Profil laden", command=self.load_profile).pack(anchor=tk.W, padx=12, pady=8)
        ttk.Button(frm, text="Profil speichern", command=self.save_profile).pack(anchor=tk.W, padx=12, pady=8)

    def load_profile(self):
        prof = load_json(USER_FILE, None)
        if not prof:
            messagebox.showinfo("Profil", "Kein Profil vorhanden.")
            return
        self.var_age.set(str(prof.get('age','')))
        self.var_sex.set(str(prof.get('sex','')))
        self.var_height.set(str(prof.get('height_cm','')))
        self.var_weight.set(str(prof.get('weight_kg','')))
        self.var_activity.set(str(prof.get('activity_factor','')))
        self.var_goal.set(str(prof.get('goal','')))

    def save_profile(self):
        try:
            age = int(self.var_age.get())
            sex = self.var_sex.get().strip().lower()
            height = float(self.var_height.get())
            weight = float(self.var_weight.get())
            activity = float(self.var_activity.get())
            goal = self.var_goal.get().strip().lower()
        except Exception:
            messagebox.showerror("Fehler", "Bitte gültige Werte eingeben.")
            return
        if sex == 'm':
            bmr = 10*weight + 6.25*height - 5*age + 5
        else:
            bmr = 10*weight + 6.25*height - 5*age - 161
        tdee = bmr * activity
        if goal in ('lose','abnehmen'):
            daily = tdee - 500
        elif goal in ('gain','zunehmen'):
            daily = tdee + 300
        else:
            daily = tdee
        profile = {
            'age': age,
            'sex': sex,
            'height_cm': height,
            'weight_kg': weight,
            'activity_factor': activity,
            'goal': goal,
            'bmr': round(bmr,1),
            'tdee': round(tdee,1),
            'daily_calorie_target': round(daily,1)
        }
        save_json(USER_FILE, profile)
        messagebox.showinfo("Profil", "Profil gespeichert.")
        self.refresh_dashboard()

    # ---------- Mahlzeit ----------
    def build_meal(self):
        frm = self.tab_meal
        ttk.Label(frm, text="Gericht").pack(anchor=tk.W, padx=12, pady=6)
        self.var_dish = tk.StringVar()
        ttk.Entry(frm, textvariable=self.var_dish).pack(fill=tk.X, padx=12)

        ttk.Label(frm, text="Gramm").pack(anchor=tk.W, padx=12, pady=6)
        self.var_grams = tk.StringVar()
        ttk.Entry(frm, textvariable=self.var_grams).pack(fill=tk.X, padx=12)

        ttk.Button(frm, text="Speichern", command=self.save_meal).pack(anchor=tk.W, padx=12, pady=12)

    def save_meal(self):
        dish = self.var_dish.get().strip()
        grams_s = self.var_grams.get().strip()
        try:
            grams = float(grams_s)
        except Exception:
            messagebox.showerror("Fehler", "Gramm muss eine Zahl sein.")
            return
        if grams <= 0:
            messagebox.showerror("Fehler", "Gramm muss > 0 sein.")
            return
        kcal = kcal_for_grams(dish, grams)
        if kcal is None:
            messagebox.showwarning("Unbekannt", "Gericht nicht in kcal/100g Tabelle.")
            return
        meals = load_json(MEALS_FILE, [])
        now = datetime.datetime.now().isoformat(timespec='seconds')
        entry = {'time': now, 'items': [{'food': dish.lower(), 'qty': grams, 'kcal': kcal}], 'totals': {'kcal': kcal, 'protein':0,'fat':0,'carbs':0}}
        meals.append(entry)
        save_json(MEALS_FILE, meals)
        messagebox.showinfo("Mahlzeit", f"Gespeichert: {kcal} kcal für {grams} g {dish}")
        self.refresh_dashboard()

    # ---------- Training ----------
    def build_training(self):
        frm = self.tab_training
        grid = ttk.Frame(frm)
        grid.pack(fill=tk.X, padx=12, pady=12)

        def add_row(row, label):
            ttk.Label(grid, text=label).grid(row=row, column=0, sticky=tk.W, padx=6, pady=6)

        add_row(0, "Übung")
        add_row(1, "Gewicht")
        add_row(2, "Wiederholungen")
        add_row(3, "Sätze")

        self.var_exercise = tk.StringVar()
        self.var_weight = tk.StringVar()
        self.var_reps = tk.StringVar()
        self.var_sets = tk.StringVar()

        ttk.Entry(grid, textvariable=self.var_exercise).grid(row=0, column=1, padx=6, pady=6)
        ttk.Entry(grid, textvariable=self.var_weight).grid(row=1, column=1, padx=6, pady=6)
        ttk.Entry(grid, textvariable=self.var_reps).grid(row=2, column=1, padx=6, pady=6)
        ttk.Entry(grid, textvariable=self.var_sets).grid(row=3, column=1, padx=6, pady=6)

        ttk.Button(frm, text="Training speichern", command=self.save_training).pack(anchor=tk.W, padx=12, pady=8)

        self.list_training = tk.Listbox(frm, height=10)
        self.list_training.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

    def save_training(self):
        try:
            exercise = self.var_exercise.get().strip()
            weight = float(self.var_weight.get())
            reps = int(self.var_reps.get())
            sets = int(self.var_sets.get())
        except Exception:
            messagebox.showerror("Fehler", "Bitte gültige Trainingswerte eingeben.")
            return
        today = datetime.date.today()
        iso = today.isoformat()
        week = today.isocalendar().week
        data = load_json(TRAINING_FILE, [])
        entry = {'date': iso, 'week': week, 'exercise': exercise, 'weight': weight, 'reps': reps, 'sets': sets}
        data.append(entry)
        save_json(TRAINING_FILE, data)
        messagebox.showinfo("Training", "Training gespeichert.")
        self.refresh_training_list()

    def refresh_training_list(self):
        self.list_training.delete(0, tk.END)
        entries = load_json(TRAINING_FILE, [])[-10:][::-1]
        for e in entries:
            self.list_training.insert(tk.END, f"{e['date']} | {e['exercise']} | {e['weight']}kg x {e['reps']} ({e['sets']} Sätze)")

    # ---------- Fortschritt ----------
    def build_progress(self):
        frm = self.tab_progress
        self.lbl_w = ttk.Label(frm, text="Durchschn. Gewicht letzte 7: -")
        self.lbl_w.pack(anchor=tk.W, padx=12, pady=8)
        self.lbl_r = ttk.Label(frm, text="Durchschn. Wdh letzte 7: -")
        self.lbl_r.pack(anchor=tk.W, padx=12, pady=8)
        ttk.Button(frm, text="Aktualisieren", command=self.refresh_progress).pack(anchor=tk.W, padx=12, pady=12)

    def refresh_progress(self):
        data = load_json(TRAINING_FILE, [])
        if len(data) < 2:
            self.lbl_w.config(text="Nicht genug Einträge.")
            self.lbl_r.config(text="")
            return
        last7 = data[-7:]
        prev7 = data[-14:-7]
        def avg(field, entries):
            return round(sum(e[field] for e in entries)/len(entries),1) if entries else 0
        w_last = avg('weight', last7)
        w_prev = avg('weight', prev7)
        r_last = avg('reps', last7)
        r_prev = avg('reps', prev7)
        self.lbl_w.config(text=f"Durchschn. Gewicht letzte 7: {w_last} (vorher: {w_prev})")
        self.lbl_r.config(text=f"Durchschn. Wdh letzte 7: {r_last} (vorher: {r_prev})")


if __name__ == '__main__':
    app = FitnessAppGUI()
    app.mainloop()
