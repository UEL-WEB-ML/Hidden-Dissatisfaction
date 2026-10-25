"""Command-line boundary for small reproducible research operations."""

import argparse
import json
import os
from collections.abc import Sequence
from dataclasses import replace
from datetime import datetime
from pathlib import Path

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
    train = subparsers.add_parser(
        "train",
        help="Run temporal model selection, calibration, and final evaluation.",
    )
    train.add_argument(
        "--data",
        type=Path,
        default=Path("data/processed/modelling_items.parquet"),
    )
    export = subparsers.add_parser(
        "export-modelling-items", help="Export a Gold modelling-items snapshot."
    )
    export.add_argument("--dsn", default=None, help="Postgres DSN (or WAREHOUSE_DSN)")
    export.add_argument("--source-run-id", required=True)
    export.add_argument(
        "--output", type=Path, default=Path("data/processed/modelling_items.parquet")
    )
    export.add_argument("--source-manifest", type=Path)
    export.add_argument("--source-hash", action="append", default=[], metavar="NAME=HASH")
    export.add_argument("--cutoff-version", default="p4")
    export.add_argument("--review-policy-version", default="adr-001-latest-answered-v1")
    export.add_argument("--feature-schema-version", default="ml-modelling-items-v1")
    export.add_argument("--git-sha")
    train.add_argument("--output-root", type=Path, default=Path("."))
    train.add_argument("--config", type=Path, default=Path("configs/experiment.toml"))
    train.add_argument("--bootstrap-iterations", type=int)
    train.add_argument(
        "--finalize-test",
        action="store_true",
        help="Evaluate the sealed test partition using a frozen selection record.",
    )
    train.add_argument(
        "--selection-record",
        "--frozen-selection-record",
        dest="selection_record",
        type=Path,
        help="Development output, or frozen selection-record JSON for finalization.",
    )
    train.add_argument(
        "--test-lock",
        help="Lock from the frozen selection record (required for finalization).",
    )

    for name, text in (
        ("recalculate-sla", "Apply changed SLA parameters to OPEN review cycles."),
        ("purge-evidence", "Delete unattached evidence uploads past retention."),
    ):
        job = subparsers.add_parser(name, help=text)
        job.add_argument("--dsn", default=None, help="Postgres DSN (or HD_RUNTIME_DSN)")
    purge = subparsers.choices["purge-evidence"]
    purge.add_argument("--root", type=Path, default=Path("data/evidence"))
    purge.add_argument("--retention-hours", type=int, default=24)
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

    if args.command == "train":
        from hidden_dissatisfaction.modeling.training import TrainingConfig, run_training

        if args.finalize_test and (args.selection_record is None or args.test_lock is None):
            parser = _build_parser()
            parser.error("--finalize-test requires both --selection-record and --test-lock")

        config = TrainingConfig.from_toml(args.config)
        if args.bootstrap_iterations is not None:
            config = replace(config, bootstrap_iterations=args.bootstrap_iterations)

        frozen_selection_record = None
        if args.finalize_test:
            try:
                frozen_selection_record = json.loads(
                    args.selection_record.read_text(encoding="utf-8")
                )
            except (OSError, json.JSONDecodeError) as error:
                raise SystemExit(f"unable to read selection record: {error}") from error
            if not isinstance(frozen_selection_record, dict):
                raise SystemExit("selection record must contain a JSON object")

        report = run_training(
            args.data,
            config=config,
            output_root=args.output_root,
            finalize_test=args.finalize_test,
            frozen_selection_record=frozen_selection_record,
            test_lock=args.test_lock,
        )
        if args.selection_record is not None and not args.finalize_test:
            args.selection_record.parent.mkdir(parents=True, exist_ok=True)
            args.selection_record.write_text(
                json.dumps(report["selection_record"], indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0

    if args.command == "export-modelling-items":
        from hidden_dissatisfaction.application.modelling_export import ModellingExportMetadata
        from hidden_dissatisfaction.infrastructure.modelling_parquet_exporter import (
            export_gold_modelling_items,
        )
        from hidden_dissatisfaction.infrastructure.postgres_modelling_items_reader import (
            PostgresGoldModellingItemsReader,
        )

        hashes = {}
        if args.source_manifest is not None:
            manifest = json.loads(args.source_manifest.read_text(encoding="utf-8"))
            hashes.update(manifest.get("source_hashes", manifest.get("hashes", {})))
        for value in args.source_hash:
            if "=" not in value:
                raise SystemExit("--source-hash must be NAME=HASH")
            name, digest = value.split("=", 1)
            hashes[name] = digest
        dsn = args.dsn or os.environ.get("WAREHOUSE_DSN") or os.environ.get("DBT_DSN")
        if not dsn:
            raise SystemExit("--dsn or WAREHOUSE_DSN is required")
        metadata = ModellingExportMetadata(
            args.source_run_id,
            hashes,
            args.cutoff_version,
            args.review_policy_version,
            args.feature_schema_version,
            args.git_sha,
        )
        export_gold_modelling_items(
            PostgresGoldModellingItemsReader(dsn, args.source_run_id), metadata, args.output
        )
        print(str(args.output))
        return 0

    if args.command in ("recalculate-sla", "purge-evidence"):
        from datetime import UTC

        dsn = args.dsn or os.environ.get("HD_RUNTIME_DSN")
        if not dsn:
            _build_parser().error("--dsn or HD_RUNTIME_DSN is required")
        now = datetime.now(UTC)
        if args.command == "recalculate-sla":
            from hidden_dissatisfaction.infrastructure.sla_recalculation import (
                PostgresSlaRecalculator,
            )

            print(json.dumps({"adjusted_cycles": PostgresSlaRecalculator(dsn).run(now)}))
        else:
            from hidden_dissatisfaction.infrastructure.evidence_cleanup import (
                purge_unattached_uploads,
            )

            removed = purge_unattached_uploads(dsn, args.root, now, args.retention_hours)
            print(json.dumps({"purged_uploads": removed}))
        return 0

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
