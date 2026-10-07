import pytest

from app.providers import RuleBasedProvider
from app.schemas.resume import ResumeIntelligence


@pytest.mark.anyio
async def test_rule_based_provider_returns_resume_intelligence():
    provider = RuleBasedProvider()

    resume_text = """
    John Doe
    Software Engineer
    john.doe@example.com

    TECHNICAL SKILLS
    Python, Laravel, Angular, Docker, MySQL

    EDUCATION
    BSc Computer Science

    PROFESSIONAL EXPERIENCE
    Software Engineer at ABC Technologies
    """

    result = await provider.analyze_resume(resume_text)

    assert isinstance(
        result,
        ResumeIntelligence,
    )

    assert result.candidate.name == "John Doe"

    assert result.candidate.email == "john.doe@example.com"


@pytest.mark.anyio
async def test_rule_based_provider_converts_detected_skills():
    provider = RuleBasedProvider()

    resume_text = """
    John Doe
    Software Engineer
    john.doe@example.com

    TECHNICAL SKILLS
    Python, Laravel, Angular, Docker, MySQL
    """

    result = await provider.analyze_resume(resume_text)

    skill_names = {skill.name for skill in result.skills}

    assert "python" in skill_names
    assert "laravel" in skill_names
    assert "angular" in skill_names
    assert "docker" in skill_names
    assert "mysql" in skill_names
