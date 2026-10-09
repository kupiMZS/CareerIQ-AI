import pytest
from pydantic import ValidationError

from app.schemas.analysis import (
    AnalyzeRequest,
    AnalyzeResponse,
)
from app.schemas.resume import (
    Candidate,
    Publication,
    ResumeIntelligence,
    Skill,
)


def test_analyze_request_accepts_resume_text():
    request = AnalyzeRequest(resume_text="John Doe Python Developer")

    assert request.resume_text == "John Doe Python Developer"


def test_analyze_request_rejects_empty_text():
    with pytest.raises(ValidationError):
        AnalyzeRequest(resume_text="")


def test_skill_confidence_must_be_between_zero_and_one():
    with pytest.raises(ValidationError):
        Skill(
            name="Python",
            confidence=1.5,
        )


def test_resume_intelligence_schema():
    result = ResumeIntelligence(
        candidate=Candidate(
            name="John Doe",
            email="john.doe@example.com",
            headline="Software Engineer",
        ),
        professional_summary=("Backend software engineer."),
        skills=[
            Skill(
                name="Python",
                category="programming_language",
                confidence=0.98,
                evidence=["Built backend services using Python."],
            ),
            Skill(
                name="Docker",
                category="devops",
                confidence=0.90,
            ),
        ],
        publications=[
            Publication(
                title="Reliable Career Recommendation Systems",
                authors=[
                    "John Doe",
                    "Jane Smith",
                ],
                venue="Example Computing Journal",
                date="2025",
                url="https://example.com/publication",
            )
        ],
    )

    assert result.analysis_version == "1.0"
    assert result.candidate.name == "John Doe"
    assert len(result.skills) == 2
    assert result.skills[0].name == "Python"
    assert result.skills[0].confidence == 0.98

    assert len(result.publications) == 1
    assert result.publications[0].title == "Reliable Career Recommendation Systems"
    assert result.publications[0].authors == [
        "John Doe",
        "Jane Smith",
    ]
    assert result.publications[0].venue == "Example Computing Journal"
    assert result.publications[0].date == "2025"
    assert result.publications[0].url == "https://example.com/publication"


def test_resume_intelligence_publications_default_to_empty_list():
    result = ResumeIntelligence()

    assert result.publications == []


def test_publication_supports_partial_resume_data():
    publication = Publication(
        title="Career Intelligence with Language Models",
    )

    assert publication.title == "Career Intelligence with Language Models"
    assert publication.authors == []
    assert publication.venue is None
    assert publication.date is None
    assert publication.url is None


def test_analyze_response_remains_backward_compatible():
    response = AnalyzeResponse(
        ats_score=90,
        extracted_name="John Doe",
        extracted_email="john.doe@example.com",
        skills=[
            "python",
            "docker",
        ],
        education=[
            "BSc Computer Science",
        ],
        experience=[
            "Software Engineer",
        ],
        summary="Resume analyzed successfully.",
        status="completed",
    )

    assert response.ats_score == 90
    assert response.extracted_name == "John Doe"
    assert response.skills == [
        "python",
        "docker",
    ]
    assert response.status == "completed"
