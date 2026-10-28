from fastapi import FastAPI

from app.core import get_settings
from app.providers.factory import create_orchestrator
from app.schemas.analysis import (
    AnalyzeEvidenceResponse,
    AnalyzeRequest,
    AnalyzeResponse,
    SkillEvidenceItem,
)
from app.schemas.ats import ATSReport
from app.schemas.career import (
    CareerRecommendationRequest,
    CareerRecommendationResponse,
)
from app.services import (
    CareerRecommendationEngine,
    build_analysis_response,
    enrich_resume_intelligence,
    summarize_resume_skill_evidence,
)
from app.services.ats_report_builder import build_ats_report

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
    "/analyze/evidence",
    response_model=AnalyzeEvidenceResponse,
)
async def analyze_resume_evidence_endpoint(
    request: AnalyzeRequest,
):
    """Run analysis with explicitly requested skill evidence."""

    settings = get_settings()

    orchestrator = create_orchestrator(settings)

    intelligence = await orchestrator.analyze_resume(request.resume_text)

    enriched_intelligence = enrich_resume_intelligence(
        request.resume_text,
        intelligence,
    )

    analysis = build_analysis_response(
        request.resume_text,
        enriched_intelligence,
    )

    reports = summarize_resume_skill_evidence(
        request.resume_text,
        enriched_intelligence,
    )

    skill_evidence = [
        SkillEvidenceItem(
            field_path=report.field_path,
            skill_name=report.skill_name,
            status=report.status,
            review_flags=list(report.review_flags),
        )
        for report in reports
    ]

    return AnalyzeEvidenceResponse(
        analysis=analysis,
        skill_evidence=skill_evidence,
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


@app.post(
    "/analyze/ats",
    response_model=ATSReport,
)
def analyze_resume_ats_endpoint(
    request: AnalyzeRequest,
) -> ATSReport:
    """Return opt-in text-only ATS findings.

    This endpoint does not invoke the AI orchestrator,
    calculate a new ATS score, or modify legacy analysis.
    """

    return build_ats_report(request.resume_text)
