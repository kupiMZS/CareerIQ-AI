from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    resume_text: str = Field(
        ...,
        min_length=1,
        description="Extracted text from the user's resume",
    )


class AnalyzeResponse(BaseModel):
    ats_score: int = Field(
        ...,
        ge=0,
        le=100,
    )

    extracted_name: str | None = None

    extracted_email: str | None = None

    skills: list[str] = Field(default_factory=list)

    education: list[str] = Field(default_factory=list)

    experience: list[str] = Field(default_factory=list)

    summary: str

    status: str


class SkillEvidenceItem(BaseModel):
    """Literal evidence coverage for one extracted skill."""

    field_path: str
    skill_name: str

    status: Literal[
        "no_literal_evidence",
        "literal_mention_only",
        "explicit_rejection_only",
        "mixed_mentions",
    ]

    review_flags: list[
        Literal[
            "aspirational_wording",
            "requirement_wording",
            "rejection_with_contrast",
        ]
    ] = Field(default_factory=list)


class AnalyzeEvidenceResponse(BaseModel):
    """Existing analysis plus explicitly requested evidence."""

    analysis: AnalyzeResponse
    skill_evidence: list[SkillEvidenceItem] = Field(default_factory=list)
