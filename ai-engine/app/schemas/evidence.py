from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class EvidenceRecord(BaseModel):
    """Internal metadata describing support for one extracted value."""

    model_config = ConfigDict(str_strip_whitespace=True)

    field_path: str = Field(min_length=1)
    extracted_value: str = Field(min_length=1)
    evidence_text: str = Field(min_length=1)

    source: Literal["deterministic", "provider_verified"]

    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )


EvidenceVerificationStatus = Literal[
    "excerpt_not_found",
    "claim_not_found",
    "explicitly_unsupported",
    "lexically_supported",
]


class EvidenceVerificationResult(BaseModel):
    """Outcome of conservative internal evidence verification."""

    status: EvidenceVerificationStatus
    excerpt_found: bool
    claim_found: bool
    explicitly_unsupported: bool = False
