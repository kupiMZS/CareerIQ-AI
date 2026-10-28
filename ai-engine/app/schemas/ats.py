from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ATSFinding(BaseModel):
    """One explainable, observable assessment finding."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
    )

    code: str = Field(min_length=1)

    status: Literal[
        "satisfied",
        "needs_attention",
        "not_assessed",
    ]

    explanation: str = Field(min_length=1)

    supporting_text: list[str] = Field(default_factory=list)

    recommendation: str | None = None


class ATSReport(BaseModel):
    """Internal Phase 3 assessment contract."""

    model_config = ConfigDict(extra="forbid")

    report_version: Literal["ats-v1"] = "ats-v1"

    score: int | None = Field(
        default=None,
        ge=0,
        le=100,
    )

    findings: list[ATSFinding] = Field(default_factory=list)

    limitations: list[str] = Field(default_factory=list)
