"""Flask Oberfläche mit sehr einfachen HTML-Formularen.
Der Benutzer kann direkt im Browser Profil und Trainingseinträge anlegen.
Keine komplexen Features, kein JavaScript.
Start: python flask_app.py  -> http://127.0.0.1:5020/
"""
from flask import Flask, render_template, request, redirect, url_for
import json, os, csv, datetime

PROFILE_FILE = 'user_profile.json'
TRAINING_FILE = 'training_log.csv'

app = Flask(__name__)

# ---------------- Datei-Helfer ----------------

def load_profile():
    if not os.path.exists(PROFILE_FILE):
        return None
    try:
        with open(PROFILE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None

def save_profile(data):
    with open(PROFILE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_training():
    entries = []
    if not os.path.exists(TRAINING_FILE):
        return entries
    try:
        with open(TRAINING_FILE, 'r', encoding='utf-8', newline='') as f:
            r = csv.DictReader(f)
            for row in r:
                try: row['weight'] = float(row.get('weight',0))
                except: row['weight'] = 0.0
                try: row['reps'] = int(row.get('reps',0))
                except: row['reps'] = 0
                try: row['sets'] = int(row.get('sets',0))
                except: row['sets'] = 0
                entries.append(row)
    except Exception:
        pass
    return entries

def append_training(entry):
    file_exists = os.path.exists(TRAINING_FILE)
    fields = ['date','week','exercise','weight','reps','sets']
    with open(TRAINING_FILE, 'a', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if not file_exists:
            w.writeheader()
        w.writerow(entry)

# ---------------- Logik ----------------

def compute_profile_extensions(p):
    if p is None: return None
    age = p.get('age'); sex = p.get('sex'); height = p.get('height_cm'); weight = p.get('weight_kg'); act = p.get('activity_factor'); goal = p.get('goal')
    if None in (age, sex, height, weight, act, goal):
        return p
    if sex == 'm':
        bmr = 10*weight + 6.25*height - 5*age + 5
    else:
        bmr = 10*weight + 6.25*height - 5*age - 161
    tdee = bmr * act
    if goal == 'abnehmen':
        daily = tdee - 500
    elif goal == 'zunehmen':
        daily = tdee + 300
    else:
        daily = tdee
    p['bmr'] = round(bmr,1)
    p['tdee'] = round(tdee,1)
    p['suggested_daily_calories'] = round(daily,1)
    return p

def calc_progress(entries):
    if len(entries) < 2:
        return {'enough': False}
    last14 = entries[-14:]
    last7 = last14[-7:]
    prev7 = last14[:-7]
    def avg(field, lst):
        if not lst: return 0.0
        s = 0.0
        for e in lst: s += e.get(field,0) or 0
        return s/len(lst)
    return {
        'enough': True,
        'avg_weight_last': round(avg('weight', last7),1),
        'avg_weight_prev': round(avg('weight', prev7),1),
        'avg_reps_last': round(avg('reps', last7),1),
        'avg_reps_prev': round(avg('reps', prev7),1),
    }

# ---------------- Routes ----------------

@app.route('/')
def dashboard():
    profile = compute_profile_extensions(load_profile())
    entries = load_training()
    progress = calc_progress(entries)
    return render_template('dashboard.html', profile=profile, entries=entries, progress=progress)

@app.route('/profil', methods=['POST'])
def profil():
    # Einfacher Formular-POST
    try:
        age = int(request.form.get('age'))
        sex = request.form.get('sex','').strip().lower()
        height = float(request.form.get('height_cm'))
        weight = float(request.form.get('weight_kg'))
        act = float(request.form.get('activity_factor'))
        goal = request.form.get('goal','').strip().lower()
    except Exception:
        return redirect(url_for('dashboard'))
    profile = {
        'age': age,
        'sex': sex,
        'height_cm': height,
        'weight_kg': weight,
        'activity_factor': act,
        'goal': goal
    }
    profile = compute_profile_extensions(profile)
    save_profile(profile)
    return redirect(url_for('dashboard'))

@app.route('/training', methods=['POST'])
def training():
    try:
        ex = request.form.get('exercise','').strip()
        w = float(request.form.get('weight'))
        r = int(request.form.get('reps'))
        s = int(request.form.get('sets'))
    except Exception:
        return redirect(url_for('dashboard'))
    if not ex:
        return redirect(url_for('dashboard'))
    today = datetime.date.today()
    entry = {
        'date': today.isoformat(),
        'week': today.isocalendar().week,
        'exercise': ex,
        'weight': w,
        'reps': r,
        'sets': s
    }
    append_training(entry)
    return redirect(url_for('dashboard'))

# ---------------- Main ----------------

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5020, debug=False)
