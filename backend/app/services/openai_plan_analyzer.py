import asyncio
import base64
import json
import logging
import re

import httpx

from app.config import Settings
from app.schemas import PlanAnalysisRequest, PlanEstimate
from app.services.openai_meal_analyzer import MealAnalysisError, _find_output_text


logger = logging.getLogger("uvicorn.error")

PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "daily_calories": {"type": "integer", "minimum": 0, "maximum": 10000},
        "daily_protein": {"type": "number", "minimum": 0, "maximum": 1000},
        "weekly_calories": {"type": "integer", "minimum": 0, "maximum": 70000},
        "weekly_protein": {"type": "number", "minimum": 0, "maximum": 7000},
        "daily_calories_range": {"type": "array", "items": {"type": "integer", "minimum": 0, "maximum": 10000}},
        "daily_protein_range": {"type": "array", "items": {"type": "number", "minimum": 0, "maximum": 1000}},
        "weekly_calories_range": {"type": "array", "items": {"type": "integer", "minimum": 0, "maximum": 70000}},
        "weekly_protein_range": {"type": "array", "items": {"type": "number", "minimum": 0, "maximum": 7000}},
        "targets_are_estimated": {"type": "boolean"},
        "goal": {"type": "string"},
        "meal_schedule": {"type": "array", "items": {"type": "object", "properties": {"label": {"type": "string"}, "options": {"type": "array", "items": {"type": "string"}}}, "required": ["label", "options"], "additionalProperties": False}},
        "hydration": {"type": "string"},
        "weekly_rules": {"type": "array", "items": {"type": "string"}},
        "recipe_names": {"type": "array", "items": {"type": "string"}},
        "summary": {"type": "string"},
        "assumptions": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["daily_calories", "daily_protein", "weekly_calories", "weekly_protein", "daily_calories_range", "daily_protein_range", "weekly_calories_range", "weekly_protein_range", "targets_are_estimated", "goal", "meal_schedule", "hydration", "weekly_rules", "recipe_names", "summary", "assumptions"],
    "additionalProperties": False,
}


def _validate_file_data(body: PlanAnalysisRequest) -> None:
    if not body.file_data_url:
        return
    if body.content_type.startswith("image/"):
        pattern = r"^data:image/(jpeg|jpg|png|webp);base64,(.+)$"
        message = "Use a JPEG, PNG, or WebP plan image."
    elif body.content_type == "application/pdf" or body.filename.lower().endswith(".pdf"):
        pattern = r"^data:application/pdf;base64,(.+)$"
        message = "The uploaded plan is not a valid PDF."
    else:
        raise MealAnalysisError("Use a PDF, image, or text plan.", 422)
    match = re.match(pattern, body.file_data_url, flags=re.I | re.S)
    if not match:
        raise MealAnalysisError(message, 422)
    encoded = match.groups()[-1]
    try:
        raw = base64.b64decode(encoded, validate=True)
    except Exception as exc:
        raise MealAnalysisError(message, 422) from exc
    if not raw:
        raise MealAnalysisError("The uploaded plan is empty.", 422)
    if len(raw) > 12_000_000:
        raise MealAnalysisError("The uploaded plan is too large. Keep it under 12 MB.", 413)


async def analyze_plan(body: PlanAnalysisRequest, settings: Settings) -> PlanEstimate:
    key = settings.openai_api_key.strip()
    if not key or key == "replace_me":
        raise MealAnalysisError("Plan analysis is not configured on the server. Set OPENAI_API_KEY on the backend.", 503)

    _validate_file_data(body)
    content = [{"type": "input_text", "text": (
        "Extract the athlete's full nutrition plan: goal, meal windows and choices, hydration, weekly rules, recipes, "
        "and nutrition allowances. Preserve important portions and conditions. If explicit calorie and protein targets "
        "exist, use them and set targets_are_estimated=false. Otherwise estimate transparent low/high daily ranges from "
        "the listed portions and choices, set targets_are_estimated=true, and use each range midpoint as the representative "
        "daily value. Calculate seven-day ranges and representative totals from those daily values. "
        f"Athlete notes: {body.notes or 'None provided.'}"
    )}]
    if body.text and body.text.strip():
        content.append({"type": "input_text", "text": body.text.strip()})
    elif body.file_data_url:
        if body.content_type.startswith("image/"):
            content.append({"type": "input_image", "image_url": body.file_data_url, "detail": "high"})
        elif body.content_type == "application/pdf" or body.filename.lower().endswith(".pdf"):
            content.append({"type": "input_file", "filename": body.filename, "file_data": body.file_data_url})
        else:
            raise MealAnalysisError("Use a PDF, image, or text plan.", 422)
    else:
        raise MealAnalysisError("Choose a plan file or add baseline notes before analyzing.", 422)

    request = {
        "model": settings.openai_model,
        "store": False,
        "instructions": (
            "You extract a structured nutrition plan from a dietitian-authored document. Never present estimated calories "
            "or protein as explicit dietitian targets. Estimates must be grounded in listed portions and alternatives, use "
            "a realistic low/high range, and name the main uncertainty in assumptions. Keep meal options concise but retain "
            "quantities and training-day conditions. Weekly totals must match explicit plan totals or equal daily values "
            "multiplied by seven. Each range array must contain exactly [low, high] in ascending order."
        ),
        "input": [{"role": "user", "content": content}],
        "text": {"format": {"type": "json_schema", "name": "nutrition_plan", "strict": True, "schema": PLAN_SCHEMA}},
    }
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=10.0)) as client:
            response = await asyncio.wait_for(
                client.post(
                    "https://api.openai.com/v1/responses",
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    json=request,
                ),
                timeout=65.0,
            )
    except (httpx.TimeoutException, asyncio.TimeoutError) as exc:
        raise MealAnalysisError("Plan analysis timed out. The previous baseline was kept; please try again.", 504) from exc
    except httpx.RequestError as exc:
        raise MealAnalysisError("The server could not analyze this plan. The previous baseline was kept.", 503) from exc
    if response.status_code >= 400:
        logger.warning("plan_provider status=%s", response.status_code)
        raise MealAnalysisError("The plan analysis service rejected this file. Try a clear image, PDF, or text file.", 503)
    try:
        result = PlanEstimate.model_validate(json.loads(_find_output_text(response.json())))
    except (ValueError, TypeError, AttributeError) as exc:
        raise MealAnalysisError("Plan analysis returned invalid targets. The previous baseline was kept.") from exc
    if result.daily_calories <= 0 and result.daily_protein <= 0:
        raise MealAnalysisError("No usable nutrition allowance could be extracted. Add clearer plan pages or baseline notes.", 422)
    updates = {}
    if result.daily_calories > 0 and result.weekly_calories <= 0:
        updates["weekly_calories"] = result.daily_calories * 7
    elif result.weekly_calories > 0 and result.daily_calories <= 0:
        updates["daily_calories"] = round(result.weekly_calories / 7)
    if result.daily_protein > 0 and result.weekly_protein <= 0:
        updates["weekly_protein"] = result.daily_protein * 7
    elif result.weekly_protein > 0 and result.daily_protein <= 0:
        updates["daily_protein"] = result.weekly_protein / 7
    if updates:
        result = result.model_copy(update=updates)
    ranges = (
        result.daily_calories_range,
        result.daily_protein_range,
        result.weekly_calories_range,
        result.weekly_protein_range,
    )
    if any(len(value) != 2 or value[0] > value[1] for value in ranges):
        raise MealAnalysisError("Plan analysis returned invalid allowance ranges. The previous baseline was kept.")
    return result
