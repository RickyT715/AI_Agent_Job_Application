"""Tests for the LinkedIn PDF profile parser.

These tests use the text-level parsing functions directly
(no actual PDF files needed for most tests).
"""

from app.schemas.profile import LinkedInProfile
from app.services.profile.linkedin_parser import (
    _extract_sections,
    _parse_contact_info,
    _parse_education_section,
    _parse_experience_section,
    _parse_header,
    _parse_list_section,
    _parse_skills_section,
    profile_to_resume_text,
)


SAMPLE_LINKEDIN_TEXT = """John Doe
Senior Software Engineer at Acme Corp
San Francisco, CA
john.doe@email.com
(555) 123-4567
linkedin.com/in/johndoe

Summary
Experienced software engineer with 8+ years of experience building
scalable web applications. Passionate about clean code and mentoring.

Experience
Senior Software Engineer
Acme Corp
San Francisco, CA
Jan 2020 - Present
Led team of 5 engineers building microservices architecture.
Designed and implemented RESTful APIs serving 1M+ requests daily.

Software Engineer
StartupCo
Remote
Jun 2016 - Dec 2019
Built full-stack web applications using Python and React.

Education
Stanford University
Master of Science in Computer Science
2014 - 2016

UC Berkeley
Bachelor of Science in Computer Science
2010 - 2014

Skills
Python · 25 endorsements
JavaScript · 15 endorsements
Docker
Kubernetes
React
PostgreSQL

Certifications
AWS Solutions Architect
Google Cloud Professional

Languages
English
Spanish
"""


class TestExtractSections:
    """Tests for section extraction."""

    def test_extracts_known_sections(self):
        sections = _extract_sections(SAMPLE_LINKEDIN_TEXT)
        assert "Summary" in sections
        assert "Experience" in sections
        assert "Education" in sections
        assert "Skills" in sections
        assert "Certifications" in sections
        assert "Languages" in sections

    def test_section_content_is_correct(self):
        sections = _extract_sections(SAMPLE_LINKEDIN_TEXT)
        assert "Experienced software engineer" in sections["Summary"]

    def test_empty_text(self):
        sections = _extract_sections("")
        assert sections == {}


class TestParseHeader:
    """Tests for header parsing."""

    def test_extracts_name(self):
        profile = LinkedInProfile()
        _parse_header(SAMPLE_LINKEDIN_TEXT, profile)
        assert profile.full_name == "John Doe"

    def test_extracts_headline(self):
        profile = LinkedInProfile()
        _parse_header(SAMPLE_LINKEDIN_TEXT, profile)
        assert "Senior Software Engineer" in profile.headline

    def test_extracts_location(self):
        profile = LinkedInProfile()
        _parse_header(SAMPLE_LINKEDIN_TEXT, profile)
        assert "San Francisco" in profile.location


class TestParseContactInfo:
    """Tests for contact info extraction."""

    def test_extracts_email(self):
        profile = LinkedInProfile()
        _parse_contact_info(SAMPLE_LINKEDIN_TEXT, profile)
        assert profile.email == "john.doe@email.com"

    def test_extracts_linkedin_url(self):
        profile = LinkedInProfile()
        _parse_contact_info(SAMPLE_LINKEDIN_TEXT, profile)
        assert "linkedin.com/in/johndoe" in profile.linkedin_url


class TestParseExperienceSection:
    """Tests for experience section parsing."""

    def test_extracts_experiences(self):
        sections = _extract_sections(SAMPLE_LINKEDIN_TEXT)
        experiences = _parse_experience_section(sections["Experience"])
        assert len(experiences) >= 1

    def test_experience_has_title(self):
        sections = _extract_sections(SAMPLE_LINKEDIN_TEXT)
        experiences = _parse_experience_section(sections["Experience"])
        titles = [e.title for e in experiences]
        assert any("Senior Software Engineer" in t for t in titles)


class TestParseEducationSection:
    """Tests for education section parsing."""

    def test_extracts_education(self):
        sections = _extract_sections(SAMPLE_LINKEDIN_TEXT)
        education = _parse_education_section(sections["Education"])
        assert len(education) >= 1

    def test_education_has_institution(self):
        sections = _extract_sections(SAMPLE_LINKEDIN_TEXT)
        education = _parse_education_section(sections["Education"])
        institutions = [e.institution for e in education]
        assert any("Stanford" in i for i in institutions)


class TestParseSkillsSection:
    """Tests for skills section parsing."""

    def test_extracts_skills(self):
        sections = _extract_sections(SAMPLE_LINKEDIN_TEXT)
        skills = _parse_skills_section(sections["Skills"])
        assert len(skills) >= 3
        names = [s.name for s in skills]
        assert "Python" in names

    def test_extracts_endorsements(self):
        sections = _extract_sections(SAMPLE_LINKEDIN_TEXT)
        skills = _parse_skills_section(sections["Skills"])
        python_skill = next((s for s in skills if s.name == "Python"), None)
        assert python_skill is not None
        assert python_skill.endorsements == 25


class TestParseListSection:
    """Tests for list section parsing."""

    def test_extracts_certifications(self):
        sections = _extract_sections(SAMPLE_LINKEDIN_TEXT)
        certs = _parse_list_section(sections["Certifications"])
        assert "AWS Solutions Architect" in certs

    def test_extracts_languages(self):
        sections = _extract_sections(SAMPLE_LINKEDIN_TEXT)
        langs = _parse_list_section(sections["Languages"])
        assert "English" in langs
        assert "Spanish" in langs


class TestProfileToResumeText:
    """Tests for profile to resume text conversion."""

    def test_includes_name(self):
        profile = LinkedInProfile(full_name="John Doe")
        text = profile_to_resume_text(profile)
        assert "John Doe" in text

    def test_includes_skills(self):
        from app.schemas.profile import Skill
        profile = LinkedInProfile(
            full_name="John",
            skills=[Skill(name="Python"), Skill(name="Docker")],
        )
        text = profile_to_resume_text(profile)
        assert "Python" in text
        assert "Docker" in text

    def test_empty_profile_returns_string(self):
        profile = LinkedInProfile()
        text = profile_to_resume_text(profile)
        assert isinstance(text, str)
