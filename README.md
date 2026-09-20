# BiteLog v1.2 Production Foundation

This package contains:

- `ios/` — the working BiteLog iPhone/Xcode app, updated to call a backend for photo estimation.
- `backend/` — FastAPI service with server-side AI meal analysis, upload primitives, and a Postgres-ready schema.
- `docs/ARCHITECTURE.md` — current and scale architecture.
- `docker-compose.yml` — local API + Postgres + Redis + MinIO environment.

## Why this architecture

The iPhone owns HealthKit and the user experience. The backend owns secrets, model calls, durable product data, and eventually async work. Photos move to object storage at scale rather than through application servers.

## Fastest path to make Estimate from photo work

1. Start or deploy `backend/`.
2. Put `OPENAI_API_KEY` only in backend environment variables.
3. In BiteLog > Settings, set the BiteLog API URL.
4. Take/select a meal photo and tap **Estimate from photo**.

For a phone connecting to a backend on your Mac, use the Mac's LAN IP, not `localhost`.

## Codex handoff
This repo is prepared for Codex. Start by reading `AGENTS.md`, then `docs/CURRENT_STATE.md` and `docs/NEXT_TASKS.md`.
