from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ScoreSummary:
    correct_count: int
    total_count: int

    @property
    def accuracy(self) -> float:
        if self.total_count == 0:
            return 0.0
        return self.correct_count / self.total_count


@dataclass(frozen=True)
class QuestionResult:
    question_id: str
    gold_answer: str
    model_answer: str | None
    correct: bool
    model_output: str


def score_subject_answers(gold_answers: list[str], predicted_answers: list[str | None]) -> ScoreSummary:
    correct_count = 0
    for gold, predicted in zip(gold_answers, predicted_answers, strict=False):
        if gold == predicted:
            correct_count += 1
    return ScoreSummary(correct_count=correct_count, total_count=len(gold_answers))


def extract_response_text(response: Any) -> str:
    return response.choices[0].message.content or ""
