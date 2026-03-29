from pathlib import Path
import json

from acc_test.core.reporting import (
    aggregate_report_data,
    discover_evaluation_results,
    render_report_markdown,
)


def test_discover_evaluation_results_finds_nested_eval_json(tmp_path: Path):
    target = tmp_path / "run1" / "evals" / "gpt-5.4" / "multiturn" / "contest8_2025_1.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("{}", encoding="utf-8")

    paths = discover_evaluation_results(tmp_path)

    assert paths == [target]


def test_aggregate_report_data_groups_by_model_and_protocol(tmp_path: Path):
    p1 = tmp_path / "run1" / "evals" / "gpt-5.4" / "multiturn" / "contest8_2024_a.json"
    p2 = tmp_path / "run1" / "evals" / "gpt-5.4" / "multiturn" / "contest8_2025_b.json"
    p1.parent.mkdir(parents=True, exist_ok=True)

    payload1 = {
        "dataset_path": "data/contest8_2024.json",
        "protocol": "multiturn",
        "model": "gpt-5.4",
        "started_at": "2026-03-29T00:00:00+00:00",
        "finished_at": "2026-03-29T00:01:00+00:00",
        "total_questions": 40,
        "correct_questions": 12,
        "accuracy": 0.30,
        "subjects": [],
    }
    payload2 = dict(payload1)
    payload2["dataset_path"] = "data/contest8_2025.json"
    payload2["accuracy"] = 0.40

    p1.write_text(json.dumps(payload1), encoding="utf-8")
    p2.write_text(json.dumps(payload2), encoding="utf-8")

    report = aggregate_report_data([p1, p2], [])

    assert report["overview"]["result_file_count"] == 2
    assert report["macro_rows"] == [
        {
            "model": "gpt-5.4",
            "protocol": "multiturn",
            "datasets": 2,
            "macro_accuracy": 0.35,
        }
    ]
    assert report["year_rows"] == [
        {
            "model": "gpt-5.4",
            "protocol": "multiturn",
            "contest8_2024": 0.30,
            "contest8_2025": 0.40,
        }
    ]


def test_render_report_markdown_contains_expected_sections():
    report = {
        "overview": {
            "result_file_count": 2,
            "failure_file_count": 1,
            "source_roots": ["result", "result/run1"],
        },
        "macro_rows": [
            {
                "model": "gpt-5.4",
                "protocol": "multiturn",
                "datasets": 2,
                "macro_accuracy": 0.35,
            }
        ],
        "year_rows": [
            {
                "model": "gpt-5.4",
                "protocol": "multiturn",
                "contest8_2024": 0.30,
                "contest8_2025": 0.40,
            }
        ],
        "failure_rows": [
            {
                "protocol": "multiturn",
                "failure_count": 1,
                "interrupted": False,
                "path": "result/run1/evals/failures_multiturn.json",
            }
        ],
    }

    markdown = render_report_markdown(report)

    assert "# BaziQA 结果汇总报告" in markdown
    assert "## 概览" in markdown
    assert "## 宏平均准确率" in markdown
    assert "## 分年份准确率" in markdown
    assert "## 失败任务" in markdown
