"""Tests for LangSmith custom evaluator functions."""


from app.services.reports.evaluation import score_accuracy, skill_match_f1


class TestSkillMatchF1:
    """Tests for skill_match_f1 evaluator."""

    def test_perfect_match_returns_1(self):
        predicted = ["Python", "FastAPI", "PostgreSQL"]
        expected = ["Python", "FastAPI", "PostgreSQL"]
        assert skill_match_f1(predicted, expected) == 1.0

    def test_no_overlap_returns_0(self):
        predicted = ["Java", "Spring"]
        expected = ["Python", "FastAPI"]
        assert skill_match_f1(predicted, expected) == 0.0

    def test_partial_overlap(self):
        predicted = ["Python", "Java", "SQL"]
        expected = ["Python", "SQL", "Go"]
        result = skill_match_f1(predicted, expected)
        # 2 TP, precision=2/3, recall=2/3, F1=2*(2/3*2/3)/(2/3+2/3)=2/3
        assert abs(result - 2 / 3) < 1e-9

    def test_empty_predicted_returns_0(self):
        assert skill_match_f1([], ["Python", "SQL"]) == 0.0

    def test_empty_expected_returns_0(self):
        assert skill_match_f1(["Python", "SQL"], []) == 0.0

    def test_both_empty_returns_1(self):
        assert skill_match_f1([], []) == 1.0

    def test_case_insensitive(self):
        predicted = ["python", "FASTAPI"]
        expected = ["Python", "FastAPI"]
        assert skill_match_f1(predicted, expected) == 1.0

    def test_whitespace_stripped(self):
        predicted = [" Python ", " SQL"]
        expected = ["Python", "SQL "]
        assert skill_match_f1(predicted, expected) == 1.0

    def test_single_match(self):
        predicted = ["Python"]
        expected = ["Python"]
        assert skill_match_f1(predicted, expected) == 1.0

    def test_predicted_superset(self):
        predicted = ["Python", "SQL", "Go", "Rust"]
        expected = ["Python", "SQL"]
        result = skill_match_f1(predicted, expected)
        # 2 TP, precision=2/4=0.5, recall=2/2=1.0, F1=2*(0.5*1)/(0.5+1)=2/3
        assert abs(result - 2 / 3) < 1e-9

    def test_expected_superset(self):
        predicted = ["Python"]
        expected = ["Python", "SQL", "Go"]
        result = skill_match_f1(predicted, expected)
        # 1 TP, precision=1/1=1.0, recall=1/3, F1=2*(1*1/3)/(1+1/3)=0.5
        assert abs(result - 0.5) < 1e-9


class TestScoreAccuracy:
    """Tests for score_accuracy evaluator."""

    def test_exact_match_returns_1(self):
        assert score_accuracy(8.0, 8.0) == 1.0

    def test_within_tolerance_returns_1(self):
        assert score_accuracy(8.0, 7.5, tolerance=1.0) == 1.0
        assert score_accuracy(7.0, 8.0, tolerance=1.0) == 1.0

    def test_at_tolerance_boundary_returns_1(self):
        assert score_accuracy(8.0, 7.0, tolerance=1.0) == 1.0

    def test_outside_tolerance_returns_0(self):
        assert score_accuracy(8.0, 6.0, tolerance=1.0) == 0.0
        assert score_accuracy(3.0, 8.0, tolerance=1.0) == 0.0

    def test_custom_tolerance(self):
        assert score_accuracy(8.0, 6.5, tolerance=2.0) == 1.0
        assert score_accuracy(8.0, 5.5, tolerance=2.0) == 0.0

    def test_zero_tolerance(self):
        assert score_accuracy(8.0, 8.0, tolerance=0.0) == 1.0
        assert score_accuracy(8.0, 8.1, tolerance=0.0) == 0.0
