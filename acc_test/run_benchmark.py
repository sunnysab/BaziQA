from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
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
    load_existing_results,
    run_jobs,
    split_pending_jobs,
)
from acc_test.core.evaluator import evaluate_dataset, prepare_chart_cache, write_evaluation_result
from acc_test.core.llm_client import OpenAICompatibleClient


DEFAULT_BAZI_SCRIPT = Path(__file__).resolve().parents[1] / "third_party" / "bazi" / "bazi.py"


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run BaziQA benchmark across contest years.")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--protocol", choices=("multiturn", "structured"), required=True)
    parser.add_argument("--limit-subjects", type=int, default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--max-workers", type=int, default=1)
    parser.add_argument("--resume", action=argparse.BooleanOptionalAction, default=True)
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
    existing_results = load_existing_results(Path(args.output_root), protocol=args.protocol) if args.resume else {}
    pending_jobs, skipped_jobs = split_pending_jobs(jobs, set(existing_results))

    for model, dataset_path in skipped_jobs:
        print(f"SKIP\t{model}\t{dataset_path.name}\treason=existing_result")

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

    all_results = list(existing_results.values())
    failures = []
    interrupted = False
    executor = ThreadPoolExecutor(max_workers=args.max_workers if args.max_workers > 0 else 1)
    future_map = {executor.submit(worker, job): job for job in pending_jobs}
    try:
        for future in as_completed(future_map):
            outcome = future.result()
            print(outcome["line"])
            if outcome["ok"]:
                all_results.append(outcome["result"])
            else:
                failures.append(outcome["failure"])
    except KeyboardInterrupt:
        interrupted = True
        print("INTERRUPTED\twriting partial progress before exit")
    finally:
        executor.shutdown(wait=not interrupted, cancel_futures=interrupted)

    summary_path, failure_path = write_run_reports(
        output_root=Path(args.output_root),
        protocol=args.protocol,
        results=all_results,
        failures=failures,
        interrupted=interrupted,
    )
    print(f"summary\t{summary_path}")
    if failure_path is not None:
        print(f"failures\t{failure_path}")

    if interrupted:
        return 130
    if failures:
        return 1
    return 0


def write_run_reports(
    *,
    output_root: Path,
    protocol: str,
    results,
    failures,
    interrupted: bool,
) -> tuple[Path, Path | None]:
    summary_rows = build_summary_rows(list(results))
    summary_path = output_root / "evals" / f"summary_{protocol}.md"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(format_summary_markdown(summary_rows), encoding="utf-8")

    failure_path: Path | None = None
    if failures or interrupted:
        failure_path = output_root / "evals" / f"failures_{protocol}.json"
        failure_path.write_text(
            json.dumps(
                build_failure_report_payload(
                    protocol=protocol,
                    failures=list(failures),
                    interrupted=interrupted,
                ),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    return summary_path, failure_path


if __name__ == "__main__":
    raise SystemExit(main())
