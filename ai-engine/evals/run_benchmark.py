import argparse
import asyncio
from pathlib import Path

from app.core import get_settings
from app.providers.factory import create_provider
from evals.loader import load_resume_eval_dataset
from evals.runner import run_resume_benchmark

DEFAULT_DATASET_PATH = Path(__file__).parent / "datasets" / "resume_extraction_v1.jsonl"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=("Run CareerIQ resume extraction benchmark.")
    )

    parser.add_argument(
        "--provider",
        choices=[
            "rule_based",
            "local",
        ],
        default="rule_based",
    )

    parser.add_argument(
        "--dataset",
        type=Path,
        default=DEFAULT_DATASET_PATH,
    )

    return parser.parse_args()


async def run() -> None:
    args = parse_args()

    settings = get_settings()

    provider = create_provider(
        args.provider,
        settings,
    )

    cases = load_resume_eval_dataset(args.dataset)

    summary = await run_resume_benchmark(
        provider_name=args.provider,
        provider=provider,
        cases=cases,
    )

    print(
        summary.model_dump_json(
            indent=2,
        )
    )


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
