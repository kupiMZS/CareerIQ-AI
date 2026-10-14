import pytest

from app.schemas.resume import ResumeIntelligence, Skill
from app.services.resume_evidence_audit import (
    audit_resume_skill_evidence,
)
from app.services.skill_evidence_collector import (
    collect_literal_skill_evidence,
)


@pytest.mark.parametrize(
    ("resume", "skill_name", "expected_excerpts"),
    [
        ("Skills: Python", "Python", ["Skills: Python"]),
        ("Skills: JavaScript", "Java", []),
        ("Skills: python", "Python", []),
        ("Skills: Pythonista", "Python", []),
        ("Skills: C++", "C++", ["Skills: C++"]),
        (
            "No experience with Docker",
            "Docker",
            ["No experience with Docker"],
        ),
        ("Skills: Python", " Python ", []),
        ("", "Python", []),
    ],
)
def test_collects_only_literal_complete_skill_mentions(
    resume,
    skill_name,
    expected_excerpts,
):
    intelligence = ResumeIntelligence(skills=[Skill(name=skill_name)])

    records = collect_literal_skill_evidence(
        resume,
        intelligence,
    )

    assert [record.evidence_text for record in records] == (expected_excerpts)

    for record in records:
        assert record.field_path == "skills[0].name"
        assert record.extracted_value == skill_name
        assert record.evidence_text in resume
        assert record.source == "deterministic"
        assert record.confidence is None


def test_collector_preserves_resume_order_and_skill_indices():
    resume = "  Built with Docker  \nPython and Docker\nNever used AWS"

    intelligence = ResumeIntelligence(
        skills=[
            Skill(name="Python"),
            Skill(name="Docker"),
            Skill(name="AWS"),
        ]
    )

    records = collect_literal_skill_evidence(
        resume,
        intelligence,
    )

    assert [(record.field_path, record.evidence_text) for record in records] == [
        ("skills[1].name", "Built with Docker"),
        ("skills[0].name", "Python and Docker"),
        ("skills[1].name", "Python and Docker"),
        ("skills[2].name", "Never used AWS"),
    ]


def test_collector_does_not_invent_provider_evidence():
    intelligence = ResumeIntelligence(
        skills=[
            Skill(
                name="AWS",
                evidence=["AWS"],
                confidence=0.8,
            )
        ]
    )

    original = intelligence.model_dump()

    records = collect_literal_skill_evidence(
        "Experience with Azure",
        intelligence,
    )

    assert records == []
    assert intelligence.model_dump() == original


def test_collector_and_audit_classify_negative_skill_evidence():
    resume = "Skills: Python\nNever used Docker"

    intelligence = ResumeIntelligence(
        skills=[
            Skill(name="Python"),
            Skill(name="Docker"),
        ]
    )

    records = collect_literal_skill_evidence(
        resume,
        intelligence,
    )

    audited = audit_resume_skill_evidence(
        resume,
        intelligence,
        records,
    )

    assert [result.status for _, result in audited] == [
        "lexically_supported",
        "explicitly_unsupported",
    ]


def test_collector_keeps_multiple_distinct_mentions():
    resume = "Python Python\nNo experience with Python\nBuilt services using Python"

    intelligence = ResumeIntelligence(skills=[Skill(name="Python")])

    records = collect_literal_skill_evidence(
        resume,
        intelligence,
    )

    assert len(records) == 3
    assert [record.evidence_text for record in records] == resume.splitlines()


def test_collector_does_not_infer_skills_from_career_goals():
    resume = "Career goal: Learn Python"

    intelligence = ResumeIntelligence(
        career_profile={
            "career_goals": ["Learn Python"],
        },
    )

    assert (
        collect_literal_skill_evidence(
            resume,
            intelligence,
        )
        == []
    )
