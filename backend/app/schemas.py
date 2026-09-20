from pydantic import BaseModel, Field, HttpUrl


class InlineMealAnalysisRequest(BaseModel):
    image_data_url: str = Field(min_length=32)


class ObjectMealAnalysisRequest(BaseModel):
    image_url: HttpUrl


class MealEstimate(BaseModel):
    name: str = Field(min_length=1, pattern=r"\S")
    calories: int = Field(ge=0, le=10000)
    protein: float = Field(ge=0, le=1000)
    confidence: float = Field(ge=0, le=1)
    description: str = ""
    assumptions: list[str] = Field(default_factory=list)


class PresignRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=180)
    content_type: str = Field(pattern=r"^image/")


class PresignResponse(BaseModel):
    object_key: str
    upload_url: str
    headers: dict[str, str]
