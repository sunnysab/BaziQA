from acc_test.core.evaluator import score_subject_answers
from acc_test.core.llm_client import parse_model_list


def test_score_subject_answers_marks_correct_and_incorrect():
    scored = score_subject_answers(
        gold_answers=["B", "D"],
        predicted_answers=["B", "A"],
    )
    assert scored.correct_count == 1
    assert scored.total_count == 2


def test_parse_model_list_supports_pipe_separator():
    models = parse_model_list("gpt-a | gpt-b|gpt-c ")
    assert models == ["gpt-a", "gpt-b", "gpt-c"]
