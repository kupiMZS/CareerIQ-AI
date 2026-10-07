from fastapi import FastAPI

from app.core import get_settings
from app.providers.factory import create_orchestrator
from app.schemas.analysis import (
    AnalyzeRequest,
    AnalyzeResponse,
)
from app.schemas.career import (
    CareerRecommendationRequest,
    CareerRecommendationResponse,
)
from app.services import (
    CareerRecommendationEngine,
    build_analysis_response,
    enrich_resume_intelligence,
)

app = FastAPI(
    title="CareerIQ AI Engine",
    version="1.0.0",
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "careeriq-ai-engine",
    }


@app.post(
    "/analyze",
    response_model=AnalyzeResponse,
)
async def analyze_resume_endpoint(
    request: AnalyzeRequest,
):
    settings = get_settings()

    orchestrator = create_orchestrator(settings)

    intelligence = await orchestrator.analyze_resume(request.resume_text)

    enriched_intelligence = enrich_resume_intelligence(
        request.resume_text,
        intelligence,
    )

    return build_analysis_response(
        request.resume_text,
        enriched_intelligence,
    )


@app.post(
    "/career/recommend",
    response_model=CareerRecommendationResponse,
)
def recommend_career_endpoint(
    request: CareerRecommendationRequest,
):
    engine = CareerRecommendationEngine()

    return engine.recommend(request)
