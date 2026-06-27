# Deploying Integreat Compass on AWS (container images)

Both services ship as **Docker images** → **Amazon ECR** → **AWS App Runner**
(App Runner runs the image and gives you an HTTPS URL).

- **Backend** (`backend/Dockerfile`) — FastAPI + the ChromaDB retrieval index
  **baked into the image at build time**. Listens on **8000**.
- **Frontend** (`frontend/Dockerfile`) — TanStack Start (Vite + Nitro SSR), built
  for a **Node server** with the backend URL compiled in. Listens on **3000**.

> **You need Docker + the AWS CLI** to build and push images. This WSL machine has
> neither — build from **Kiro** (which has the AWS/Docker integration) or install
> Docker Desktop (enable WSL integration) + the AWS CLI. Everything else is console.

**Deploy the backend first** — the frontend bakes in the backend URL at build time.

---

## 0. One-time setup

```bash
# pick a region close to you
export AWS_REGION=eu-central-1
export ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
export ECR=$ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com

# create two ECR repos
aws ecr create-repository --repository-name compass-backend  --region $AWS_REGION
aws ecr create-repository --repository-name compass-frontend --region $AWS_REGION

# log docker in to ECR
aws ecr get-login-password --region $AWS_REGION \
  | docker login --username AWS --password-stdin $ECR
```

---

## 1. Backend → image → ECR → App Runner

```bash
# build from the REPO ROOT (the Dockerfile fetches Integreat + builds the index,
# so this needs network and downloads the ~2GB e5 model — multi-minute build).
docker build -f backend/Dockerfile -t compass-backend .
docker tag  compass-backend:latest $ECR/compass-backend:latest
docker push $ECR/compass-backend:latest
```

Then in the console: **App Runner → Create service → Container registry → Amazon
ECR** → pick `compass-backend:latest`:
- **Port**: `8000`
- **CPU/Memory**: **1 vCPU / 4 GB** (the e5 model needs the headroom).
- **LLM (required for grounded answers)** — add env var `LLM_API_KEY` = your key.
  The LLM turns the retrieved sources into the answer (`answer_generator`), so
  without it content turns fall back to the human-handoff message. Local
  embeddings/search still work without a key, but you won't get real answers.
  - To use **Amazon Bedrock** or a **self-hosted open model** instead, also set
    `LLM_BASE_URL` (OpenAI-compatible endpoint) and `LLM_MODEL`. The defaults are
    OpenAI `gpt-4o-mini`.
- **Health check**: HTTP path `/health` (optional; TCP also works).

After ~5 min you get `https://xxxx.eu-central-1.awsapprunner.com`. Verify:
```bash
curl https://xxxx.eu-central-1.awsapprunner.com/health
# -> {"status":"ok","journeys":[...9 ids...]}
```
**Copy this URL.**

---

## 2. Frontend → image (with backend URL) → ECR → App Runner

```bash
# pass the backend URL as a build-arg — it is COMPILED IN, not read at runtime.
docker build -f frontend/Dockerfile \
  --build-arg VITE_API_URL=https://xxxx.eu-central-1.awsapprunner.com \
  -t compass-frontend frontend/
docker tag  compass-frontend:latest $ECR/compass-frontend:latest
docker push $ECR/compass-frontend:latest
```

Console: **App Runner → Create service → ECR** → `compass-frontend:latest`:
- **Port**: `3000`
- **CPU/Memory**: 1 vCPU / 2 GB is plenty.

Open the resulting `…awsapprunner.com` URL — it talks to your backend.

> Changed the backend URL? **Rebuild the frontend image** with the new
> `--build-arg` and redeploy — the value is baked in at build time.

---

## Refreshing source data

The Integreat snapshot + vector index live inside the backend image. To pull
fresher content: **rebuild and repush the backend image** (step 1), then App
Runner redeploys. (Faster-build alternative: build the index once locally and
commit `data/sources/` instead of building it in the Dockerfile.)

## Notes

- **CORS** is open in `backend/src/api/main.py` (fine for a hackathon). Tighten
  `allow_origins` to the frontend URL before any real use.
- **The LLM is required for grounded answers.** Search/embeddings run locally on
  e5 (no key), but generating the answer from the retrieved sources uses the LLM —
  set `LLM_API_KEY` (or point `LLM_BASE_URL`/`LLM_MODEL` at Bedrock or a
  self-hosted open model). Without it, content turns degrade to a handoff.
- **Cost**: pause both App Runner services between demos; delete after the event.
- **Security**: bump `next`… n/a now (frontend is Vite); keep deps patched before
  any public deploy.
