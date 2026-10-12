"""Command-line boundary for small reproducible research operations."""

import argparse
import json
from collections.abc import Sequence
from datetime import datetime

from hidden_dissatisfaction.domain.cohort import OrderObservation


def _parse_datetime(value: str) -> datetime:
    """Parse an ISO-8601 timestamp supplied at the CLI boundary."""
    try:
        return datetime.fromisoformat(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(f"Invalid ISO-8601 datetime: {value}") from error


def _build_parser() -> argparse.ArgumentParser:
    """Build the command parser without executing application logic."""
    parser = argparse.ArgumentParser(prog="hidden-dissatisfaction")
    subparsers = parser.add_subparsers(dest="command", required=True)

    assess = subparsers.add_parser(
        "assess-order",
        help="Assess one order against the primary observed-review cohort.",
    )
    assess.add_argument("--order-id", required=True)
    assess.add_argument("--delivered-at", required=True, type=_parse_datetime)
    assess.add_argument("--estimated-at", required=True, type=_parse_datetime)
    assess.add_argument("--review-score", type=int)
    assess.add_argument("--review-created-at", type=_parse_datetime)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a process exit code."""
    args = _build_parser().parse_args(argv)
    if args.command == "assess-order":
        observation = OrderObservation(
            order_id=args.order_id,
            delivered_at=args.delivered_at,
            estimated_delivery_at=args.estimated_at,
            review_score=args.review_score,
            review_created_at=args.review_created_at,
        )
        assessment = observation.assess_primary_cohort()
        print(
            json.dumps(
                {
                    "order_id": observation.order_id,
                    "is_eligible": assessment.is_eligible,
                    "low_review": assessment.low_review,
                    "exclusion_reason": assessment.exclusion_reason,
                }
            )
        )
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
