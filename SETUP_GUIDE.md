# AI List Assist — current run path

## What is checked in

`app_enhanced.py` is the Flask entry point. The browser UI is served from `templates/index.html`, with service modules under `services/` and local SQLite persistence. The FastAPI/PostgreSQL/React stack described in the roadmap is planned migration work.

This repository does not include a ready-to-use `.env`, sample `test_data/` images, or the Postman collections described by an earlier version of this guide. External analysis, marketplace OAuth, and listing publication have not been validated by the offline test below.

## Offline smoke test

Use a fresh, disposable clone with Python 3.12+. Do not place production credentials, a `.env`, or important local database files in it.

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest tests/test_smoke.py -q
```

`tests/test_smoke.py` supplies sentinel configuration and uses Flask's test client. It checks app import, `/health`, and rejection of unauthenticated draft requests. Its fixture creates and removes `listings.db`, `valuations.db`, and `consignment.db` in the working directory. It makes no intentional external service calls.

## Interactive application

The current local entry point is `python app_enhanced.py`, which binds a Flask server to port 5000. That path initializes integration services and includes routes for analysis, OAuth, and marketplace writes. Run it only in a controlled local environment after reviewing the required configuration and side effects. The offline smoke test does not establish that the interactive application or any external service flow works.

Do not run `simulate_listing_flow.py` as an offline test: it sends a request to an external eBay sandbox endpoint. Any credential-based validation or publication needs a separately approved test plan.
