from abc import ABC, abstractmethod

from app.schemas.resume import ResumeIntelligence


class LLMProvider(ABC):
    """
    Base interface for all CareerIQ LLM providers.

    Concrete providers may use a local model,
    cloud API, or another inference service.
    """

    @abstractmethod
    async def analyze_resume(
        self,
        resume_text: str,
    ) -> ResumeIntelligence:
        """
        Analyze resume text and return validated
        structured resume intelligence.
        """

        raise NotImplementedError
