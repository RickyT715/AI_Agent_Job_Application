"""Tests for Chinese pipeline support in MatchingPipeline."""

from app.services.matching.pipeline import _extract_skills_section


class TestExtractSkillsSectionZh:
    """Tests for Chinese skills section extraction."""

    def test_extracts_chinese_skills_section(self):
        resume = """教育背景
清华大学 计算机科学与技术

技术技能：
编程语言：Python、Java、C++
框架：Spring Boot、FastAPI、React
工具：Docker、Kubernetes、Git

工作经历
腾讯 高级工程师"""
        skills = _extract_skills_section(resume)
        assert "Python" in skills
        assert "Java" in skills

    def test_extracts_chinese_programming_languages_header(self):
        resume = """编程语言：Python、JavaScript、Go

工作经历
字节跳动 后端开发"""
        skills = _extract_skills_section(resume)
        assert "Python" in skills

    def test_extracts_chinese_tech_ability_header(self):
        resume = """技术能力：
精通Python和FastAPI
熟悉Docker和Kubernetes

项目经历"""
        skills = _extract_skills_section(resume)
        assert "Python" in skills or "FastAPI" in skills

    def test_still_extracts_english_skills(self):
        """Ensure English skills extraction is not broken."""
        resume = """SKILLS
Languages: Python, JavaScript, C++
Technologies: AWS, Docker, React

EXPERIENCE
Software Engineer at TestCo"""
        skills = _extract_skills_section(resume)
        assert "Python" in skills
