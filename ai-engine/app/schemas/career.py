from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CareerProfile(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    current_role: str | None = None
    career_goal: str | None = None

    years_experience: float | None = Field(
        default=None,
        ge=0.0,
    )

    education: list[str] = Field(
        default_factory=list,
    )

    interests: list[str] = Field(
        default_factory=list,
    )


class CareerRecommendationRequest(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    profile: CareerProfile = Field(
        default_factory=CareerProfile,
    )

    skills: list[str] = Field(
        default_factory=list,
    )


class CareerRecommendation(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    career_title: str

    match_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
    )

    rationale: str

    matched_skills: list[str] = Field(
        default_factory=list,
    )

    missing_skills: list[str] = Field(
        default_factory=list,
    )

    entry_level: bool = False


class LearningRoadmapStep(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    step: int = Field(
        ...,
        ge=1,
    )

    title: str
    description: str

    skills: list[str] = Field(
        default_factory=list,
    )


class CareerRecommendationResponse(BaseModel):
    recommendation_version: str = "1.0"

    status: Literal[
        "ok",
        "needs_more_information",
    ]

    recommendations: list[CareerRecommendation] = Field(
        default_factory=list,
    )

    roadmap: list[LearningRoadmapStep] = Field(
        default_factory=list,
    )

    missing_information: list[str] = Field(
        default_factory=list,
    )
