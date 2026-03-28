from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import traceback


if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from acc_test.core.bazi_provider import BaziProvider
from acc_test.core.benchmark import (
    build_failure_report_payload,
    build_summary_rows,
    discover_contest_datasets,
    format_summary_markdown,
    run_jobs,
)
from acc_test.core.evaluator import evaluate_dataset, prepare_chart_cache, write_evaluation_result
from acc_test.core.llm_client import OpenAICompatibleClient


DEFAULT_BAZI_SCRIPT = Path("/home/sunnysab/Code/0-Cloned/bazi/bazi.py")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run BaziQA benchmark across contest years.")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--protocol", choices=("multiturn", "structured"), required=True)
    parser.add_argument("--limit-subjects", type=int, default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--max-workers", type=int, default=1)
    parser.add_argument("--bazi-script", default=str(DEFAULT_BAZI_SCRIPT))
    parser.add_argument("--cache-root", default="result")
    parser.add_argument("--output-root", default="result")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    config = OpenAICompatibleClient.from_env().config
    models = [args.model] if args.model else list(config.models)
    datasets = discover_contest_datasets(Path(args.data_dir))
    provider = BaziProvider(cache_root=Path(args.cache_root), bazi_script=Path(args.bazi_script))

    for dataset_path in datasets:
        prepare_chart_cache(
            dataset_path=dataset_path,
            provider=provider,
            limit_subjects=args.limit_subjects,
        )

    jobs = [(model, dataset_path) for model in models for dataset_path in datasets]

    def worker(job: tuple[str, Path]):
        model, dataset_path = job
        try:
            client = OpenAICompatibleClient(config)
            result = evaluate_dataset(
                dataset_path=dataset_path,
                protocol=args.protocol,
                client=client,
                model=model,
                provider=provider,
                limit_subjects=args.limit_subjects,
            )
            output_path = write_evaluation_result(result, output_root=args.output_root)
            return {
                "ok": True,
                "result": result,
                "line": f"{model}\t{dataset_path.name}\taccuracy={result.accuracy:.2%}\toutput={output_path}",
            }
        except Exception as exc:
            return {
                "ok": False,
                "failure": {
                    "model": model,
                    "dataset": dataset_path.name,
                    "protocol": args.protocol,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc),
                    "traceback": traceback.format_exc(),
                },
                "line": f"ERROR\t{model}\t{dataset_path.name}\t{type(exc).__name__}: {exc}",
            }

    all_results = []
    failures = []
    for outcome in run_jobs(jobs, worker, max_workers=args.max_workers):
        print(outcome["line"])
        if outcome["ok"]:
            all_results.append(outcome["result"])
        else:
            failures.append(outcome["failure"])

    summary_rows = build_summary_rows(all_results)
    summary_path = (
        Path(args.output_root)
        / "evals"
        / f"summary_{args.protocol}.md"
    )
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(format_summary_markdown(summary_rows), encoding="utf-8")
    print(f"summary\t{summary_path}")

    if failures:
        failure_path = Path(args.output_root) / "evals" / f"failures_{args.protocol}.json"
        failure_path.write_text(
            json.dumps(
                build_failure_report_payload(protocol=args.protocol, failures=failures),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"failures\t{failure_path}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
