from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path
import sys


if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from acc_test.core.reporting import (
    aggregate_report_data,
    discover_evaluation_results,
    discover_failure_reports,
    render_report_markdown,
)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a lightweight report from stored BaziQA results.")
    parser.add_argument("--root", default="result")
    parser.add_argument("--output", default=None)
    return parser


def main() -> int:
    args = build_arg_parser().parse_args()
    root = Path(args.root)
    result_paths = discover_evaluation_results(root)
    failure_paths = discover_failure_reports(root)
    report = aggregate_report_data(result_paths, failure_paths)
    markdown = render_report_markdown(report)

    output_path = Path(args.output) if args.output else Path("reports") / f"summary-{datetime.now(UTC).strftime('%Y-%m-%d')}.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
