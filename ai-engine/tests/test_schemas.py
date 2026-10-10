import pytest
from pydantic import ValidationError

from app.schemas.analysis import (
    AnalyzeRequest,
    AnalyzeResponse,
)
from app.schemas.resume import (
    Achievement,
    Candidate,
    Language,
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


def test_language_schema_supports_explicit_proficiency():
    language = Language(
        name="English",
        proficiency="Professional working proficiency",
    )

    assert language.name == "English"
    assert language.proficiency == "Professional working proficiency"


def test_language_schema_allows_missing_proficiency():
    language = Language(
        name="Bangla",
    )

    assert language.name == "Bangla"
    assert language.proficiency is None


def test_resume_intelligence_supports_multiple_languages():
    intelligence = ResumeIntelligence(
        languages=[
            Language(
                name="English",
                proficiency="IELTS 7.5",
            ),
            Language(
                name="German",
                proficiency="B2",
            ),
        ]
    )

    assert len(intelligence.languages) == 2

    assert intelligence.languages[0].name == "English"
    assert intelligence.languages[0].proficiency == "IELTS 7.5"

    assert intelligence.languages[1].name == "German"
    assert intelligence.languages[1].proficiency == "B2"


def test_resume_intelligence_defaults_languages_to_empty_list():
    intelligence = ResumeIntelligence()

    assert intelligence.languages == []
    assert intelligence.analysis_version == "1.0"


def test_achievement_schema_supports_explicit_metadata():
    achievement = Achievement(
        title="Best Capstone Project",
        description=("Selected as the top project from 42 teams."),
        organization="Example University",
        date="2025",
    )

    assert achievement.title == "Best Capstone Project"
    assert achievement.description == "Selected as the top project from 42 teams."
    assert achievement.organization == "Example University"
    assert achievement.date == "2025"


def test_achievement_schema_allows_partial_resume_data():
    achievement = Achievement(
        title="Employee of the Month",
    )

    assert achievement.title == "Employee of the Month"
    assert achievement.description is None
    assert achievement.organization is None
    assert achievement.date is None


def test_resume_intelligence_supports_multiple_achievements():
    intelligence = ResumeIntelligence(
        achievements=[
            Achievement(
                title="Winner, AI Hackathon",
                organization="Example Tech",
                date="2025",
            ),
            Achievement(
                title="Dean's List",
                organization="Example University",
            ),
        ]
    )

    assert len(intelligence.achievements) == 2

    assert intelligence.achievements[0].title == "Winner, AI Hackathon"
    assert intelligence.achievements[0].organization == "Example Tech"
    assert intelligence.achievements[0].date == "2025"

    assert intelligence.achievements[1].title == "Dean's List"
    assert intelligence.achievements[1].organization == "Example University"


def test_resume_intelligence_defaults_achievements_to_empty_list():
    intelligence = ResumeIntelligence()

    assert intelligence.achievements == []
    assert intelligence.analysis_version == "1.0"
