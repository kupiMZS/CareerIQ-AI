import pytest

from app.schemas.resume import ResumeIntelligence, Skill
from app.services.analysis_response_adapter import (
    build_analysis_response,
)
from app.services.resume_evidence_coverage import (
    summarize_resume_skill_evidence,
)
from app.services.resume_intelligence_enricher import (
    enrich_resume_intelligence,
)


@pytest.mark.parametrize(
    ("resume", "name", "status", "excerpts"),
    [
        (
            "Skills: Python",
            "Python",
            "literal_mention_only",
            ["Skills: Python"],
        ),
        (
            "Never used Docker",
            "Docker",
            "explicit_rejection_only",
            ["Never used Docker"],
        ),
        (
            "Currently learning AWS",
            "AWS",
            "explicit_rejection_only",
            ["Currently learning AWS"],
        ),
        (
            "Skills: Docker\nNever used Docker",
            "Docker",
            "mixed_mentions",
            ["Skills: Docker", "Never used Docker"],
        ),
        (
            "Skills: JavaScript",
            "Java",
            "no_literal_evidence",
            [],
        ),
        (
            "Skills: python",
            "Python",
            "no_literal_evidence",
            [],
        ),
        (
            "Career goal: Learn Python",
            "Python",
            "literal_mention_only",
            ["Career goal: Learn Python"],
        ),
    ],
)
def test_coverage_classifies_literal_evidence(
    resume,
    name,
    status,
    excerpts,
):
    intelligence = ResumeIntelligence(skills=[Skill(name=name)])

    report = summarize_resume_skill_evidence(
        resume,
        intelligence,
    )

    assert len(report) == 1
    assert report[0].field_path == "skills[0].name"
    assert report[0].skill_name == name
    assert report[0].status == status

    assert [record.evidence_text for record, _ in report[0].audited_records] == excerpts


def test_coverage_handles_duplicate_skills_by_index():
    resume = "Python and Docker\nNever used Python\nDocker"

    intelligence = ResumeIntelligence(
        skills=[
            Skill(name="Python"),
            Skill(name="Docker"),
            Skill(name="Python"),
        ]
    )

    reports = summarize_resume_skill_evidence(
        resume,
        intelligence,
    )

    assert [report.field_path for report in reports] == [
        "skills[0].name",
        "skills[1].name",
        "skills[2].name",
    ]

    assert [report.status for report in reports] == [
        "mixed_mentions",
        "literal_mention_only",
        "mixed_mentions",
    ]

    assert [len(report.audited_records) for report in reports] == [2, 2, 2]

    for report in reports:
        assert all(
            record.field_path == report.field_path
            for record, _ in report.audited_records
        )


def test_coverage_handles_empty_skill_list():
    intelligence = ResumeIntelligence()

    assert (
        summarize_resume_skill_evidence(
            "Skills: Python",
            intelligence,
        )
        == []
    )


def test_coverage_ignores_unmatched_provider_evidence():
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

    reports = summarize_resume_skill_evidence(
        "Experience with Azure",
        intelligence,
    )

    assert len(reports) == 1
    assert reports[0].status == "no_literal_evidence"
    assert reports[0].audited_records == ()
    assert intelligence.model_dump() == original


def test_coverage_preserves_public_response():
    resume = "Jane Doe\njane@example.com\nSkills\nPython\nNever used Docker"

    intelligence = ResumeIntelligence(
        skills=[
            Skill(name="Python", confidence=0.7),
            Skill(name="Docker", confidence=0.5),
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

    assert intelligence.model_dump() == original
    assert enriched.model_dump() == before_enriched

    after_response = build_analysis_response(
        resume,
        enriched,
    ).model_dump()

    assert after_response == before_response
