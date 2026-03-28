from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class BirthInfo:
    year: int
    month: int
    day: int
    hour: int
    minute: int
    place: str
    raw: str
    approximate: bool


@dataclass(frozen=True)
class Question:
    question_id: str
    question: str
    options: tuple[str, ...]
    answer: str


@dataclass(frozen=True)
class Subject:
    person_id: str
    name: str
    gender: str
    birth: BirthInfo
    questions: tuple[Question, ...]


def _is_subject_record(record: dict[str, object]) -> bool:
    return "person_id" in record and "questions" in record


def load_contest_dataset(path: str | Path) -> list[Subject]:
    dataset_path = Path(path)
    records = json.loads(dataset_path.read_text(encoding="utf-8"))
    subjects: list[Subject] = []

    for record in records:
        if not _is_subject_record(record):
            continue

        profile = record["profile"]
        birth = profile["birth"]
        questions = tuple(
            Question(
                question_id=item["question_id"],
                question=item["question"],
                options=tuple(item["options"]),
                answer=item["answer"],
            )
            for item in record["questions"]
        )

        subjects.append(
            Subject(
                person_id=record["person_id"],
                name=record["name"],
                gender=profile["gender"],
                birth=BirthInfo(
                    year=birth["year"],
                    month=birth["month"],
                    day=birth["day"],
                    hour=birth["hour"],
                    minute=birth["minute"],
                    place=birth["place"],
                    raw=birth.get("raw", ""),
                    approximate=birth.get("approximate", False),
                ),
                questions=questions,
            )
        )

    return subjects
