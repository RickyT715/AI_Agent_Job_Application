"""LinkedIn PDF profile parser.

Extracts structured profile data from LinkedIn PDF exports using PyMuPDF.
"""

import logging
import re

import pymupdf

from app.schemas.profile import Education, LinkedInProfile, Skill, WorkExperience

logger = logging.getLogger(__name__)

# Section headers found in LinkedIn PDF exports
_SECTION_HEADERS = [
    "Experience",
    "Education",
    "Skills",
    "Certifications",
    "Licenses & Certifications",
    "Languages",
    "Summary",
    "About",
    "Honors & Awards",
    "Projects",
    "Volunteer Experience",
    "Publications",
    "Courses",
]


def parse_linkedin_pdf(pdf_bytes: bytes) -> LinkedInProfile:
    """Parse a LinkedIn PDF export into a structured profile.

    Args:
        pdf_bytes: Raw PDF file bytes.

    Returns:
        LinkedInProfile with extracted data.
    """
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    full_text = ""
    for page in doc:
        full_text += page.get_text() + "\n"
    doc.close()

    sections = _extract_sections(full_text)
    profile = LinkedInProfile()

    # Parse header (name, headline, location)
    _parse_header(full_text, profile)

    # Parse contact info
    _parse_contact_info(full_text, profile)

    # Parse sections
    if "Experience" in sections:
        profile.experience = _parse_experience_section(sections["Experience"])
    if "Education" in sections:
        profile.education = _parse_education_section(sections["Education"])
    if "Skills" in sections:
        profile.skills = _parse_skills_section(sections["Skills"])
    if "Summary" in sections:
        profile.summary = sections["Summary"].strip()
    elif "About" in sections:
        profile.summary = sections["About"].strip()
    if "Certifications" in sections:
        profile.certifications = _parse_list_section(sections["Certifications"])
    elif "Licenses & Certifications" in sections:
        profile.certifications = _parse_list_section(sections["Licenses & Certifications"])
    if "Languages" in sections:
        profile.languages = _parse_list_section(sections["Languages"])

    return profile


def profile_to_resume_text(profile: LinkedInProfile) -> str:
    """Convert a parsed LinkedIn profile to plain resume text.

    Args:
        profile: Parsed LinkedIn profile.

    Returns:
        Resume text suitable for storing as resume_text.
    """
    parts: list[str] = []

    if profile.full_name:
        parts.append(profile.full_name)
    if profile.headline:
        parts.append(profile.headline)
    if profile.location:
        parts.append(profile.location)

    if profile.summary:
        parts.append(f"\nSUMMARY\n{profile.summary}")

    if profile.experience:
        parts.append("\nEXPERIENCE")
        for exp in profile.experience:
            date_range = ""
            if exp.start_date:
                date_range = f" ({exp.start_date} - {exp.end_date or 'Present'})"
            parts.append(f"{exp.title} at {exp.company}{date_range}")
            if exp.location:
                parts.append(f"  {exp.location}")
            if exp.description:
                parts.append(f"  {exp.description}")

    if profile.education:
        parts.append("\nEDUCATION")
        for edu in profile.education:
            line = edu.institution
            if edu.degree:
                line += f", {edu.degree}"
            if edu.field_of_study:
                line += f" in {edu.field_of_study}"
            parts.append(line)

    if profile.skills:
        parts.append("\nSKILLS")
        parts.append(", ".join(s.name for s in profile.skills))

    if profile.certifications:
        parts.append("\nCERTIFICATIONS")
        for cert in profile.certifications:
            parts.append(f"- {cert}")

    return "\n".join(parts)


def _extract_sections(text: str) -> dict[str, str]:
    """Split text into sections based on known LinkedIn headers."""
    sections: dict[str, str] = {}
    lines = text.split("\n")
    current_section: str | None = None
    current_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if stripped in _SECTION_HEADERS:
            if current_section is not None:
                sections[current_section] = "\n".join(current_lines)
            current_section = stripped
            current_lines = []
        elif current_section is not None:
            current_lines.append(line)

    if current_section is not None:
        sections[current_section] = "\n".join(current_lines)

    return sections


def _parse_header(text: str, profile: LinkedInProfile) -> None:
    """Extract name, headline, location from the top of the PDF."""
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    if lines:
        profile.full_name = lines[0]
    if len(lines) > 1:
        profile.headline = lines[1]
    if len(lines) > 2:
        # Location is usually the 3rd non-empty line
        candidate = lines[2]
        # Skip if it looks like a section header
        if candidate not in _SECTION_HEADERS:
            profile.location = candidate


def _parse_contact_info(text: str, profile: LinkedInProfile) -> None:
    """Extract email, phone, and LinkedIn URL from text."""
    # Email
    email_match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
    if email_match:
        profile.email = email_match.group()

    # Phone
    phone_match = re.search(r"[\+]?[\d\s\-\(\)]{7,15}", text)
    if phone_match:
        candidate = phone_match.group().strip()
        if len(re.sub(r"\D", "", candidate)) >= 7:
            profile.phone = candidate

    # LinkedIn URL
    linkedin_match = re.search(r"linkedin\.com/in/[\w-]+", text)
    if linkedin_match:
        profile.linkedin_url = f"https://www.{linkedin_match.group()}"


def _parse_experience_section(text: str) -> list[WorkExperience]:
    """Parse experience section into WorkExperience objects."""
    experiences: list[WorkExperience] = []
    blocks = re.split(r"\n(?=\S)", text)

    for block in blocks:
        lines = [l.strip() for l in block.strip().split("\n") if l.strip()]
        if not lines:
            continue

        title = lines[0]
        company = lines[1] if len(lines) > 1 else "Unknown"
        location = None
        start_date = None
        end_date = None
        description_lines: list[str] = []

        for line in lines[2:]:
            # Date range pattern: "Jan 2020 - Present" or "2020 - 2023"
            date_match = re.search(
                r"(\w+\s+\d{4}|\d{4})\s*[-–]\s*(\w+\s+\d{4}|\d{4}|Present)",
                line,
            )
            if date_match:
                start_date = date_match.group(1)
                end_date = date_match.group(2)
                if end_date == "Present":
                    end_date = None
            elif not location and re.search(r"[A-Z][a-z]+,\s+[A-Z]", line):
                location = line
            else:
                description_lines.append(line)

        if title and title not in _SECTION_HEADERS:
            experiences.append(
                WorkExperience(
                    title=title,
                    company=company,
                    location=location,
                    start_date=start_date,
                    end_date=end_date,
                    description="\n".join(description_lines),
                )
            )

    return experiences


def _parse_education_section(text: str) -> list[Education]:
    """Parse education section into Education objects."""
    entries: list[Education] = []
    blocks = re.split(r"\n(?=\S)", text)

    for block in blocks:
        lines = [l.strip() for l in block.strip().split("\n") if l.strip()]
        if not lines:
            continue

        institution = lines[0]
        degree = None
        field_of_study = None

        for line in lines[1:]:
            if any(
                kw in line.lower()
                for kw in ["bachelor", "master", "phd", "doctor", "associate", "diploma", "degree"]
            ):
                degree = line
            elif not field_of_study and line not in _SECTION_HEADERS:
                field_of_study = line

        if institution and institution not in _SECTION_HEADERS:
            entries.append(
                Education(
                    institution=institution,
                    degree=degree,
                    field_of_study=field_of_study,
                )
            )

    return entries


def _parse_skills_section(text: str) -> list[Skill]:
    """Parse skills section into Skill objects."""
    skills: list[Skill] = []
    for line in text.split("\n"):
        line = line.strip()
        if not line or line in _SECTION_HEADERS:
            continue

        # Handle "Skill Name · 5 endorsements" format
        endorsement_match = re.search(r"·\s*(\d+)\s*endorsement", line)
        endorsements = int(endorsement_match.group(1)) if endorsement_match else 0
        name = re.sub(r"\s*·.*$", "", line).strip()

        if name:
            skills.append(Skill(name=name, endorsements=endorsements))

    return skills


def _parse_list_section(text: str) -> list[str]:
    """Parse a simple list section into strings."""
    items: list[str] = []
    for line in text.split("\n"):
        line = line.strip()
        if line and line not in _SECTION_HEADERS:
            items.append(line)
    return items
