import pytest
from pydantic import ValidationError

from app.schemas.analysis import AnalyzeResponse
from app.schemas.ats import ATSFinding, ATSReport


def test_ats_report_defaults_to_unscored():
    report = ATSReport()

    assert report.report_version == "ats-v1"
    assert report.score is None
    assert report.findings == []
    assert report.limitations == []


def test_ats_finding_preserves_explanation():
    finding = ATSFinding(
        code="contact_email",
        status="satisfied",
        explanation="Email appears in the resume text.",
        supporting_text=["person@example.com"],
    )

    assert finding.code == "contact_email"
    assert finding.status == "satisfied"
    assert finding.supporting_text == ["person@example.com"]


@pytest.mark.parametrize(
    "status",
    [
        "satisfied",
        "needs_attention",
        "not_assessed",
    ],
)
def test_supported_finding_statuses(status):
    finding = ATSFinding(
        code="section_check",
        status=status,
        explanation="Synthetic assessment explanation.",
    )

    assert finding.status == status


def test_invalid_finding_status_rejected():
    with pytest.raises(ValidationError):
        ATSFinding(
            code="section_check",
            status="guaranteed_ats_acceptance",
            explanation="Invalid result.",
        )


@pytest.mark.parametrize("score", [-1, 101])
def test_out_of_range_score_rejected(score):
    with pytest.raises(ValidationError):
        ATSReport(score=score)


def test_report_retains_limitations():
    report = ATSReport(
        findings=[
            ATSFinding(
                code="job_alignment",
                status="not_assessed",
                explanation="No job description supplied.",
            )
        ],
        limitations=[
            "Job-specific suitability was not assessed.",
        ],
    )

    assert report.score is None
    assert report.findings[0].status == "not_assessed"
    assert len(report.limitations) == 1


def test_unknown_fields_rejected():
    with pytest.raises(ValidationError):
        ATSReport(guaranteed_hiring_probability=99)


def test_existing_analysis_contract_remains_separate():
    assert set(AnalyzeResponse.model_fields) == {
        "ats_score",
        "extracted_name",
        "extracted_email",
        "skills",
        "education",
        "experience",
        "summary",
        "status",
    }

    assert "ats_score" not in ATSReport.model_fields
