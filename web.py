from flask import Flask, request, redirect, render_template, url_for
import json, os, datetime
from app import USER_FILE, MEALS_FILE, TRAINING_FILE, FOOD_DB, load_json, save_json, parse_meal_input

# Zusätzliche einfache kcal/100g Tabelle (offline, nur Python)
KCAL_PER_100G = {
    'apfel': 52,
    'banane': 89,
    'haferflocken': 379,
    'brot': 265,
    'ei': 155,  # als Referenz pro 100g
    'hähnchenbrust gekocht': 165,
    'reis gekocht': 130,
    'nudeln gekocht': 131,
    'quark mager': 67,
    'joghurt natur': 60,
}

def kcal_for_grams(name: str, grams: float):
    n = name.strip().lower()
    if n not in KCAL_PER_100G:
        return None
    per100 = KCAL_PER_100G[n]
    return round(per100 * grams / 100.0, 1)

app = Flask(__name__)

@app.route('/')
def dashboard():
    profile = load_json(USER_FILE, None)
    meals = load_json(MEALS_FILE, [])
    today = datetime.date.today().isoformat()
    consumed = sum(e['totals']['kcal'] for e in meals if e['time'].startswith(today))
    if profile:
        target = profile['daily_calorie_target']
        remaining = round(target - consumed, 1)
    else:
        target = consumed = remaining = 0
    last_meals = meals[-5:][::-1]
    return render_template('dashboard.html', target=target, consumed=consumed, remaining=remaining, meals=last_meals)

@app.route('/profil', methods=['GET','POST'])
def profil():
    if request.method == 'POST':
        age = int(request.form['age'])
        sex = request.form['sex']
        height = float(request.form['height'])
        weight = float(request.form['weight'])
        activity = float(request.form['activity'])
        goal = request.form['goal']
        if sex == 'm':
            bmr = 10*weight + 6.25*height - 5*age + 5
        else:
            bmr = 10*weight + 6.25*height - 5*age - 161
        tdee = bmr * activity
        if goal == 'lose':
            daily = tdee - 500
        elif goal == 'gain':
            daily = tdee + 300
        else:
            daily = tdee
        profile = {'age':age,'sex':sex,'height_cm':height,'weight_kg':weight,'activity_factor':activity,'goal':goal,'bmr':round(bmr,1),'tdee':round(tdee,1),'daily_calorie_target':round(daily,1)}
        save_json(USER_FILE, profile)
        return redirect(url_for('profil'))
    profile = load_json(USER_FILE, None)
    return render_template('profil.html', profile=profile)

@app.route('/mahlzeit', methods=['GET','POST'])
def mahlzeit():
    msg = ''
    if request.method == 'POST':
        text = request.form.get('text','').strip()
        dish = request.form.get('dish','').strip()
        grams_str = request.form.get('grams','').strip()

        meals = load_json(MEALS_FILE, [])
        now = datetime.datetime.now().isoformat(timespec='seconds')
        total_entry = {'time': now, 'items': [], 'totals': {'kcal':0,'protein':0,'fat':0,'carbs':0}}

        # Modus A: Gericht + Gramm -> nur kcal Berechnung über Tabelle
        if dish and grams_str:
            try:
                grams = float(grams_str)
            except ValueError:
                grams = None
            if grams is None or grams <= 0:
                msg = 'Bitte gültige Gramm-Zahl angeben.'
            else:
                kcal_val = kcal_for_grams(dish, grams)
                if kcal_val is None:
                    msg = 'Gericht nicht in Tabelle. Bitte hinzufügen oder Freitext nutzen.'
                else:
                    total_entry['items'].append({'food': dish.lower(), 'qty': grams, 'kcal': kcal_val})
                    total_entry['totals']['kcal'] += kcal_val
                    meals.append(total_entry)
                    save_json(MEALS_FILE, meals)
                    msg = f"Gespeichert: {kcal_val} kcal für {grams} g {dish}"

        # Modus B: ursprünglicher Freitext Parser
        elif text:
            parsed = parse_meal_input(text)
            if parsed:
                for food, qty in parsed:
                    data = FOOD_DB.get(food)
                    if not data:
                        continue
                    item_totals = {k: data[k]*qty for k in data}
                    total_entry['items'].append({'food':food,'qty':qty, **item_totals})
                    for k in total_entry['totals']:
                        total_entry['totals'][k] += item_totals[k]
                meals.append(total_entry)
                save_json(MEALS_FILE, meals)
                msg = f"Gespeichert: {total_entry['totals']['kcal']} kcal"
            else:
                msg = 'Nichts erkannt.'
        else:
            msg = 'Bitte Freitext oder Gericht + Gramm ausfüllen.'
    return render_template('mahlzeit.html', msg=msg)

@app.route('/training', methods=['GET','POST'])
def training():
    msg = ''
    if request.method == 'POST':
        exercise = request.form['exercise']
        weight = float(request.form['weight'])
        reps = int(request.form['reps'])
        sets = int(request.form['sets'])
        today = datetime.date.today()
        iso = today.isoformat()
        week = today.isocalendar().week
        data = load_json(TRAINING_FILE, [])
        entry = {'date':iso,'week':week,'exercise':exercise,'weight':weight,'reps':reps,'sets':sets}
        data.append(entry)
        save_json(TRAINING_FILE, data)
        msg = 'Training gespeichert.'
    entries = load_json(TRAINING_FILE, [])[-10:][::-1]
    return render_template('training.html', msg=msg, entries=entries)

@app.route('/fortschritt')
def fortschritt():
    data = load_json(TRAINING_FILE, [])
    if len(data) < 2:
        return render_template('fortschritt.html', enough=False)
    last7 = data[-7:]
    prev7 = data[-14:-7]
    def avg(field, entries):
        return round(sum(e[field] for e in entries)/len(entries),1) if entries else 0
    w_last = avg('weight', last7); w_prev = avg('weight', prev7)
    r_last = avg('reps', last7); r_prev = avg('reps', prev7)
    return render_template('fortschritt.html', enough=True, w_last=w_last, w_prev=w_prev, r_last=r_last, r_prev=r_prev)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', '5010'))
    app.run(debug=True, port=port)
