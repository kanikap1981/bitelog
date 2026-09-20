import asyncio
import json
import logging
from typing import Any

import httpx

from app.config import Settings
from app.schemas import MealEstimate


MEAL_SCHEMA = {
    "type": "object",
    "properties": {
        "name": {"type": "string"},
        "calories": {"type": "integer", "minimum": 0, "maximum": 10000},
        "protein": {"type": "number", "minimum": 0, "maximum": 1000},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "description": {"type": "string"},
        "assumptions": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["name", "calories", "protein", "confidence", "description", "assumptions"],
    "additionalProperties": False,
}


logger = logging.getLogger("uvicorn.error")


class MealAnalysisError(RuntimeError):
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message)
        self.status_code = status_code


def _find_output_text(payload: dict[str, Any]) -> str:
    if not isinstance(payload, dict) or payload.get("status") != "completed":
        raise MealAnalysisError("Photo analysis did not finish. Please try again.")
    # Responses API output is a sequence of items; message items contain content blocks.
    for item in payload.get("output", []):
        for content in (item.get("content") or []) if isinstance(item, dict) else []:
            if isinstance(content, dict) and content.get("type") == "refusal":
                raise MealAnalysisError("This photo could not be analyzed. Try a clear photo of your meal.", 422)
            if isinstance(content, dict) and content.get("type") == "output_text" and content.get("text"):
                return content["text"]
    # Defensive fallback for SDK/API representations that expose output_text directly.
    if isinstance(payload.get("output_text"), str) and payload["output_text"]:
        return payload["output_text"]
    raise MealAnalysisError("Model returned no structured meal estimate")


async def analyze_meal(image_url: str, settings: Settings) -> MealEstimate:
    if not settings.openai_api_key.strip() or settings.openai_api_key == "replace_me":
        raise MealAnalysisError("Photo analysis is not configured on the server. Set OPENAI_API_KEY on the backend.", 503)

    request_body = {
        "model": settings.openai_model,
        "store": False,
        "instructions": (
            "You estimate food nutrition from a meal photo. Be conservative and transparent. "
            "Return the likely meal name, total calories, total protein in grams, a confidence from 0 to 1, "
            "a short description, and concise assumptions about portions or hidden ingredients. "
            "This is an estimate, not medical advice."
        ),
        "input": [{
            "role": "user",
            "content": [
                {"type": "input_text", "text": "Estimate this meal from the photo."},
                {"type": "input_image", "image_url": image_url, "detail": "high"},
            ],
        }],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "meal_estimate",
                "strict": True,
                "schema": MEAL_SCHEMA,
            }
        },
    }

    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json",
    }
    timeout = httpx.Timeout(45.0, connect=10.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await asyncio.wait_for(
                client.post("https://api.openai.com/v1/responses", headers=headers, json=request_body),
                timeout=50.0,
            )
    except (httpx.TimeoutException, asyncio.TimeoutError) as exc:
        raise MealAnalysisError("Photo analysis timed out. Please try again.", 504) from exc
    except httpx.RequestError as exc:
        raise MealAnalysisError("The server could not reach the photo analysis service. Please try again.", 503) from exc

    if response.status_code >= 400:
        # Never echo provider bodies: they may contain credentials or submitted content.
        logger.warning("meal_provider status=%s", response.status_code)
        if response.status_code in (401, 403):
            raise MealAnalysisError("Photo analysis credentials were rejected. Check the backend API key and model access.", 503)
        if response.status_code == 429:
            raise MealAnalysisError("Photo analysis is temporarily unavailable. Try later; check server quota if this continues.", 503)
        raise MealAnalysisError("The photo analysis service rejected the request. Check the server model configuration or try another photo.")

    try:
        text = _find_output_text(response.json())
        return MealEstimate.model_validate(json.loads(text))
    except (ValueError, TypeError, AttributeError) as exc:
        raise MealAnalysisError("Photo analysis returned an invalid estimate. Please try again.") from exc
