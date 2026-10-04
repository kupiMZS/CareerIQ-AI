from app.schemas.resume import (
    Candidate,
    Certification,
    Education,
    Experience,
    Project,
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


def test_enricher_extracts_responsibilities_from_explicit_experience_block():
    intelligence = ResumeIntelligence()

    enriched = enrich_resume_intelligence(
        """
Aisha Rahman
aisha.rahman@example.com
Senior Backend Engineer

Experience
Backend Engineer at Nova Systems
2021 - Present
Built REST APIs
Improved deployment automation
""",
        intelligence,
    )

    assert len(enriched.experience) == 1

    experience = enriched.experience[0]

    assert experience.job_title == "Backend Engineer"
    assert experience.company == "Nova Systems"
    assert experience.start_date == "2021"
    assert experience.end_date == "Present"
    assert experience.responsibilities == [
        "Built REST APIs",
        "Improved deployment automation",
    ]


def test_enricher_attributes_responsibilities_to_correct_experience():
    intelligence = ResumeIntelligence()

    enriched = enrich_resume_intelligence(
        """
Victor Chen
victor.chen@example.com
Senior Software Engineer

Experience
Software Engineer at Alpha Systems
2019 - 2021
Built internal APIs

Senior Software Engineer at Beta Cloud
2021 - Present
Led backend architecture
Mentored junior engineers
""",
        intelligence,
    )

    assert len(enriched.experience) == 2

    assert enriched.experience[0].responsibilities == [
        "Built internal APIs",
    ]

    assert enriched.experience[1].responsibilities == [
        "Led backend architecture",
        "Mentored junior engineers",
    ]


def test_enricher_replaces_provider_responsibilities_with_literal_block_evidence():
    intelligence = ResumeIntelligence(
        experience=[
            Experience(
                job_title="Backend Engineer",
                company="Nova Systems",
                start_date="2021-01-01",
                end_date="Present",
                responsibilities=[
                    "Unsupported provider responsibility",
                ],
            )
        ]
    )

    enriched = enrich_resume_intelligence(
        """
Aisha Rahman
aisha.rahman@example.com
Backend Engineer

Experience
Backend Engineer at Nova Systems
January 2021 - Present
Built REST APIs
""",
        intelligence,
    )

    assert len(enriched.experience) == 1

    experience = enriched.experience[0]

    assert experience.start_date == "2021-01-01"
    assert experience.end_date == "Present"
    assert experience.responsibilities == [
        "Built REST APIs",
    ]


def test_enricher_extracts_project_with_explicit_technologies():
    intelligence = ResumeIntelligence()

    enriched = enrich_resume_intelligence(
        """
Lina Ahmed
lina.ahmed@example.com
Software Developer

Skills
Python
Django
Redis

Projects
TaskFlow
Task management application with background processing
Technologies: Python, Django, Redis
""",
        intelligence,
    )

    assert len(enriched.projects) == 1

    project = enriched.projects[0]

    assert project.name == "TaskFlow"
    assert (
        project.description == "Task management application with background processing"
    )
    assert project.technologies == [
        "Python",
        "Django",
        "Redis",
    ]


def test_enricher_extracts_multiple_projects():
    intelligence = ResumeIntelligence()

    enriched = enrich_resume_intelligence(
        """
Lucas Meyer
lucas.meyer@example.com
Full Stack Developer

Projects
ShopAPI
E-commerce API
Technologies: Python, FastAPI

DashboardUI
Administrative dashboard
Technologies: TypeScript, React
""",
        intelligence,
    )

    assert len(enriched.projects) == 2

    assert enriched.projects[0].name == "ShopAPI"
    assert enriched.projects[0].description == "E-commerce API"
    assert enriched.projects[0].technologies == [
        "Python",
        "FastAPI",
    ]

    assert enriched.projects[1].name == "DashboardUI"
    assert enriched.projects[1].description == "Administrative dashboard"
    assert enriched.projects[1].technologies == [
        "TypeScript",
        "React",
    ]


def test_enricher_infers_project_technologies_from_literal_skill_evidence():
    intelligence = ResumeIntelligence()

    enriched = enrich_resume_intelligence(
        """
Aisha Rahman
aisha.rahman@example.com
Senior Backend Engineer

Skills
Python
FastAPI
PostgreSQL
Docker

Projects
CareerHub
Career platform built with Python, FastAPI, and PostgreSQL
""",
        intelligence,
    )

    assert len(enriched.projects) == 1

    project = enriched.projects[0]

    assert project.name == "CareerHub"
    assert (
        project.description
        == "Career platform built with Python, FastAPI, and PostgreSQL"
    )
    assert project.technologies == [
        "Python",
        "FastAPI",
        "PostgreSQL",
    ]


def test_enricher_preserves_provider_projects_without_projects_section():
    intelligence = ResumeIntelligence(
        projects=[
            Project(
                name="Existing Project",
                description="Provider supplied project",
                technologies=[
                    "Python",
                ],
            )
        ]
    )

    enriched = enrich_resume_intelligence(
        """
Jane Doe
jane@example.com
Software Engineer

Skills
Python
""",
        intelligence,
    )

    assert len(enriched.projects) == 1
    assert enriched.projects[0].name == "Existing Project"
    assert enriched.projects[0].description == "Provider supplied project"
    assert enriched.projects[0].technologies == [
        "Python",
    ]


def test_enricher_extracts_inline_certification():
    intelligence = ResumeIntelligence(
        certifications=[
            Certification(
                name="Unsupported Certification",
                issuer="Wrong Issuer",
                date="2020",
            )
        ]
    )

    enriched = enrich_resume_intelligence(
        """
Aisha Rahman
aisha.rahman@example.com
Senior Backend Engineer

Certifications
Cloud Developer - Example Cloud - 2024
""",
        intelligence,
    )

    assert len(enriched.certifications) == 1

    certification = enriched.certifications[0]

    assert certification.name == "Cloud Developer"
    assert certification.issuer == "Example Cloud"
    assert certification.date == "2024"


def test_enricher_extracts_multiline_certification():
    intelligence = ResumeIntelligence()

    enriched = enrich_resume_intelligence(
        """
Nora Ibrahim
nora.ibrahim@example.com
Cloud Engineer

Certifications
AWS Developer Associate
Amazon Web Services
2025
""",
        intelligence,
    )

    assert len(enriched.certifications) == 1

    certification = enriched.certifications[0]

    assert certification.name == "AWS Developer Associate"
    assert certification.issuer == "Amazon Web Services"
    assert certification.date == "2025"


def test_enricher_extracts_multiple_certifications():
    intelligence = ResumeIntelligence()

    enriched = enrich_resume_intelligence(
        """
Ethan Cole
ethan.cole@example.com
DevOps Engineer

Certifications
Certified Kubernetes Administrator
Cloud Native Computing Foundation
2024

Terraform Associate
HashiCorp
2023
""",
        intelligence,
    )

    assert len(enriched.certifications) == 2

    assert enriched.certifications[0].name == "Certified Kubernetes Administrator"
    assert enriched.certifications[0].issuer == "Cloud Native Computing Foundation"
    assert enriched.certifications[0].date == "2024"

    assert enriched.certifications[1].name == "Terraform Associate"
    assert enriched.certifications[1].issuer == "HashiCorp"
    assert enriched.certifications[1].date == "2023"


def test_enricher_preserves_provider_certifications_without_section():
    intelligence = ResumeIntelligence(
        certifications=[
            Certification(
                name="Existing Certification",
                issuer="Existing Issuer",
                date="2025",
            )
        ]
    )

    enriched = enrich_resume_intelligence(
        """
Jane Doe
jane@example.com
Software Engineer

Skills
Python
""",
        intelligence,
    )

    assert len(enriched.certifications) == 1

    certification = enriched.certifications[0]

    assert certification.name == "Existing Certification"
    assert certification.issuer == "Existing Issuer"
    assert certification.date == "2025"
