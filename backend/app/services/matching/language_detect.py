"""Language detection for CJK vs Latin text.

Simple heuristic based on character class counts — no external dependency needed.
"""

import re


def detect_language(text: str) -> str:
    """Detect whether text is predominantly Chinese or English.

    Args:
        text: Input text to analyze.

    Returns:
        ``"zh"`` if text is predominantly Chinese (CJK Unified Ideographs),
        ``"en"`` otherwise.
    """
    if not text:
        return "en"
    cjk_chars = len(re.findall(r"[\u4e00-\u9fff\u3400-\u4dbf]", text))
    latin_chars = len(re.findall(r"[a-zA-Z]", text))
    if cjk_chars > latin_chars:
        return "zh"
    return "en"
