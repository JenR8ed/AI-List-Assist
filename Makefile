.PHONY: venv install init-db test smoke lint run docker-build docker-up clean

PYTHON ?= python3
VENV ?= .venv

venv:
	$(PYTHON) -m venv $(VENV)
	$(VENV)/bin/python -m pip install --upgrade pip
	$(VENV)/bin/python -m pip install -r requirements.txt

install:
	$(PYTHON) -m pip install -r requirements.txt

init-db:
	SECRET_KEY=$${SECRET_KEY:-dev-secret} API_KEY=$${API_KEY:-dev-key} GOOGLE_API_KEY=$${GOOGLE_API_KEY:-dev-google-key} \
	$(PYTHON) -c "from app_enhanced import init_db; from services.consignment_database import init_db as init_consignment; init_db(); init_consignment()"

smoke:
	PYTHONPATH=. SECRET_KEY=smoke-test-secret API_KEY=smoke-test-api-key \
	EBAY_CLIENT_ID=smoke-test-client-id EBAY_CLIENT_SECRET=smoke-test-client-secret \
	GOOGLE_API_KEY=smoke-test-google-key \
	$(PYTHON) -m pytest tests/test_smoke.py -v --tb=short

test:
	PYTHONPATH=. SECRET_KEY=smoke-test-secret API_KEY=smoke-test-api-key \
	EBAY_CLIENT_ID=smoke-test-client-id EBAY_CLIENT_SECRET=smoke-test-client-secret \
	GOOGLE_API_KEY=smoke-test-google-key \
	$(PYTHON) -m pytest tests/ -v --tb=short

lint:
	$(PYTHON) -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

run: init-db
	SECRET_KEY=$${SECRET_KEY:-dev-secret} API_KEY=$${API_KEY:-dev-key} GOOGLE_API_KEY=$${GOOGLE_API_KEY:-dev-google-key} \
	$(PYTHON) app_enhanced.py

docker-build:
	mkdir -p data
	docker compose -f docker-compose.dev.yml build

docker-up:
	mkdir -p data
	docker compose -f docker-compose.dev.yml up --build

clean:
	rm -rf __pycache__ .pytest_cache *.db *.db-shm *.db-wal
