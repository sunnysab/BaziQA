from acc_test.core.parser import extract_answer_letter
from acc_test.core.protocols import build_question_prompt


def test_extract_answer_letter_prefers_explicit_final_answer():
    text = "分析略\n最终答案：B\n另一个字母 A"
    assert extract_answer_letter(text, choices=("A", "B", "C", "D")) == "B"


def test_build_structured_prompt_contains_three_required_stages():
    prompt = build_question_prompt(
        protocol="structured",
        question="婚姻如何？",
        options=("A. 一婚", "B. 二婚", "C. 一生未嫁", "D. 夫早亡"),
    )
    assert "量化扫描" in prompt
    assert "冲突定级" in prompt
    assert "应象映射" in prompt
