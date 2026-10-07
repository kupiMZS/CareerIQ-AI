from app.schemas.resume import (
    Candidate,
    Education,
    Experience,
    ResumeIntelligence,
    Skill,
)
from app.services.analysis_response_adapter import (
    build_analysis_response,
)


def test_adapter_builds_legacy_response():
    resume_text = """
John Doe
john.doe@example.com

Skills
Python
Laravel

Education
BSc Computer Science

Experience
Software Engineer at ABC Technologies
""".strip()

    intelligence = ResumeIntelligence(
        candidate=Candidate(
            name="John Doe",
            email="john.doe@example.com",
        ),
        skills=[
            Skill(
                name="python",
            ),
            Skill(
                name="laravel",
            ),
        ],
        education=[
            Education(
                degree="BSc Computer Science",
            )
        ],
        experience=[
            Experience(
                job_title=("Software Engineer at ABC Technologies"),
            )
        ],
    )

    response = build_analysis_response(
        resume_text,
        intelligence,
    )

    assert response.extracted_name == "John Doe"

    assert response.extracted_email == "john.doe@example.com"

    assert response.skills == [
        "python",
        "laravel",
    ]

    assert response.education == ["BSc Computer Science"]

    assert response.experience == [("Software Engineer at ABC Technologies")]

    assert response.status == "completed"

    assert 0 <= response.ats_score <= 100


def test_adapter_formats_rich_llm_fields():
    resume_text = """
Jane Doe
jane@example.com
Software Engineer
""".strip()

    intelligence = ResumeIntelligence(
        candidate=Candidate(
            name="Jane Doe",
            email="jane@example.com",
        ),
        professional_summary=("Experienced software engineer."),
        education=[
            Education(
                institution="Example University",
                degree="BSc",
                field_of_study="Computer Science",
            )
        ],
        experience=[
            Experience(
                company="Example Technologies",
                job_title="Software Engineer",
            )
        ],
    )

    response = build_analysis_response(
        resume_text,
        intelligence,
    )

    assert response.education == [("BSc Computer Science at Example University")]

    assert response.experience == [("Software Engineer at Example Technologies")]

    assert response.summary == "Experienced software engineer."


def test_adapter_uses_rule_based_fallback_for_missing_fields():
    resume_text = """
John Doe
john.doe@example.com

Python Docker MySQL

Education
BSc Computer Science

Experience
Software Engineer at ABC Technologies
""".strip()

    intelligence = ResumeIntelligence()

    response = build_analysis_response(
        resume_text,
        intelligence,
    )

    assert response.extracted_name == "John Doe"

    assert response.extracted_email == "john.doe@example.com"

    assert "python" in response.skills

    assert response.summary

    assert response.status == "completed"
