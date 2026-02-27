"""LangSmith custom evaluator functions.

These evaluators can be used with LangSmith to measure matching quality
on hand-labeled datasets.
"""


def skill_match_f1(
    predicted: list[str],
    expected: list[str],
) -> float:
    """Compute F1 score between predicted and expected skill lists.

    Case-insensitive comparison. Used as a LangSmith custom evaluator
    to measure how well the matching pipeline identifies relevant skills.

    Args:
        predicted: Skills predicted by the model.
        expected: Ground-truth skill labels.

    Returns:
        F1 score between 0.0 and 1.0.
    """
    if not predicted and not expected:
        return 1.0
    if not predicted or not expected:
        return 0.0

    pred_set = {s.lower().strip() for s in predicted}
    exp_set = {s.lower().strip() for s in expected}

    true_positives = len(pred_set & exp_set)

    if true_positives == 0:
        return 0.0

    precision = true_positives / len(pred_set)
    recall = true_positives / len(exp_set)

    return 2 * (precision * recall) / (precision + recall)


def score_accuracy(
    predicted_score: float,
    expected_score: float,
    tolerance: float = 1.0,
) -> float:
    """Check if predicted score is within tolerance of expected.

    Args:
        predicted_score: Model's score.
        expected_score: Ground-truth score.
        tolerance: Acceptable difference.

    Returns:
        1.0 if within tolerance, 0.0 otherwise.
    """
    return 1.0 if abs(predicted_score - expected_score) <= tolerance else 0.0
