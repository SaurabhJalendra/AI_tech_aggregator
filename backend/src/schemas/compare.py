from pydantic import BaseModel, Field


class CompareRequest(BaseModel):
    slugs: list[str] = Field(..., min_length=2, max_length=5)
    dimensions: list[str] | None = None
    weights: dict[str, float] | None = None


class Score(BaseModel):
    value: float
    justification: str
    normalized: float


class ComparisonResult(BaseModel):
    modules: list[str]
    dimensions: list[str]
    matrix: dict[str, dict[str, Score]]
    rankings: dict[str, list[str]]
    overall_ranking: list[str]
    highlights: dict[str, list[str]]
    recommendation: str
