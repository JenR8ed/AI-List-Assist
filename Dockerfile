FROM python:3.12-slim

# Prevent Python from writing .pyc files and ensure logs are unbuffered
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create a non-root user and group
RUN groupadd -g 1000 appuser && \
    useradd -u 1000 -g appuser -s /bin/bash -m appuser

# Create working directory and change ownership
RUN mkdir -p /app && chown appuser:appuser /app
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y gcc sqlite3 libsqlite3-dev && rm -rf /var/lib/apt/lists/*

# Optimal layer caching: copy requirements and install dependencies BEFORE copying the rest of the source code.
# This ensures that changes to the application code do not invalidate the cached layer containing installed dependencies.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# We explicitly install some extra packages that might be needed based on app imports if they aren't in requirements
RUN pip install --no-cache-dir flask werkzeug python-dotenv requests pandas pydantic pillow

# Drop root privileges by switching to the non-root user
USER appuser

# Ensure standard app user configuration
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/data && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 5000

ENV FLASK_APP=app_enhanced.py
ENV FLASK_ENV=development
ENV FLASK_RUN_HOST=0.0.0.0

CMD ["flask", "run", "--host=0.0.0.0", "--port=5000"]
