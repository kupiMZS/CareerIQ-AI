import json

import httpx
import pytest

from app.providers.errors import (
    ProviderConnectionError,
    ProviderHTTPError,
    ProviderResponseError,
    ProviderTimeoutError,
)
from app.providers.ollama import (
    OllamaProvider,
    OllamaProviderError,
)
from app.schemas.resume import ResumeIntelligence


def build_success_response() -> dict:
    return {
        "candidate": {
            "name": "John Doe",
            "email": "john.doe@example.com",
            "headline": "Software Engineer",
        },
        "professional_summary": "Backend software engineer.",
        "skills": [
            {
                "name": "Python",
                "category": "programming_language",
                "confidence": 0.98,
                "evidence": ["Built backend services using Python."],
            }
        ],
        "education": [],
        "experience": [],
        "projects": [],
        "certifications": [],
        "publications": [
            {
                "title": "Reliable Career Recommendation Systems",
                "authors": [
                    "John Doe",
                    "Jane Smith",
                ],
                "venue": "Example Computing Journal",
                "date": "2025",
                "url": "https://example.com/publication",
            }
        ],
    }


@pytest.mark.anyio
async def test_ollama_provider_returns_resume_intelligence():
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        assert request.url.path == "/api/chat"

        payload = json.loads(request.content)

        assert "publications" in payload["format"]["properties"]

        assert any(
            "publications" in message["content"].casefold()
            for message in payload["messages"]
        )

        return httpx.Response(
            status_code=200,
            json={"message": {"content": json.dumps(build_success_response())}},
        )

    transport = httpx.MockTransport(handler)

    async with httpx.AsyncClient(transport=transport) as client:
        provider = OllamaProvider(
            base_url="http://ollama.test",
            model="test-model",
            client=client,
        )

        result = await provider.analyze_resume("John Doe Python Software Engineer")

    assert isinstance(
        result,
        ResumeIntelligence,
    )

    assert result.candidate.name == "John Doe"

    assert result.skills[0].name == "Python"

    assert len(result.publications) == 1

    publication = result.publications[0]

    assert publication.title == "Reliable Career Recommendation Systems"
    assert publication.authors == [
        "John Doe",
        "Jane Smith",
    ]
    assert publication.venue == "Example Computing Journal"
    assert publication.date == "2025"
    assert publication.url == "https://example.com/publication"


@pytest.mark.anyio
async def test_ollama_provider_rejects_empty_resume():
    provider = OllamaProvider(
        base_url="http://ollama.test",
        model="test-model",
    )

    with pytest.raises(
        OllamaProviderError,
        match="cannot be empty",
    ):
        await provider.analyze_resume("   ")


@pytest.mark.anyio
async def test_ollama_provider_classifies_http_failure():
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            status_code=500,
        )

    transport = httpx.MockTransport(handler)

    async with httpx.AsyncClient(transport=transport) as client:
        provider = OllamaProvider(
            base_url="http://ollama.test",
            model="test-model",
            client=client,
        )

        with pytest.raises(
            ProviderHTTPError,
        ) as exception_info:
            await provider.analyze_resume("John Doe Software Engineer")

    assert exception_info.value.status_code == 500


@pytest.mark.anyio
async def test_ollama_provider_classifies_invalid_response():
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            status_code=200,
            json={
                "message": {
                    "content": "not-json",
                }
            },
        )

    transport = httpx.MockTransport(handler)

    async with httpx.AsyncClient(transport=transport) as client:
        provider = OllamaProvider(
            base_url="http://ollama.test",
            model="test-model",
            client=client,
        )

        with pytest.raises(
            ProviderResponseError,
        ):
            await provider.analyze_resume("John Doe Software Engineer")


@pytest.mark.anyio
async def test_ollama_provider_classifies_timeout():
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        raise httpx.ReadTimeout(
            "Request timed out",
            request=request,
        )

    transport = httpx.MockTransport(handler)

    async with httpx.AsyncClient(transport=transport) as client:
        provider = OllamaProvider(
            base_url="http://ollama.test",
            model="test-model",
            client=client,
        )

        with pytest.raises(
            ProviderTimeoutError,
        ):
            await provider.analyze_resume("John Doe Software Engineer")


@pytest.mark.anyio
async def test_ollama_provider_classifies_connection_failure():
    def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        raise httpx.ConnectError(
            "Connection refused",
            request=request,
        )

    transport = httpx.MockTransport(handler)

    async with httpx.AsyncClient(transport=transport) as client:
        provider = OllamaProvider(
            base_url="http://ollama.test",
            model="test-model",
            client=client,
        )

        with pytest.raises(
            ProviderConnectionError,
        ):
            await provider.analyze_resume("John Doe Software Engineer")
