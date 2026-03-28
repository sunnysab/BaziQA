from acc_test.run_benchmark import build_arg_parser as build_benchmark_arg_parser
from pathlib import Path

from acc_test.core.benchmark import (
    build_summary_rows,
    discover_contest_datasets,
    run_jobs,
)
from acc_test.core.evaluator import EvaluationResult, SubjectResult


def test_discover_contest_datasets_returns_year_sorted_paths():
    paths = discover_contest_datasets(Path("data"))
    assert [path.name for path in paths] == [
        "contest8_2021.json",
        "contest8_2022.json",
        "contest8_2023.json",
        "contest8_2024.json",
        "contest8_2025.json",
    ]


def test_build_summary_rows_computes_macro_average_per_model_and_protocol():
    subject = SubjectResult(
        person_id="p1",
        anonymous_id="命主001",
        chart_cache_path="result/bazi-results/a.json",
        correct_count=3,
        total_count=5,
        accuracy=0.6,
        questions=(),
    )
    results = [
        EvaluationResult(
            dataset_path="data/contest8_2024.json",
            protocol="multiturn",
            model="gpt-5.4",
            started_at="2026-03-28T00:00:00+00:00",
            finished_at="2026-03-28T00:01:00+00:00",
            total_questions=40,
            correct_questions=12,
            accuracy=0.30,
            subjects=(subject,),
        ),
        EvaluationResult(
            dataset_path="data/contest8_2025.json",
            protocol="multiturn",
            model="gpt-5.4",
            started_at="2026-03-28T00:02:00+00:00",
            finished_at="2026-03-28T00:03:00+00:00",
            total_questions=40,
            correct_questions=16,
            accuracy=0.40,
            subjects=(subject,),
        ),
    ]

    rows = build_summary_rows(results)

    assert rows == [
        {
            "model": "gpt-5.4",
            "protocol": "multiturn",
            "datasets": 2,
            "macro_accuracy": 0.35,
        }
    ]


def test_run_jobs_returns_results_in_input_order():
    jobs = [1, 2, 3]

    def worker(job: int) -> int:
        return job * 10

    assert run_jobs(jobs, worker, max_workers=2) == [10, 20, 30]


def test_benchmark_cli_accepts_max_workers():
    parser = build_benchmark_arg_parser()
    args = parser.parse_args(["--protocol", "multiturn", "--max-workers", "3"])
    assert args.protocol == "multiturn"
    assert args.max_workers == 3
