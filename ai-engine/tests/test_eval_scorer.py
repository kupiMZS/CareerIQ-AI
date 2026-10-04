import pytest

from app.schemas.resume import (
    Candidate,
    Certification,
    Education,
    Experience,
    Project,
    ResumeIntelligence,
    Skill,
)
from evals.schemas import (
    ExpectedCertification,
    ExpectedEducation,
    ExpectedExperience,
    ExpectedExtendedEducation,
    ExpectedExtendedExperience,
    ExpectedExtendedResumeExtraction,
    ExpectedProject,
    ExpectedResumeExtraction,
)
from evals.scorer import (
    score_extended_resume_extraction,
    score_resume_extraction,
)


def test_scorer_gives_perfect_score_for_equivalent_extraction():
    expected = ExpectedResumeExtraction(
        name="John Doe",
        email="john.doe@example.com",
        skills=[
            "Python",
            "Docker",
        ],
        education=[
            ExpectedEducation(
                degree="BSc Computer Science",
                institution="Example University",
            )
        ],
        experience=[
            ExpectedExperience(
                job_title="Software Engineer",
                company="ABC Technologies",
            )
        ],
    )

    actual = ResumeIntelligence(
        candidate=Candidate(
            name="  JOHN   DOE ",
            email="JOHN.DOE@EXAMPLE.COM",
        ),
        skills=[
            Skill(name="python"),
            Skill(name="DOCKER"),
        ],
        education=[
            Education(
                degree="bsc computer science",
                institution="EXAMPLE UNIVERSITY",
            )
        ],
        experience=[
            Experience(
                job_title="software engineer",
                company="abc technologies",
            )
        ],
    )

    score = score_resume_extraction(
        expected,
        actual,
    )

    assert score.name.score == 1.0
    assert score.email.score == 1.0
    assert score.skills.f1 == 1.0
    assert score.education.f1 == 1.0
    assert score.experience.f1 == 1.0
    assert score.overall == 1.0


def test_scorer_calculates_partial_skill_f1():
    expected = ExpectedResumeExtraction(
        skills=[
            "Python",
            "Docker",
        ]
    )

    actual = ResumeIntelligence(
        skills=[
            Skill(name="Python"),
            Skill(name="Go"),
        ]
    )

    score = score_resume_extraction(
        expected,
        actual,
    )

    assert score.skills.matched_count == 1
    assert score.skills.expected_count == 2
    assert score.skills.actual_count == 2
    assert score.skills.precision == 0.5
    assert score.skills.recall == 0.5
    assert score.skills.f1 == 0.5


def test_scorer_treats_empty_expected_and_actual_collection_as_perfect():
    expected = ExpectedResumeExtraction()
    actual = ResumeIntelligence()

    score = score_resume_extraction(
        expected,
        actual,
    )

    assert score.skills.f1 == 1.0
    assert score.education.f1 == 1.0
    assert score.experience.f1 == 1.0


def test_scorer_penalizes_unexpected_collection_values():
    expected = ExpectedResumeExtraction()

    actual = ResumeIntelligence(
        skills=[
            Skill(name="Go"),
        ]
    )

    score = score_resume_extraction(
        expected,
        actual,
    )

    assert score.skills.precision == 0.0
    assert score.skills.recall == 1.0
    assert score.skills.f1 == 0.0


def test_scorer_matches_education_records():
    expected = ExpectedResumeExtraction(
        education=[
            ExpectedEducation(
                degree="BSc Computer Science",
                institution="University A",
            ),
            ExpectedEducation(
                degree="MSc AI",
                institution="University B",
            ),
        ]
    )

    actual = ResumeIntelligence(
        education=[
            Education(
                degree="BSc Computer Science",
                institution="University A",
            )
        ]
    )

    score = score_resume_extraction(
        expected,
        actual,
    )

    assert score.education.precision == 1.0
    assert score.education.recall == 0.5
    assert score.education.f1 == pytest.approx(2 / 3)


def test_scorer_matches_experience_records():
    expected = ExpectedResumeExtraction(
        experience=[
            ExpectedExperience(
                job_title="Backend Developer",
                company="Nova Systems",
            ),
            ExpectedExperience(
                job_title="Software Engineer",
                company="Orbit Digital",
            ),
        ]
    )

    actual = ResumeIntelligence(
        experience=[
            Experience(
                job_title="Backend Developer",
                company="Nova Systems",
            ),
            Experience(
                job_title="Software Engineer",
                company="Wrong Company",
            ),
        ]
    )

    score = score_resume_extraction(
        expected,
        actual,
    )

    assert score.experience.matched_count == 1
    assert score.experience.precision == 0.5
    assert score.experience.recall == 0.5
    assert score.experience.f1 == 0.5


def test_scorer_calculates_equal_weighted_overall_score():
    expected = ExpectedResumeExtraction(
        name="John Doe",
        email="john.doe@example.com",
        skills=[
            "Python",
        ],
        education=[
            ExpectedEducation(
                degree="BSc Computer Science",
            )
        ],
        experience=[
            ExpectedExperience(
                job_title="Software Engineer",
                company="ABC Technologies",
            )
        ],
    )

    actual = ResumeIntelligence(
        candidate=Candidate(
            name="John Doe",
            email="wrong@example.com",
        )
    )

    score = score_resume_extraction(
        expected,
        actual,
    )

    assert score.name.score == 1.0
    assert score.email.score == 0.0
    assert score.skills.f1 == 0.0
    assert score.education.f1 == 0.0
    assert score.experience.f1 == 0.0

    assert score.overall == pytest.approx(0.2)


def test_extended_scorer_gives_perfect_score():
    expected = ExpectedExtendedResumeExtraction(
        headline="Senior Software Engineer",
        education=[
            ExpectedExtendedEducation(
                degree="BSc Computer Science",
                institution="Example University",
                field_of_study="Computer Science",
                start_date="2018",
                end_date="2022",
            )
        ],
        experience=[
            ExpectedExtendedExperience(
                job_title="Software Engineer",
                company="Example Technologies",
                start_date="2022",
                end_date="Present",
                responsibilities=[
                    "Built backend APIs",
                    "Improved deployment automation",
                ],
            )
        ],
        projects=[
            ExpectedProject(
                name="CareerIQ",
                description="Career intelligence platform",
                technologies=[
                    "Python",
                    "FastAPI",
                ],
            )
        ],
        certifications=[
            ExpectedCertification(
                name="Cloud Developer",
                issuer="Example Cloud",
                date="2025",
            )
        ],
    )

    actual = ResumeIntelligence(
        candidate=Candidate(
            headline="  SENIOR   SOFTWARE ENGINEER ",
        ),
        education=[
            Education(
                degree="BSC COMPUTER SCIENCE",
                institution="Example University",
                field_of_study="computer science",
                start_date="2018",
                end_date="2022",
            )
        ],
        experience=[
            Experience(
                job_title="software engineer",
                company="EXAMPLE TECHNOLOGIES",
                start_date="2022",
                end_date="present",
                responsibilities=[
                    "Built backend APIs",
                    "Improved deployment automation",
                ],
            )
        ],
        projects=[
            Project(
                name="CareerIQ",
                description="Career intelligence platform",
                technologies=[
                    "FastAPI",
                    "Python",
                ],
            )
        ],
        certifications=[
            Certification(
                name="Cloud Developer",
                issuer="Example Cloud",
                date="2025",
            )
        ],
    )

    score = score_extended_resume_extraction(
        expected,
        actual,
    )

    assert score.headline.score == 1.0
    assert score.education_field_of_study.f1 == 1.0
    assert score.education_dates.f1 == 1.0
    assert score.experience_dates.f1 == 1.0
    assert score.responsibilities.f1 == 1.0
    assert score.projects.f1 == 1.0
    assert score.certifications.f1 == 1.0
    assert score.overall == 1.0


def test_extended_scorer_penalizes_wrong_headline():
    expected = ExpectedExtendedResumeExtraction(
        headline="Backend Engineer",
    )

    actual = ResumeIntelligence(
        candidate=Candidate(
            headline="Frontend Engineer",
        )
    )

    score = score_extended_resume_extraction(
        expected,
        actual,
    )

    assert score.headline.score == 0.0


def test_extended_scorer_scores_education_field_of_study():
    expected = ExpectedExtendedResumeExtraction(
        education=[
            ExpectedExtendedEducation(
                degree="BSc Computer Science",
                institution="Example University",
                field_of_study="Computer Science",
            )
        ]
    )

    actual = ResumeIntelligence(
        education=[
            Education(
                degree="BSc Computer Science",
                institution="Example University",
                field_of_study="Software Engineering",
            )
        ]
    )

    score = score_extended_resume_extraction(
        expected,
        actual,
    )

    assert score.education_field_of_study.f1 == 0.0


def test_extended_scorer_keeps_date_matching_strict():
    expected = ExpectedExtendedResumeExtraction(
        experience=[
            ExpectedExtendedExperience(
                job_title="Software Engineer",
                company="Example Technologies",
                start_date="January 2022",
                end_date="Present",
            )
        ]
    )

    actual = ResumeIntelligence(
        experience=[
            Experience(
                job_title="Software Engineer",
                company="Example Technologies",
                start_date="Jan 2022",
                end_date="present",
            )
        ]
    )

    score = score_extended_resume_extraction(
        expected,
        actual,
    )

    assert score.experience_dates.f1 == 0.0


def test_extended_scorer_attributes_responsibilities_to_experience():
    expected = ExpectedExtendedResumeExtraction(
        experience=[
            ExpectedExtendedExperience(
                job_title="Backend Engineer",
                company="Alpha Labs",
                responsibilities=[
                    "Built APIs",
                ],
            )
        ]
    )

    actual = ResumeIntelligence(
        experience=[
            Experience(
                job_title="Backend Engineer",
                company="Beta Labs",
                responsibilities=[
                    "Built APIs",
                ],
            )
        ]
    )

    score = score_extended_resume_extraction(
        expected,
        actual,
    )

    assert score.responsibilities.f1 == 0.0


def test_extended_scorer_ignores_project_technology_order():
    expected = ExpectedExtendedResumeExtraction(
        projects=[
            ExpectedProject(
                name="CareerIQ",
                description="Career platform",
                technologies=[
                    "Python",
                    "FastAPI",
                    "Redis",
                ],
            )
        ]
    )

    actual = ResumeIntelligence(
        projects=[
            Project(
                name="careeriq",
                description="Career platform",
                technologies=[
                    "Redis",
                    "python",
                    "FASTAPI",
                ],
            )
        ]
    )

    score = score_extended_resume_extraction(
        expected,
        actual,
    )

    assert score.projects.f1 == 1.0


def test_extended_scorer_scores_certification_metadata():
    expected = ExpectedExtendedResumeExtraction(
        certifications=[
            ExpectedCertification(
                name="Cloud Developer",
                issuer="Example Cloud",
                date="2025",
            )
        ]
    )

    actual = ResumeIntelligence(
        certifications=[
            Certification(
                name="Cloud Developer",
                issuer="Wrong Issuer",
                date="2025",
            )
        ]
    )

    score = score_extended_resume_extraction(
        expected,
        actual,
    )

    assert score.certifications.f1 == 0.0


def test_extended_scorer_does_not_change_core_overall_semantics():
    expected = ExpectedResumeExtraction(
        name="John Doe",
        email="john@example.com",
        skills=[
            "Python",
        ],
    )

    actual = ResumeIntelligence(
        candidate=Candidate(
            name="John Doe",
            email="wrong@example.com",
        ),
    )

    score = score_resume_extraction(
        expected,
        actual,
    )

    assert score.name.score == 1.0
    assert score.email.score == 0.0
    assert score.skills.f1 == 0.0
    assert score.education.f1 == 1.0
    assert score.experience.f1 == 1.0

    assert score.overall == pytest.approx(0.6)
