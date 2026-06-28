# Deploy the frontend to Vercel (full app)

The **frontend** runs on Vercel; the **Python backend** (FastAPI + ChromaDB +
LangGraph + the vector index + long SSE streams) does **not** run on Vercel —
host it separately (App Runner / Render / Fly / a VM) and point the frontend at
its public URL.

```
Browser ──► Vercel (TanStack Start SSR, this app)
   │
   └── fetch(VITE_API_URL) ──► Backend host (FastAPI)  ◄── OpenAI, Integreat RAG
```

The browser talks to the backend **directly** (client-side `fetch`), so the SSE
reasoning stream never passes through Vercel — no serverless timeout issue.

---

## 1. Deploy the backend (get a public HTTPS URL)

Use the existing Docker setup (see repo `DEPLOY.md` / `infra/`):

- `backend/Dockerfile` — bakes the RAG index at build (needs `LLM_API_KEY` +
  network at build time). Full functionality.
- `backend/Dockerfile.deploy` — fast image, **no** index (RAG degrades to
  handoff). Fine for a first smoke test.

Set these **environment variables** on the backend host (no `.env` in the image):

| var | value |
|---|---|
| `LLM_API_KEY` | your OpenAI key |
| `LLM_MODEL` | e.g. `gpt-4o-mini` (or your gpt-5.x) |
| `EMBED_MODEL` | `text-embedding-3-small` |
| `STT_MODEL` | `gpt-4o-mini-transcribe` (voice) |
| `INTEGREAT_REGION` | `testumgebung-frag-integreat` |

CORS is already open (`allow_origins=["*"]`), so the Vercel domain can call it.
Confirm `GET https://<backend-host>/health` returns `{"status":"ok",...}`.

> Quick option without AWS: deploy `backend/Dockerfile` to **Render** (New →
> Web Service → Docker), add the env vars above, and copy the resulting URL.

## 2. Deploy the frontend to Vercel

**Build is verified** — Nitro's Vercel preset emits `.vercel/output`. Config
lives in `frontend/vercel.json` (`framework: null`, build runs with
`NITRO_PRESET=vercel`).

### Dashboard (recommended)
1. Vercel → **Add New → Project** → import this GitHub repo.
2. **Root Directory: `frontend`**.
3. Framework Preset: **Other** (vercel.json sets the build command).
4. **Environment Variables:**
   - `VITE_API_URL` = `https://<your-backend-host>`
   - `VITE_USE_MOCK` = `false`
   - `NITRO_PRESET` = `vercel` *(belt-and-suspenders; also in the build command)*
5. **Deploy.**

### CLI (alternative)
```bash
cd frontend
npm i -g vercel
vercel login
vercel link                 # pick/create the project, root = this dir
vercel env add VITE_API_URL production     # paste the backend URL
vercel env add VITE_USE_MOCK production     # false
vercel --prod
```

## 3. Verify
Open the Vercel URL → the welcome screen loads → send a message → reasoning
steps stream in and a grounded answer appears (i.e. it's hitting your backend,
not the mock). If you see canned/mock replies, `VITE_USE_MOCK` isn't `false` or
`VITE_API_URL` is unset — fix the env and redeploy.
