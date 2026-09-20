import base64
import logging
import re
import time
import uuid

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import Settings, get_settings
from app.schemas import (
    InlineMealAnalysisRequest,
    MealEstimate,
    ObjectMealAnalysisRequest,
    PresignRequest,
    PresignResponse,
)
from app.services.openai_meal_analyzer import MealAnalysisError, analyze_meal
from app.services.storage import presign_upload

app = FastAPI(title="BiteLog API", version="1.2.0")
logger = logging.getLogger("uvicorn.error")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


@app.middleware("http")
async def request_diagnostics(request: Request, call_next):
    request.state.request_id = uuid.uuid4().hex
    started = time.monotonic()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    logger.info("request_id=%s method=%s path=%s status=%s duration_ms=%d",
                request.state.request_id, request.method, request.url.path,
                response.status_code, (time.monotonic() - started) * 1000)
    return response


@app.exception_handler(MealAnalysisError)
async def meal_analysis_error_handler(_: Request, exc: MealAnalysisError):
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})


@app.get("/health")
async def health():
    return {"status": "ok", "service": "bitelog-api", "version": "1.2.0"}


def _validate_inline_image(data_url: str, settings: Settings) -> None:
    match = re.match(r"^data:image/(jpeg|jpg|png|webp);base64,(.+)$", data_url, flags=re.I | re.S)
    if not match:
        raise HTTPException(status_code=400, detail="Expected a JPEG, PNG, or WebP data URL")
    if len(match.group(2)) > 4 * ((settings.max_inline_image_bytes + 2) // 3):
        raise HTTPException(status_code=413, detail="Image is too large for inline analysis")
    try:
        raw = base64.b64decode(match.group(2), validate=True)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid base64 image") from exc
    if len(raw) > settings.max_inline_image_bytes:
        raise HTTPException(status_code=413, detail="Image is too large for inline analysis")
    if not raw:
        raise HTTPException(status_code=400, detail="The photo is empty. Choose another photo.")


@app.post("/v1/meals/analyze-inline", response_model=MealEstimate)
async def analyze_inline(
    body: InlineMealAnalysisRequest,
    settings: Settings = Depends(get_settings),
):
    """MVP/mobile-compatible path. The API key stays server-side.

    For scale, migrate the app to /v1/uploads/presign and analyze by object URL.
    """
    _validate_inline_image(body.image_data_url, settings)
    return await analyze_meal(body.image_data_url, settings)


@app.post("/v1/meals/analyze", response_model=MealEstimate)
async def analyze_object(
    body: ObjectMealAnalysisRequest,
    settings: Settings = Depends(get_settings),
):
    return await analyze_meal(str(body.image_url), settings)


@app.post("/v1/uploads/presign", response_model=PresignResponse)
async def create_presigned_upload(
    body: PresignRequest,
    settings: Settings = Depends(get_settings),
):
    try:
        return presign_upload(body.filename, body.content_type, settings)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Storage is not configured: {exc}") from exc
