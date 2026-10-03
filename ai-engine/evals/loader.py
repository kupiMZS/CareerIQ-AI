import json
from pathlib import Path

from evals.schemas import ResumeEvalCase


class EvalDatasetError(RuntimeError):
    """
    Raised when an evaluation dataset is invalid.
    """


def load_resume_eval_dataset(
    path: Path,
) -> list[ResumeEvalCase]:
    if not path.exists():
        raise EvalDatasetError(f"Evaluation dataset does not exist: {path}")

    cases: list[ResumeEvalCase] = []
    seen_case_ids: set[str] = set()

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:
        for line_number, raw_line in enumerate(
            file,
            start=1,
        ):
            line = raw_line.strip()

            if not line:
                continue

            try:
                payload = json.loads(line)
            except json.JSONDecodeError as exception:
                raise EvalDatasetError(
                    f"Invalid JSON in evaluation dataset at line {line_number}."
                ) from exception

            case = ResumeEvalCase.model_validate(payload)

            if case.case_id in seen_case_ids:
                raise EvalDatasetError(f"Duplicate evaluation case_id: {case.case_id}")

            seen_case_ids.add(case.case_id)
            cases.append(case)

    if not cases:
        raise EvalDatasetError("Evaluation dataset contains no cases.")

    return cases
