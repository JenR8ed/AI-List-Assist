# AI List Assist Makefile

.PHONY: help install test smoke lint run docker-up docker-down clean

help:
	@echo "AI List Assist targets:"
	@echo "  install     Install Python dependencies"
	@echo "  test        Run full pytest suite"
	@echo "  smoke       Run offline smoke tests only"
	@echo "  lint        Run flake8"
	@echo "  run         Start Flask app (dev)"
	@echo "  docker-up   Start postgres + redis via docker-compose.db.yml"
	@echo "  docker-down Stop docker services"
	@echo "  clean       Remove caches and local DBs"

install:
	python -m pip install -r requirements.txt

test:
	PYTHONPATH=. python -m pytest tests/ -v --tb=short

smoke:
	PYTHONPATH=. python -m pytest tests/test_smoke.py -q

lint:
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	run:
	FLASK_APP=app_enhanced.py FLASK_ENV=development python -m flask run --host=0.0.0.0 --port=5000

docker-up:
	docker compose -f docker-compose.db.yml up -d

docker-down:
	docker compose -f docker-compose.db.yml down

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	rm -f *.db *.db-shm *.db-wal
	rm -rf .pytest_cache .coverage htmlcov
