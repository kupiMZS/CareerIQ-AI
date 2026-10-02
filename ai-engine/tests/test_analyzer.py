from app.analyzer import (
    analyze_resume,
    calculate_ats_score,
    extract_education,
    extract_email,
    extract_experience,
    extract_name,
    extract_skills,
)


def test_extract_email():
    text = "John Doe\njohn.doe@example.com\nSoftware Engineer"

    assert extract_email(text) == "john.doe@example.com"


def test_extract_email_when_missing():
    text = "John Doe\nSoftware Engineer"

    assert extract_email(text) is None


def test_extract_name():
    text = "John Doe\njohn.doe@example.com\nSoftware Engineer"

    assert extract_name(text) == "John Doe"


def test_extract_name_when_missing():
    text = "Software Engineer\nPython Laravel Angular"

    assert extract_name(text) is None


def test_extract_skills():
    text = "Python Laravel Angular Docker MySQL"

    assert extract_skills(text) == [
        "python",
        "laravel",
        "angular",
        "docker",
        "mysql",
    ]


def test_extract_education():
    text = """
    BSc Computer Science
    MSc Software Engineering
    """

    assert extract_education(text) == [
        "BSc Computer Science",
        "MSc Software Engineering",
    ]


def test_extract_experience():
    text = """
    Software Engineer
    Researcher
    """

    assert extract_experience(text) == [
        "Software Engineer",
        "Researcher",
    ]


def test_calculate_ats_score():
    text = (
        "John Doe\n"
        "john@example.com\n"
        "Software Engineer\n"
        "Python Laravel Angular Docker\n"
        "BSc Computer Science\n"
        "Software Engineer at ABC Company\n" + ("Additional resume information. " * 5)
    )

    skills = extract_skills(text)
    education = extract_education(text)
    experience = extract_experience(text)

    score = calculate_ats_score(
        text,
        skills,
        education,
        experience,
    )

    assert score == 80


def test_analyze_resume():
    text = """
    John Doe
    john@example.com
    Software Engineer
    Python Laravel Angular Docker
    BSc Computer Science
    Software Engineer at ABC Company
    """

    result = analyze_resume(text)

    assert result["extracted_name"] == "John Doe"
    assert result["extracted_email"] == "john@example.com"

    assert result["skills"] == [
        "python",
        "laravel",
        "angular",
        "docker",
    ]

    assert result["education"] == [
        "BSc Computer Science",
    ]

    assert result["experience"] == [
        "Software Engineer",
        "Software Engineer at ABC Company",
    ]

    assert result["status"] == "completed"
    assert isinstance(result["ats_score"], int)
    assert 0 <= result["ats_score"] <= 100


def test_analyze_resume_with_minimal_text():
    result = analyze_resume("Hello")

    assert result["extracted_name"] is None
    assert result["extracted_email"] is None
    assert result["skills"] == []
    assert result["education"] == []
    assert result["experience"] == []
    assert result["ats_score"] == 0
    assert result["status"] == "completed"
