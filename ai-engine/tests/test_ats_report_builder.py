import pytest

from app.analyzer import analyze_resume
from app.schemas.ats import ATSFinding, ATSReport
from app.services import ats_report_builder as builder
from app.services.ats_achievement_evidence import (
    assess_quantified_outcome_evidence,
)
from app.services.ats_assessment import (
    assess_resume_section_content,
    assess_resume_structure,
)
from app.services.ats_report_builder import build_ats_report

EXPECTED_CODES = [
    "contact_email",
    "section_skills",
    "section_education",
    "section_experience",
    "section_skills_content",
    "section_education_content",
    "section_experience_content",
    "quantified_outcome_evidence",
]


def _findings(report):
    return {finding.code: finding for finding in report.findings}


def test_combined_report_contains_eight_ordered_findings():
    text = """
Taylor Example
taylor@example.com

Skills
Python

Education
BSc Computer Science

Experience
Reduced processing time by 35%.
"""

    report = build_ats_report(text)

    assert report.report_version == "ats-v1"
    assert report.score is None
    assert [finding.code for finding in report.findings] == EXPECTED_CODES

    assert all(finding.status == "satisfied" for finding in report.findings)


def test_heading_and_content_findings_remain_distinct():
    text = """
Skills
Education
BSc Computer Science

Experience
Worked on internal systems.
"""

    findings = _findings(build_ats_report(text))

    assert findings["section_skills"].status == "satisfied"

    assert findings["section_skills_content"].status == "needs_attention"

    assert findings["section_education_content"].status == "satisfied"

    assert findings["quantified_outcome_evidence"].status == "needs_attention"

    assert findings["contact_email"].status == "needs_attention"


def test_empty_resume_produces_eight_unassessed_findings():
    report = build_ats_report("  \n  ")

    assert report.score is None
    assert [finding.code for finding in report.findings] == EXPECTED_CODES

    assert all(finding.status == "not_assessed" for finding in report.findings)


def test_limitations_are_deduplicated_in_original_order():
    text = "Skills\nPython"

    reports = (
        assess_resume_structure(text),
        assess_resume_section_content(text),
        assess_quantified_outcome_evidence(text),
    )

    expected = list(
        dict.fromkeys(
            limitation for report in reports for limitation in report.limitations
        )
    )

    merged = build_ats_report(text)

    assert merged.limitations == expected
    assert len(merged.limitations) == len(set(expected))


def test_repeated_assessment_is_deterministic():
    text = """
person@example.com
Skills
Python
Experience
Reduced errors by 20%.
"""

    first = build_ats_report(text)
    second = build_ats_report(text)

    assert first.model_dump() == second.model_dump()


def test_independent_assessments_are_not_mutated():
    text = """
person@example.com
Skills
Python
Projects
Saved $3,000.
"""

    evaluators = (
        assess_resume_structure,
        assess_resume_section_content,
        assess_quantified_outcome_evidence,
    )

    before = [evaluator(text).model_dump() for evaluator in evaluators]

    build_ats_report(text)

    after = [evaluator(text).model_dump() for evaluator in evaluators]

    assert before == after


def test_duplicate_finding_codes_are_rejected(monkeypatch):
    def duplicate_component(_text):
        return ATSReport(
            findings=[
                ATSFinding(
                    code="contact_email",
                    status="satisfied",
                    explanation="Synthetic duplicate finding.",
                )
            ]
        )

    monkeypatch.setattr(
        builder,
        "assess_quantified_outcome_evidence",
        duplicate_component,
    )

    with pytest.raises(
        ValueError,
        match="Duplicate ATS finding code",
    ):
        builder.build_ats_report("Skills\nPython")


def test_scored_component_is_rejected(monkeypatch):
    def scored_component(_text):
        return ATSReport(score=50)

    monkeypatch.setattr(
        builder,
        "assess_quantified_outcome_evidence",
        scored_component,
    )

    with pytest.raises(
        ValueError,
        match="Unexpected score",
    ):
        builder.build_ats_report("Skills\nPython")


def test_quantified_claim_remains_unverified():
    report = build_ats_report(
        """
Experience
Reduced processing time by 35%.
"""
    )

    finding = _findings(report)["quantified_outcome_evidence"]

    assert finding.status == "satisfied"
    assert "not independently verified" in finding.explanation

    assert any("not verified" in limitation for limitation in report.limitations)

    assert any("job-specific" in limitation for limitation in report.limitations)

    assert report.score is None


def test_legacy_analysis_is_unchanged():
    text = """
Jordan Example
jordan@example.com

Skills
Python

Education
BSc Computer Science

Experience
Improved processing time by 20%.
"""

    original = analyze_resume(text)

    report = build_ats_report(text)

    assert len(report.findings) == 8
    assert report.score is None
    assert analyze_resume(text) == original
    assert isinstance(original["ats_score"], int)
