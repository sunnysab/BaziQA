from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from acc_test.core.evaluator import EvaluationResult


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
