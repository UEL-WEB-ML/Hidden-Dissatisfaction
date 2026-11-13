"""Pure contracts for loading immutable Olist CSV files into Bronze."""

import csv
import hashlib
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast


@dataclass(frozen=True)
class BronzeFileSpec:
    """Describe one allowlisted raw file and its Bronze destination."""

    filename: str
    table_name: str
    headers: tuple[str, ...]


BRONZE_FILE_SPECS: tuple[BronzeFileSpec, ...] = (
    BronzeFileSpec(
        "olist_customers_dataset.csv",
        "customers",
        (
            "customer_id",
            "customer_unique_id",
            "customer_zip_code_prefix",
            "customer_city",
            "customer_state",
        ),
    ),
    BronzeFileSpec(
        "olist_sellers_dataset.csv",
        "sellers",
        ("seller_id", "seller_zip_code_prefix", "seller_city", "seller_state"),
    ),
    BronzeFileSpec(
        "olist_products_dataset.csv",
        "products",
        (
            "product_id",
            "product_category_name",
            "product_name_lenght",
            "product_description_lenght",
            "product_photos_qty",
            "product_weight_g",
            "product_length_cm",
            "product_height_cm",
            "product_width_cm",
        ),
    ),
    BronzeFileSpec(
        "olist_orders_dataset.csv",
        "orders",
        (
            "order_id",
            "customer_id",
            "order_status",
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ),
    ),
    BronzeFileSpec(
        "olist_order_items_dataset.csv",
        "order_items",
        (
            "order_id",
            "order_item_id",
            "product_id",
            "seller_id",
            "shipping_limit_date",
            "price",
            "freight_value",
        ),
    ),
    BronzeFileSpec(
        "olist_order_payments_dataset.csv",
        "order_payments",
        ("order_id", "payment_sequential", "payment_type", "payment_installments", "payment_value"),
    ),
    BronzeFileSpec(
        "olist_order_reviews_dataset.csv",
        "order_reviews",
        (
            "review_id",
            "order_id",
            "review_score",
            "review_comment_title",
            "review_comment_message",
            "review_creation_date",
            "review_answer_timestamp",
        ),
    ),
    BronzeFileSpec(
        "olist_geolocation_dataset.csv",
        "geolocation",
        (
            "geolocation_zip_code_prefix",
            "geolocation_lat",
            "geolocation_lng",
            "geolocation_city",
            "geolocation_state",
        ),
    ),
    BronzeFileSpec(
        "product_category_name_translation.csv",
        "category_translation",
        ("product_category_name", "product_category_name_english"),
    ),
)


class InvalidBronzeManifest(ValueError):
    """Raised when raw inputs do not match the declared immutable manifest."""


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of a raw file without loading it into memory."""

    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest(raw_dir: Path) -> dict[str, object]:
    """Build a deterministic manifest after validating the nine expected files."""

    files: list[dict[str, object]] = []
    for spec in BRONZE_FILE_SPECS:
        path = raw_dir / spec.filename
        if not path.is_file():
            raise InvalidBronzeManifest(f"missing raw file: {spec.filename}")
        with path.open("r", encoding="utf-8-sig", newline="") as source:
            headers = tuple(next(csv.reader(source), ()))
        if headers != spec.headers:
            raise InvalidBronzeManifest(f"unexpected header in {spec.filename}: {headers!r}")
        files.append({"name": spec.filename, "table": spec.table_name, "sha256": sha256_file(path)})
    unexpected = sorted(
        path.name
        for path in raw_dir.glob("*.csv")
        if path.name not in {s.filename for s in BRONZE_FILE_SPECS}
    )
    if unexpected:
        raise InvalidBronzeManifest(f"unexpected raw CSV files: {', '.join(unexpected)}")
    return {"manifest_version": 1, "files": files}


def validate_manifest(raw_dir: Path, manifest: Mapping[str, Any]) -> None:
    """Validate a supplied manifest against the allowlist and current file hashes."""

    if manifest.get("manifest_version") != 1:
        raise InvalidBronzeManifest("manifest_version must be 1")
    entries = manifest.get("files")
    if not isinstance(entries, list):
        raise InvalidBronzeManifest("manifest files must be a list")
    expected = {spec.filename: spec for spec in BRONZE_FILE_SPECS}
    observed: dict[str, Mapping[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, Mapping) or not isinstance(entry.get("name"), str):
            raise InvalidBronzeManifest("each manifest file entry requires a name")
        name = entry["name"]
        if name in observed:
            raise InvalidBronzeManifest(f"duplicate manifest entry: {name}")
        observed[name] = entry
    if set(observed) != set(expected):
        raise InvalidBronzeManifest("manifest must contain exactly the nine expected raw files")
    generated = build_manifest(raw_dir)
    generated_entries = cast(list[dict[str, object]], generated["files"])
    generated_by_name = {str(entry["name"]): entry for entry in generated_entries}
    for name, spec in expected.items():
        entry = observed[name]
        if entry.get("table") != spec.table_name:
            raise InvalidBronzeManifest(f"unexpected Bronze table for {name}")
        if entry.get("sha256") != generated_by_name[name]["sha256"]:
            raise InvalidBronzeManifest(f"checksum mismatch: {name}")


def iter_csv_rows(path: Path, headers: tuple[str, ...]) -> Iterable[tuple[str | None, ...]]:
    """Yield checked CSV rows in header order, preserving empty values as NULL."""

    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if tuple(reader.fieldnames or ()) != headers:
            raise InvalidBronzeManifest(f"unexpected header in {path.name}")
        for row in reader:
            if None in row or set(row) != set(headers):
                raise InvalidBronzeManifest(f"malformed CSV row in {path.name}")
            yield tuple(row[column] if row[column] != "" else None for column in headers)
