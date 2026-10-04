from app.schemas.resume import (
    Candidate,
    Education,
    Experience,
    ResumeIntelligence,
    Skill,
)
from app.services.resume_intelligence_enricher import (
    enrich_resume_intelligence,
)

RESUME = """
John Doe
john.doe@example.com

Software Engineer

Skills
Python
Laravel
Docker
MySQL

Education
BSc Computer Science

Experience
Software Engineer at ABC Technologies
""".strip()


def test_enricher_fills_missing_email():
    intelligence = ResumeIntelligence(
        candidate=Candidate(
            name="John Doe",
        )
    )

    result = enrich_resume_intelligence(
        RESUME,
        intelligence,
    )

    assert result.candidate.email == "john.doe@example.com"


def test_enricher_preserves_existing_llm_values():
    intelligence = ResumeIntelligence(
        candidate=Candidate(
            name="LLM Name",
            email="llm@example.com",
        )
    )

    result = enrich_resume_intelligence(
        RESUME,
        intelligence,
    )

    assert result.candidate.name == "LLM Name"
    assert result.candidate.email == "llm@example.com"


def test_enricher_merges_skills_without_duplicates():
    intelligence = ResumeIntelligence(
        skills=[
            Skill(
                name="Python",
            )
        ]
    )

    result = enrich_resume_intelligence(
        RESUME,
        intelligence,
    )

    skill_names = {skill.name.casefold() for skill in result.skills}

    assert skill_names == {
        "python",
        "laravel",
        "docker",
        "mysql",
    }


def test_enricher_fills_missing_education_degree():
    intelligence = ResumeIntelligence(education=[Education()])

    result = enrich_resume_intelligence(
        RESUME,
        intelligence,
    )

    assert result.education[0].degree == "BSc Computer Science"


def test_enricher_fills_missing_experience_company():
    intelligence = ResumeIntelligence(
        experience=[
            Experience(
                job_title="Software Engineer",
            )
        ]
    )

    result = enrich_resume_intelligence(
        RESUME,
        intelligence,
    )

    assert result.experience[0].job_title == "Software Engineer"

    assert result.experience[0].company == "ABC Technologies"


def test_enricher_does_not_mutate_original_result():
    intelligence = ResumeIntelligence(
        candidate=Candidate(
            name="John Doe",
        ),
        experience=[
            Experience(
                job_title="Software Engineer",
            )
        ],
    )

    result = enrich_resume_intelligence(
        RESUME,
        intelligence,
    )

    assert intelligence.candidate.email is None
    assert intelligence.experience[0].company is None

    assert result.candidate.email == "john.doe@example.com"

    assert result.experience[0].company == "ABC Technologies"


def test_enricher_normalizes_rule_based_experience_without_duplicate():
    intelligence = ResumeIntelligence(
        experience=[
            Experience(
                job_title=("Software Engineer at ABC Technologies"),
            )
        ]
    )

    result = enrich_resume_intelligence(
        RESUME,
        intelligence,
    )

    assert len(result.experience) == 1

    assert result.experience[0].job_title == "Software Engineer"

    assert result.experience[0].company == "ABC Technologies"


def test_enricher_does_not_add_headline_as_experience_without_section():
    result = enrich_resume_intelligence(
        (
            "Nora Ibrahim\n"
            "nora.ibrahim@example.com\n"
            "Cloud Engineer\n\n"
            "Certifications\n"
            "AWS Developer Associate\n"
            "Amazon Web Services\n"
            "2025"
        ),
        ResumeIntelligence(),
    )

    assert result.experience == []


def test_enricher_keeps_structured_experience_without_section_heading():
    result = enrich_resume_intelligence(
        (
            "Lucas Martin\n"
            "lucas.martin@example.com\n"
            "Software Developer at Bright Apps\n"
            "Python\n"
            "Git\n"
            "Docker"
        ),
        ResumeIntelligence(),
    )

    assert len(result.experience) == 1

    assert result.experience[0].job_title == "Software Developer"

    assert result.experience[0].company == "Bright Apps"
