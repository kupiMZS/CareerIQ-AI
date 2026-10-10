from pydantic import BaseModel, Field


class Candidate(BaseModel):
    name: str | None = None
    email: str | None = None
    headline: str | None = None


class Skill(BaseModel):
    name: str

    category: str | None = None

    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
    )

    evidence: list[str] = Field(default_factory=list)


class Education(BaseModel):
    institution: str | None = None
    degree: str | None = None
    field_of_study: str | None = None
    start_date: str | None = None
    end_date: str | None = None


class Experience(BaseModel):
    company: str | None = None
    job_title: str | None = None
    start_date: str | None = None
    end_date: str | None = None

    responsibilities: list[str] = Field(default_factory=list)


class Project(BaseModel):
    name: str

    description: str | None = None

    technologies: list[str] = Field(default_factory=list)


class Certification(BaseModel):
    name: str

    issuer: str | None = None

    date: str | None = None


class Publication(BaseModel):
    title: str

    authors: list[str] = Field(default_factory=list)

    venue: str | None = None

    date: str | None = None

    url: str | None = None


class Language(BaseModel):
    name: str

    proficiency: str | None = None


class Achievement(BaseModel):
    title: str

    description: str | None = None

    organization: str | None = None

    date: str | None = None


class ResumeIntelligence(BaseModel):
    analysis_version: str = "1.0"

    candidate: Candidate = Field(default_factory=Candidate)

    professional_summary: str | None = None

    skills: list[Skill] = Field(default_factory=list)

    education: list[Education] = Field(default_factory=list)

    experience: list[Experience] = Field(default_factory=list)

    projects: list[Project] = Field(default_factory=list)

    certifications: list[Certification] = Field(default_factory=list)

    publications: list[Publication] = Field(default_factory=list)

    languages: list[Language] = Field(default_factory=list)

    achievements: list[Achievement] = Field(default_factory=list)
