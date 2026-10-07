import argparse
import asyncio
from pathlib import Path

from app.services.career_recommendation_engine import (
    CareerRecommendationEngine,
)
from evals.loader import load_career_eval_dataset
from evals.reporting import (
    CareerBenchmarkReport,
    build_career_benchmark_report,
)
from evals.runner import run_career_benchmark

DEFAULT_DATASET_PATH = (
    Path(__file__).parent / "datasets" / "career_recommendation_v1.jsonl"
)

DEFAULT_ENGINE = "deterministic"


def positive_int(value: str) -> int:
    parsed_value = int(value)

    if parsed_value < 1:
        raise argparse.ArgumentTypeError("value must be at least 1")

    return parsed_value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=("Run CareerIQ career recommendation benchmark.")
    )

    parser.add_argument(
        "--engine",
        choices=[
            "deterministic",
        ],
        default=DEFAULT_ENGINE,
    )

    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET_PATH,
    )

    parser.add_argument(
        "--runs",
        type=positive_int,
        default=1,
        help=("Number of repeated benchmark runs (default: 1)."),
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help=("Optional path for the JSON benchmark report."),
    )

    return parser.parse_args()


def build_benchmark_engine(
    engine_name: str,
) -> CareerRecommendationEngine:
    if engine_name == "deterministic":
        return CareerRecommendationEngine()

    raise ValueError(f"Unsupported career benchmark engine: {engine_name}")


def write_benchmark_report(
    report: CareerBenchmarkReport,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        (
            report.model_dump_json(
                indent=2,
            )
            + "\n"
        ),
        encoding="utf-8",
    )


async def run() -> None:
    args = parse_args()

    engine = build_benchmark_engine(args.engine)

    cases = load_career_eval_dataset(args.dataset)

    runs = []

    for _ in range(args.runs):
        summary = await run_career_benchmark(
            engine_name=args.engine,
            engine=engine,
            cases=cases,
        )

        runs.append(summary)

    report = build_career_benchmark_report(
        engine=args.engine,
        dataset=str(args.dataset),
        runs=runs,
    )

    if args.output is not None:
        write_benchmark_report(
            report,
            args.output,
        )

    print(
        report.model_dump_json(
            indent=2,
        )
    )


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
