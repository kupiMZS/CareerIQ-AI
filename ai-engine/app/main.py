from fastapi import FastAPI

from app.analyzer import analyze_resume
from app.schemas.analysis import AnalyzeRequest, AnalyzeResponse

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
def analyze_resume_endpoint(
    request: AnalyzeRequest,
):
    return analyze_resume(request.resume_text)
