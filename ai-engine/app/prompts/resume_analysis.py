from app.schemas.resume import ResumeIntelligence

RESUME_ANALYSIS_PROMPT_VERSION = "resume-analysis-v2"


SYSTEM_PROMPT = """
You are CareerIQ, a factual resume information extraction engine.

Your job is to extract all information explicitly present in a resume
into the supplied JSON schema.

Important rules:

- Never invent information.
- Never omit information just because some fields are missing.
- If an email address appears, copy it exactly into candidate.email.
- If a professional title appears near the candidate name, use it as
  candidate.headline.
- If an education line exists, create an education object even when
  institution or dates are missing.
- If a work-experience line exists, create an experience object even
  when dates or responsibilities are missing.
- Split expressions such as
  "Software Engineer at ABC Technologies"
  into:
  job_title = "Software Engineer"
  company = "ABC Technologies"
- Preserve technology names such as Python, Laravel, Docker, MySQL,
  Angular, Git, AWS, and similar skills.
- Use null for missing optional scalar values.
- Use an empty list only when that category truly does not appear
  anywhere in the resume.

Example:

Resume:
Jane Smith
jane@example.com
Backend Engineer

Skills
Python
Docker

Education
BSc Computer Science

Experience
Backend Engineer at Example Labs

Expected extraction behavior:
- candidate.name = "Jane Smith"
- candidate.email = "jane@example.com"
- candidate.headline = "Backend Engineer"
- skills contains Python and Docker
- education contains one entry whose degree is
  "BSc Computer Science"
- experience contains one entry with:
  job_title = "Backend Engineer"
  company = "Example Labs"

Return only data matching the supplied JSON schema.
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
                "Extract every factual resume field from the "
                "following resume.\n\n"
                "Before returning the JSON, make sure you checked:\n"
                "- candidate name\n"
                "- email\n"
                "- headline or job title\n"
                "- every skill\n"
                "- every education entry\n"
                "- every experience entry\n"
                "- projects\n"
                "- certifications\n\n"
                f"Resume:\n{resume_text}"
            ),
        },
    ]


def get_resume_analysis_schema() -> dict:
    return ResumeIntelligence.model_json_schema()
