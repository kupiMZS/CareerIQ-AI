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
