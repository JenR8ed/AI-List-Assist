FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc sqlite3 libsqlite3-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# We explicitly install some extra packages that might be needed based on app imports if they aren't in requirements
RUN pip install flask werkzeug python-dotenv requests pandas pydantic pillow

COPY . .

EXPOSE 5000

ENV FLASK_APP=app_enhanced.py
ENV FLASK_ENV=development
ENV FLASK_RUN_HOST=0.0.0.0

CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
