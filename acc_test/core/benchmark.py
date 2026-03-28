from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor, as_completed
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
) -> dict[str, object]:
    return {
        "protocol": protocol,
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
