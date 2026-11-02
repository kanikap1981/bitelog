# Next tasks

## Protect production AI usage before broad public release

- Keep the first pilot limited to approximately 20 to 30 invited athletes through TestFlight while access controls are implemented.
- Start a five-day trial when an installation makes its first AI analysis request, not merely when the app is installed.
- Enforce the trial and per-day photo, voice, transcription, and plan-analysis allowances on the server. A client-only timer is not a security boundary.
- Add a privacy-preserving installation identity and validate requests with Apple App Attest before relying on device-level limits.
- Add backend rate limits, request-size limits, usage metrics, and budget alerts. Return a clear trial-ended or allowance-reached message without exposing provider details.
- Provide App Review with a review path that is not blocked by an expired trial or quota.
- Define the paid-access and entitlement model before public App Store distribution.

## Product priorities agreed October 25, 2026

### 1. Refresh the app design

- Review every screen as one product rather than polishing isolated cards.
- Establish a clearer visual system for typography, spacing, navigation, cards, actions, empty states, and feedback.
- Produce and review screen designs before changing the working implementation.
- Preserve the current meal, plan, journal, Health, progress, and email workflows during the redesign.

### 2. Add adaptive weekly plan guidance

- Use the athlete's active dietitian plan and confirmed meal logs to calculate the week's consumed allowance, remaining allowance, and remaining days.
- When intake runs ahead of the plan, show the variance immediately and offer a practical daily range for the rest of the week.
- Show the calculation clearly, including which plan target, meals, days, and assumptions were used.
- Treat roughly 7,700 kcal per kilogram as an explanatory energy-balance heuristic, not a promise of measured weight change.
- Never recommend intake below the dietitian's stated minimum or an agreed safety floor. Avoid punitive language and extreme compensation after one meal or day.
- If the plan has no numeric targets, data is missing, or the required adjustment would be unsafe, explain that and recommend checking with the dietitian instead of inventing a target.
- Include the week's variance and any guidance shown to the athlete in the dietitian update so the recommendation is reviewable.

### 3. Review the codebase, data model, and architecture

- Map the iOS shell, bundled web app, native HealthKit bridge, FastAPI backend, AI services, production deployment, and App Store configuration.
- Document where profile data, meals, journal notes, plans, extracted targets, Health summaries, and settings are stored today.
- Compare the current local WebView storage with `backend/app/db/schema.sql` and identify what is implemented, unused, duplicated, or missing.
- Review data ownership, privacy, authentication, sync, deletion, migrations, error handling, tests, and production observability.
- Produce a prioritized architecture plan before adding cloud persistence or materially changing storage.

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
