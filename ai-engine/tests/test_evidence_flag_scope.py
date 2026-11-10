import pytest

from app.schemas.resume import ResumeIntelligence, Skill
from app.services import (
    build_analysis_response,
    enrich_resume_intelligence,
    summarize_resume_skill_evidence,
)


@pytest.mark.parametrize(
    ("resume", "skill", "status", "flags"),
    [
        (
            "Career goal: Learn Java; Skills: Python",
            "Python",
            "literal_mention_only",
            (),
        ),
        (
            "Career goal: Learn Java; Skills: Python",
            "Java",
            "literal_mention_only",
            ("aspirational_wording",),
        ),
        (
            "I want to learn Docker, but I use Python",
            "Python",
            "literal_mention_only",
            (),
        ),
        (
            "Job requirements: Java; Skills: Python",
            "Python",
            "literal_mention_only",
            (),
        ),
        (
            "Job requirements: Java; Skills: Python",
            "Java",
            "literal_mention_only",
            ("requirement_wording",),
        ),
        (
            "Required skills: Docker; Skills: Python",
            "Python",
            "literal_mention_only",
            (),
        ),
        (
            "No experience with Python. I used Docker, but not Java",
            "Python",
            "explicit_rejection_only",
            (),
        ),
        (
            "No experience with Python, but proficient in Python",
            "Python",
            "explicit_rejection_only",
            ("rejection_with_contrast",),
        ),
        (
            "Career goal: Learn C++",
            "C++",
            "literal_mention_only",
            ("aspirational_wording",),
        ),
        (
            "Job requirements: C++",
            "C++",
            "literal_mention_only",
            ("requirement_wording",),
        ),
        (
            "No experience with Java, but proficient in Python",
            "Python",
            "literal_mention_only",
            (),
        ),
        (
            "Interested in learning Python, but I have used Docker",
            "Docker",
            "literal_mention_only",
            (),
        ),
    ],
)
def test_context_flags_are_scoped_to_the_correct_skill(
    resume,
    skill,
    status,
    flags,
):
    intelligence = ResumeIntelligence(skills=[Skill(name=skill)])

    reports = summarize_resume_skill_evidence(
        resume,
        intelligence,
    )

    assert len(reports) == 1
    assert reports[0].status == status
    assert reports[0].review_flags == flags


def test_multiple_contexts_on_same_lines_remain_separate():
    resume = (
        "Career goal: Learn Java; Skills: Python\n"
        "Job requirements: Java; Skills: Docker\n"
        "No experience with AWS. I used Docker, but not Java"
    )

    intelligence = ResumeIntelligence(
        skills=[
            Skill(name="Java"),
            Skill(name="Python"),
            Skill(name="Docker"),
            Skill(name="AWS"),
        ]
    )

    reports = summarize_resume_skill_evidence(
        resume,
        intelligence,
    )

    assert [report.status for report in reports] == [
        "literal_mention_only",
        "literal_mention_only",
        "literal_mention_only",
        "explicit_rejection_only",
    ]

    assert [report.review_flags for report in reports] == [
        ("aspirational_wording", "requirement_wording"),
        (),
        (),
        (),
    ]

    assert [report.field_path for report in reports] == [
        "skills[0].name",
        "skills[1].name",
        "skills[2].name",
        "skills[3].name",
    ]


def test_scoped_review_preserves_inputs_and_public_response():
    resume = (
        "Jane Doe\n"
        "jane@example.com\n"
        "Career goal: Learn Java; Skills: Python\n"
        "No experience with Docker. I used Python, but not Docker"
    )

    intelligence = ResumeIntelligence(
        skills=[
            Skill(
                name="Java",
                confidence=0.3,
                evidence=["Provider Java"],
            ),
            Skill(
                name="Python",
                confidence=0.7,
                evidence=["Provider Python"],
            ),
            Skill(
                name="Docker",
                confidence=0.5,
                evidence=["Provider Docker"],
            ),
        ]
    )

    original = intelligence.model_dump()

    enriched = enrich_resume_intelligence(
        resume,
        intelligence,
    )

    before_enriched = enriched.model_dump()

    before_response = build_analysis_response(
        resume,
        enriched,
    ).model_dump()

    reports = summarize_resume_skill_evidence(
        resume,
        enriched,
    )

    assert [report.review_flags for report in reports] == [
        ("aspirational_wording",),
        (),
        (),
    ]

    assert [report.status for report in reports] == [
        "literal_mention_only",
        "literal_mention_only",
        "explicit_rejection_only",
    ]

    assert intelligence.model_dump() == original
    assert enriched.model_dump() == before_enriched

    after_response = build_analysis_response(
        resume,
        enriched,
    ).model_dump()

    assert after_response == before_response
    assert enriched.analysis_version == "1.0"
