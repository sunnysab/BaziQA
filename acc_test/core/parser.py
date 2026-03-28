from __future__ import annotations

import re
from collections.abc import Sequence


def extract_answer_letter(text: str, choices: Sequence[str]) -> str | None:
    normalized_choices = tuple(choice.upper() for choice in choices)
    explicit_pattern = re.compile(r"最终答案[:：]\s*([A-Z])")
    explicit_match = explicit_pattern.search(text)
    if explicit_match:
        candidate = explicit_match.group(1).upper()
        if candidate in normalized_choices:
            return candidate

    generic_pattern = re.compile(r"\b([A-Z])\b")
    candidates = [match.group(1).upper() for match in generic_pattern.finditer(text)]
    for candidate in reversed(candidates):
        if candidate in normalized_choices:
            return candidate

    return None
