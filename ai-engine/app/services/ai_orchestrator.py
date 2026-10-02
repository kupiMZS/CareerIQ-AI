from app.providers.base import ResumeAnalysisProvider
from app.schemas.resume import ResumeIntelligence


class AIOrchestrator:
    """
    Coordinates resume analysis providers.

    The primary provider is attempted first.
    If it fails and a fallback provider exists,
    the fallback provider is used.
    """

    def __init__(
        self,
        primary_provider: ResumeAnalysisProvider,
        fallback_provider: ResumeAnalysisProvider | None = None,
    ):
        self.primary_provider = primary_provider
        self.fallback_provider = fallback_provider

    async def analyze_resume(
        self,
        resume_text: str,
    ) -> ResumeIntelligence:
        try:
            return await self.primary_provider.analyze_resume(resume_text)
        except Exception:
            if self.fallback_provider is None:
                raise

            return await self.fallback_provider.analyze_resume(resume_text)
