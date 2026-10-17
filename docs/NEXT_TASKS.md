# Next tasks

## P0 — physical iPhone validation

- Install BiteLog 1.5.0 build 9 on the connected, unlocked iPhone.
- Complete manual/photo/voice save, Food Log display, and deletion checks.
- Upload and reopen the sample PDF in the iPhone app; verify extracted plan sections and estimate labeling.
- Validate the weekly email draft without sending it.

## P0 — Apple Health

- Trigger HealthKit authorization from the physical app.
- Verify steps, active energy, and workout minutes against Apple Health.
- Surface authorization or data-read failures clearly in the app.

## P1 — durable persistence

- Add a user model and Sign in with Apple.
- Store confirmed meals, journal entries, profile data, and extracted plans in a backend database.
- Store original plan files in private object storage and support retrieval across devices.
- Keep AI estimates distinct from athlete-confirmed values.

## P1 — plan accuracy

- Add an explicit user choice for plans without numeric targets: rules-only or estimated ranges.
- Preserve version history when a dietitian sends a revised plan.
- Add a review/edit step before extracted targets become active.

## P2 — production deployment

- Deploy the backend behind HTTPS.
- Authenticate API requests, restrict CORS, and add rate limits.
- Move the API URL out of the production Settings experience.
- Add observability and privacy-safe error monitoring.
