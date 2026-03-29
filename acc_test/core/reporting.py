from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
import json
from pathlib import Path


def discover_evaluation_results(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*.json")
        if "/evals/" in path.as_posix() and "/failures" not in path.as_posix() and path.name.startswith("contest8_")
    )


def discover_failure_reports(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("failures_*.json"))


def aggregate_report_data(result_paths: list[Path], failure_paths: list[Path]) -> dict[str, object]:
    results = [json.loads(path.read_text(encoding="utf-8")) for path in result_paths]
    grouped: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    source_roots = sorted({str(path.parents[2]) for path in result_paths} | {str(path.parents[2]) for path in failure_paths})

    for result in results:
        grouped[(result["model"], result["protocol"])].append(result)

    macro_rows = []
    year_rows = []
    for (model, protocol), items in sorted(grouped.items()):
        macro_rows.append(
            {
                "model": model,
                "protocol": protocol,
                "datasets": len(items),
                "macro_accuracy": sum(item["accuracy"] for item in items) / len(items),
            }
        )

        year_row = {"model": model, "protocol": protocol}
        for item in sorted(items, key=lambda value: value["dataset_path"]):
            year_row[Path(item["dataset_path"]).stem] = item["accuracy"]
        year_rows.append(year_row)

    failure_rows = []
    for path in failure_paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        failure_rows.append(
            {
                "protocol": payload["protocol"],
                "failure_count": payload["failure_count"],
                "interrupted": payload.get("interrupted", False),
                "path": str(path),
            }
        )

    return {
        "overview": {
            "generated_at": datetime.now(UTC).isoformat(),
            "result_file_count": len(result_paths),
            "failure_file_count": len(failure_paths),
            "source_roots": source_roots,
        },
        "macro_rows": macro_rows,
        "year_rows": year_rows,
        "failure_rows": failure_rows,
    }


def render_report_markdown(report: dict[str, object]) -> str:
    overview = report["overview"]
    generated_at = overview.get("generated_at", "(unknown)")
    lines = [
        "# BaziQA 结果汇总报告",
        "",
        "## 概览",
        "",
        f"- 生成时间：{generated_at}",
        f"- 结果文件数：{overview['result_file_count']}",
        f"- 失败报告数：{overview['failure_file_count']}",
        f"- 扫描来源：{', '.join(overview['source_roots']) if overview['source_roots'] else '(无)'}",
        "",
        "## 宏平均准确率",
        "",
        "| Model | Protocol | Datasets | Macro Accuracy |",
        "|---|---|---:|---:|",
    ]

    for row in report["macro_rows"]:
        lines.append(
            f"| {row['model']} | {row['protocol']} | {row['datasets']} | {row['macro_accuracy']:.2%} |"
        )

    lines.extend(["", "## 分年份准确率", ""])
    if report["year_rows"]:
        year_columns = sorted(
            {
                key
                for row in report["year_rows"]
                for key in row
                if key not in {"model", "protocol"}
            }
        )
        lines.append("| Model | Protocol | " + " | ".join(year_columns) + " |")
        lines.append("|---|---|" + "---:|" * len(year_columns))
        for row in report["year_rows"]:
            values = [f"{row.get(column, 0.0):.2%}" if column in row else "-" for column in year_columns]
            lines.append(f"| {row['model']} | {row['protocol']} | " + " | ".join(values) + " |")
    else:
        lines.append("暂无结果。")

    lines.extend(["", "## 失败任务", ""])
    if report["failure_rows"]:
        lines.append("| Protocol | Failure Count | Interrupted | Path |")
        lines.append("|---|---:|---|---|")
        for row in report["failure_rows"]:
            lines.append(
                f"| {row['protocol']} | {row['failure_count']} | {row['interrupted']} | {row['path']} |"
            )
    else:
        lines.append("无失败任务记录。")

    return "\n".join(lines) + "\n"
