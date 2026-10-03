import pytest

from app.schemas.resume import (
    Candidate,
    Education,
    Experience,
    ResumeIntelligence,
    Skill,
)
from evals.schemas import (
    ExpectedEducation,
    ExpectedExperience,
    ExpectedResumeExtraction,
)
from evals.scorer import score_resume_extraction


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
