\set ON_ERROR_STOP on

-- P2 is added after the already-issued application migrations to preserve the
-- repository's forward-only migration history. Bronze remains raw text plus
-- immutable source-run lineage; all casts belong to dbt Silver models.
SET ROLE hidden_dissatisfaction_owner;

CREATE TABLE bronze.ingestion_runs (
  run_id uuid PRIMARY KEY,
  status text NOT NULL CHECK (status IN ('STARTED', 'COMPLETE', 'FAILED')),
  manifest jsonb NOT NULL CHECK (jsonb_typeof(manifest) = 'object'),
  started_at timestamptz NOT NULL DEFAULT now(),
  completed_at timestamptz,
  failed_at timestamptz,
  failure_reason text,
  CHECK (
    (status = 'STARTED' AND completed_at IS NULL AND failed_at IS NULL)
    OR (status = 'COMPLETE' AND completed_at IS NOT NULL AND failed_at IS NULL)
    OR (status = 'FAILED' AND failed_at IS NOT NULL)
  )
);

CREATE TABLE bronze.customers (
  run_id uuid NOT NULL REFERENCES bronze.ingestion_runs(run_id),
  customer_id text NOT NULL, customer_unique_id text, customer_zip_code_prefix text,
  customer_city text, customer_state text
);
CREATE TABLE bronze.sellers (
  run_id uuid NOT NULL REFERENCES bronze.ingestion_runs(run_id),
  seller_id text NOT NULL, seller_zip_code_prefix text, seller_city text, seller_state text
);
CREATE TABLE bronze.products (
  run_id uuid NOT NULL REFERENCES bronze.ingestion_runs(run_id),
  product_id text NOT NULL, product_category_name text, product_name_lenght text,
  product_description_lenght text, product_photos_qty text, product_weight_g text,
  product_length_cm text, product_height_cm text, product_width_cm text
);
CREATE TABLE bronze.orders (
  run_id uuid NOT NULL REFERENCES bronze.ingestion_runs(run_id),
  order_id text NOT NULL, customer_id text, order_status text, order_purchase_timestamp text,
  order_approved_at text, order_delivered_carrier_date text,
  order_delivered_customer_date text, order_estimated_delivery_date text
);
CREATE TABLE bronze.order_items (
  run_id uuid NOT NULL REFERENCES bronze.ingestion_runs(run_id),
  order_id text NOT NULL, order_item_id text, product_id text, seller_id text,
  shipping_limit_date text, price text, freight_value text
);
CREATE TABLE bronze.order_payments (
  run_id uuid NOT NULL REFERENCES bronze.ingestion_runs(run_id),
  order_id text NOT NULL, payment_sequential text, payment_type text,
  payment_installments text, payment_value text
);
CREATE TABLE bronze.order_reviews (
  run_id uuid NOT NULL REFERENCES bronze.ingestion_runs(run_id),
  review_id text NOT NULL, order_id text NOT NULL, review_score text,
  review_comment_title text, review_comment_message text, review_creation_date text,
  review_answer_timestamp text
);
CREATE TABLE bronze.geolocation (
  run_id uuid NOT NULL REFERENCES bronze.ingestion_runs(run_id),
  geolocation_zip_code_prefix text, geolocation_lat text, geolocation_lng text,
  geolocation_city text, geolocation_state text
);
CREATE TABLE bronze.category_translation (
  run_id uuid NOT NULL REFERENCES bronze.ingestion_runs(run_id),
  product_category_name text, product_category_name_english text
);

CREATE INDEX bronze_ingestion_runs_complete_idx ON bronze.ingestion_runs(run_id)
  WHERE status = 'COMPLETE';
CREATE INDEX bronze_customers_run_idx ON bronze.customers(run_id);
CREATE INDEX bronze_sellers_run_idx ON bronze.sellers(run_id);
CREATE INDEX bronze_products_run_idx ON bronze.products(run_id);
CREATE INDEX bronze_orders_run_idx ON bronze.orders(run_id);
CREATE INDEX bronze_order_items_run_idx ON bronze.order_items(run_id);
CREATE INDEX bronze_order_payments_run_idx ON bronze.order_payments(run_id);
CREATE INDEX bronze_order_reviews_run_idx ON bronze.order_reviews(run_id);
CREATE INDEX bronze_geolocation_run_idx ON bronze.geolocation(run_id);
CREATE INDEX bronze_category_translation_run_idx ON bronze.category_translation(run_id);

RESET ROLE;
REVOKE ALL ON ALL TABLES IN SCHEMA bronze FROM PUBLIC, app_runtime, reader;
GRANT SELECT, INSERT, UPDATE ON bronze.ingestion_runs TO ingest_writer;
GRANT SELECT, INSERT ON bronze.customers, bronze.sellers, bronze.products,
  bronze.orders, bronze.order_items, bronze.order_payments, bronze.order_reviews,
  bronze.geolocation, bronze.category_translation TO ingest_writer;
GRANT SELECT ON ALL TABLES IN SCHEMA bronze TO transform_runner;
