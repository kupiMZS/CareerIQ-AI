import pytest

from app.analyzer import analyze_resume
from app.services.ats_achievement_evidence import (
    assess_quantified_outcome_evidence,
)


def _finding(text):
    report = assess_quantified_outcome_evidence(text)

    assert report.score is None
    assert len(report.findings) == 1
    assert report.findings[0].code == ("quantified_outcome_evidence")

    return report.findings[0]


def test_percentage_outcome_is_detected():
    statement = "Reduced processing time by 35%."

    finding = _finding("Experience\n" + statement)

    assert finding.status == "satisfied"
    assert finding.supporting_text == [statement]


def test_monetary_savings_are_detected():
    finding = _finding("Work Experience\nSaved $20,000 annually.")

    assert finding.status == "satisfied"


def test_time_reduction_is_detected():
    finding = _finding("Projects\nShortened processing by 2 hours.")

    assert finding.status == "satisfied"


def test_achievement_section_is_supported():
    finding = _finding("Achievements\nImproved accuracy by 12%.")

    assert finding.status == "satisfied"


def test_duplicate_evidence_is_not_repeated():
    text = """
Experience
Reduced errors by 20%.
Reduced errors by 20%.
"""

    finding = _finding(text)

    assert finding.supporting_text == ["Reduced errors by 20%."]


def test_supporting_evidence_is_bounded():
    text = """
Experience
Reduced errors by 20%.
Saved $3,000.
Improved response time by 4 hours.
Increased completed orders by 50%.
"""

    finding = _finding(text)

    assert finding.status == "satisfied"
    assert len(finding.supporting_text) == 3


@pytest.mark.parametrize(
    "statement",
    [
        "Managed a $50,000 budget.",
        "Worked from 2022 to 2025.",
        "Handled 100 customer requests.",
        "Software Engineer, 2021-2024.",
        "Received an award in 2024.",
    ],
)
def test_numbers_without_outcome_are_not_achievements(
    statement,
):
    finding = _finding("Experience\n" + statement)

    assert finding.status == "needs_attention"
    assert finding.supporting_text == []


def test_phone_number_is_not_an_outcome():
    finding = _finding(
        """
Alex Example
Phone: +8801712345678

Experience
Worked on internal applications.
"""
    )

    assert finding.status == "needs_attention"
    assert finding.supporting_text == []


@pytest.mark.parametrize(
    "statement",
    [
        "Target: reduce costs by 25%.",
        "Will improve accuracy by 30%.",
        "Planned to save $10,000.",
        "Did not reduce costs by 20%.",
    ],
)
def test_future_or_negated_claims_are_rejected(
    statement,
):
    finding = _finding("Projects\n" + statement)

    assert finding.status == "needs_attention"
    assert finding.supporting_text == []


def test_unrelated_clauses_are_not_combined():
    finding = _finding(
        """
Experience
Reduced errors; managed a $50,000 budget.
"""
    )

    assert finding.status == "needs_attention"


def test_unrelated_sections_are_not_assessed():
    finding = _finding(
        """
Skills
Reduced processing time by 35%.
"""
    )

    assert finding.status == "not_assessed"


def test_empty_resume_is_not_assessed():
    finding = _finding("   \n   ")

    assert finding.status == "not_assessed"


def test_empty_relevant_section_is_not_assessed():
    finding = _finding("Experience\nSkills\nPython")

    assert finding.status == "not_assessed"


def test_report_has_explicit_limitations():
    report = assess_quantified_outcome_evidence("Experience\nReduced costs by 20%.")

    assert report.score is None

    assert any("not verified" in item for item in report.limitations)

    assert any("layout" in item for item in report.limitations)


def test_legacy_analysis_is_unchanged():
    text = """
Taylor Example
taylor@example.com

Experience
Reduced errors by 20%.
"""

    original = analyze_resume(text)

    assess_quantified_outcome_evidence(text)

    assert analyze_resume(text) == original
    assert isinstance(original["ats_score"], int)
