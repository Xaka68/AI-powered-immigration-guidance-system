# Deployment: AWS App Runner (GitHub Source)

Source lives on GitHub → builds on AWS → runs on AWS.  
Both services get **auto-deploy on push** and free **HTTPS URLs**.

## Architecture

```
GitHub (main branch)
    │ push
    ▼
┌─────────────────────────────────────────┐
│ AWS App Runner                          │
│                                         │
│  compass-backend   (FastAPI, port 8000) │──→ OpenAI / Bedrock (LLM)
│       ▲                                 │──→ Integreat API (source content)
│       │ HTTPS                           │
│  compass-frontend  (Nitro SSR, port 3000)│
└─────────────────────────────────────────┘
```

## One-Time Setup (5 minutes)

### 1. Install AWS CLI

```bash
# Windows
winget install Amazon.AWSCLI
# or download from https://aws.amazon.com/cli/

aws configure
# Enter: Access Key ID, Secret Access Key, Region (eu-central-1 recommended)
```

### 2. Create a GitHub Connection in App Runner

This lets App Runner pull from your private/public repo.

1. Go to [AWS App Runner Console](https://console.aws.amazon.com/apprunner)
2. Click **Create service** → **Source code repository** → **Add new** connection
3. Authorize AWS to your GitHub account/org
4. Copy the **Connection ARN** — you'll need it below

### 3. Store your LLM API key in SSM Parameter Store

```bash
aws ssm put-parameter \
  --name /compass/llm-api-key \
  --value "sk-your-openai-key-here" \
  --type SecureString \
  --region eu-central-1
```

## Deploy

### Option A: AWS Console (easiest for first time)

1. **Backend**:
   - App Runner → Create service
   - Source: GitHub repository → select your repo + branch `main`
   - Configuration: **Custom** (not automatic)
   - Build command: `pip install ./backend/`
   - Start command: `cd backend && uvicorn api.main:app --host 0.0.0.0 --port 8000 --app-dir src`
   - Port: `8000`
   - Add environment variables:
     - `LLM_BASE_URL` = `https://api.openai.com/v1`
     - `LLM_API_KEY` = your key (or reference SSM)
     - `LLM_MODEL` = `gpt-4o-mini`
     - `EMBED_MODEL` = `intfloat/multilingual-e5-large`
     - `INTEGREAT_REGION` = `testumgebung-frag-integreat`
     - `APP_ROOT` = `/app`
   - Instance: 1 vCPU, 2 GB
   - Health check: HTTP `/health`
   - Create & deploy

2. **Frontend**:
   - Same flow, but:
   - Build command: `cd frontend && npm ci && npm run build`
   - Start command: `cd frontend && node .output/server/index.mjs`
   - Port: `3000`
   - Env vars:
     - `VITE_API_URL` = `https://<backend-url-from-step-1>`
     - `VITE_USE_MOCK` = `false`
   - Instance: 0.25 vCPU, 0.5 GB

### Option B: CLI script

```bash
export GITHUB_CONNECTION_ARN="arn:aws:apprunner:eu-central-1:123456789:connection/github/abc123"
export AWS_REGION="eu-central-1"
bash infra/deploy.sh
```

### Option C: Docker-based (if source-based build hits limits)

App Runner also supports image-based deployment. Push images to ECR instead:

```bash
# Build locally (or in CodeBuild)
docker build -f backend/Dockerfile -t compass-backend .
docker build -f frontend/Dockerfile -t compass-frontend ./frontend

# Tag and push to ECR
aws ecr get-login-password --region eu-central-1 | docker login --username AWS --password-stdin <ACCOUNT_ID>.dkr.ecr.eu-central-1.amazonaws.com
docker tag compass-backend <ACCOUNT_ID>.dkr.ecr.eu-central-1.amazonaws.com/compass-backend:latest
docker push <ACCOUNT_ID>.dkr.ecr.eu-central-1.amazonaws.com/compass-backend:latest
```

## After Deployment

- Both services get HTTPS URLs like `https://abc123.eu-central-1.awsapprunner.com`
- Auto-deploy: push to `main` → App Runner rebuilds and redeploys (~2-4 min)
- Logs: App Runner console → your service → Logs tab
- Custom domain: App Runner console → your service → Custom domains

## Updating the Backend's CORS

Once you have the frontend URL, update `backend/src/api/main.py` CORS origins
from `["*"]` to `["https://your-frontend-url.awsapprunner.com"]` for production.

## Cost Estimate (hackathon scope)

- App Runner: ~$0.007/vCPU-hour when active, pauses to zero when idle
- With the provisioned sizes above and low traffic: **< $5/day**
- Auto-pause kicks in after no requests for a configurable period

## Environment Variables Reference

| Variable | Where | Required | Description |
|----------|-------|----------|-------------|
| `LLM_BASE_URL` | Backend | Yes | OpenAI-compatible endpoint |
| `LLM_API_KEY` | Backend | Yes | API key (use SSM SecureString) |
| `LLM_MODEL` | Backend | Yes | Model name |
| `EMBED_MODEL` | Backend | No | Embedding model (default: multilingual-e5-large) |
| `INTEGREAT_REGION` | Backend | No | Integreat source region |
| `APP_ROOT` | Backend | In container | Base path for data/ directory |
| `VITE_API_URL` | Frontend | Yes | Backend HTTPS URL |
| `VITE_USE_MOCK` | Frontend | No | Set `false` for real backend |
