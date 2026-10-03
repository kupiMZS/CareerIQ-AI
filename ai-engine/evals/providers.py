from app.providers.base import ResumeAnalysisProvider
from app.schemas.resume import ResumeIntelligence
from app.services import enrich_resume_intelligence


class EnrichedResumeProvider(ResumeAnalysisProvider):
    """
    Evaluation wrapper that applies CareerIQ's
    deterministic enrichment to another provider.

    Provider failures are not hidden or replaced
    with fallback behavior.
    """

    def __init__(
        self,
        provider: ResumeAnalysisProvider,
    ):
        self.provider = provider

    async def analyze_resume(
        self,
        resume_text: str,
    ) -> ResumeIntelligence:
        intelligence = await self.provider.analyze_resume(resume_text)

        return enrich_resume_intelligence(
            resume_text,
            intelligence,
        )
