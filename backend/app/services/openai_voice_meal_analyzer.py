import asyncio
import json
import logging

import httpx

from app.config import Settings
from app.schemas import VoiceMealEstimate
from app.services.openai_meal_analyzer import MealAnalysisError


logger = logging.getLogger("uvicorn.error")

VOICE_MEAL_SCHEMA = {
    "type": "object",
    "properties": {
        "understood": {"type": "boolean"},
        "name": {"type": "string"},
        "calories": {"type": "integer", "minimum": 0, "maximum": 10000},
        "protein": {"type": "number", "minimum": 0, "maximum": 1000},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "description": {"type": "string"},
        "assumptions": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["understood", "name", "calories", "protein", "confidence", "description", "assumptions"],
    "additionalProperties": False,
}


def _api_key(settings: Settings) -> str:
    key = settings.openai_api_key.strip()
    if not key or key == "replace_me":
        raise MealAnalysisError("Voice meal analysis is not configured on the server. Set OPENAI_API_KEY on the backend.", 503)
    return key


def _output_text(payload: dict) -> str:
    if not isinstance(payload, dict) or payload.get("status") != "completed":
        raise MealAnalysisError("Voice meal analysis did not finish. Please try again.")
    for item in payload.get("output", []):
        for content in (item.get("content") or []) if isinstance(item, dict) else []:
            if isinstance(content, dict) and content.get("type") == "refusal":
                raise MealAnalysisError("The voice note did not contain a clear meal. Nothing was saved.", 422)
            if isinstance(content, dict) and content.get("type") == "output_text" and content.get("text"):
                return content["text"]
    raise MealAnalysisError("Voice meal analysis returned no estimate. Nothing was saved.")


async def analyze_voice_meal(
    audio: bytes,
    content_type: str,
    extension: str,
    settings: Settings,
) -> VoiceMealEstimate:
    transcript = await transcribe_audio(audio, content_type, extension, settings)
    key = _api_key(settings)
    headers = {"Authorization": f"Bearer {key}"}
    timeout = httpx.Timeout(45.0, connect=10.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            estimate_response = await asyncio.wait_for(
                client.post(
                    "https://api.openai.com/v1/responses",
                    headers={**headers, "Content-Type": "application/json"},
                    json={
                        "model": settings.openai_model,
                        "store": False,
                        "instructions": (
                            "Convert a spoken food log into one estimated meal. Set understood=false when the transcript "
                            "does not clearly describe food or drink the athlete consumed; use empty name, zero nutrition, "
                            "and explain why in description. Otherwise estimate total calories and protein conservatively, "
                            "with assumptions about missing portions or ingredients."
                        ),
                        "input": [{"role": "user", "content": [{"type": "input_text", "text": transcript}]}],
                        "text": {"format": {"type": "json_schema", "name": "voice_meal_estimate", "strict": True, "schema": VOICE_MEAL_SCHEMA}},
                    },
                ),
                timeout=50.0,
            )
    except MealAnalysisError:
        raise
    except (httpx.TimeoutException, asyncio.TimeoutError) as exc:
        raise MealAnalysisError("Voice meal analysis timed out. Nothing was saved; please try again.", 504) from exc
    except (httpx.RequestError, ValueError) as exc:
        raise MealAnalysisError("The server could not analyze the voice note. Nothing was saved; please try again.", 503) from exc

    if estimate_response.status_code >= 400:
        logger.warning("voice_meal_provider status=%s", estimate_response.status_code)
        raise MealAnalysisError("The voice meal estimate failed. Nothing was saved; please try again.", 503)

    try:
        estimate = json.loads(_output_text(estimate_response.json()))
        if not estimate.get("understood") or not str(estimate.get("name", "")).strip():
            raise MealAnalysisError("The voice note did not contain a clear meal. Nothing was saved.", 422)
        estimate.pop("understood", None)
        return VoiceMealEstimate(transcript=transcript, **estimate)
    except MealAnalysisError:
        raise
    except (ValueError, TypeError, AttributeError) as exc:
        raise MealAnalysisError("Voice meal analysis returned an invalid estimate. Nothing was saved.") from exc


async def transcribe_audio(
    audio: bytes,
    content_type: str,
    extension: str,
    settings: Settings,
) -> str:
    """Transcribe a short journal or meal recording without storing the audio."""
    headers = {"Authorization": f"Bearer {_api_key(settings)}"}
    timeout = httpx.Timeout(45.0, connect=10.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await asyncio.wait_for(
                client.post(
                    "https://api.openai.com/v1/audio/transcriptions",
                    headers=headers,
                    data={
                        "model": "gpt-4o-mini-transcribe",
                        "response_format": "json",
                        "prompt": "A short athlete journal reflection or spoken food log.",
                    },
                    files={"file": (f"voice-note.{extension}", audio, content_type)},
                ),
                timeout=50.0,
            )
    except (httpx.TimeoutException, asyncio.TimeoutError) as exc:
        raise MealAnalysisError("Voice transcription timed out. Nothing was saved; please try again.", 504) from exc
    except httpx.RequestError as exc:
        raise MealAnalysisError("The server could not transcribe the voice note. Nothing was saved.", 503) from exc

    if response.status_code >= 400:
        logger.warning("voice_transcription_provider status=%s", response.status_code)
        raise MealAnalysisError("The voice note could not be transcribed. Nothing was saved.", 503)
    try:
        transcript = str(response.json().get("text", "")).strip()
    except (ValueError, AttributeError) as exc:
        raise MealAnalysisError("The voice note could not be understood. Nothing was saved.", 422) from exc
    if len(transcript) < 3:
        raise MealAnalysisError("The voice note could not be understood. Nothing was saved.", 422)
    return transcript
