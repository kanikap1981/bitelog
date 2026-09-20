# Next tasks

## P0 — connectivity and photo analysis
- Add an in-app dev diagnostics panel showing API base URL, `/health` status, and last request error.
- Verify iPhone can load `/health` on the LAN.
- Verify request payload shape for `/v1/meals/analyze-inline`.
- Verify provider model name and Responses API request schema against current official docs.
- Add backend request IDs and concise structured logging.
- Add backend test fixture for a tiny image data URL without calling the external provider.

## P0 — Apple Health
- Verify HealthKit authorization request is triggered by UI action.
- Log authorization callback errors to Xcode console and surface a user-friendly status.
- Confirm HealthKit read types and entitlements match.
- Test steps and active energy first; add heart rate/workouts after basics work.

## P1 — UX cleanup
- Rename “Meal analysis endpoint” to “BiteLog API URL” in dev builds.
- Hide API configuration from production UX.
- Add photo-analysis loading/progress/error states.
- Make Today screen clearer around calories remaining, protein target, and activity.

## P1 — persistence
- Add user model + Sign in with Apple.
- Save confirmed meals to Postgres.
- Add direct object-storage upload via presigned URL.
- Store AI estimate separately from user-confirmed nutrition values.

## P2 — production hardening
- HTTPS-only backend deployment.
- Authenticated API requests.
- Rate limiting and abuse protection.
- Remove broad CORS policy.
- Background jobs for heavier processing.
- Observability and error monitoring.
