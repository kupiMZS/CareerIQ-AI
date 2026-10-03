import httpx
from pydantic import ValidationError

from app.prompts.resume_analysis import (
    build_resume_analysis_messages,
    get_resume_analysis_schema,
)
from app.providers.base import LLMProvider
from app.providers.errors import (
    ProviderConnectionError,
    ProviderError,
    ProviderHTTPError,
    ProviderResponseError,
    ProviderTimeoutError,
)
from app.schemas.resume import ResumeIntelligence

# Backward-compatible alias for code that currently
# imports OllamaProviderError.
OllamaProviderError = ProviderError


class OllamaProvider(LLMProvider):
    def __init__(
        self,
        base_url: str,
        model: str,
        request_path: str = "/api/chat",
        timeout_seconds: float = 30.0,
        client: httpx.AsyncClient | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.request_path = request_path
        self.timeout_seconds = timeout_seconds
        self.client = client

    async def analyze_resume(
        self,
        resume_text: str,
    ) -> ResumeIntelligence:
        if not resume_text.strip():
            raise OllamaProviderError("Resume text cannot be empty.")

        if self.client is not None:
            return await self._analyze_with_client(
                self.client,
                resume_text,
            )

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            return await self._analyze_with_client(
                client,
                resume_text,
            )

    async def _analyze_with_client(
        self,
        client: httpx.AsyncClient,
        resume_text: str,
    ) -> ResumeIntelligence:
        payload = {
            "model": self.model,
            "stream": False,
            "messages": (build_resume_analysis_messages(resume_text)),
            "format": get_resume_analysis_schema(),
            "options": {
                "temperature": 0,
            },
        }

        try:
            response = await client.post(
                (f"{self.base_url}{self.request_path}"),
                json=payload,
            )

            response.raise_for_status()

            body = response.json()

            content = body["message"]["content"]

            if not isinstance(content, str):
                raise ProviderResponseError("Ollama returned invalid message content.")

            return ResumeIntelligence.model_validate_json(content)

        except ProviderError:
            raise

        except httpx.TimeoutException as exception:
            raise ProviderTimeoutError("Ollama request timed out.") from exception

        except httpx.ConnectError as exception:
            raise ProviderConnectionError("Could not connect to Ollama.") from exception

        except httpx.HTTPStatusError as exception:
            status_code = exception.response.status_code

            raise ProviderHTTPError(
                (f"Ollama returned HTTP {status_code}."),
                status_code=status_code,
            ) from exception

        except httpx.RequestError as exception:
            raise ProviderConnectionError("Ollama request failed.") from exception

        except (
            KeyError,
            TypeError,
            ValueError,
            ValidationError,
        ) as exception:
            raise ProviderResponseError(
                "Ollama returned an invalid response."
            ) from exception
