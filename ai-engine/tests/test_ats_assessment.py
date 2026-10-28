from app.analyzer import analyze_resume
from app.schemas.ats import ATSReport
from app.services.ats_assessment import assess_resume_structure


def _findings(report: ATSReport):
    return {item.code: item for item in report.findings}


def test_complete_synthetic_resume_has_supported_checks():
    text = """
Taylor Example
taylor@example.com

Skills:
Python

Education
BSc Computer Science

Work Experience
Software Developer
"""

    report = assess_resume_structure(text)
    findings = _findings(report)

    assert report.score is None
    assert len(findings) == 4
    assert all(finding.status == "satisfied" for finding in findings.values())
    assert findings["contact_email"].supporting_text == ["taylor@example.com"]


def test_missing_email_is_reported_without_guessing():
    text = "Skills\nPython\nEducation\nBSc"

    findings = _findings(assess_resume_structure(text))
    email = findings["contact_email"]

    assert email.status == "needs_attention"
    assert email.supporting_text == []
    assert email.recommendation is not None


def test_existing_section_aliases_are_reused():
    text = """
alex@example.com
Technical Skills:
Python

Academic Background
BSc

Employment History
Engineer
"""

    findings = _findings(assess_resume_structure(text))

    assert findings["section_skills"].status == "satisfied"
    assert findings["section_education"].status == "satisfied"
    assert findings["section_experience"].status == "satisfied"


def test_headings_are_case_insensitive():
    text = """
jordan@example.com

SKILLS:
Python

EDUCATION:
BSc

EXPERIENCE:
Developer
"""

    findings = _findings(assess_resume_structure(text))

    assert all(finding.status == "satisfied" for finding in findings.values())


def test_casual_mentions_are_not_section_headings():
    text = """
casey@example.com
I developed technical skills through education
and gained experience working on projects.
"""

    findings = _findings(assess_resume_structure(text))

    assert findings["contact_email"].status == "satisfied"

    for code in (
        "section_skills",
        "section_education",
        "section_experience",
    ):
        assert findings[code].status == "needs_attention"
        assert "does not establish" in findings[code].explanation


def test_empty_text_is_not_assessed():
    report = assess_resume_structure("   \n   ")

    assert report.score is None
    assert len(report.findings) == 4
    assert all(item.status == "not_assessed" for item in report.findings)


def test_duplicate_heading_does_not_duplicate_finding():
    text = """
sam@example.com
Skills
Python
Technical Skills:
Docker
"""

    report = assess_resume_structure(text)
    findings = _findings(report)

    assert len(report.findings) == 4
    assert findings["section_skills"].supporting_text == ["Skills"]


def test_report_does_not_claim_format_compatibility():
    report = assess_resume_structure("lee@example.com\nSkills\nPython")

    assert report.score is None
    assert any(
        "layout and formatting were not assessed" in item for item in report.limitations
    )
    assert any("job-specific" in item for item in report.limitations)


def test_assessment_does_not_change_legacy_analysis():
    text = """
Morgan Example
morgan@example.com
Skills
Python
Education
BSc
Experience
Software Engineer
"""

    original = analyze_resume(text)

    report = assess_resume_structure(text)

    assert report.score is None
    assert analyze_resume(text) == original
    assert isinstance(original["ats_score"], int)
