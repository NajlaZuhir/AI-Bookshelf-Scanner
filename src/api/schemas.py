from pydantic import BaseModel, ConfigDict, Field


class ScanCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    image_path: str = Field(min_length=1)


class RecommendationCreate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    preference_text: str = Field(min_length=1)
    top_k: int | None = Field(default=3, gt=0, strict=True)