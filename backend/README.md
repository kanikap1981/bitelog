# BiteLog API

## Local start

```bash
cp .env.example .env
# Put your server-side OPENAI_API_KEY in .env
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Check `http://localhost:8000/health`.

The production API is deployed at `https://bitelog-api.vercel.app`. BiteLog 1.6.2 build 21 and later use that HTTPS origin automatically; the API key remains server-side.

## Production deploy

The Vercel project root is this `backend` directory. `app/main.py` is the FastAPI entrypoint and `vercel.json` configures the function duration. Production requires `OPENAI_API_KEY`, `OPENAI_MODEL`, `APP_ENV`, and `MAX_INLINE_IMAGE_BYTES` in Vercel's protected environment settings.

```bash
cd backend
vercel deploy --prod
curl https://bitelog-api.vercel.app/health
```

## Endpoints
- `GET /health`
- `POST /v1/meals/analyze-inline` — current mobile-compatible photo analysis
- `POST /v1/meals/analyze-voice` — transcribe a meal note and estimate nutrition
- `POST /v1/voice/transcribe` — transcribe a journal reflection without logging food
- `POST /v1/plans/analyze` — extract structured targets from a dietitian plan
- `POST /v1/uploads/presign` — scalable direct-upload primitive
- `POST /v1/meals/analyze` — analyze a remotely reachable image URL

## Photo-estimation troubleshooting and tests

See `../docs/PHOTO_ANALYSIS.md` for the exact API contract, Python 3.9 startup instructions, iPhone checks, and verification limits.

```bash
python -m unittest discover -s tests -v
node ../ios/tests/photo-analysis.test.cjs
```
