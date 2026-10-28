"""Compose independently assessed ATS findings into one report."""

from app.schemas.ats import ATSFinding, ATSReport
from app.services.ats_achievement_evidence import (
    assess_quantified_outcome_evidence,
)
from app.services.ats_assessment import (
    assess_resume_section_content,
    assess_resume_structure,
)


def build_ats_report(resume_text: str) -> ATSReport:
    """Combine observable findings without introducing scoring.

    Preserve the findings and explanations produced by each
    existing evaluator. Reject duplicate codes or unexpected
    component scoring rather than silently discarding them.
    """

    reports = (
        assess_resume_structure(resume_text),
        assess_resume_section_content(resume_text),
        assess_quantified_outcome_evidence(resume_text),
    )

    findings: list[ATSFinding] = []
    limitations: list[str] = []

    seen_codes: set[str] = set()
    seen_limitations: set[str] = set()

    for report in reports:
        if report.score is not None:
            raise ValueError("Unexpected score in an internal ATS component.")

        for finding in report.findings:
            if finding.code in seen_codes:
                raise ValueError(f"Duplicate ATS finding code: {finding.code}")

            seen_codes.add(finding.code)
            findings.append(finding.model_copy(deep=True))

        for limitation in report.limitations:
            if limitation in seen_limitations:
                continue

            seen_limitations.add(limitation)
            limitations.append(limitation)

    return ATSReport(
        score=None,
        findings=findings,
        limitations=limitations,
    )
