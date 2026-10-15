"""Safety tests for research-only skill shadow v6."""

from evals.skill_recall_experiment_v6 import (
    NEW_TERMS,
    propose_additional_skills,
)


def test_recovers_eight_explicit_category_skills():
    text = (
        "Professional Summary\n"
        "Experienced software engineer.\n\n"
        "Technical Skills\n"
        "Programming Languages: Dart\n"
        "Frontend & Mobile: Flutter\n"
        "Backend & APIs: ASP.NET Core, Express.js, "
        "SignalR, Socket.IO\n"
        "Databases: SQL Server\n"
        "Testing & QA: Jest\n\n"
        "Professional Experience\n"
        "Built applications."
    )

    actual = propose_additional_skills(text, ["Python"])

    assert actual == NEW_TERMS


def test_existing_skills_are_not_repeated():
    text = (
        "Technical Skills\n"
        "Programming Languages: Dart, Dart\n"
        "Databases: SQL Server, SQL Server\n"
    )

    assert propose_additional_skills(
        text,
        ["Dart"],
    ) == ("SQL Server",)


def test_inline_skills_are_supported():
    assert propose_additional_skills(
        "Skills: Flutter, Dart",
        [],
    ) == ("Flutter", "Dart")


def test_prose_does_not_establish_skills():
    assert (
        propose_additional_skills(
            "Professional Summary\nI would like to learn Flutter and Dart.",
            [],
        )
        == ()
    )


def test_project_mentions_do_not_establish_new_skills():
    assert (
        propose_additional_skills(
            "Projects\nA job posting asks for ASP.NET Core and Jest.",
            [],
        )
        == ()
    )


def test_certification_mentions_do_not_establish_new_skills():
    assert (
        propose_additional_skills(
            "Certifications\nTraining included Flutter, Dart, and Jest.",
            [],
        )
        == ()
    )


def test_job_requirement_skill_heading_is_blocked():
    text = (
        "Job Requirements\n"
        "Technical Skills\n"
        "Programming Languages: Dart\n"
        "Testing & QA: Jest\n"
    )

    assert propose_additional_skills(text, []) == ()


def test_nested_career_goal_skill_heading_is_blocked():
    text = "Career Goals\nTechnical Skills\nProgramming Languages: Dart\n"

    assert propose_additional_skills(text, []) == ()


def test_skills_stop_after_another_section():
    text = (
        "Technical Skills\n"
        "Programming Languages: Dart\n"
        "Professional Experience\n"
        "Testing & QA: Jest\n"
    )

    assert propose_additional_skills(
        text,
        [],
    ) == ("Dart",)


def test_unknown_heading_stops_skill_scope():
    text = (
        "Technical Skills\n"
        "Programming Languages: Dart\n"
        "Software Projects\n"
        "Testing & QA: Jest\n"
    )

    assert propose_additional_skills(
        text,
        [],
    ) == ("Dart",)


def test_v5_excel_recovery_is_preserved():
    assert propose_additional_skills(
        "Skills\nExcel",
        [],
    ) == ("Excel",)


def test_no_inference_from_aspnet_to_dotnet():
    assert propose_additional_skills(
        "Technical Skills\nBackend & APIs: ASP.NET Core",
        [],
    ) == ("ASP.NET Core",)


def test_blocks_inline_skills_in_experience():
    text = "Professional Experience\nSkills: Flutter, Dart\nWorked on a project."
    assert propose_additional_skills(text, []) == ()


def test_blocks_inline_skills_in_certifications():
    text = "Certifications\nSkills: Jest"
    assert propose_additional_skills(text, []) == ()


def test_blocks_nested_skills_in_projects():
    text = "Projects\nTechnical Skills\nProgramming Languages: Dart"
    assert propose_additional_skills(text, []) == ()


def test_blocks_nested_skills_in_experience():
    text = "Professional Experience\nTechnical Skills\nBackend & APIs: SignalR"
    assert propose_additional_skills(text, []) == ()


def test_blocks_nested_skills_in_education():
    text = "Education\nTechnical Skills\nDatabases: SQL Server"
    assert propose_additional_skills(text, []) == ()


def test_blocks_inline_skills_in_publications():
    text = "Publications\nSkills: Jest"
    assert propose_additional_skills(text, []) == ()


def test_preserves_summary_to_skills_transition():
    text = (
        "Professional Summary\n"
        "Experienced software engineer.\n\n"
        "Technical Skills\n"
        "Programming Languages: Dart\n"
        "Backend & APIs: ASP.NET Core"
    )
    assert propose_additional_skills(text, []) == ("Dart", "ASP.NET Core")


def test_unknown_heading_blocks_skill_reactivation():
    text = (
        "Technical Skills\n"
        "Programming Languages: Dart\n"
        "Software Projects\n"
        "Technical Skills\n"
        "Testing & QA: Jest"
    )
    assert propose_additional_skills(text, []) == ("Dart",)


def test_blank_line_does_not_authorize_nested_skills():
    text = (
        "Professional Experience\n"
        "Worked on deployment.\n\n"
        "Technical Skills\n"
        "Programming Languages: Dart"
    )
    assert propose_additional_skills(text, []) == ()
