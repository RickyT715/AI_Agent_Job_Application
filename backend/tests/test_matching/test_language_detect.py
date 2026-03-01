"""Tests for language detection utility."""

from app.services.matching.language_detect import detect_language


class TestDetectLanguage:
    """Tests for CJK vs Latin language detection."""

    def test_chinese_text(self):
        assert detect_language("我们正在寻找一名高级软件工程师") == "zh"

    def test_english_text(self):
        assert detect_language("We are looking for a Senior Software Engineer") == "en"

    def test_mixed_predominantly_chinese(self):
        text = "我们需要熟悉Python和React的工程师，要求有分布式系统经验"
        assert detect_language(text) == "zh"

    def test_mixed_predominantly_english(self):
        text = "Looking for a Python developer with 机器学习 experience"
        assert detect_language(text) == "en"

    def test_empty_string(self):
        assert detect_language("") == "en"

    def test_pure_numbers(self):
        assert detect_language("12345 67890") == "en"

    def test_cjk_extension_b(self):
        # CJK Unified Ideographs Extension A range (U+3400-U+4DBF)
        assert detect_language("\u3400\u3401\u3402") == "zh"

    def test_equal_counts_returns_english(self):
        # When CJK == Latin, returns "en" (not strictly >)
        text = "abc\u4e00\u4e01\u4e02"
        assert detect_language(text) == "en"
