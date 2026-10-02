import re

SKILL_KEYWORDS = [
    "python",
    "java",
    "javascript",
    "typescript",
    "php",
    "c",
    "c++",
    "c#",
    "laravel",
    "django",
    "fastapi",
    "flask",
    "angular",
    "react",
    "vue",
    "node.js",
    "docker",
    "kubernetes",
    "git",
    "github",
    "mysql",
    "postgresql",
    "mongodb",
    "redis",
    "aws",
    "azure",
    "gcp",
    "linux",
    "sql",
    "html",
    "css",
    "tailwind",
    "rest api",
    "machine learning",
    "deep learning",
    "tensorflow",
    "pytorch",
    "pandas",
    "numpy",
    "scikit-learn",
]


SECTION_ALIASES = {
    # Summary
    "summary": "summary",
    "professional summary": "summary",
    "profile": "summary",
    "professional profile": "summary",
    "objective": "summary",
    "career objective": "summary",
    # Experience
    "experience": "experience",
    "work experience": "experience",
    "professional experience": "experience",
    "employment history": "experience",
    "work history": "experience",
    # Education
    "education": "education",
    "educational background": "education",
    "academic background": "education",
    "academic qualifications": "education",
    # Skills
    "skills": "skills",
    "technical skills": "skills",
    "core skills": "skills",
    "key skills": "skills",
    "technologies": "skills",
    "technical expertise": "skills",
    # Projects
    "projects": "projects",
    "personal projects": "projects",
    "academic projects": "projects",
    "key projects": "projects",
    # Certifications
    "certifications": "certifications",
    "certificates": "certifications",
    "professional certifications": "certifications",
}


def extract_email(text: str) -> str | None:
    match = re.search(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        text,
    )

    return match.group(0) if match else None


def extract_name(text: str) -> str | None:
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    if not lines:
        return None

    email = extract_email(text)

    excluded_terms = {
        "engineer",
        "developer",
        "manager",
        "analyst",
        "consultant",
        "intern",
        "researcher",
        "designer",
        "scientist",
        "administrator",
        "architect",
        "technician",
        "specialist",
        "coordinator",
        "director",
        "officer",
        "professor",
        "student",
        "resume",
        "curriculum vitae",
        "cv",
        "profile",
        "summary",
        "objective",
        "experience",
        "education",
        "skills",
    }

    normalized_skills = {skill.lower() for skill in SKILL_KEYWORDS}

    single_word_skills = {skill.lower() for skill in SKILL_KEYWORDS if " " not in skill}

    for line in lines[:5]:
        line_lower = line.lower().strip()

        # Do not treat the email address as a name.
        if email and line_lower == email.lower():
            continue

        # A person's name should contain only alphabetic words,
        # apostrophes, hyphens, or spaces.
        if not re.fullmatch(
            r"[A-Za-z]+(?:[ '-][A-Za-z]+){1,2}",
            line,
        ):
            continue

        words = line_lower.split()

        # Names should normally contain 2 or 3 words.
        if len(words) not in (2, 3):
            continue

        # Reject obvious job titles and resume section labels.
        if any(term in line_lower for term in excluded_terms):
            continue

        # Reject lines that exactly match a known skill,
        # such as "Machine Learning" or "Python".
        if line_lower in normalized_skills:
            continue

        # Reject lines made entirely from individual skill names,
        # such as:
        #
        # Python Laravel Angular
        # Java Docker Git
        #
        # This was the specific bug causing the failing test.
        if words and all(word in single_word_skills for word in words):
            continue

        return line

    return None


def detect_sections(text: str) -> dict[str, list[str]]:
    """
    Detect common resume sections and return their lines.

    Example:

        PROFESSIONAL EXPERIENCE

        Software Engineer

        ABC Technologies

    becomes:

        {
            "experience": [
                "Software Engineer",
                "ABC Technologies"
            ]
        }
    """

    sections: dict[str, list[str]] = {}
    current_section: str | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        normalized = line.lower()

        # Remove common trailing separators/bullets.
        normalized = re.sub(
            r"[\s:|•\-]+$",
            "",
            normalized,
        )

        normalized = re.sub(
            r"\s+",
            " ",
            normalized,
        )

        section_name = SECTION_ALIASES.get(normalized)

        if section_name:
            current_section = section_name
            sections.setdefault(current_section, [])
            continue

        if current_section:
            sections[current_section].append(line)

    return sections


def extract_skills(text: str) -> list[str]:
    text_lower = text.lower()

    found = []

    for skill in SKILL_KEYWORDS:
        pattern = (
            rf"(?<![a-z0-9])"
            rf"{re.escape(skill.lower())}"
            rf"(?![a-z0-9])"
        )

        if re.search(pattern, text_lower):
            found.append(skill)

    # Avoid reporting "c" when the resume explicitly contains
    # the more specific "c++" or "c#".
    if "c++" in found or "c#" in found:
        found = [skill for skill in found if skill != "c"]

    return found


def extract_education(text: str) -> list[str]:
    education = []

    patterns = [
        r"\b(?:BSc|B\.Sc\.|Bachelor(?:'s)?|BS|B\.S\.)[^.\n]*",
        r"\b(?:MSc|M\.Sc\.|Master(?:'s)?|MS|M\.S\.)[^.\n]*",
        r"\b(?:PhD|Ph\.D\.|Doctorate)[^.\n]*",
    ]

    sections = detect_sections(text)

    if "education" in sections:
        education_text = "\n".join(sections["education"])
    else:
        education_text = text

    for pattern in patterns:
        matches = re.findall(
            pattern,
            education_text,
            flags=re.IGNORECASE,
        )

        for match in matches:
            cleaned = match.strip()

            if cleaned and cleaned not in education:
                education.append(cleaned)

    return education


def extract_experience(text: str) -> list[str]:
    """
    Extract likely experience entries.

    If an explicit experience section exists, only that section
    is analyzed. This prevents a resume headline such as
    "Software Engineer" from being mistaken for work experience.

    When no experience section exists, the function falls back
    to keyword-based detection.
    """

    sections = detect_sections(text)

    if "experience" in sections:
        lines = sections["experience"]
    else:
        lines = [line.strip() for line in text.splitlines() if line.strip()]

    keywords = [
        "engineer",
        "developer",
        "manager",
        "analyst",
        "consultant",
        "intern",
        "researcher",
        "designer",
        "scientist",
        "administrator",
    ]

    candidates = []

    for line in lines:
        line_lower = line.lower()

        if (
            any(keyword in line_lower for keyword in keywords)
            and line not in candidates
        ):
            candidates.append(line)

    return candidates


def generate_summary(
    text: str,
    skills: list[str],
    education: list[str],
    experience: list[str],
) -> str:
    parts = []

    if experience:
        parts.append(
            f"Experience-related information was identified "
            f"from {len(experience)} resume entries."
        )

    if skills:
        parts.append(f"The resume mentions {len(skills)} technical skills.")

    if education:
        parts.append(
            f"{len(education)} education-related qualification(s) were identified."
        )

    if not parts:
        return text[:500].strip()

    return " ".join(parts)


def calculate_ats_score(
    text: str,
    skills: list[str],
    education: list[str],
    experience: list[str],
) -> int:
    """
    Prototype ATS scoring model.

    This scoring model is intentionally simple for now.
    It will be replaced with a more meaningful weighted model
    after the extraction pipeline is stable.
    """

    score = 0

    # Resume length / content
    if len(text.strip()) >= 100:
        score += 20

    # Technical skills: maximum 30 points
    if skills:
        score += min(
            len(skills) * 5,
            30,
        )

    # Education
    if education:
        score += 20

    # Experience: maximum 20 points
    if experience:
        score += min(
            len(experience) * 5,
            20,
        )

    # Email
    if extract_email(text):
        score += 5

    # Name
    if extract_name(text):
        score += 5

    return min(score, 100)


def analyze_resume(text: str) -> dict:
    text = text.strip()

    name = extract_name(text)
    email = extract_email(text)
    skills = extract_skills(text)
    education = extract_education(text)
    experience = extract_experience(text)

    return {
        "ats_score": calculate_ats_score(
            text,
            skills,
            education,
            experience,
        ),
        "extracted_name": name,
        "extracted_email": email,
        "skills": skills,
        "education": education,
        "experience": experience,
        "summary": generate_summary(
            text,
            skills,
            education,
            experience,
        ),
        "status": "completed",
    }
