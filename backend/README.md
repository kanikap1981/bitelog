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

For an iPhone on the same Wi-Fi, use your Mac's LAN IP in BiteLog settings, for example `http://192.168.1.25:8000`.
For real production, deploy the API behind HTTPS and enter that HTTPS origin once; the API key remains server-side.

## Endpoints
- `GET /health`
- `POST /v1/meals/analyze-inline` — current mobile-compatible photo analysis
- `POST /v1/uploads/presign` — scalable direct-upload primitive
- `POST /v1/meals/analyze` — analyze a remotely reachable image URL

## Photo-estimation troubleshooting and tests

See `../docs/PHOTO_ANALYSIS.md` for the exact API contract, Python 3.9 startup instructions, iPhone checks, and verification limits. In app Settings, **Check API connection** verifies `/health`; an actual photo estimate separately checks the AI provider. Full legacy analysis URLs are normalized to the base URL automatically.

```bash
python -m unittest discover -s tests -v
node ../ios/tests/photo-analysis.test.cjs
```
