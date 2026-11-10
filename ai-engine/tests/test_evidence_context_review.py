import pytest

from app.schemas.resume import ResumeIntelligence, Skill
from app.services import (
    build_analysis_response,
    enrich_resume_intelligence,
    summarize_resume_skill_evidence,
)


@pytest.mark.parametrize(
    ("resume", "name", "status", "flags"),
    [
        (
            "Career goal: Learn Python",
            "Python",
            "literal_mention_only",
            ("aspirational_wording",),
        ),
        (
            "I want to learn Python",
            "Python",
            "literal_mention_only",
            ("aspirational_wording",),
        ),
        (
            "Job requirements: Python",
            "Python",
            "literal_mention_only",
            ("requirement_wording",),
        ),
        (
            "Required skills: Docker",
            "Docker",
            "literal_mention_only",
            ("requirement_wording",),
        ),
        (
            "No experience with Python, but proficient in Python",
            "Python",
            "explicit_rejection_only",
            ("rejection_with_contrast",),
        ),
        (
            "Skills: Python",
            "Python",
            "literal_mention_only",
            (),
        ),
        (
            "Never used Python",
            "Python",
            "explicit_rejection_only",
            (),
        ),
        (
            "Experience with Azure",
            "AWS",
            "no_literal_evidence",
            (),
        ),
    ],
)
def test_context_review_flags(
    resume,
    name,
    status,
    flags,
):
    intelligence = ResumeIntelligence(skills=[Skill(name=name)])

    reports = summarize_resume_skill_evidence(
        resume,
        intelligence,
    )

    assert len(reports) == 1
    assert reports[0].status == status
    assert reports[0].review_flags == flags


def test_review_flags_remain_scoped_to_matching_skill():
    resume = "Career goal: Learn Python\nSkills: Docker"

    intelligence = ResumeIntelligence(
        skills=[
            Skill(name="Python"),
            Skill(name="Docker"),
        ]
    )

    reports = summarize_resume_skill_evidence(
        resume,
        intelligence,
    )

    assert [report.review_flags for report in reports] == [
        ("aspirational_wording",),
        (),
    ]


def test_contrasting_excerpt_retains_original_audit():
    resume = "No experience with Python, but proficient in Python\nSkills: Python"

    intelligence = ResumeIntelligence(skills=[Skill(name="Python")])

    report = summarize_resume_skill_evidence(
        resume,
        intelligence,
    )[0]

    assert report.status == "mixed_mentions"
    assert report.review_flags == ("rejection_with_contrast",)

    assert [result.status for _, result in report.audited_records] == [
        "explicitly_unsupported",
        "lexically_supported",
    ]


def test_context_review_preserves_inputs_and_public_response():
    resume = (
        "Jane Doe\n"
        "jane@example.com\n"
        "Skills: Python\n"
        "Career goal: Learn Python\n"
        "Never used Docker"
    )

    intelligence = ResumeIntelligence(
        skills=[
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

    assert [report.status for report in reports] == [
        "literal_mention_only",
        "explicit_rejection_only",
    ]

    assert [report.review_flags for report in reports] == [
        ("aspirational_wording",),
        (),
    ]

    assert intelligence.model_dump() == original
    assert enriched.model_dump() == before_enriched

    after_response = build_analysis_response(
        resume,
        enriched,
    ).model_dump()

    assert after_response == before_response
