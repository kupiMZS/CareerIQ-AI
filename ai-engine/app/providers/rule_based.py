from app.analyzer import analyze_resume
from app.providers.base import ResumeAnalysisProvider
from app.schemas.resume import (
    Candidate,
    Education,
    Experience,
    ResumeIntelligence,
    Skill,
)


class RuleBasedProvider(ResumeAnalysisProvider):
    """
    Adapter around CareerIQ's deterministic
    rule-based resume analyzer.

    This provider acts as a baseline and future
    fallback when an LLM provider is unavailable.
    """

    async def analyze_resume(
        self,
        resume_text: str,
    ) -> ResumeIntelligence:
        result = analyze_resume(resume_text)

        candidate = Candidate(
            name=result.get("extracted_name"),
            email=result.get("extracted_email"),
        )

        skills = [
            Skill(
                name=skill,
            )
            for skill in result.get("skills", [])
        ]

        education = [
            Education(
                degree=item,
            )
            for item in result.get("education", [])
        ]

        experience = [
            Experience(
                job_title=item,
            )
            for item in result.get("experience", [])
        ]

        return ResumeIntelligence(
            candidate=candidate,
            skills=skills,
            education=education,
            experience=experience,
        )
