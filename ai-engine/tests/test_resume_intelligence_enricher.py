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


def test_enricher_fills_missing_headline_from_resume_preamble():
    result = enrich_resume_intelligence(
        (
            "Aisha Rahman\n"
            "aisha.rahman@example.com\n"
            "Senior Backend Engineer\n\n"
            "Skills\n"
            "Python\n"
            "FastAPI"
        ),
        ResumeIntelligence(),
    )

    assert result.candidate.headline == "Senior Backend Engineer"


def test_enricher_preserves_existing_llm_headline():
    intelligence = ResumeIntelligence(
        candidate=Candidate(
            headline="LLM Headline",
        )
    )

    result = enrich_resume_intelligence(
        (
            "Aisha Rahman\n"
            "aisha.rahman@example.com\n"
            "Senior Backend Engineer\n\n"
            "Skills\n"
            "Python"
        ),
        intelligence,
    )

    assert result.candidate.headline == "LLM Headline"


def test_enricher_does_not_infer_headline_from_experience_section():
    result = enrich_resume_intelligence(
        (
            "Aisha Rahman\n"
            "aisha.rahman@example.com\n\n"
            "Experience\n"
            "Senior Backend Engineer at Nova Systems"
        ),
        ResumeIntelligence(),
    )

    assert result.candidate.headline is None


def test_enricher_uses_literal_experience_dates_from_section():
    intelligence = ResumeIntelligence(
        experience=[
            Experience(
                job_title="Backend Engineer",
                start_date="2021-00-00",
            )
        ]
    )

    result = enrich_resume_intelligence(
        (
            "Aisha Rahman\n"
            "aisha.rahman@example.com\n"
            "Senior Backend Engineer\n\n"
            "Experience\n"
            "Backend Engineer at Nova Systems\n"
            "2021 - Present\n"
            "Built REST APIs"
        ),
        intelligence,
    )

    assert len(result.experience) == 1
    assert result.experience[0].company == "Nova Systems"
    assert result.experience[0].start_date == "2021"
    assert result.experience[0].end_date == "Present"


def test_enricher_clears_unsupported_experience_dates_without_evidence():
    intelligence = ResumeIntelligence(
        experience=[
            Experience(
                job_title="Data Engineer",
                start_date="2020-00-00",
            )
        ]
    )

    result = enrich_resume_intelligence(
        (
            "Daniel Wong\n"
            "daniel.wong@example.com\n"
            "Data Engineer\n\n"
            "Experience\n"
            "Data Engineer at Signal Labs"
        ),
        intelligence,
    )

    assert len(result.experience) == 1
    assert result.experience[0].company == "Signal Labs"
    assert result.experience[0].start_date is None
    assert result.experience[0].end_date is None


def test_enricher_reconciles_multiple_jobs_without_false_positive_entries():
    result = enrich_resume_intelligence(
        (
            "Victor Chen\n"
            "victor.chen@example.com\n"
            "Senior Software Engineer\n\n"
            "Experience\n"
            "Software Engineer at Alpha Systems\n"
            "2019 - 2021\n"
            "Built internal APIs\n\n"
            "Senior Software Engineer at Beta Cloud\n"
            "2021 - Present\n"
            "Led backend architecture\n"
            "Mentored junior engineers"
        ),
        ResumeIntelligence(),
    )

    assert len(result.experience) == 2

    assert result.experience[0].job_title == "Software Engineer"
    assert result.experience[0].company == "Alpha Systems"
    assert result.experience[0].start_date == "2019"
    assert result.experience[0].end_date == "2021"

    assert result.experience[1].job_title == "Senior Software Engineer"
    assert result.experience[1].company == "Beta Cloud"
    assert result.experience[1].start_date == "2021"
    assert result.experience[1].end_date == "Present"


def test_enricher_preserves_provider_dates_for_unparsed_date_evidence():
    intelligence = ResumeIntelligence(
        experience=[
            Experience(
                job_title="Backend Engineer",
                company="Nova Systems",
                start_date="2021-01-01",
                end_date="Present",
            )
        ]
    )

    result = enrich_resume_intelligence(
        (
            "Aisha Rahman\n"
            "aisha.rahman@example.com\n\n"
            "Experience\n"
            "Backend Engineer at Nova Systems\n"
            "January 2021 - Present"
        ),
        intelligence,
    )

    assert len(result.experience) == 1
    assert result.experience[0].start_date == "2021-01-01"
    assert result.experience[0].end_date == "Present"
