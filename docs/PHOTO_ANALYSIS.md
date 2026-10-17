# Photo estimation: implementation and test guide

## Contract (preserved)

The bundled iOS HTML UI resizes a photo to at most 640 pixels on its longest edge and encodes JPEG at 0.68 quality for a smaller Wi-Fi upload. It sends:

`POST /v1/meals/analyze-inline`, `Content-Type: application/json`

```json
{"image_data_url":"data:image/jpeg;base64,..."}
```

Success is a JSON object containing `name` (nonempty string), `calories` (integer 0–10000 kcal), `protein` (number 0–1000 grams), `confidence` (number 0–1), `description` (string), and `assumptions` (array of strings). The athlete reviews/edits the estimate before saving. No meal is automatically saved by analysis.

Errors use a non-2xx status and a readable `detail` string. Every response includes `X-Request-ID`, also shown in photo errors for troubleshooting. Logs contain request ID, route, status and duration; they do not contain photos, API keys, or provider error bodies.

The backend alone calls `https://api.openai.com/v1/responses`. Its existing `gpt-5.6-luna` default and strict `text.format` JSON schema are preserved. Meal photos use `detail: low`, which the official vision guide defines for coarse image understanding; this avoids unnecessary high-detail processing for visible food identification and rough portion estimation. Verified against official documentation on September 20, 2026:
- https://developers.openai.com/api/docs/models/gpt-5.6-luna
- https://developers.openai.com/api/docs/guides/images-vision
- https://developers.openai.com/api/docs/guides/structured-outputs

## Run locally

From this project's backend directory, use the existing Python 3.9 environment if available. No dependency upgrades are required.

```bash
cd /Users/kanika/Documents/Healthapp/BiteLog-v1.2-production/backend
source /Users/kanika/Documents/Healthapp/BiteLogproduction/backend/.venv/bin/activate
```

If setting up a separate environment instead:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Create `.env` from `.env.example` only if `.env` does not already exist, and set your real `OPENAI_API_KEY` there. Keep `OPENAI_MODEL=gpt-5.6-luna` unless your account requires a different vision/structured-output model. Do not place the key in iOS settings or source.

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

No database, Redis or object store is needed for inline estimation. `/health` confirms the API is running, not that the AI key is valid.

## iPhone verification

1. Build/install this copy's `ios/BiteLogHealth.xcodeproj` in Xcode. Keep your existing team/signing settings.
2. Connect Mac and iPhone to the same Wi-Fi. Find the Mac's current IP with `ipconfig getifaddr en0` (or the active network interface).
3. In iPhone Safari, open `http://<MAC-IP>:8000/health`; expect `status: ok`.
4. In BiteLog Settings, enter `http://<MAC-IP>:8000` as **BiteLog API URL**. Never use localhost on the iPhone. Older full `/v1/meals/analyze-inline` URLs are normalized automatically.
5. Tap **Check API connection**, then Save. Allow Local Network access in iOS Settings if prompted. The existing Info.plist contains local networking permission and ATS local-network allowance.
6. Add a meal photo. Tap **Estimate from photo**. Confirm editable meal name, calories, protein, confidence, and assumptions appear. Review portions, then Save meal and check daily totals.
7. Stop the backend and retry: expect a readable connection error and manual entry to remain available. Restart it and retry successfully.
8. Start an estimate, cancel, and open another meal: the old response must not fill the new form.

## Automated regression checks

```bash
cd /Users/kanika/Documents/Healthapp/BiteLog-v1.2-production/backend
python -m unittest discover -s tests -v
node ../ios/tests/photo-analysis.test.cjs
```

Backend tests use a valid tiny PNG and mocked provider HTTP responses. They exercise the real FastAPI routes and provider request construction. UI tests execute the actual bundled JavaScript handlers with a minimal DOM. They are not a substitute for WebKit/device testing or a real meal-photo accuracy check.

## Verified and outstanding

Verified in the task workspace using the existing Python 3.9.6 environment: success contract, invalid/oversized upload rejection, missing key, provider failures, timeout, refusal/incomplete output, malformed estimates, CORS from a bundled-file origin, URL migration, network errors, precision of protein values, and stale response cancellation.

A live request through the optimized FastAPI route to OpenAI using the existing server-side configuration and a valid 64×64 synthetic PNG returned HTTP 200 with all six expected fields in 3.10 seconds; provider processing was 3.05 seconds. This establishes provider connectivity and contract compatibility; it does not establish nutrition accuracy. A first one-pixel fixture was rejected because its PNG CRC was invalid; the regression fixture now uses the valid image. BiteLog 1.5.2 build 11 built, signed, and installed on the physical iPhone. Real meal-photo speed and nutrition accuracy remain manual device checks. Full Xcode is available at `/Users/kanika/Downloads/Xcode.app`. No HealthKit functionality was changed. Local HTTP remains development-only; production authentication and HTTPS remain separate work.
