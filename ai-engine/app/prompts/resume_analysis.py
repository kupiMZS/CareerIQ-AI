from app.schemas.resume import ResumeIntelligence

RESUME_ANALYSIS_PROMPT_VERSION = "resume-analysis-v1"


SYSTEM_PROMPT = """
You are CareerIQ, a resume intelligence engine.

Extract factual information only from the supplied resume.

Do not invent employers, education, skills, dates,
certifications, projects, or candidate details.

Return data matching the supplied JSON schema.
""".strip()


def build_resume_analysis_messages(
    resume_text: str,
) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": (
                "Analyze the following resume and return "
                "structured JSON only.\n\n"
                f"Resume:\n{resume_text}"
            ),
        },
    ]


def get_resume_analysis_schema() -> dict:
    return ResumeIntelligence.model_json_schema()
