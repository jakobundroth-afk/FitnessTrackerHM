import json, os, datetime

USER_FILE = 'user.json'
MEALS_FILE = 'meals.json'
TRAINING_FILE = 'training.json'

# ---------- Hilfsfunktionen für Dateien ----------

def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ---------- 1. Benutzerprofil & Zielsetzung ----------

def setup_profile():
    print('--- Profil Einrichtung ---')
    age = int(input('Alter: '))
    sex = input('Geschlecht (m/f): ').strip().lower()
    height = float(input('Größe (cm): '))
    weight = float(input('Gewicht (kg): '))
    print('Aktivität: 1=Sitzend 2=Leicht 3=Moderat 4=Sehr Aktiv')
    activity_choice = input('Wahl (1-4): ').strip()
    activity_factor = {'1':1.2,'2':1.375,'3':1.55,'4':1.725}.get(activity_choice,'1.2')
    print('Ziel: 1=Abnehmen 2=Halten 3=Zunehmen')
    goal_choice = input('Wahl (1-3): ').strip()

    # Grundumsatz (Mifflin St. Jeor)
    if sex == 'm':
        bmr = 10*weight + 6.25*height - 5*age + 5
    else:
        bmr = 10*weight + 6.25*height - 5*age - 161

    tdee = bmr * float(activity_factor)

    # Ziel Kalorien Anpassung
    if goal_choice == '1':
        daily_target = tdee - 500  # moderates Defizit
    elif goal_choice == '3':
        daily_target = tdee + 300  # leichter Überschuss
    else:
        daily_target = tdee

    profile = {
        'age': age,
        'sex': sex,
        'height_cm': height,
        'weight_kg': weight,
        'activity_factor': float(activity_factor),
        'goal': goal_choice,
        'bmr': round(bmr,1),
        'tdee': round(tdee,1),
        'daily_calorie_target': round(daily_target,1)
    }
    save_json(USER_FILE, profile)
    print('Profil gespeichert. Tagesziel Kalorien:', profile['daily_calorie_target'])

# ---------- Lebensmittel Datenbank (vereinfachte "API") ----------
FOOD_DB = {
    'ei': {'kcal':78,'protein':6,'fat':5,'carbs':0},
    'eier': {'kcal':78,'protein':6,'fat':5,'carbs':0},
    'apfel': {'kcal':95,'protein':0,'fat':0,'carbs':25},
    'banane': {'kcal':105,'protein':1,'fat':0,'carbs':27},
    'haferflocken': {'kcal':150,'protein':5,'fat':3,'carbs':27},
    'brot': {'kcal':80,'protein':3,'fat':1,'carbs':15},
}

# ---------- 2. Ernährungs-Tracking ----------

def parse_meal_input(text):
    # sehr einfache Logik: "2 eier und ein apfel" -> tokens zählen
    tokens = text.lower().replace(',', ' ').split()
    items = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token.isdigit():
            qty = int(token)
            i += 1
            if i < len(tokens):
                food = tokens[i]
                items.append((food, qty))
        else:
            # Wörter wie 'ein'/'eine' als 1 behandeln
            if token in ('ein','eine','1'): 
                i += 1
                if i < len(tokens):
                    food = tokens[i]
                    items.append((food,1))
            else:
                # einzelnes Lebensmittel ohne Zahl -> Menge 1
                if token in FOOD_DB:
                    items.append((token,1))
        i += 1
    return items


def add_meal():
    text = input('Was hast du gegessen? ').strip()
    parsed = parse_meal_input(text)
    if not parsed:
        print('Nichts erkannt.')
        return
    meals = load_json(MEALS_FILE, [])
    now = datetime.datetime.now().isoformat(timespec='seconds')
    total_entry = {'time': now, 'items': [], 'totals': {'kcal':0,'protein':0,'fat':0,'carbs':0}}
    for food, qty in parsed:
        data = FOOD_DB.get(food)
        if not data:
            print(f'Unbekannt: {food}')
            continue
        item_totals = {k: data[k]*qty for k in data}
        total_entry['items'].append({'food':food,'qty':qty, **item_totals})
        for k in total_entry['totals']:
            total_entry['totals'][k] += item_totals[k]
    meals.append(total_entry)
    save_json(MEALS_FILE, meals)
    print('Gespeichert. Kalorien dieser Eingabe:', total_entry['totals']['kcal'])

# ---------- 3. Tägliches Dashboard ----------

def show_dashboard():
    profile = load_json(USER_FILE, None)
    if not profile:
        print('Kein Profil. Bitte zuerst erstellen.')
        return
    meals = load_json(MEALS_FILE, [])
    today = datetime.date.today().isoformat()
    kcal_today = 0
    for entry in meals:
        if entry['time'].startswith(today):
            kcal_today += entry['totals']['kcal']
    target = profile['daily_calorie_target']
    remaining = target - kcal_today
    print('--- Dashboard ---')
    print('Ziel Kalorien:', target)
    print('Konsumiert heute:', kcal_today)
    print('Verbleibend:', round(remaining,1))

# ---------- 4. Trainings Logbuch ----------

def add_training():
    print('--- Training hinzufügen ---')
    exercise = input('Übung: ').strip()
    weight = float(input('Gewicht (kg oder Gerät): '))
    reps = int(input('Wiederholungen: '))
    sets = int(input('Sätze: '))
    today = datetime.date.today()
    iso = today.isoformat()
    week = today.isocalendar().week

    data = load_json(TRAINING_FILE, [])
    entry = {
        'date': iso,
        'week': week,
        'exercise': exercise,
        'weight': weight,
        'reps': reps,
        'sets': sets
    }
    data.append(entry)
    save_json(TRAINING_FILE, data)
    print('Training gespeichert.')


def show_training_progress():
    data = load_json(TRAINING_FILE, [])
    if len(data) < 2:
        print('Nicht genug Einträge für Vergleich.')
        return
    # letzte 7 vs vorherige 7
    last7 = data[-7:]
    prev7 = data[-14:-7]
    def avg_weight(entries):
        if not entries:
            return 0
        return sum(e['weight'] for e in entries) / len(entries)
    def avg_reps(entries):
        if not entries:
            return 0
        return sum(e['reps'] for e in entries) / len(entries)
    w_last = avg_weight(last7)
    w_prev = avg_weight(prev7)
    r_last = avg_reps(last7)
    r_prev = avg_reps(prev7)
    print('--- Trainings Fortschritt ---')
    print(f'Durchschn. Gewicht letzte 7: {w_last:.1f} (vorher: {w_prev:.1f})')
    print(f'Durchschn. Wdh letzte 7: {r_last:.1f} (vorher: {r_prev:.1f})')

# ---------- CLI Menü ----------

def main_menu():
    while True:
        print('\nMenü:')
        print('1 Profil einrichten/neu')
        print('2 Mahlzeit hinzufügen')
        print('3 Dashboard anzeigen')
        print('4 Training hinzufügen')
        print('5 Trainings Fortschritt')
        print('0 Ende')
        choice = input('Wahl: ').strip()
        if choice == '1':
            setup_profile()
        elif choice == '2':
            add_meal()
        elif choice == '3':
            show_dashboard()
        elif choice == '4':
            add_training()
        elif choice == '5':
            show_training_progress()
        elif choice == '0':
            print('Tschüss!')
            break
        else:
            print('Ungültig.')

if __name__ == '__main__':
    main_menu()
