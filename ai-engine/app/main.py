from fastapi import FastAPI
from pydantic import BaseModel, Field

from app.analyzer import analyze_resume


app = FastAPI(
    title="CareerIQ AI Engine",
    version="1.0.0",
)


class AnalyzeRequest(BaseModel):
    resume_text: str = Field(
        ...,
        min_length=1,
        description="Extracted text from the user's resume",
    )


class AnalyzeResponse(BaseModel):
    ats_score: int
    extracted_name: str | None
    extracted_email: str | None
    skills: list[str]
    education: list[str]
    experience: list[str]
    summary: str
    status: str


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "careeriq-ai-engine",
    }


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze_resume_endpoint(
    request: AnalyzeRequest,
):
    return analyze_resume(request.resume_text)
