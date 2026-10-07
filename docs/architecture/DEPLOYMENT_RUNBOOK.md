# Hybrid Cloud Deployment Runbook

This operations runbook provides step-by-step instructions for provisioning and configuring the automated CI/CD pipeline for **Portfolio Assistant** across **Google Cloud Platform (GCP Cloud Run)** and **Vercel**.

---

## 1. Architecture Overview

- **Backend API:** Python FastAPI container deployed to **GCP Cloud Run** (`asia-south1`, Mumbai) with zero-downtime rolling updates:
  - **Live Endpoint:** `https://portfolio-assistant-api-njcmv33m6q-el.a.run.app`
- **Frontend App:** Next.js 14 App Router deployed globally to **Vercel Edge Network**:
  - **Live URL:** `https://portfolio-assistant-rouge.vercel.app`
- **Container Registry:** **GCP Artifact Registry** (`asia-south1-docker.pkg.dev`).
- **CI/CD Orchestration:** **GitHub Actions** (`.github/workflows/ci.yml` & `.github/workflows/deploy.yml`).

---

## 2. Google Cloud Platform (GCP) One-Time Setup

Run the following commands using the `gcloud` CLI (either locally or inside Google Cloud Shell):

### Step 2.1: Set Your Project & Region
```bash
# Set your GCP Project ID
export PROJECT_ID="your-gcp-project-id"
export REGION="asia-south1"

gcloud config set project "$PROJECT_ID"
```

### Step 2.2: Enable Required APIs
```bash
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  iam.googleapis.com
```

### Step 2.3: Create Artifact Registry Repository
```bash
gcloud artifacts repositories create portfolio-assistant \
  --repository-format=docker \
  --location="$REGION" \
  --description="Docker repository for Portfolio Assistant backend images"
```

### Step 2.4: Create Deployer Service Account for GitHub Actions
```bash
# Create service account
gcloud iam service-accounts create github-deployer \
  --description="Service account for GitHub Actions CI/CD deployment" \
  --display-name="GitHub Deployer"

export SA_EMAIL="github-deployer@${PROJECT_ID}.iam.gserviceaccount.com"

# Grant Cloud Run Admin role
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/run.admin"

# Grant Artifact Registry Writer role
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/artifactregistry.writer"

# Grant Service Account User role (allows deploying services that run as the default compute account)
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${SA_EMAIL}" \
  --role="roles/iam.serviceAccountUser"
```

### Step 2.5: Generate Service Account Key for GitHub
```bash
# Generate JSON private key
gcloud iam service-accounts keys create ./gcp-sa-key.json \
  --iam-account="${SA_EMAIL}"

# View key content to paste into GitHub Secrets
cat ./gcp-sa-key.json

# (IMPORTANT) Delete the local key file after copying to GitHub Secrets
rm ./gcp-sa-key.json
```

---

## 3. GitHub Repository Secrets Setup

Navigate to your GitHub Repository:  
**Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret**.

Add the following secrets:

| Secret Name | Description | Example / Source |
|---|---|---|
| `GCP_PROJECT_ID` | Your Google Cloud project ID | `my-portfolio-proj-123` |
| `GCP_SA_KEY` | Entire JSON content of `gcp-sa-key.json` | `{"type": "service_account", ...}` |
| `DATABASE_URL` | Supabase PostgreSQL Connection String | `postgresql://postgres.[REF]:[PWD]@aws-0-ap-south-1.pooler.supabase.com:6543/postgres?sslmode=require` |
| `REDIS_URL` | Upstash Redis Connection String | `rediss://default:[PWD]@[HOST].upstash.io:6379` |
| `GEMINI_API_KEY` | Google Gemini API Key | Free key from [Google AI Studio](https://aistudio.google.com/app/apikey) |
| `JWT_SECRET_KEY` | 32+ character random string for signing JWTs | Generate with `openssl rand -hex 32` |
| `ENCRYPTION_SECRET_KEY` | 32-byte URL-safe base64 Fernet key | Generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `GOOGLE_CLIENT_ID` | Google IAM OAuth 2.0 Web Client ID | From GCP Console -> Credentials |
| `GOOGLE_CLIENT_SECRET` | Google IAM OAuth 2.0 Client Secret | From GCP Console -> Credentials |
| `ALLOWED_ORIGINS` | *(Optional)* Comma-separated allowed frontend origins | `https://portfolio-assistant-rouge.vercel.app,http://localhost:3000` |

---

## 4. Vercel Frontend One-Time Setup

### Step 4.1: Import Project into Vercel
1. Log in to [vercel.com](https://vercel.com) and click **Add New** -> **Project**.
2. Select your repository `portfolio-assistant`.
3. In **Root Directory**, click **Edit** and select `frontend`.
4. Leave framework preset as **Next.js**.

### Step 4.2: Configure Environment Variables in Vercel
Under the **Environment Variables** tab, add:

| Variable Name | Value | Purpose |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `https://portfolio-assistant-api-njcmv33m6q-el.a.run.app` | Cloud Run backend API URL |
| `NEXT_PUBLIC_GOOGLE_CLIENT_ID` | `[YOUR_CLIENT_ID].apps.googleusercontent.com` | Google OAuth Web Client ID |

Click **Deploy**.

---

## 5. Production Approval Gate Setup (GitHub Environments)

To prevent accidental deployments and require manual sign-off before code reaches Google Cloud Run:

1. In your GitHub repository, navigate to:
   **Settings** -> **Environments** (under *Code and automation*).
2. Click **New environment** and enter the name:
   `production`
3. Under **Deployment protection rules**, select:
   - ✅ **Required reviewers**: Check this and add your GitHub username (or team).
4. Click **Save protection rules**.

### How the Approval Gate Works:
- When changes are pushed to `main` (or triggered manually via `workflow_dispatch`):
  1. `test-backend` (49 tests) and `test-frontend` (`npm run build`) run first in parallel.
  2. The workflow **pauses** at `deploy-backend` with the status: **Waiting for review**.
  3. You (and any configured reviewers) receive a notification and can review the run details.
  4. Click **Review deployments** -> select **production** -> click **Approve and deploy**.
  5. The job proceeds to build the Docker image, push to Artifact Registry, deploy to Cloud Run, and verify `/health`.

---

## 6. Automated CI/CD Workflow Operations

### 6.1 Quality Gates on Pull Requests (`ci.yml`)
When opening a pull request to `main`:
1. **Backend:** Runs all unit tests (`python -m unittest discover -s backend/tests -p "test_*.py"`).
2. **Frontend:** Runs `npm run lint` and Next.js production build (`npm run build`).

### 6.2 Production Release on Merge to `main` (`deploy.yml`)
When code merges or is pushed to `main`:
1. **Quality Gates:** Unit tests and build checks run automatically.
2. **Approval Gate:** The pipeline pauses at `deploy-backend` waiting for manual reviewer approval.
3. **Backend CD (Post-Approval):**
   - Docker image is built using multi-stage caching.
   - Image is pushed to `asia-south1-docker.pkg.dev/<PROJECT_ID>/portfolio-assistant/backend:<SHA>`.
   - Cloud Run service `portfolio-assistant-api` is updated with zero downtime.
   - Workflow executes automated `/health` probe verification with retries.
4. **Frontend CD:**
   - Vercel automatically deploys the updated Next.js frontend to its global edge CDN.

---

## 7. Monitoring, Logs & Zero-Downtime Rollbacks

### 6.1 View Live Cloud Run Logs
```bash
gcloud beta run services logs tail portfolio-assistant-api \
  --project="$PROJECT_ID" \
  --region=asia-south1
```

### 6.2 Instant Cloud Run Rollback
If a defect occurs in a deployed revision:
```bash
# List recent revisions
gcloud run revisions list --service=portfolio-assistant-api --region=asia-south1

# Roll back 100% traffic to previous known healthy revision
gcloud run services update-traffic portfolio-assistant-api \
  --to-revisions=portfolio-assistant-api-00001-abc=100 \
  --region=asia-south1
```

### 6.3 Vercel Instant Rollback
In the Vercel Dashboard -> **Deployments**, select any previous deployment and click **Rollback to this deployment**.
