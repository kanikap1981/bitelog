# BiteLog — Codex project instructions

## Product
BiteLog is an iPhone nutrition logging app. The current UX is a SwiftUI/WKWebView shell around a local HTML app, with native HealthKit bridging. The backend is FastAPI and owns AI meal-photo analysis, secrets, and future persistence/storage.

## Current architecture
- `ios/` — Xcode project (`BiteLogHealth.xcodeproj`), SwiftUI shell, WKWebView, HealthKit bridge, bundled web UI.
- `backend/` — FastAPI API.
- `backend/app/services/openai_meal_analyzer.py` — meal-photo analysis provider integration.
- `backend/app/db/schema.sql` — Postgres-ready schema.
- `docker-compose.yml` — local Postgres, Redis, MinIO stack.
- `docs/ARCHITECTURE.md` — target architecture.

## Current working state
- iPhone app can build, install, and launch on a physical iPhone after signing/trusting developer certificate.
- `CFBundleExecutable` issue has been fixed in `ios/BiteLog/Info.plist`.
- Backend dependencies install and Uvicorn starts successfully on Python 3.9 after replacing `str | None` with `Optional[str]` in `backend/app/config.py`.
- Local backend command:
  `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- HealthKit capability is present, but Apple Health sync still needs validation/fixing on-device.
- Photo estimate flow is wired to backend but has not yet been fully validated end-to-end.

## Local development facts
- User's current Mac LAN IP during setup was `10.0.0.214`. Do not hard-code it; it changes by network.
- The current iOS source expects a **base API URL**, e.g. `http://10.0.0.214:8000`, and appends `/v1/meals/analyze-inline` itself.
- The user's previously installed older build displayed a field called “Meal analysis endpoint” and expected a full endpoint. When modifying UX, migrate cleanly to a base URL field named “BiteLog API URL”.
- iPhone and Mac must be on the same LAN for local HTTP testing.
- `NSAllowsLocalNetworking` and `NSLocalNetworkUsageDescription` are present in Info.plist.

## Secrets
Never commit `.env`, API keys, signing identities, provisioning data, or user credentials. `backend/.env.example` is safe to edit; `backend/.env` must remain ignored.

## Priorities
1. Make `/health` and photo analysis verifiably work from physical iPhone.
2. Fix/validate HealthKit authorization + data reads.
3. Replace technical “endpoint” UX with a product-grade API/environment configuration suitable for dev builds only.
4. Keep production secrets server-side.
5. Add persistence/auth only after core photo + HealthKit flows are stable.
6. Continue Browserbase-inspired UX direction: bold typography, short copy, strong hierarchy, modular capability cards; do not copy Browserbase branding/text verbatim.

## Engineering preferences
- Prefer small, testable changes over rewrites.
- Preserve working iPhone signing/project structure unless a change is necessary.
- Keep mobile app thin; business logic and AI provider calls live server-side.
- HealthKit reads should stay native/on-device; only persist health data if explicitly required.
- Use clear errors in UI and backend logs. Avoid silent failure.
- Maintain Python 3.9 compatibility unless the project explicitly upgrades runtime and docs together.

## Before changing AI provider code
Validate the currently supported OpenAI Responses API model and image/structured-output syntax against current official OpenAI documentation. Do not assume the model string in `.env.example` is valid forever.

## Useful commands
Backend:
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health check from Mac:
```bash
curl http://127.0.0.1:8000/health
```

Find current Wi-Fi IP:
```bash
ipconfig getifaddr en0
```

## Definition of done for next milestone
- `/health` reachable from iPhone Safari on LAN.
- Photo capture -> Estimate from photo returns name/calories/protein/confidence from backend.
- Failure states are human-readable in app.
- Apple Health authorization sheet appears and at least steps/activity are read successfully.
- No API keys exist in iOS bundle or git history.

## Multi-device workflow (user requirement)

The Git repository is the source of truth for code, project state, architecture decisions, current issues, and next steps. Never rely on Codex chat history as the only project context.

At session start:
1. Verify this is a Git checkout, inspect local changes, fetch remote updates, check the current branch's upstream, and pull the latest changes before editing. Prefer a fast-forward pull; do not overwrite local work.
2. Read `AGENTS.md`, `docs/CURRENT_STATE.md`, and `docs/HANDOFF.md`.
3. Summarize the current project state before changing code.
4. Before subsequent changes, check whether the local branch is behind its remote branch and pull first when it is.
5. If pulling causes conflicts, show the conflicts and explain what must be resolved; do not guess. If Git metadata, a remote, or an upstream is missing, report that and obtain the repository location rather than inventing it.

At the end of meaningful work:
1. Update `docs/HANDOFF.md` with completed work, changed files, current branch, known issues, next recommended task, exact run commands, and exact test steps.
2. Update `docs/CURRENT_STATE.md` when state materially changes.
3. Show the proposed commit message, then commit completed work. Check that secrets, local environment files, and signing artifacts are excluded.
4. Push only when the user has explicitly authorized pushing for this project. Otherwise stop after the commit and report it ready to push.

## Product source of truth

BiteLog connects an athlete with any dietitian. The MVP is: upload the dietitian's plan → extract/store targets → track daily adherence → log meals manually or by photo → generate a weekly summary → athlete reviews and emails it to the dietitian. The dietitian's plan is the source of nutrition targets; photo estimates assist logging and require athlete review.

Product vision: https://app.notion.com/p/browserbase/BiteLog-Product-Vision-MVP-3e13c11b6614813fb13bd99f3301173a
