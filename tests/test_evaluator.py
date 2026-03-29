from pathlib import Path
import subprocess
import sys

from acc_test.bazi_eval_multiturn import build_arg_parser
from acc_test.core.evaluator import (
    extract_response_text,
    request_chat_completion,
    request_completion_text,
    score_subject_answers,
)
from acc_test.core.llm_client import (
    build_chat_completions_url,
    build_chat_completion_payload,
    build_config_from_env,
    parse_model_list,
)


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


def test_build_config_from_env_supports_legacy_aliases():
    config = build_config_from_env(
        {
            "URL": "https://example.test",
            "KEY": "secret",
            "MODEL": "gpt-a|gpt-b",
        }
    )
    assert config.base_url == "https://example.test/v1"
    assert config.api_key == "secret"
    assert config.models == ("gpt-a", "gpt-b")


def test_build_config_from_env_normalizes_chat_completion_endpoint():
    config = build_config_from_env(
        {
            "URL": "https://example.test/v1/chat/completion",
            "KEY": "secret",
            "MODEL": "gpt-a",
        }
    )
    assert config.base_url == "https://example.test/v1"


def test_build_chat_completions_url_targets_standard_endpoint():
    assert (
        build_chat_completions_url("https://example.test/v1/chat/completion")
        == "https://example.test/v1/chat/completions"
    )


def test_build_chat_completion_payload_disables_streaming():
    payload = build_chat_completion_payload(
        model="gpt-a",
        messages=[{"role": "user", "content": "hi"}],
    )
    assert payload["stream"] is False


def test_cli_accepts_dataset_path_and_limit_subjects():
    parser = build_arg_parser()
    args = parser.parse_args(
        ["data/contest8_2025.json", "--limit-subjects", "1", "--max-workers", "2"]
    )
    assert args.dataset_path.endswith("contest8_2025.json")
    assert args.limit_subjects == 1
    assert args.max_workers == 2
    assert args.bazi_script.endswith("third_party/bazi/bazi.py")


def test_multiturn_script_can_be_invoked_directly():
    repo_root = Path(__file__).resolve().parents[1]
    script_path = repo_root / "acc_test" / "bazi_eval_multiturn.py"
    result = subprocess.run(
        [sys.executable, str(script_path), "--help"],
        capture_output=True,
        text=True,
        cwd=repo_root,
    )
    assert result.returncode == 0


def test_extract_response_text_supports_dict_completion_payload():
    response = {"choices": [{"message": {"content": "A"}}]}
    assert extract_response_text(response) == "A"


def test_extract_response_text_supports_sse_payload():
    response = (
        'data: {"choices":[{"delta":{"content":"最终"}}]}\n\n'
        'data: {"choices":[{"delta":{"content":"答案：A"}}]}\n\n'
        "data: [DONE]\n"
    )
    assert extract_response_text(response) == "最终答案：A"


def test_request_chat_completion_retries_on_nonstandard_response():
    class StubClient:
        def __init__(self) -> None:
            self.calls = 0

        def create_chat_completion(self, *, model, messages):
            self.calls += 1
            if self.calls == 1:
                return "data: [DONE]"
            return {"choices": [{"message": {"content": "最终答案：A"}}]}

    stub = StubClient()
    response = request_chat_completion(
        client=stub,
        model="gpt-a",
        messages=[{"role": "user", "content": "hi"}],
        max_attempts=2,
    )
    assert response == {"choices": [{"message": {"content": "最终答案：A"}}]}
    assert stub.calls == 2


def test_request_chat_completion_retries_on_exception():
    class StubClient:
        def __init__(self) -> None:
            self.calls = 0

        def create_chat_completion(self, *, model, messages):
            self.calls += 1
            if self.calls == 1:
                raise TimeoutError("slow gateway")
            return {"choices": [{"message": {"content": "最终答案：B"}}]}

    stub = StubClient()
    response = request_chat_completion(
        client=stub,
        model="gpt-a",
        messages=[{"role": "user", "content": "hi"}],
        max_attempts=2,
    )
    assert response == {"choices": [{"message": {"content": "最终答案：B"}}]}
    assert stub.calls == 2


def test_request_completion_text_retries_until_text_is_extractable():
    class StubClient:
        def __init__(self) -> None:
            self.calls = 0

        def create_chat_completion(self, *, model, messages):
            self.calls += 1
            if self.calls < 3:
                return "data: [DONE]"
            return {"choices": [{"message": {"content": "最终答案：C"}}]}

    stub = StubClient()
    text = request_completion_text(
        client=stub,
        model="gpt-a",
        messages=[{"role": "user", "content": "hi"}],
        max_attempts=3,
    )
    assert text == "最终答案：C"
    assert stub.calls == 3


def test_extract_response_text_raises_on_empty_sse_payload():
    try:
        extract_response_text("data: [DONE]\n")
    except ValueError as exc:
        assert "Expected OpenAI chat completion object" in str(exc)
    else:
        raise AssertionError("ValueError expected for empty SSE payload")
