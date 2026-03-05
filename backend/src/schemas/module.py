from pydantic import BaseModel


class DimensionScore(BaseModel):
    value: float
    justification: str
    normalized: float | None = None


class ModuleSummary(BaseModel):
    slug: str
    name: str
    category: str
    subcategory: str | None = None
    tagline: str | None = None
    status: str
    logo_url: str | None = None
    pricing_model: str | None = None


class ModuleDetail(BaseModel):
    slug: str
    name: str
    category: str
    subcategory: str | None = None
    status: str
    version: str

    # Identity
    tagline: str | None = None
    description: str
    logo_url: str | None = None
    website: str | None = None
    documentation: str | None = None
    github_url: str | None = None
    license: str | None = None
    pricing_model: str | None = None

    # Data
    technical_specs: dict = {}
    primary_use_cases: list[str] = []
    supported_operations: list[str] = []
    comparison_scores: dict = {}
    code_examples: list[dict] = []

    # Relationships
    alternatives: list[dict] = []
    complements: list[dict] = []
    pipeline_position: str | None = None

    # Knowledge
    knowledge_entries: list[dict] = []
    benchmarks: list[dict] = []


class CategoryResponse(BaseModel):
    slug: str
    name: str
    description: str | None = None
    icon: str | None = None
    module_count: int = 0
