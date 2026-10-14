import pytest

from app.schemas.resume import ResumeIntelligence, Skill
from app.services import (
    build_analysis_response,
    enrich_resume_intelligence,
    summarize_resume_skill_evidence,
)
from app.services.evidence_verifier import verify_evidence_record
from app.services.resume_evidence_audit import (
    audit_resume_skill_evidence,
    collect_and_audit_resume_skill_evidence,
)
from app.services.skill_evidence_collector import (
    collect_literal_skill_evidence,
)


@pytest.mark.parametrize(
    ("resume", "names", "statuses", "flags"),
    [
        (
            "",
            ["Python", "Docker"],
            ["no_literal_evidence", "no_literal_evidence"],
            [(), ()],
        ),
        (
            "Skills: Python, Node.js, C++, C#, scikit-learn",
            [
                "Python",
                "Node",
                "Node.js",
                "C",
                "C++",
                "C#",
                "scikit",
                "scikit-learn",
            ],
            [
                "literal_mention_only",
                "no_literal_evidence",
                "literal_mention_only",
                "no_literal_evidence",
                "literal_mention_only",
                "literal_mention_only",
                "no_literal_evidence",
                "literal_mention_only",
            ],
            [()] * 8,
        ),
        (
            (
                "Career goal: Learn Java; Skills: Python\n"
                "Job requirements: Node.js; Skills: Docker"
            ),
            ["Java", "Python", "Node.js", "Docker"],
            ["literal_mention_only"] * 4,
            [
                ("aspirational_wording",),
                (),
                ("requirement_wording",),
                (),
            ],
        ),
        (
            ("Skills: Docker\nNever used Docker\nCareer goal: Learn Docker"),
            ["Docker"],
            ["mixed_mentions"],
            [("aspirational_wording",)],
        ),
        (
            ("Never used C+++\nNever used Node.js.v2\nSkills: C##"),
            ["C++", "Node.js", "C#"],
            ["no_literal_evidence"] * 3,
            [(), (), ()],
        ),
        (
            "No experience with C++, but proficient in C++",
            ["C++"],
            ["explicit_rejection_only"],
            [("rejection_with_contrast",)],
        ),
        (
            "Never used JavaScript\nSkills: Java",
            ["Java", "JavaScript"],
            ["literal_mention_only", "explicit_rejection_only"],
            [(), ()],
        ),
        (
            "Skills: Python\nSkills: Python",
            ["Python", "Python"],
            ["literal_mention_only", "literal_mention_only"],
            [(), ()],
        ),
    ],
)
def test_collection_audit_and_coverage_agree(
    resume,
    names,
    statuses,
    flags,
):
    intelligence = ResumeIntelligence(skills=[Skill(name=name) for name in names])

    before = intelligence.model_dump()

    collected = collect_literal_skill_evidence(
        resume,
        intelligence,
    )

    audited = collect_and_audit_resume_skill_evidence(
        resume,
        intelligence,
    )

    coverage = summarize_resume_skill_evidence(
        resume,
        intelligence,
    )

    assert [record for record, _ in audited] == collected

    assert len(coverage) == len(names)

    assert [item.field_path for item in coverage] == [
        f"skills[{index}].name" for index in range(len(names))
    ]

    assert [item.skill_name for item in coverage] == names
    assert [item.status for item in coverage] == statuses
    assert [item.review_flags for item in coverage] == flags

    for item in coverage:
        expected = tuple(
            (record, result)
            for record, result in audited
            if record.field_path == item.field_path
        )

        assert item.audited_records == expected

    for record, result in audited:
        assert record.evidence_text in resume
        assert record.source == "deterministic"
        assert record.confidence is None
        assert result == verify_evidence_record(resume, record)
        assert result.excerpt_found is True
        assert result.claim_found is True
        assert result.status in {
            "lexically_supported",
            "explicitly_unsupported",
        }

    assert intelligence.model_dump() == before


def test_explicit_audit_matches_orchestrated_audit():
    resume = "Skills: Python and Docker\nNever used Docker\nSkills: Node.js and C++"

    intelligence = ResumeIntelligence(
        skills=[
            Skill(name="Python"),
            Skill(name="Docker"),
            Skill(name="Node.js"),
            Skill(name="C++"),
        ]
    )

    records = collect_literal_skill_evidence(
        resume,
        intelligence,
    )

    direct = audit_resume_skill_evidence(
        resume,
        intelligence,
        records,
    )

    orchestrated = collect_and_audit_resume_skill_evidence(
        resume,
        intelligence,
    )

    assert direct == orchestrated

    assert [(record.field_path, result.status) for record, result in orchestrated] == [
        ("skills[0].name", "lexically_supported"),
        ("skills[1].name", "lexically_supported"),
        ("skills[1].name", "explicitly_unsupported"),
        ("skills[2].name", "lexically_supported"),
        ("skills[3].name", "lexically_supported"),
    ]


def test_duplicate_skills_preserve_indices_and_line_order():
    resume = "Skills: Python, Docker\nNever used Python\nSkills: Docker"

    intelligence = ResumeIntelligence(
        skills=[
            Skill(name="Python"),
            Skill(name="Docker"),
            Skill(name="Python"),
        ]
    )

    audited = collect_and_audit_resume_skill_evidence(
        resume,
        intelligence,
    )

    assert [(record.field_path, result.status) for record, result in audited] == [
        ("skills[0].name", "lexically_supported"),
        ("skills[1].name", "lexically_supported"),
        ("skills[2].name", "lexically_supported"),
        ("skills[0].name", "explicitly_unsupported"),
        ("skills[2].name", "explicitly_unsupported"),
        ("skills[1].name", "lexically_supported"),
    ]

    reports = summarize_resume_skill_evidence(
        resume,
        intelligence,
    )

    assert [item.status for item in reports] == [
        "mixed_mentions",
        "literal_mention_only",
        "mixed_mentions",
    ]

    assert [len(item.audited_records) for item in reports] == [2, 2, 2]


def test_provider_evidence_is_not_automatically_verified():
    intelligence = ResumeIntelligence(
        skills=[
            Skill(
                name="AWS",
                confidence=0.8,
                evidence=["AWS"],
            )
        ]
    )

    original = intelligence.model_dump()
    resume = "Experience with Azure"

    assert (
        collect_literal_skill_evidence(
            resume,
            intelligence,
        )
        == []
    )

    assert (
        collect_and_audit_resume_skill_evidence(
            resume,
            intelligence,
        )
        == []
    )

    report = summarize_resume_skill_evidence(
        resume,
        intelligence,
    )[0]

    assert report.status == "no_literal_evidence"
    assert report.audited_records == ()
    assert report.review_flags == ()

    assert intelligence.model_dump() == original


def test_cross_layer_reporting_preserves_public_response():
    resume = (
        "Jane Doe\n"
        "jane@example.com\n"
        "Skills: Python, Node.js\n"
        "Career goal: Learn Docker\n"
        "Never used C++\n"
        "Skills: C++"
    )

    intelligence = ResumeIntelligence(
        skills=[
            Skill(
                name="Python",
                confidence=0.7,
                evidence=["Provider Python"],
            ),
            Skill(
                name="Node.js",
                confidence=0.6,
                evidence=["Provider Node.js"],
            ),
            Skill(
                name="Docker",
                confidence=0.5,
                evidence=["Provider Docker"],
            ),
            Skill(name="C++", confidence=None),
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

    collected = collect_literal_skill_evidence(
        resume,
        enriched,
    )

    audited = collect_and_audit_resume_skill_evidence(
        resume,
        enriched,
    )

    reports = summarize_resume_skill_evidence(
        resume,
        enriched,
    )

    assert len(collected) == len(audited)

    assert [item.status for item in reports] == [
        "literal_mention_only",
        "literal_mention_only",
        "literal_mention_only",
        "mixed_mentions",
    ]

    assert [item.review_flags for item in reports] == [
        (),
        (),
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
    assert enriched.analysis_version == "1.0"


def test_empty_skill_list_produces_no_records_or_reports():
    intelligence = ResumeIntelligence()

    resume = "Skills: Python and Docker"

    assert (
        collect_literal_skill_evidence(
            resume,
            intelligence,
        )
        == []
    )

    assert (
        collect_and_audit_resume_skill_evidence(
            resume,
            intelligence,
        )
        == []
    )

    assert (
        summarize_resume_skill_evidence(
            resume,
            intelligence,
        )
        == []
    )
