from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.career import CareerRecommendationRequest


class ExpectedEducation(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    degree: str | None = None
    institution: str | None = None


class ExpectedExperience(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    job_title: str | None = None
    company: str | None = None


class ExpectedResumeExtraction(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    name: str | None = None
    email: str | None = None

    skills: list[str] = Field(
        default_factory=list,
    )

    education: list[ExpectedEducation] = Field(
        default_factory=list,
    )

    experience: list[ExpectedExperience] = Field(
        default_factory=list,
    )


class ExpectedExtendedEducation(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    degree: str | None = None
    institution: str | None = None
    field_of_study: str | None = None
    start_date: str | None = None
    end_date: str | None = None


class ExpectedExtendedExperience(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    job_title: str | None = None
    company: str | None = None
    start_date: str | None = None
    end_date: str | None = None

    responsibilities: list[str] = Field(
        default_factory=list,
    )


class ExpectedProject(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    name: str
    description: str | None = None

    technologies: list[str] = Field(
        default_factory=list,
    )


class ExpectedCertification(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    name: str
    issuer: str | None = None
    date: str | None = None


class ExpectedPublication(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    title: str

    authors: list[str] = Field(
        default_factory=list,
    )

    venue: str | None = None
    date: str | None = None
    url: str | None = None


class ExpectedExtendedResumeExtraction(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    headline: str | None = None

    education: list[ExpectedExtendedEducation] = Field(
        default_factory=list,
    )

    experience: list[ExpectedExtendedExperience] = Field(
        default_factory=list,
    )

    projects: list[ExpectedProject] = Field(
        default_factory=list,
    )

    certifications: list[ExpectedCertification] = Field(
        default_factory=list,
    )


class ExpectedLanguage(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    name: str
    proficiency: str | None = None


class ExpectedPhase2ResumeExtraction(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    publications: list[ExpectedPublication] | None = None

    languages: list[ExpectedLanguage] | None = None


class ResumeEvalCase(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    case_id: str = Field(
        min_length=1,
    )

    description: str = Field(
        min_length=1,
    )

    tags: list[str] = Field(
        default_factory=list,
    )

    resume_text: str = Field(
        min_length=1,
    )

    expected: ExpectedResumeExtraction

    extended_expected: ExpectedExtendedResumeExtraction | None = None

    phase2_expected: ExpectedPhase2ResumeExtraction | None = None


class ExpectedCareerRecommendation(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    status: Literal[
        "ok",
        "needs_more_information",
    ]

    top_career: str | None = None

    relevant_careers: list[str] = Field(
        default_factory=list,
    )

    missing_skills: list[str] = Field(
        default_factory=list,
    )

    roadmap_skills: list[str] = Field(
        default_factory=list,
    )

    entry_level: bool | None = None

    missing_information: list[str] = Field(
        default_factory=list,
    )


class CareerEvalCase(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
    )

    case_id: str = Field(
        min_length=1,
    )

    description: str = Field(
        min_length=1,
    )

    tags: list[str] = Field(
        default_factory=list,
    )

    request: CareerRecommendationRequest

    expected: ExpectedCareerRecommendation
