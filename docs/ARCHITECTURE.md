# BiteLog production architecture

## Now

```text
iPhone / SwiftUI + WKWebView
  |-- HealthKit (local, native)
  |-- meal photo capture
  |-- local-first UI cache
  |
  +---- HTTPS ----> BiteLog API (FastAPI)
                       |-- auth boundary (next step: Sign in with Apple)
                       |-- validation + rate limiting
                       |-- meal analyzer abstraction
                       |       +--> OpenAI Responses API
                       |-- Postgres
                       |-- Redis queue/cache
                       +-- S3-compatible object storage
```

## Photo flow

### v1.2 working path
1. iPhone compresses the image.
2. App POSTs a data URL to `/v1/meals/analyze-inline`.
3. API validates size/type and calls the model server-side.
4. API returns strict structured nutrition fields.
5. User confirms/edits before saving.

This is intentionally simple so the feature works immediately and no AI key ships in the app.

### Scale path
1. App requests `/v1/uploads/presign`.
2. App uploads directly to S3/R2 using the signed URL.
3. App creates an analysis job with the object reference.
4. Worker analyzes asynchronously and stores the estimate.
5. App receives/polls job status.

This prevents large uploads from consuming API workers and gives clean retry/idempotency boundaries.

## Boundaries
- HealthKit authorization and raw health access stay on iPhone.
- OpenAI credentials stay only in backend secrets.
- Model/provider code is isolated in `services/openai_meal_analyzer.py`.
- Postgres is the source of truth for account-synced BiteLog data.
- Object storage holds photos/audio, not Postgres.
- Redis is optional initially and becomes the job/cache layer when async work is enabled.

## Next production milestones
- Sign in with Apple + JWT verification.
- Persist meals and user corrections.
- Presigned direct uploads as the default path.
- Background jobs with idempotency keys.
- Per-user rate limiting and budget controls.
- Observability (request IDs, structured logs, traces, error monitoring).
- Data retention/deletion controls for meal images and health snapshots.
