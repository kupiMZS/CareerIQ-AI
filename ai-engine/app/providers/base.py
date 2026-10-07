from abc import ABC, abstractmethod

from app.schemas.resume import ResumeIntelligence


class ResumeAnalysisProvider(ABC):
    """
    Base interface for any CareerIQ resume analysis provider.

    Implementations may use deterministic rules,
    local models, cloud LLMs, or other inference systems.
    """

    @abstractmethod
    async def analyze_resume(
        self,
        resume_text: str,
    ) -> ResumeIntelligence:
        raise NotImplementedError


class LLMProvider(ResumeAnalysisProvider, ABC):
    """
    Base interface for resume analysis providers
    powered specifically by large language models.
    """
