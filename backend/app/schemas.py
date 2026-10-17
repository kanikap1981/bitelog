from typing import Optional

from pydantic import BaseModel, Field, HttpUrl


class InlineMealAnalysisRequest(BaseModel):
    image_data_url: str = Field(min_length=32)


class VoiceMealAnalysisRequest(BaseModel):
    audio_data_url: str = Field(min_length=32)


class ObjectMealAnalysisRequest(BaseModel):
    image_url: HttpUrl


class MealEstimate(BaseModel):
    name: str = Field(min_length=1, pattern=r"\S")
    calories: int = Field(ge=0, le=10000)
    protein: float = Field(ge=0, le=1000)
    confidence: float = Field(ge=0, le=1)
    description: str = ""
    assumptions: list[str] = Field(default_factory=list)


class VoiceMealEstimate(MealEstimate):
    transcript: str = Field(min_length=1)


class VoiceTranscription(BaseModel):
    transcript: str = Field(min_length=1)


class PlanAnalysisRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=180)
    content_type: str = Field(min_length=1, max_length=100)
    file_data_url: Optional[str] = Field(default=None, max_length=17000000)
    text: Optional[str] = Field(default=None, max_length=50000)
    notes: str = Field(default="", max_length=10000)


class PlanMealWindow(BaseModel):
    label: str = Field(min_length=1)
    options: list[str] = Field(default_factory=list)


class PlanEstimate(BaseModel):
    daily_calories: int = Field(ge=0, le=10000)
    daily_protein: float = Field(ge=0, le=1000)
    weekly_calories: int = Field(ge=0, le=70000)
    weekly_protein: float = Field(ge=0, le=7000)
    daily_calories_range: list[int] = Field(min_length=2, max_length=2)
    daily_protein_range: list[float] = Field(min_length=2, max_length=2)
    weekly_calories_range: list[int] = Field(min_length=2, max_length=2)
    weekly_protein_range: list[float] = Field(min_length=2, max_length=2)
    targets_are_estimated: bool
    goal: str = ""
    meal_schedule: list[PlanMealWindow] = Field(default_factory=list)
    hydration: str = ""
    weekly_rules: list[str] = Field(default_factory=list)
    recipe_names: list[str] = Field(default_factory=list)
    summary: str = Field(min_length=1)
    assumptions: list[str] = Field(default_factory=list)


class PresignRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=180)
    content_type: str = Field(pattern=r"^image/")


class PresignResponse(BaseModel):
    object_key: str
    upload_url: str
    headers: dict[str, str]
