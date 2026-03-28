from __future__ import annotations

import argparse
from pathlib import Path
import sys


if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from acc_test.core.bazi_provider import BaziProvider
from acc_test.core.benchmark import run_jobs
from acc_test.core.evaluator import evaluate_dataset, prepare_chart_cache, write_evaluation_result
from acc_test.core.llm_client import OpenAICompatibleClient


DEFAULT_BAZI_SCRIPT = Path("/home/sunnysab/Code/0-Cloned/bazi/bazi.py")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run BaziQA structured evaluation.")
    parser.add_argument("dataset_path")
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
    provider = BaziProvider(cache_root=Path(args.cache_root), bazi_script=Path(args.bazi_script))

    prepare_chart_cache(
        dataset_path=args.dataset_path,
        provider=provider,
        limit_subjects=args.limit_subjects,
    )

    def worker(model: str) -> str:
        client = OpenAICompatibleClient(config)
        result = evaluate_dataset(
            dataset_path=args.dataset_path,
            protocol="structured",
            client=client,
            model=model,
            provider=provider,
            limit_subjects=args.limit_subjects,
        )
        output_path = write_evaluation_result(result, output_root=args.output_root)
        return f"{model}\taccuracy={result.accuracy:.2%}\toutput={output_path}"

    for line in run_jobs(models, worker, max_workers=args.max_workers, preserve_order=False):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
