# Multi-stage build for a lightweight production image
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final runtime image
FROM python:3.11-slim

WORKDIR /app

# Install Doppler CLI and CA certificates
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    ca-certificates \
    && curl -sLf --retry 3 --tlsv1.2 'https://packages.doppler.com/public/cli/gpg.key' | gpg --dearmor -o /usr/share/keyrings/doppler-archive-keyring.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/doppler-archive-keyring.gpg] https://packages.doppler.com/public/cli/deb/debian any-version main" | tee /etc/apt/sources.list.d/doppler-cli.list \
    && apt-get update && apt-get install -y --no-install-recommends doppler \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application source code
COPY . .

# Cloud Run injects $PORT (default to 8000 for local runs)
ENV PORT=8000
EXPOSE 8000

# Doppler wraps uvicorn when DOPPLER_TOKEN is present (Cloud Run Secret Manager).
# Local/emulation runs uvicorn directly so the image still boots without Doppler.
CMD ["sh", "-c", "if [ -n \"${DOPPLER_TOKEN:-}\" ]; then exec doppler run -- uvicorn app.main:app --host 0.0.0.0 --port ${PORT}; else exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT}; fi"]
