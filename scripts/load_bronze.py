#!/usr/bin/env python3
"""Preflight and load the canonical Olist files into Bronze."""
import argparse, csv, hashlib, json, subprocess, sys, uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/raw/olist"
COMPOSE = ROOT.parent / "Docker_Environment"
FILES = {
 "olist_customers_dataset.csv": ("customers", ["customer_id","customer_unique_id","customer_zip_code_prefix","customer_city","customer_state"]),
 "olist_geolocation_dataset.csv": ("geolocation", ["geolocation_zip_code_prefix","geolocation_lat","geolocation_lng","geolocation_city","geolocation_state"]),
 "olist_order_items_dataset.csv": ("order_items", ["order_id","order_item_id","product_id","seller_id","shipping_limit_date","price","freight_value"]),
 "olist_order_payments_dataset.csv": ("order_payments", ["order_id","payment_sequential","payment_type","payment_installments","payment_value"]),
 "olist_order_reviews_dataset.csv": ("order_reviews", ["review_id","order_id","review_score","review_comment_title","review_comment_message","review_creation_date","review_answer_timestamp"]),
 "olist_orders_dataset.csv": ("orders", ["order_id","customer_id","order_status","order_purchase_timestamp","order_approved_at","order_delivered_carrier_date","order_delivered_customer_date","order_estimated_delivery_date"]),
 "olist_products_dataset.csv": ("products", ["product_id","product_category_name","product_name_lenght","product_description_lenght","product_photos_qty","product_weight_g","product_length_cm","product_height_cm","product_width_cm"]),
 "olist_sellers_dataset.csv": ("sellers", ["seller_id","seller_zip_code_prefix","seller_city","seller_state"]),
 "product_category_name_translation.csv": ("category_translation", ["product_category_name","product_category_name_english"]),
}
def q(value): return "'" + str(value).replace("'", "''") + "'"

def psql_cmd(env):
    return ["docker", "compose", "--env-file", str(env), "exec", "-T", "postgres",
            "psql", "-U", "postgres", "-d", "ironman", "-v", "ON_ERROR_STOP=1", "-At"]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--env-file", type=Path); args = ap.parse_args()
    env = args.env_file or (Path.home() / ".config/docker-environment/.env")
    if not env.is_file(): raise SystemExit(f"Docker environment file unavailable: {env} (use --env-file)")
    manifest = json.loads((DATA/"manifest.json").read_text(encoding="utf-8")); entries = manifest.get("files", [])
    names = [x.get("name") for x in entries]
    if len(names) != len(FILES) or len(set(names)) != len(names) or set(names) != set(FILES): raise SystemExit("manifest must contain exactly the nine unique canonical filenames")
    mh = hashlib.sha256((DATA/"manifest.json").read_bytes()).hexdigest(); records = []
    for item in entries:
        name = item["name"]; path = DATA/name
        if not path.is_file(): raise SystemExit(f"missing file: {path}")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != item.get("sha256"): raise SystemExit(f"sha256 mismatch: {name}")
        with path.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.reader(f); header = next(reader, None); rows = sum(1 for _ in reader)
        if header != FILES[name][1]: raise SystemExit(f"header mismatch: {name}: {header}")
        records.append((name, rows, digest)); print(f"preflight {name}: {rows} rows, sha256 OK")
    cmd = psql_cmd(env)
    preflight = subprocess.run(cmd + ["-c", f"SELECT EXISTS (SELECT 1 FROM bronze.ingestion_runs WHERE manifest_sha256={q(mh)} AND status='complete')"], cwd=COMPOSE, text=True, capture_output=True)
    if preflight.returncode != 0:
        print(preflight.stderr, file=sys.stderr); raise SystemExit(preflight.returncode)
    run = str(uuid.uuid4())
    session = subprocess.Popen(cmd, cwd=COMPOSE, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, text=True, bufsize=1)
    assert session.stdin is not None and session.stdout is not None and session.stderr is not None
    session.stdin.write("SELECT pg_advisory_lock(48190217);\n")
    session.stdin.write(f"SELECT EXISTS (SELECT 1 FROM bronze.ingestion_runs WHERE manifest_sha256={q(mh)} AND status='complete');\n")
    session.stdin.write("SELECT 'LOCKED_CHECK_DONE';\n"); session.stdin.flush()
    locked_output = []
    for line in session.stdout:
        locked_output.append(line.strip())
        if line.strip() == "LOCKED_CHECK_DONE": break
    if "t" in locked_output:
        session.stdin.write("SELECT pg_advisory_unlock(48190217);\n"); session.stdin.close(); session.wait()
        print("matching complete manifest already loaded; no-op"); return
    statements = [f"INSERT INTO bronze.ingestion_runs(run_id,manifest_sha256,status) VALUES ({q(run)},{q(mh)},'running')", "COMMIT", "BEGIN"]
    for name, rows, sha in records:
        table, cols = FILES[name]; c=",".join(cols); staging=table+"_staging"
        statements += [f"INSERT INTO bronze.ingestion_files(run_id,file_name,expected_sha256,actual_sha256,expected_rows) VALUES ({q(run)},{q(name)},{q(sha)},{q(sha)},{rows})", f"TRUNCATE bronze.{staging} RESTART IDENTITY", f"\\copy bronze.{staging} ({c}) FROM '/data/raw/olist/{name}' WITH (FORMAT csv, HEADER true, ENCODING 'UTF8')", f"INSERT INTO bronze.{table} ({c},run_id,source_row_number,ingested_at) SELECT {c},{q(run)}::uuid,stage_row_number,now() FROM bronze.{staging} ORDER BY stage_row_number", f"UPDATE bronze.ingestion_files SET loaded_rows={rows},status='loaded' WHERE run_id={q(run)} AND file_name={q(name)}"]
    statements += [f"UPDATE bronze.ingestion_runs SET status='complete',completed_at=now() WHERE run_id={q(run)}", "COMMIT", "SELECT pg_advisory_unlock(48190217)"]
    session.stdin.write(";\n".join(statements) + ";\n"); session.stdin.close(); session.wait()
    if session.returncode == 0:
        staging = [table + "_staging" for table, _ in FILES.values()]
        raw = [table for table, _ in FILES.values()]
        maintenance = ";\n".join(
            [f"TRUNCATE bronze.{table} RESTART IDENTITY" for table in staging]
            + [f"ANALYZE bronze.{table}" for table in raw + ["ingestion_runs", "ingestion_files"]]
        ) + ";\n"
        maintenance_result = subprocess.run(cmd + ["-c", maintenance], cwd=COMPOSE, text=True, capture_output=True)
        if maintenance_result.returncode != 0:
            print(f"Bronze run {run} committed complete, but staging cleanup/ANALYZE failed; run was not marked failed.\n{maintenance_result.stderr}", file=sys.stderr)
            raise SystemExit(maintenance_result.returncode)
        print("complete"); return
    subprocess.run(cmd + ["-c", f"UPDATE bronze.ingestion_runs SET status='failed',error_message='loader failure' WHERE run_id={q(run)} AND status='running'"], cwd=COMPOSE, text=True, capture_output=True)
    print(session.stderr.read(), file=sys.stderr); raise SystemExit(session.returncode)
if __name__ == "__main__": main()
