from app.schemas.resume import (
    Education,
    Experience,
    ResumeIntelligence,
)
from app.services import (
    enrich_resume_intelligence,
)


def test_merges_complementary_education_records():
    intelligence = ResumeIntelligence(
        education=[
            Education(
                institution=("Northern State University"),
                degree=None,
            ),
            Education(
                institution=("Northern State University"),
                degree="BSc Computer Science",
            ),
        ]
    )

    result = enrich_resume_intelligence(
        (
            "John Doe\n"
            "john.doe@example.com\n\n"
            "Education\n"
            "BSc Computer Science\n"
            "Northern State University"
        ),
        intelligence,
    )

    assert len(result.education) == 1

    assert result.education[0].degree == "BSc Computer Science"

    assert result.education[0].institution == "Northern State University"


def test_splits_multiple_degree_at_institution_entries():
    intelligence = ResumeIntelligence(
        education=[
            Education(institution=("Eastern University")),
            Education(institution=("Metro University")),
        ]
    )

    result = enrich_resume_intelligence(
        (
            "Nadia Karim\n"
            "nadia.karim@example.com\n\n"
            "Education\n"
            "BSc Computer Science at "
            "Eastern University\n"
            "MSc Data Science at "
            "Metro University"
        ),
        intelligence,
    )

    assert len(result.education) == 2

    assert result.education[0].degree == "BSc Computer Science"
    assert result.education[0].institution == "Eastern University"

    assert result.education[1].degree == "MSc Data Science"
    assert result.education[1].institution == "Metro University"


def test_splits_degree_at_institution_without_section_heading():
    result = enrich_resume_intelligence(
        (
            "Lucas Martin\n"
            "lucas.martin@example.com\n"
            "BSc Computer Science at "
            "Central University\n"
            "Software Developer at "
            "Bright Apps\n"
            "Python\n"
            "Git\n"
            "Docker"
        ),
        ResumeIntelligence(),
    )

    matching = [
        item
        for item in result.education
        if (
            item.degree == "BSc Computer Science"
            and item.institution == "Central University"
        )
    ]

    assert len(matching) == 1


def test_splits_dash_separated_experience():
    result = enrich_resume_intelligence(
        (
            "Priya Das\n"
            "priya.das@example.com\n\n"
            "Experience\n"
            "Frontend Developer - "
            "Nova Studio"
        ),
        ResumeIntelligence(),
    )

    assert len(result.experience) == 1

    assert result.experience[0].job_title == "Frontend Developer"

    assert result.experience[0].company == "Nova Studio"


def test_merges_complementary_experience_records():
    intelligence = ResumeIntelligence(
        experience=[
            Experience(
                job_title=("Software Engineer"),
                company=None,
            ),
            Experience(
                job_title=("Software Engineer"),
                company=("ABC Technologies"),
            ),
        ]
    )

    result = enrich_resume_intelligence(
        ("John Doe\n\nExperience\nSoftware Engineer at ABC Technologies"),
        intelligence,
    )

    assert len(result.experience) == 1

    assert result.experience[0].job_title == "Software Engineer"

    assert result.experience[0].company == "ABC Technologies"


def test_splits_title_first_pipe_experience():
    result = enrich_resume_intelligence(
        (
            "Daniel Cruz\n"
            "daniel.cruz@example.com\n\n"
            "Experience\n"
            "Backend Developer | Orbit Works"
        ),
        ResumeIntelligence(),
    )

    assert len(result.experience) == 1
    assert result.experience[0].job_title == "Backend Developer"
    assert result.experience[0].company == "Orbit Works"


def test_splits_company_first_pipe_experience():
    result = enrich_resume_intelligence(
        (
            "Sophia Lee\n"
            "sophia.lee@example.com\n\n"
            "Experience\n"
            "Acme Systems | Senior Java Developer"
        ),
        ResumeIntelligence(),
    )

    assert len(result.experience) == 1
    assert result.experience[0].job_title == "Senior Java Developer"
    assert result.experience[0].company == "Acme Systems"


def test_pairs_multiline_degree_and_institution():
    result = enrich_resume_intelligence(
        (
            "Isabella Rossi\n"
            "isabella.rossi@example.com\n\n"
            "Education\n"
            "MSc Data Science\n"
            "European Technical University\n\n"
            "Experience\n"
            "Data Scientist at Insight AI"
        ),
        ResumeIntelligence(),
    )

    assert len(result.education) == 1
    assert result.education[0].degree == "MSc Data Science"
    assert result.education[0].institution == "European Technical University"


def test_pairs_multiple_multiline_education_entries():
    result = enrich_resume_intelligence(
        (
            "Yusuf Ahmed\n"
            "yusuf.ahmed@example.com\n\n"
            "Education\n"
            "BSc Computer Science\n"
            "North University\n"
            "MSc Software Engineering\n"
            "West Institute of Technology"
        ),
        ResumeIntelligence(),
    )

    assert len(result.education) == 2

    assert result.education[0].degree == "BSc Computer Science"
    assert result.education[0].institution == "North University"

    assert result.education[1].degree == "MSc Software Engineering"
    assert result.education[1].institution == "West Institute of Technology"


def test_strips_bullet_prefix_from_experience():
    result = enrich_resume_intelligence(
        (
            "Michael Green\n"
            "michael.green@example.com\n\n"
            "Experience:\n"
            "- DevOps Engineer at Runtime Labs"
        ),
        ResumeIntelligence(),
    )

    assert len(result.experience) == 1
    assert result.experience[0].job_title == "DevOps Engineer"
    assert result.experience[0].company == "Runtime Labs"
