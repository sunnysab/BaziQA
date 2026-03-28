from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
import re
import time
from typing import Any

from acc_test.core.bazi_provider import BaziProvider
from acc_test.core.dataset import Subject, load_contest_dataset
from acc_test.core.llm_client import OpenAICompatibleClient
from acc_test.core.parser import extract_answer_letter
from acc_test.core.protocols import build_question_prompt, build_system_prompt


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
    question: str
    options: tuple[str, ...]
    gold_answer: str
    model_answer: str | None
    correct: bool
    model_output: str


@dataclass(frozen=True)
class SubjectResult:
    person_id: str
    anonymous_id: str
    chart_cache_path: str
    correct_count: int
    total_count: int
    accuracy: float
    questions: tuple[QuestionResult, ...]


@dataclass(frozen=True)
class EvaluationResult:
    dataset_path: str
    protocol: str
    model: str
    started_at: str
    finished_at: str
    total_questions: int
    correct_questions: int
    accuracy: float
    subjects: tuple[SubjectResult, ...]


def score_subject_answers(gold_answers: list[str], predicted_answers: list[str | None]) -> ScoreSummary:
    correct_count = 0
    for gold, predicted in zip(gold_answers, predicted_answers, strict=False):
        if gold == predicted:
            correct_count += 1
    return ScoreSummary(correct_count=correct_count, total_count=len(gold_answers))


def extract_response_text(response: Any) -> str:
    if isinstance(response, dict):
        choices = response.get("choices") or []
        if choices:
            message = choices[0].get("message") or {}
            return message.get("content") or ""
    if isinstance(response, str):
        parsed_sse_text = _extract_text_from_sse_response(response)
        if parsed_sse_text:
            return parsed_sse_text
        sample = response[:120].replace("\n", " ")
        raise ValueError(
            f"Expected OpenAI chat completion object, got plain string response. "
            f"Check OPENAI_BASE_URL/URL. Response starts with: {sample}"
        )
    return response.choices[0].message.content or ""


def request_chat_completion(
    *,
    client: Any,
    model: str,
    messages: list[dict[str, str]],
    max_attempts: int = 6,
) -> Any:
    last_response: Any = None
    last_error: Exception | None = None
    for _ in range(max_attempts):
        try:
            response = client.create_chat_completion(model=model, messages=messages)
        except Exception as exc:
            last_error = exc
            time.sleep(0.5)
            continue
        last_response = response
        if isinstance(response, dict):
            return response
        time.sleep(0.5)
    if last_error is not None:
        raise last_error
    return last_response


def evaluate_dataset(
    *,
    dataset_path: str | Path,
    protocol: str,
    client: OpenAICompatibleClient,
    model: str,
    provider: BaziProvider,
    limit_subjects: int | None = None,
) -> EvaluationResult:
    started_at = datetime.now(UTC).isoformat()
    dataset_file = Path(dataset_path)
    dataset_name = dataset_file.stem
    subjects = load_contest_dataset(dataset_file)
    if limit_subjects is not None:
        subjects = subjects[:limit_subjects]

    subject_results: list[SubjectResult] = []
    for index, subject in enumerate(subjects, start=1):
        subject_results.append(
            evaluate_subject(
                client=client,
                model=model,
                protocol=protocol,
                provider=provider,
                dataset_name=dataset_name,
                subject=subject,
                subject_index=index,
            )
        )

    total_questions = sum(item.total_count for item in subject_results)
    correct_questions = sum(item.correct_count for item in subject_results)
    accuracy = correct_questions / total_questions if total_questions else 0.0
    return EvaluationResult(
        dataset_path=str(dataset_file),
        protocol=protocol,
        model=model,
        started_at=started_at,
        finished_at=datetime.now(UTC).isoformat(),
        total_questions=total_questions,
        correct_questions=correct_questions,
        accuracy=accuracy,
        subjects=tuple(subject_results),
    )


def evaluate_subject(
    *,
    client: OpenAICompatibleClient,
    model: str,
    protocol: str,
    provider: BaziProvider,
    dataset_name: str,
    subject: Subject,
    subject_index: int,
) -> SubjectResult:
    anonymous_id = f"命主{subject_index:03d}"
    cache_record = provider.generate_or_load(
        dataset_name=dataset_name,
        person_id=subject.person_id,
        subject_name=subject.name,
        anonymous_id=anonymous_id,
        birth=subject.birth,
        gender=subject.gender,
    )

    messages = [
        {"role": "system", "content": build_system_prompt(protocol)},
        {"role": "user", "content": cache_record.formatted_text},
    ]

    question_results: list[QuestionResult] = []
    predicted_answers: list[str | None] = []
    gold_answers: list[str] = []

    for question in subject.questions:
        prompt = build_question_prompt(protocol, question.question, question.options)
        response = request_chat_completion(
            client=client,
            model=model,
            messages=messages + [{"role": "user", "content": prompt}],
        )
        output_text = extract_response_text(response)
        answer = extract_answer_letter(output_text, choices=_extract_choice_letters(question.options))
        question_results.append(
            QuestionResult(
                question_id=question.question_id,
                question=question.question,
                options=question.options,
                gold_answer=question.answer,
                model_answer=answer,
                correct=answer == question.answer,
                model_output=output_text,
            )
        )
        predicted_answers.append(answer)
        gold_answers.append(question.answer)
        messages.extend(
            [
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": output_text},
            ]
        )

    score = score_subject_answers(gold_answers, predicted_answers)
    return SubjectResult(
        person_id=subject.person_id,
        anonymous_id=anonymous_id,
        chart_cache_path=str(provider.cache_path(dataset_name, subject.person_id)),
        correct_count=score.correct_count,
        total_count=score.total_count,
        accuracy=score.accuracy,
        questions=tuple(question_results),
    )


def write_evaluation_result(result: EvaluationResult, *, output_root: str | Path) -> Path:
    output_dir = Path(output_root) / "evals" / sanitize_path_component(result.model) / result.protocol
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{Path(result.dataset_path).stem}_{_timestamp_for_filename()}.json"
    output_path.write_text(
        json.dumps(asdict(result), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_path


def sanitize_path_component(value: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return sanitized or "model"


def _extract_choice_letters(options: tuple[str, ...]) -> tuple[str, ...]:
    letters: list[str] = []
    pattern = re.compile(r"^\s*([A-Z])[\.\u3001\)]?")
    for option in options:
        match = pattern.match(option)
        if match:
            letters.append(match.group(1))
    return tuple(letters)


def _timestamp_for_filename() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _extract_text_from_sse_response(response_text: str) -> str:
    parts: list[str] = []
    for line in response_text.splitlines():
        line = line.strip()
        if not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if not payload or payload == "[DONE]":
            continue
        try:
            chunk = json.loads(payload)
        except json.JSONDecodeError:
            continue
        for choice in chunk.get("choices") or []:
            delta = choice.get("delta") or {}
            if isinstance(delta.get("content"), str):
                parts.append(delta["content"])
            message = choice.get("message") or {}
            if isinstance(message.get("content"), str):
                parts.append(message["content"])
    return "".join(parts)
