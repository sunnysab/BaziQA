from __future__ import annotations

import argparse
from pathlib import Path

from acc_test.core.bazi_provider import BaziProvider
from acc_test.core.evaluator import evaluate_dataset, write_evaluation_result
from acc_test.core.llm_client import OpenAICompatibleClient


DEFAULT_BAZI_SCRIPT = Path("/home/sunnysab/Code/0-Cloned/bazi/bazi.py")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run BaziQA structured evaluation.")
    parser.add_argument("dataset_path")
    parser.add_argument("--limit-subjects", type=int, default=None)
    parser.add_argument("--model", default=None)
    parser.add_argument("--bazi-script", default=str(DEFAULT_BAZI_SCRIPT))
    parser.add_argument("--cache-root", default="result")
    parser.add_argument("--output-root", default="result")
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    client = OpenAICompatibleClient.from_env()
    models = [args.model] if args.model else list(client.config.models)
    provider = BaziProvider(cache_root=Path(args.cache_root), bazi_script=Path(args.bazi_script))
    for model in models:
        result = evaluate_dataset(
            dataset_path=args.dataset_path,
            protocol="structured",
            client=client,
            model=model,
            provider=provider,
            limit_subjects=args.limit_subjects,
        )
        output_path = write_evaluation_result(result, output_root=args.output_root)
        print(f"{model}\taccuracy={result.accuracy:.2%}\toutput={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
