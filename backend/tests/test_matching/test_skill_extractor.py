"""Tests for the public skill extractor API."""

from app.services.matching.skill_extractor import extract_skills, extract_skills_from_job


class TestExtractSkills:
    """Tests for extract_skills()."""

    def test_english_technical_skills(self):
        text = "We need a Python developer with experience in React and Docker."
        tech, soft = extract_skills(text, language="en")
        assert "python" in tech
        assert "react" in tech
        assert "docker" in tech

    def test_english_soft_skills(self):
        text = "Strong leadership and communication skills required. Must be detail-oriented."
        tech, soft = extract_skills(text, language="en")
        assert "leadership" in soft
        assert "communication" in soft

    def test_auto_detect_english(self):
        text = "Looking for a Python developer who knows PostgreSQL and AWS."
        tech, soft = extract_skills(text, language="auto")
        assert "python" in tech
        assert "aws" in tech

    def test_auto_detect_chinese(self):
        text = "要求熟悉机器学习和深度学习框架，有良好的沟通能力和团队合作精神"
        tech, soft = extract_skills(text, language="auto")
        assert "机器学习" in tech
        assert "深度学习" in tech
        assert len(soft) > 0

    def test_empty_text_returns_empty(self):
        tech, soft = extract_skills("")
        assert tech == set()
        assert soft == set()

    def test_whitespace_only_returns_empty(self):
        tech, soft = extract_skills("   \n  ")
        assert tech == set()
        assert soft == set()


class TestExtractSkillsFromJob:
    """Tests for extract_skills_from_job()."""

    def test_combines_description_and_requirements(self):
        desc = "We are building a Django web application."
        reqs = "Must have experience with PostgreSQL and Docker."
        tech, soft = extract_skills_from_job(desc, reqs)
        assert "django" in tech
        assert "docker" in tech

    def test_description_only(self):
        desc = "FastAPI and Python required. Must have leadership skills."
        tech, soft = extract_skills_from_job(desc)
        assert "fastapi" in tech
        assert "python" in tech
        assert "leadership" in soft
