import argparse
import asyncio
from pathlib import Path

from app.core import get_settings
from app.core.config import Settings
from app.prompts.resume_analysis import (
    RESUME_ANALYSIS_PROMPT_VERSION,
)
from app.providers.base import ResumeAnalysisProvider
from app.providers.factory import create_provider
from evals.loader import load_resume_eval_dataset
from evals.providers import EnrichedResumeProvider
from evals.reporting import (
    ResumeBenchmarkReport,
    build_resume_benchmark_report,
)
from evals.runner import run_resume_benchmark

DEFAULT_DATASET_PATH = Path(__file__).parent / "datasets" / "resume_extraction_v1.jsonl"

LOCAL_PROVIDERS = frozenset(
    {
        "local",
        "local_enriched",
    }
)


def positive_int(value: str) -> int:
    parsed_value = int(value)

    if parsed_value < 1:
        raise argparse.ArgumentTypeError("value must be at least 1")

    return parsed_value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=("Run CareerIQ resume extraction benchmark.")
    )

    parser.add_argument(
        "--provider",
        choices=[
            "rule_based",
            "rule_based_enriched",
            "local",
            "local_enriched",
        ],
        default="rule_based",
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


def build_benchmark_provider(
    provider_name: str,
    settings: Settings,
) -> ResumeAnalysisProvider:
    if provider_name == "local_enriched":
        return EnrichedResumeProvider(
            create_provider(
                "local",
                settings,
            )
        )

    if provider_name == "rule_based_enriched":
        return EnrichedResumeProvider(
            create_provider(
                "rule_based",
                settings,
            )
        )

    return create_provider(
        provider_name,
        settings,
    )


def get_benchmark_model(
    provider_name: str,
    settings: Settings,
) -> str | None:
    if provider_name in LOCAL_PROVIDERS:
        return settings.ai_model

    return None


def get_benchmark_prompt_version(
    provider_name: str,
) -> str | None:
    if provider_name in LOCAL_PROVIDERS:
        return RESUME_ANALYSIS_PROMPT_VERSION

    return None


def write_benchmark_report(
    report: ResumeBenchmarkReport,
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

    settings = get_settings()

    provider = build_benchmark_provider(
        args.provider,
        settings,
    )

    cases = load_resume_eval_dataset(args.dataset)

    runs = []

    for _ in range(args.runs):
        summary = await run_resume_benchmark(
            provider_name=args.provider,
            provider=provider,
            cases=cases,
        )

        runs.append(summary)

    report = build_resume_benchmark_report(
        provider=args.provider,
        model=get_benchmark_model(
            args.provider,
            settings,
        ),
        prompt_version=(get_benchmark_prompt_version(args.provider)),
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
