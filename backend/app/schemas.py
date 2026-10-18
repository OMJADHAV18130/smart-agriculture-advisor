"""Pydantic request/response schemas for the advisory API."""

from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from . import dataset

Rainfall = Literal["Yes", "No", "Unknown"]
Symptom = Literal["None", "Yellowing Leaves", "Leaf Spots", "Insects and Leaf Damage", "Wilting"]


class AnalyzeRequest(BaseModel):
    """Facts collected from the farmer/student using the dashboard."""

    crop: str = Field(
        ...,
        min_length=1,
        description="Crop label exactly as listed in GET /crops (dataset labels, "
                    "e.g. 'rice', 'cotton', 'mango')",
        examples=["rice"],
    )
    soil_moisture: int = Field(..., ge=0, le=100, description="Soil moisture percent (0-100)")
    rainfall: Rainfall = Field(..., description="Significant rain in the last ~7 days?")
    temperature: float = Field(..., ge=-20, le=60, description="Air temperature in Celsius")
    humidity: float = Field(60, ge=0, le=100, description="Relative humidity percent (0-100)")
    ph: float = Field(7.0, ge=0, le=14, description="Soil pH (0-14)")
    symptom: Symptom = Field("None", description="Most noticeable plant symptom")
    goal: Optional[str] = Field(
        None,
        description="Optional fact to verify with backward chaining, e.g. 'irrigation=needed'",
    )

    @field_validator("crop")
    @classmethod
    def crop_must_exist_in_dataset(cls, value: str) -> str:
        """Accept only crops present in the bundled dataset (case-insensitive,
        normalized to the dataset's lowercase label). If the CSV cannot be
        loaded, any non-empty crop is accepted so the API still works."""
        value = value.strip().lower()
        labels = dataset.crop_labels()
        if labels and value not in labels:
            raise ValueError(
                f"crop '{value}' is not in the dataset; use one of: "
                f"{', '.join(labels)}"
            )
        return value


class Summary(BaseModel):
    """One-line verdict shown as a banner in the UI."""

    status: Literal["normal", "monitor", "attention"]
    headline: str
    detail: str


class Conclusion(BaseModel):
    issue: str
    category: str  # irrigation | stress | leaf_symptoms | pest | soil_nutrient
    source_rules: List[str]


class Recommendation(BaseModel):
    advice: str
    source_rules: List[str]


class BackwardChainResult(BaseModel):
    goal: str
    supported: bool
    proof: List[str]


class DatasetReference(BaseModel):
    """Per-crop typical ranges computed from backend/data/*.csv (no ML)."""

    available: bool
    crop: str
    source: str  # "crop" (rows found) | "all_crops" (fallback) | "unavailable"
    rows_for_crop: int
    typical_ranges: dict          # metric -> {min, max, p10, p90}
    deviations: List[str]         # human-readable out-of-range readings


class AnalyzeResponse(BaseModel):
    summary: Summary
    conclusions: List[Conclusion]
    recommendations: List[Recommendation]
    fired_rule_ids: List[str]
    inferred_facts: List[str]
    rules_evaluated: int
    reasoning_trace: List[str]
    backward_chain: Optional[BackwardChainResult] = None
    dataset_reference: Optional[DatasetReference] = None
    note: str


class HealthResponse(BaseModel):
    status: str
    environment: Optional[str] = "development"
    rules_loaded: int
    thresholds: dict
    dataset: dict

