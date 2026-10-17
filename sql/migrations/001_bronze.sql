\set ON_ERROR_STOP on
BEGIN;
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE TABLE IF NOT EXISTS bronze.ingestion_runs (
  run_id uuid PRIMARY KEY, manifest_sha256 text NOT NULL, started_at timestamptz NOT NULL DEFAULT now(),
  completed_at timestamptz, status text NOT NULL CHECK (status IN ('running','complete','failed')), error_message text
);
CREATE TABLE IF NOT EXISTS bronze.ingestion_files (
  run_id uuid NOT NULL REFERENCES bronze.ingestion_runs(run_id), file_name text NOT NULL,
  expected_sha256 text NOT NULL, actual_sha256 text, expected_rows bigint, loaded_rows bigint,
  status text NOT NULL DEFAULT 'pending', PRIMARY KEY (run_id,file_name)
);
CREATE TABLE IF NOT EXISTS bronze.load_exceptions (
  exception_id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, run_id uuid REFERENCES bronze.ingestion_runs,
  file_name text, source_row_number bigint, error_message text NOT NULL, details text, created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS bronze.customers (customer_id text, customer_unique_id text, customer_zip_code_prefix text, customer_city text, customer_state text, run_id uuid NOT NULL REFERENCES bronze.ingestion_runs, source_row_number bigint NOT NULL, ingested_at timestamptz NOT NULL, PRIMARY KEY(run_id,source_row_number));
CREATE TABLE IF NOT EXISTS bronze.geolocation (geolocation_zip_code_prefix text, geolocation_lat text, geolocation_lng text, geolocation_city text, geolocation_state text, run_id uuid NOT NULL REFERENCES bronze.ingestion_runs, source_row_number bigint NOT NULL, ingested_at timestamptz NOT NULL, PRIMARY KEY(run_id,source_row_number));
CREATE TABLE IF NOT EXISTS bronze.order_items (order_id text, order_item_id text, product_id text, seller_id text, shipping_limit_date text, price text, freight_value text, run_id uuid NOT NULL REFERENCES bronze.ingestion_runs, source_row_number bigint NOT NULL, ingested_at timestamptz NOT NULL, PRIMARY KEY(run_id,source_row_number));
CREATE TABLE IF NOT EXISTS bronze.order_payments (order_id text, payment_sequential text, payment_type text, payment_installments text, payment_value text, run_id uuid NOT NULL REFERENCES bronze.ingestion_runs, source_row_number bigint NOT NULL, ingested_at timestamptz NOT NULL, PRIMARY KEY(run_id,source_row_number));
CREATE TABLE IF NOT EXISTS bronze.order_reviews (review_id text, order_id text, review_score text, review_comment_title text, review_comment_message text, review_creation_date text, review_answer_timestamp text, run_id uuid NOT NULL REFERENCES bronze.ingestion_runs, source_row_number bigint NOT NULL, ingested_at timestamptz NOT NULL, PRIMARY KEY(run_id,source_row_number));
CREATE TABLE IF NOT EXISTS bronze.orders (order_id text, customer_id text, order_status text, order_purchase_timestamp text, order_approved_at text, order_delivered_carrier_date text, order_delivered_customer_date text, order_estimated_delivery_date text, run_id uuid NOT NULL REFERENCES bronze.ingestion_runs, source_row_number bigint NOT NULL, ingested_at timestamptz NOT NULL, PRIMARY KEY(run_id,source_row_number));
CREATE TABLE IF NOT EXISTS bronze.products (product_id text, product_category_name text, product_name_lenght text, product_description_lenght text, product_photos_qty text, product_weight_g text, product_length_cm text, product_height_cm text, product_width_cm text, run_id uuid NOT NULL REFERENCES bronze.ingestion_runs, source_row_number bigint NOT NULL, ingested_at timestamptz NOT NULL, PRIMARY KEY(run_id,source_row_number));
CREATE TABLE IF NOT EXISTS bronze.sellers (seller_id text, seller_zip_code_prefix text, seller_city text, seller_state text, run_id uuid NOT NULL REFERENCES bronze.ingestion_runs, source_row_number bigint NOT NULL, ingested_at timestamptz NOT NULL, PRIMARY KEY(run_id,source_row_number));
CREATE TABLE IF NOT EXISTS bronze.category_translation (product_category_name text, product_category_name_english text, run_id uuid NOT NULL REFERENCES bronze.ingestion_runs, source_row_number bigint NOT NULL, ingested_at timestamptz NOT NULL, PRIMARY KEY(run_id,source_row_number));

CREATE TABLE IF NOT EXISTS bronze.customers_staging (stage_row_number bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, customer_id text,customer_unique_id text,customer_zip_code_prefix text,customer_city text,customer_state text);
CREATE TABLE IF NOT EXISTS bronze.geolocation_staging (stage_row_number bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, geolocation_zip_code_prefix text,geolocation_lat text,geolocation_lng text,geolocation_city text,geolocation_state text);
CREATE TABLE IF NOT EXISTS bronze.order_items_staging (stage_row_number bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, order_id text,order_item_id text,product_id text,seller_id text,shipping_limit_date text,price text,freight_value text);
CREATE TABLE IF NOT EXISTS bronze.order_payments_staging (stage_row_number bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, order_id text,payment_sequential text,payment_type text,payment_installments text,payment_value text);
CREATE TABLE IF NOT EXISTS bronze.order_reviews_staging (stage_row_number bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, review_id text,order_id text,review_score text,review_comment_title text,review_comment_message text,review_creation_date text,review_answer_timestamp text);
CREATE TABLE IF NOT EXISTS bronze.orders_staging (stage_row_number bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, order_id text,customer_id text,order_status text,order_purchase_timestamp text,order_approved_at text,order_delivered_carrier_date text,order_delivered_customer_date text,order_estimated_delivery_date text);
CREATE TABLE IF NOT EXISTS bronze.products_staging (stage_row_number bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, product_id text,product_category_name text,product_name_lenght text,product_description_lenght text,product_photos_qty text,product_weight_g text,product_length_cm text,product_height_cm text,product_width_cm text);
CREATE TABLE IF NOT EXISTS bronze.sellers_staging (stage_row_number bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, seller_id text,seller_zip_code_prefix text,seller_city text,seller_state text);
CREATE TABLE IF NOT EXISTS bronze.category_translation_staging (stage_row_number bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, product_category_name text,product_category_name_english text);

GRANT SELECT ON ALL TABLES IN SCHEMA bronze TO transform_runner;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA bronze TO ingest_writer;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA bronze TO ingest_writer;
COMMIT;
