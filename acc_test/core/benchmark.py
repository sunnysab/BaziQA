from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
from typing import TypeVar

from acc_test.core.evaluator import EvaluationResult

T = TypeVar("T")
R = TypeVar("R")


def discover_contest_datasets(data_dir: Path) -> list[Path]:
    return sorted(data_dir.glob("contest8_*.json"))


def build_summary_rows(results: list[EvaluationResult]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str], list[EvaluationResult]] = defaultdict(list)
    for result in results:
        grouped[(result.model, result.protocol)].append(result)

    rows: list[dict[str, object]] = []
    for (model, protocol), group in sorted(grouped.items()):
        macro_accuracy = sum(item.accuracy for item in group) / len(group)
        rows.append(
            {
                "model": model,
                "protocol": protocol,
                "datasets": len(group),
                "macro_accuracy": macro_accuracy,
            }
        )
    return rows


def format_summary_markdown(rows: list[dict[str, object]]) -> str:
    header = "| Model | Protocol | Datasets | Macro Accuracy |\n|---|---|---:|---:|"
    lines = [header]
    for row in rows:
        lines.append(
            f"| {row['model']} | {row['protocol']} | {row['datasets']} | {row['macro_accuracy']:.2%} |"
        )
    return "\n".join(lines) + "\n"


def build_failure_report_payload(
    *,
    protocol: str,
    failures: list[dict[str, object]],
    interrupted: bool = False,
) -> dict[str, object]:
    return {
        "protocol": protocol,
        "interrupted": interrupted,
        "failure_count": len(failures),
        "failures": failures,
    }


def run_jobs(
    jobs: Iterable[T],
    worker: Callable[[T], R],
    *,
    max_workers: int = 1,
    preserve_order: bool = True,
) -> list[R]:
    job_list = list(jobs)
    if max_workers <= 1:
        return [worker(job) for job in job_list]
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        if preserve_order:
            return list(executor.map(worker, job_list))
        futures = [executor.submit(worker, job) for job in job_list]
        return [future.result() for future in as_completed(futures)]


def load_existing_results(
    output_root: Path,
    *,
    protocol: str,
) -> dict[tuple[str, str], EvaluationResult]:
    root = Path(output_root) / "evals"
    latest_paths: dict[tuple[str, str], Path] = {}
    if not root.exists():
        return {}

    for path in root.glob(f"*/{protocol}/contest8_*.json"):
        payload = json.loads(path.read_text(encoding="utf-8"))
        key = (payload["model"], Path(payload["dataset_path"]).name)
        current = latest_paths.get(key)
        if current is None or path.name > current.name:
            latest_paths[key] = path

    loaded: dict[tuple[str, str], EvaluationResult] = {}
    for key, path in latest_paths.items():
        payload = json.loads(path.read_text(encoding="utf-8"))
        loaded[key] = EvaluationResult(
            dataset_path=payload["dataset_path"],
            protocol=payload["protocol"],
            model=payload["model"],
            started_at=payload["started_at"],
            finished_at=payload["finished_at"],
            total_questions=payload["total_questions"],
            correct_questions=payload["correct_questions"],
            accuracy=payload["accuracy"],
            subjects=(),
        )
    return loaded


def split_pending_jobs(
    jobs: list[tuple[str, Path]],
    completed_keys: set[tuple[str, str]],
) -> tuple[list[tuple[str, Path]], list[tuple[str, Path]]]:
    pending: list[tuple[str, Path]] = []
    skipped: list[tuple[str, Path]] = []
    for model, dataset_path in jobs:
        key = (model, dataset_path.name)
        if key in completed_keys:
            skipped.append((model, dataset_path))
        else:
            pending.append((model, dataset_path))
    return pending, skipped
