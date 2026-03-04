from app_enhanced import app

def test_routes():
    rules = [str(rule) for rule in app.url_map.iter_rules()]
    print(rules)

if __name__ == '__main__':
    test_routes()
