# Deploying Integreat Compass on AWS (source-based, no Docker)

Both services deploy **straight from this GitHub repo** — AWS clones the code,
builds it on AWS, and hosts it on AWS. No Docker, no ECR, no AWS CLI required.

- **Backend (FastAPI)** → **AWS App Runner**, configured by [`apprunner.yaml`](apprunner.yaml).
- **Frontend (Next.js)** → **AWS Amplify Hosting**, configured by [`amplify.yml`](amplify.yml).

> **What you get today:** a working skeleton. The engine boots and the
> options-first flow runs, but answers say *"pending"* until retrieval (Track B)
> and journeys (Track C) land. No LLM key is needed to demo the flow — the router
> falls back to keyword matching without one.

---

## 0. Prerequisites (one-time)

1. The deploy configs must be on the branch you connect. Make sure the branch
   you point AWS at (recommended: **`main`**) contains Phase 0 + Track A + these
   config files, then **push to GitHub**:
   ```bash
   git push origin main
   ```
2. An AWS account in a region close to you (examples below use **eu-central-1 /
   Frankfurt**). You already have credentials configured in Kiro.

**Deploy the backend first** — you need its URL before building the frontend.

---

## 1. Backend → App Runner

1. AWS Console → **App Runner** → **Create service**.
2. **Source**: *Source code repository* → **Add new** → connect GitHub → pick
   `Xaka68/AI-powered-immigration-guidance-system` → branch **`main`**.
3. **Deployment trigger**: *Automatic* (redeploys on every push) is fine.
4. **Configuration file**: choose **Use a configuration file** — App Runner reads
   [`apprunner.yaml`](apprunner.yaml) from the repo root. (Source directory: `/`.)
5. **Service settings**:
   - Name: `integreat-compass-api`
   - CPU/Memory: **1 vCPU / 2 GB** is plenty for the skeleton.
   - Port: **8000** (already set in the config file).
6. **(Optional) Real LLM**: Configuration → **Environment variables** → add
   `LLM_API_KEY` = your key. Leave it out to demo with the offline fallback.
   *Never commit this key.*
7. **(Optional) Health check**: set path to `/health` (HTTP). Default TCP works too.
8. **Create & deploy.** After ~3–5 min you get a URL like
   `https://xxxxx.eu-central-1.awsapprunner.com`.
9. **Verify**:
   ```bash
   curl https://xxxxx.eu-central-1.awsapprunner.com/health
   # -> {"status":"ok","journeys":[]}
   ```
   **Copy this URL** — the frontend needs it.

---

## 2. Frontend → Amplify Hosting

1. AWS Console → **AWS Amplify** → **Create new app** → **Host web app**.
2. **Source**: GitHub → same repo → branch **`main`**.
3. Amplify detects the monorepo. Set **app root / monorepo root** to **`frontend`**
   (it will use [`amplify.yml`](amplify.yml); confirm the build spec is detected).
4. **Environment variables** (App settings → Environment variables) — add **before**
   the first build, because `NEXT_PUBLIC_*` is baked in at build time:
   - `NEXT_PUBLIC_API_URL` = the App Runner URL from step 1.9
     (e.g. `https://xxxxx.eu-central-1.awsapprunner.com`).
5. **Save and deploy.** After the build you get a URL like
   `https://main.xxxxx.amplifyapp.com`.
6. Open it — the seed page calls `/chat` on your App Runner backend and shows the
   options-first reply.

---

## 3. After it's live

- **Update either service**: just `git push` to `main`. App Runner and Amplify
  redeploy automatically.
- **Changed the backend URL?** Re-set `NEXT_PUBLIC_API_URL` in Amplify and
  **redeploy the frontend** (the value is compiled in, not read at runtime).
- **CORS**: the backend allows all origins (fine for a hackathon). Tighten
  `allow_origins` in `backend/src/api/main.py` to the Amplify URL before any real use.

## When Track B (retrieval) lands

The skeleton becomes a full demo with **no infra change**:
1. Add `chromadb` + `sentence-transformers` to `backend/requirements.txt`.
2. Commit the prebuilt vector index (or build it on first boot) so answers ground.
3. Bump App Runner CPU/Memory if the embedding model needs it (e.g. 2 vCPU / 4 GB).
4. `git push` → App Runner rebuilds.

## Cost note (hackathon)

App Runner and Amplify both bill for usage; a small demo runs for a few dollars.
**Pause the App Runner service** (Console → Actions → Pause) when you're not
demoing to stop backend charges. Delete both services after the event.

## Security note

`next@14.2.5` has a published advisory — bump to a patched `14.2.x` before any
public/production deploy. For a closed hackathon demo it's acceptable.
