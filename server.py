"""Einfacher HTTP-Server NUR mit Standardbibliothek.
Bietet JSON-Endpunkte für Profil, Training und Fortschritt.

Endpunkte:
  GET  /              -> Dashboard (Profil + Basiswerte) oder Hinweis wenn kein Profil
  GET  /profil        -> Profil-Daten als JSON (oder Fehler)
  POST /profil        -> Profil anlegen/aktualisieren (JSON Body)
  GET  /training      -> Letzte Trainings-Einträge (alle)
  POST /training      -> Neuen Trainings-Eintrag speichern (JSON Body)
  GET  /fortschritt   -> Vergleich letzte 7 vs vorherige 7 Trainings-Einträge

Keine externen Abhängigkeiten, keine HTML-Ausgabe.
Start: python server.py
Dann im Browser: http://127.0.0.1:5010/
Oder mit PowerShell Invoke-WebRequest.
"""

from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
import datetime
import csv

PROFILE_FILE = 'user_profile.json'
TRAINING_FILE = 'training_log.csv'
PORT = 5010

# ------------------ Datei-Helfer ------------------

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
            reader = csv.DictReader(f)
            for row in reader:
                try: row['weight'] = float(row.get('weight', 0))
                except: row['weight'] = 0.0
                try: row['reps'] = int(row.get('reps', 0))
                except: row['reps'] = 0
                try: row['sets'] = int(row.get('sets', 0))
                except: row['sets'] = 0
                entries.append(row)
    except Exception:
        pass
    return entries

def append_training(entry):
    file_exists = os.path.exists(TRAINING_FILE)
    fieldnames = ['date','week','exercise','weight','reps','sets']
    with open(TRAINING_FILE, 'a', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            w.writeheader()
        w.writerow(entry)

# ------------------ Logik ------------------

def compute_profile_extensions(p):
    """Berechnet BMR/TDEE/Ziel wenn noch nicht vorhanden."""
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

# ------------------ HTTP Handler ------------------

class Handler(BaseHTTPRequestHandler):
    def _json_response(self, code, payload):
        data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _parse_json_body(self):
        length = self.headers.get('Content-Length')
        if not length:
            return None
        try:
            raw = self.rfile.read(int(length))
            return json.loads(raw.decode('utf-8'))
        except Exception:
            return None

    def do_GET(self):
        if self.path == '/' or self.path == '/dashboard':
            profile = compute_profile_extensions(load_profile())
            if not profile:
                self._json_response(200, {'message':'kein Profil vorhanden'})
                return
            self._json_response(200, {'profile': profile})
            return
        if self.path == '/profil':
            profile = compute_profile_extensions(load_profile())
            if not profile:
                self._json_response(404, {'error':'kein Profil'})
                return
            self._json_response(200, profile)
            return
        if self.path == '/training':
            entries = load_training()
            self._json_response(200, {'entries': entries})
            return
        if self.path == '/fortschritt':
            entries = load_training()
            prog = calc_progress(entries)
            self._json_response(200, prog)
            return
        self._json_response(404, {'error':'nicht gefunden'})

    def do_POST(self):
        if self.path == '/profil':
            data = self._parse_json_body() or {}
            required = ['age','sex','height_cm','weight_kg','activity_factor','goal']
            if not all(k in data for k in required):
                self._json_response(400, {'error':'fehlende Felder','required':required})
                return
            profile = {
                'age': int(data['age']),
                'sex': str(data['sex']).strip().lower(),
                'height_cm': float(data['height_cm']),
                'weight_kg': float(data['weight_kg']),
                'activity_factor': float(data['activity_factor']),
                'goal': str(data['goal']).strip().lower()
            }
            profile = compute_profile_extensions(profile)
            save_profile(profile)
            self._json_response(200, {'status':'ok','profile':profile})
            return
        if self.path == '/training':
            data = self._parse_json_body() or {}
            required = ['exercise','weight','reps','sets']
            if not all(k in data for k in required):
                self._json_response(400, {'error':'fehlende Felder','required':required})
                return
            today = datetime.date.today()
            entry = {
                'date': today.isoformat(),
                'week': today.isocalendar().week,
                'exercise': str(data['exercise']).strip(),
                'weight': float(data['weight']),
                'reps': int(data['reps']),
                'sets': int(data['sets'])
            }
            append_training(entry)
            self._json_response(200, {'status':'ok','entry': entry})
            return
        self._json_response(404, {'error':'nicht gefunden'})

    def log_message(self, format, *args):
        # Unterdrücke Standard-Logging auf stdout für Ruhe
        return

# ------------------ Start ------------------

def run():
    print(f"Starte einfachen Server auf http://127.0.0.1:{PORT}")
    httpd = HTTPServer(('127.0.0.1', PORT), Handler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer beendet.")

if __name__ == '__main__':
    run()
