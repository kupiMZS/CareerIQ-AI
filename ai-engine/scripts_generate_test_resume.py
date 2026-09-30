from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from pathlib import Path

output = str(
    Path(__file__).resolve().parents[1]
    / "tests"
    / "fixtures"
    / "resumes"
    / "enterprise-test-resume.pdf"
)

c = canvas.Canvas(output, pagesize=A4)
width, height = A4

x = 25 * mm
y = height - 25 * mm

lines = [
    "John Doe",
    "Software Engineer",
    "john.doe@example.com",
    "",
    "PROFESSIONAL SUMMARY",
    "Software Engineer with experience building web applications",
    "using Python, Laravel, Angular, Docker and MySQL.",
    "",
    "TECHNICAL SKILLS",
    "Python, Laravel, Angular, Docker, MySQL, Git",
    "",
    "EDUCATION",
    "BSc Computer Science",
    "University of Technology",
    "",
    "PROFESSIONAL EXPERIENCE",
    "Software Engineer at ABC Technologies",
    "2023 - Present",
    "Developed and maintained web applications using Laravel and Angular.",
    "",
    "Junior Software Developer at XYZ Solutions",
    "2021 - 2023",
    "Built backend services using Python and MySQL.",
]

c.setFont("Helvetica", 11)

for line in lines:
    if y < 25 * mm:
        c.showPage()
        c.setFont("Helvetica", 11)
        y = height - 25 * mm

    c.drawString(x, y, line)
    y -= 7 * mm

c.save()

print(f"Created: {output}")
