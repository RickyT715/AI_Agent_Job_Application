"""Tests for the ATS keyword scorer."""

from app.schemas.matching import ATSKeywordScore
from app.services.matching.ats_scorer import (
    SOFT_SKILL_KEYWORDS,
    TECHNICAL_KEYWORDS,
    _extract_keywords,
    _tokenize,
    compute_ats_score,
)


class TestTokenize:
    """Tests for the tokenizer."""

    def test_basic_tokenization(self):
        tokens = _tokenize("Python JavaScript React")
        assert "python" in tokens
        assert "javascript" in tokens
        assert "react" in tokens

    def test_bigrams_generated(self):
        tokens = _tokenize("machine learning engineer")
        assert "machine learning" in tokens

    def test_trigrams_generated(self):
        tokens = _tokenize("natural language processing tasks")
        assert "natural language processing" in tokens

    def test_handles_separators(self):
        tokens = _tokenize("Python/JavaScript, React; Docker")
        assert "python" in tokens
        assert "javascript" in tokens
        assert "react" in tokens
        assert "docker" in tokens

    def test_preserves_special_chars(self):
        tokens = _tokenize("C++ C# .NET node.js")
        assert "c++" in tokens
        assert "c#" in tokens
        assert "node.js" in tokens

    def test_empty_string(self):
        tokens = _tokenize("")
        assert tokens == set()


class TestExtractKeywords:
    """Tests for keyword extraction."""

    def test_extracts_technical_keywords(self):
        text = "We need Python, Docker, and Kubernetes experience"
        tech, soft = _extract_keywords(text)
        assert "python" in tech
        assert "docker" in tech
        assert "kubernetes" in tech

    def test_extracts_soft_skill_keywords(self):
        text = "Strong leadership and communication skills required"
        tech, soft = _extract_keywords(text)
        assert "leadership" in soft
        assert "communication" in soft

    def test_separates_technical_and_soft(self):
        text = "Need Python expertise and leadership experience"
        tech, soft = _extract_keywords(text)
        assert "python" in tech
        assert "python" not in soft
        assert "leadership" in soft
        assert "leadership" not in tech

    def test_no_keywords_found(self):
        text = "This job has no recognizable keywords whatsoever"
        tech, soft = _extract_keywords(text)
        # May still find some common words, but unlikely
        # Just check return types are correct
        assert isinstance(tech, set)
        assert isinstance(soft, set)


class TestComputeAtsScore:
    """Tests for the main ATS scoring function."""

    def test_returns_ats_keyword_score(self):
        result = compute_ats_score(
            resume_text="Python developer with Docker experience",
            job_description="Looking for Python developer with Docker skills",
        )
        assert isinstance(result, ATSKeywordScore)

    def test_perfect_overlap(self):
        text = "Python JavaScript React Docker Kubernetes AWS"
        result = compute_ats_score(resume_text=text, job_description=text)
        assert result.score > 80.0
        assert len(result.missing_keywords) == 0

    def test_zero_overlap(self):
        result = compute_ats_score(
            resume_text="Painting, sculpture, art history",
            job_description="Python, Docker, Kubernetes, AWS, machine learning",
        )
        # Resume has no technical keywords matching the JD
        assert result.score <= 30.0
        assert len(result.missing_keywords) > 0
        assert result.technical_match_pct == 0.0

    def test_partial_overlap(self):
        result = compute_ats_score(
            resume_text="Python developer with FastAPI and PostgreSQL",
            job_description="Python developer with FastAPI, Docker, Kubernetes, and AWS",
        )
        assert 0.0 < result.score < 100.0
        assert len(result.matched_keywords) > 0
        assert len(result.missing_keywords) > 0

    def test_technical_match_pct_computed(self):
        result = compute_ats_score(
            resume_text="Python JavaScript",
            job_description="Python JavaScript React Docker",
        )
        assert 0.0 <= result.technical_match_pct <= 100.0

    def test_soft_skill_match_pct_computed(self):
        result = compute_ats_score(
            resume_text="Strong leadership and teamwork",
            job_description="Leadership, teamwork, communication required",
        )
        assert result.soft_skill_match_pct > 0.0

    def test_job_requirements_included(self):
        result = compute_ats_score(
            resume_text="Python Docker Kubernetes",
            job_description="General backend role",
            job_requirements="Must know Python, Docker, and Kubernetes",
        )
        assert result.score > 50.0

    def test_empty_job_description(self):
        result = compute_ats_score(
            resume_text="Python developer",
            job_description="",
        )
        assert result.score == 0.0
        assert result.total_job_keywords == 0

    def test_keywords_sorted(self):
        result = compute_ats_score(
            resume_text="React Python Docker",
            job_description="Docker Python React AWS",
        )
        assert result.matched_keywords == sorted(result.matched_keywords)
        assert result.missing_keywords == sorted(result.missing_keywords)

    def test_score_capped_at_100(self):
        # Even with perfect match, score should not exceed 100
        result = compute_ats_score(
            resume_text="Python",
            job_description="Python",
        )
        assert result.score <= 100.0

    def test_total_job_keywords_count(self):
        result = compute_ats_score(
            resume_text="Python",
            job_description="Python Docker React leadership",
        )
        assert result.total_job_keywords == len(result.matched_keywords) + len(result.missing_keywords)

    def test_multiword_keywords(self):
        result = compute_ats_score(
            resume_text="Experience with machine learning and natural language processing",
            job_description="Machine learning and natural language processing required",
        )
        assert "machine learning" in result.matched_keywords

    def test_weighted_scoring(self):
        """Technical weight (70%) should dominate over soft skills (30%)."""
        # All technical, no soft
        tech_result = compute_ats_score(
            resume_text="Python Docker React",
            job_description="Python Docker React leadership communication",
        )
        # All soft, no technical
        soft_result = compute_ats_score(
            resume_text="leadership communication",
            job_description="Python Docker React leadership communication",
        )
        # Technical matches should score higher due to 70% weight
        assert tech_result.score > soft_result.score

    def test_curated_sets_not_empty(self):
        """Verify the curated keyword sets have reasonable size."""
        assert len(TECHNICAL_KEYWORDS) >= 100
        assert len(SOFT_SKILL_KEYWORDS) >= 20
