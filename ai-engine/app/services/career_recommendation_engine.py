from dataclasses import dataclass

from app.schemas.career import (
    CareerRecommendation,
    CareerRecommendationRequest,
    CareerRecommendationResponse,
    LearningRoadmapStep,
)


@dataclass(frozen=True)
class CareerDefinition:
    title: str
    required_skills: tuple[str, ...]
    aliases: tuple[str, ...] = ()


CAREER_CATALOG: tuple[CareerDefinition, ...] = (
    CareerDefinition(
        title="Backend Engineer",
        required_skills=(
            "Python",
            "FastAPI",
            "PostgreSQL",
            "Docker",
        ),
        aliases=(
            "Backend Developer",
            "Backend Software Engineer",
        ),
    ),
    CareerDefinition(
        title="Data Engineer",
        required_skills=(
            "Python",
            "SQL",
            "PostgreSQL",
            "Apache Airflow",
            "ETL",
        ),
        aliases=("Data Engineering",),
    ),
    CareerDefinition(
        title="Frontend Developer",
        required_skills=(
            "JavaScript",
            "TypeScript",
            "Angular",
            "HTML",
            "CSS",
        ),
        aliases=(
            "Frontend Engineer",
            "Front End Developer",
        ),
    ),
    CareerDefinition(
        title="DevOps Engineer",
        required_skills=(
            "Docker",
            "Kubernetes",
            "Linux",
            "CI/CD",
            "AWS",
        ),
        aliases=(
            "DevOps",
            "Platform Engineer",
        ),
    ),
    CareerDefinition(
        title="Machine Learning Engineer",
        required_skills=(
            "Python",
            "Machine Learning",
            "scikit-learn",
            "Docker",
            "FastAPI",
        ),
        aliases=(
            "ML Engineer",
            "AI Engineer",
        ),
    ),
)

MAX_RECOMMENDATIONS = 3


def _normalize(
    value: str,
) -> str:
    return value.strip().casefold()


def _normalized_skill_set(
    skills: list[str],
) -> set[str]:
    return {normalized for skill in skills if (normalized := _normalize(skill))}


def _matched_skills(
    definition: CareerDefinition,
    skill_set: set[str],
) -> list[str]:
    return [
        skill for skill in definition.required_skills if _normalize(skill) in skill_set
    ]


def _missing_skills(
    definition: CareerDefinition,
    skill_set: set[str],
) -> list[str]:
    return [
        skill
        for skill in definition.required_skills
        if _normalize(skill) not in skill_set
    ]


def _matches_role(
    value: str | None,
    definition: CareerDefinition,
) -> bool:
    if not value:
        return False

    normalized_value = _normalize(value)

    candidates = (
        definition.title,
        *definition.aliases,
    )

    for candidate in candidates:
        normalized_candidate = _normalize(candidate)

        if normalized_value == normalized_candidate:
            return True

        if normalized_value in normalized_candidate:
            return True

        if normalized_candidate in normalized_value:
            return True

    return False


def _score_definition(
    definition: CareerDefinition,
    request: CareerRecommendationRequest,
    skill_set: set[str],
) -> float:
    weighted_score = 0.0
    total_weight = 0.0

    if skill_set:
        skill_score = len(
            _matched_skills(
                definition,
                skill_set,
            )
        ) / len(definition.required_skills)

        weighted_score += skill_score * 0.6
        total_weight += 0.6

    if request.profile.career_goal:
        goal_score = float(
            _matches_role(
                request.profile.career_goal,
                definition,
            )
        )

        weighted_score += goal_score * 0.3
        total_weight += 0.3

    if request.profile.current_role:
        current_role_score = float(
            _matches_role(
                request.profile.current_role,
                definition,
            )
        )

        weighted_score += current_role_score * 0.1
        total_weight += 0.1

    if total_weight == 0.0:
        return 0.0

    return round(
        weighted_score / total_weight,
        4,
    )


def _build_rationale(
    definition: CareerDefinition,
    request: CareerRecommendationRequest,
    matched_skills: list[str],
    *,
    entry_level: bool,
) -> str:
    parts: list[str] = []

    if _matches_role(
        request.profile.career_goal,
        definition,
    ):
        parts.append("Aligns with your stated career goal.")

    if _matches_role(
        request.profile.current_role,
        definition,
    ):
        parts.append("Builds naturally on your current role.")

    if request.skills:
        parts.append(
            f"Matches {len(matched_skills)} of "
            f"{len(definition.required_skills)} "
            "core baseline skills."
        )

    if entry_level:
        parts.append(
            "Presented as an entry-level path "
            "because no professional experience "
            "was provided."
        )

    if not parts:
        parts.append(
            "Potential career path based on the available profile information."
        )

    return " ".join(parts)


def _build_roadmap(
    recommendation: CareerRecommendation,
) -> list[LearningRoadmapStep]:
    if recommendation.missing_skills:
        return [
            LearningRoadmapStep(
                step=index,
                title=(f"Build {skill} proficiency"),
                description=(
                    f"Learn and apply {skill} "
                    "through a focused project "
                    f"aligned with "
                    f"{recommendation.career_title}."
                ),
                skills=[
                    skill,
                ],
            )
            for index, skill in enumerate(
                recommendation.missing_skills,
                start=1,
            )
        ]

    return [
        LearningRoadmapStep(
            step=1,
            title=("Build a role-focused portfolio project"),
            description=(
                "Apply your existing skills in a "
                "portfolio project that demonstrates "
                f"readiness for "
                f"{recommendation.career_title}."
            ),
            skills=list(recommendation.matched_skills),
        )
    ]


def _missing_information(
    request: CareerRecommendationRequest,
    skill_set: set[str],
) -> list[str]:
    if skill_set or request.profile.career_goal or request.profile.current_role:
        return []

    return [
        "skills",
        "career_goal",
    ]


class CareerRecommendationEngine:
    """
    Deterministic baseline CareerIQ career engine.

    This baseline provides transparent, repeatable
    career ranking, skill-gap detection, and learning
    roadmap generation before model-backed career
    recommendation providers are introduced.
    """

    def recommend(
        self,
        request: CareerRecommendationRequest,
    ) -> CareerRecommendationResponse:
        skill_set = _normalized_skill_set(request.skills)

        missing_information = _missing_information(
            request,
            skill_set,
        )

        if missing_information:
            return CareerRecommendationResponse(
                status="needs_more_information",
                missing_information=(missing_information),
            )

        entry_level = request.profile.years_experience == 0

        ranked: list[
            tuple[
                int,
                CareerDefinition,
                float,
                list[str],
                list[str],
            ]
        ] = []

        for index, definition in enumerate(CAREER_CATALOG):
            matched = _matched_skills(
                definition,
                skill_set,
            )

            missing = _missing_skills(
                definition,
                skill_set,
            )

            score = _score_definition(
                definition,
                request,
                skill_set,
            )

            if score <= 0.0:
                continue

            ranked.append(
                (
                    index,
                    definition,
                    score,
                    matched,
                    missing,
                )
            )

        ranked.sort(
            key=lambda item: (
                -item[2],
                item[0],
            )
        )

        recommendations: list[CareerRecommendation] = []

        for (
            _,
            definition,
            score,
            matched,
            missing,
        ) in ranked[:MAX_RECOMMENDATIONS]:
            recommendations.append(
                CareerRecommendation(
                    career_title=definition.title,
                    match_score=score,
                    rationale=_build_rationale(
                        definition,
                        request,
                        matched,
                        entry_level=(entry_level),
                    ),
                    matched_skills=matched,
                    missing_skills=missing,
                    entry_level=entry_level,
                )
            )

        if not recommendations:
            return CareerRecommendationResponse(
                status="needs_more_information",
                missing_information=[
                    "career_goal",
                ],
            )

        roadmap = _build_roadmap(recommendations[0])

        return CareerRecommendationResponse(
            status="ok",
            recommendations=recommendations,
            roadmap=roadmap,
        )
