from acc_test.bazi_eval_multiturn import build_arg_parser
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


def test_cli_accepts_dataset_path_and_limit_subjects():
    parser = build_arg_parser()
    args = parser.parse_args(["data/contest8_2025.json", "--limit-subjects", "1"])
    assert args.dataset_path.endswith("contest8_2025.json")
    assert args.limit_subjects == 1
