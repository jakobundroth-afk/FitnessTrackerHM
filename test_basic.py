import app

# Mini Smoke Tests ohne Input (nur Funktionen direkt testen mit Dummy Daten)

def test_parse_meal():
    items = app.parse_meal_input('2 eier und ein apfel')
    assert ('eier',2) in items or ('ei',2) in items
    assert ('apfel',1) in items

if __name__ == '__main__':
    test_parse_meal()
    print('Smoke Tests OK')
