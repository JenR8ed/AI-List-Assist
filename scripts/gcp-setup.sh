#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID=$(gcloud config get-value project)
REGION="us-west1"
SA_NAME="ai-list-assist-run"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
SECRET_NAME="AI_LIST_ASSIST_DOPPLER_TOKEN"
REPO_NAME="ai-list-assist"

echo "=== 1. Enabling GCP APIs ==="
gcloud services enable \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  run.googleapis.com \
  secretmanager.googleapis.com \
  iam.googleapis.com

echo "=== 2. Creating Artifact Registry Repository ==="
gcloud artifacts repositories create "${REPO_NAME}" \
  --repository-format=docker \
  --location="${REGION}" \
  --description="Docker repository for AI List Assist" || true

echo "=== 3. Creating Runtime Service Account ==="
gcloud iam service-accounts create "${SA_NAME}" \
  --display-name="AI List Assist Cloud Run Runtime SA" || true

echo "=== 4. Granting Secret Manager Access to Runtime SA ==="
# Allow runtime SA to read secrets
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/secretmanager.secretAccessor"

echo "=== 5. Granting Cloud Build Permissions ==="
CB_SA_NUMBER=$(gcloud projects describe "${PROJECT_ID}" --format="value(projectNumber)")
CB_SA="${CB_SA_NUMBER}@cloudbuild.gserviceaccount.com"

# Allow Cloud Build to deploy to Cloud Run and act as runtime SA
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${CB_SA}" \
  --role="roles/run.admin"

gcloud iam service-accounts add-iam-policy-binding "${SA_EMAIL}" \
  --member="serviceAccount:${CB_SA}" \
  --role="roles/iam.serviceAccountUser"

echo "=== Setup Complete! Next: Add your Doppler Token to Secret Manager ==="
echo "Run: echo -n 'dp.st.xxxx' | gcloud secrets create ${SECRET_NAME} --data-file=- --replication-policy=automatic"
