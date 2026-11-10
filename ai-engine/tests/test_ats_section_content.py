from app.analyzer import analyze_resume
from app.services.ats_assessment import (
    assess_resume_section_content,
    assess_resume_structure,
)


def _findings(text):
    report = assess_resume_section_content(text)
    return {finding.code: finding for finding in report.findings}


def test_sections_with_content_are_detected():
    findings = _findings(
        """
Skills
Python and Docker

Education
BSc Computer Science

Experience
Software Developer
"""
    )

    assert len(findings) == 3
    assert all(item.status == "satisfied" for item in findings.values())


def test_empty_sections_need_attention():
    findings = _findings("Skills\nEducation\nExperience\n")

    assert all(item.status == "needs_attention" for item in findings.values())


def test_missing_headings_are_not_assessed():
    findings = _findings("Taylor developed applications using Python.")

    assert all(item.status == "not_assessed" for item in findings.values())


def test_whitespace_only_resume_is_not_assessed():
    report = assess_resume_section_content("  \n  ")

    assert report.score is None
    assert len(report.findings) == 3

    assert all(finding.status == "not_assessed" for finding in report.findings)


def test_placeholder_content_is_not_sufficient():
    findings = _findings(
        """
Skills
N/A

Education
TBD

Experience
None
"""
    )

    assert all(item.status == "needs_attention" for item in findings.values())


def test_next_heading_does_not_count_as_content():
    findings = _findings(
        """
Skills
Education
BSc Computer Science

Experience
Engineer
"""
    )

    assert findings["section_skills_content"].status == "needs_attention"

    assert findings["section_education_content"].status == "satisfied"


def test_duplicate_heading_can_supply_content():
    findings = _findings(
        """
Skills
TBD

Technical Skills:
Python
"""
    )

    skill = findings["section_skills_content"]

    assert skill.status == "satisfied"
    assert skill.supporting_text == ["Python"]


def test_other_known_heading_ends_content_section():
    findings = _findings(
        """
Skills
Summary
Experienced developer.
"""
    )

    assert findings["section_skills_content"].status == "needs_attention"


def test_report_remains_unscored_and_limited():
    report = assess_resume_section_content("Skills\nPython")

    assert report.score is None

    assert any("do not validate qualifications" in item for item in report.limitations)

    assert any("job-specific" in item for item in report.limitations)


def test_existing_structure_assessment_is_unchanged():
    text = """
Taylor Example
taylor@example.com

Skills
Python
"""

    structure = assess_resume_structure(text)
    content = assess_resume_section_content(text)

    assert len(structure.findings) == 4
    assert len(content.findings) == 3
    assert structure.score is None
    assert content.score is None


def test_legacy_analysis_remains_unchanged():
    text = """
Alex Example
alex@example.com

Skills
Python

Education
BSc

Experience
Developer
"""

    baseline = analyze_resume(text)

    assess_resume_section_content(text)

    assert analyze_resume(text) == baseline
    assert isinstance(baseline["ats_score"], int)
