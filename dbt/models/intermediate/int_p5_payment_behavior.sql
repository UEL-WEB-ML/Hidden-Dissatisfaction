{{ config(materialized='table', schema='intermediate', indexes=[{'columns': ['source_run_id', 'product_item_id'], 'unique': true}]) }}

-- Payment records are first reduced to one row/order. This prevents an order
-- with multiple payment rows from multiplying its product-item rows.
with cohort_orders as (
    select distinct source_run_id, order_id from {{ ref('int_p4_cohort') }}
), order_values as (
    select source_run_id, order_id, sum(item_plus_freight_amount) as order_item_value_total
    from {{ ref('int_p4_cohort') }} group by source_run_id, order_id
), type_values as (
    select source_run_id, order_id, payment_type, sum(payment_value) as payment_type_value,
           min(payment_sequential) as first_payment_sequential
    from {{ ref('stg_order_payments') }} group by source_run_id, order_id, payment_type
), ranked_types as (
    select *, row_number() over (
        partition by source_run_id, order_id
        order by payment_type_value desc, first_payment_sequential, payment_type
    ) as type_rank
    from type_values
), payment_totals as (
    select p.source_run_id, p.order_id, count(*)::int as payment_record_count,
           count(distinct p.payment_type)::int as payment_type_count,
           sum(p.payment_value) as payment_value_total,
           avg(p.payment_installments) as payment_installments_mean,
           max(p.payment_installments)::int as payment_installments_max,
           sum(case when p.payment_type = 'credit_card' then p.payment_value else 0 end) as credit_card_payment_value,
           sum(case when p.payment_type = 'voucher' then p.payment_value else 0 end) as voucher_payment_value,
           bool_or(p.payment_type = 'credit_card')::int as credit_card_payment_flag,
           bool_or(p.payment_type = 'boleto')::int as boleto_payment_flag,
           bool_or(p.payment_type = 'voucher')::int as voucher_payment_flag,
           bool_or(p.payment_type = 'debit_card')::int as debit_card_payment_flag
    from {{ ref('stg_order_payments') }} p group by p.source_run_id, p.order_id
), payment_hhi as (
    select v.source_run_id, v.order_id,
           sum(power(v.payment_type_value / nullif(t.payment_value_total, 0), 2)) as payment_type_hhi
    from type_values v join payment_totals t using (source_run_id, order_id)
    group by v.source_run_id, v.order_id
), order_features as (
    select o.source_run_id, o.order_id,
           coalesce(t.payment_type_count, 0)::int as payment_type_count,
           coalesce(t.payment_installments_mean, 0) as payment_installments_mean,
           coalesce(t.payment_value_total / nullif(t.payment_installments_max, 0), 0) as installment_amount,
           t.payment_value_total / nullif(v.order_item_value_total, 0) as payment_to_order_value_ratio,
           coalesce(t.credit_card_payment_value / nullif(t.payment_value_total, 0), 0) as credit_card_payment_share,
           coalesce(t.voucher_payment_value / nullif(t.payment_value_total, 0), 0) as voucher_payment_share,
           coalesce(h.payment_type_hhi, 0) as payment_type_hhi,
           (coalesce(t.payment_record_count, 0) > 1)::int as split_payment_flag,
           (coalesce(t.payment_type_count, 0) > 1)::int as mixed_payment_type_flag,
           coalesce(t.credit_card_payment_flag, 0)::int as credit_card_payment_flag,
           coalesce(t.boleto_payment_flag, 0)::int as boleto_payment_flag,
           coalesce(t.voucher_payment_flag, 0)::int as voucher_payment_flag,
           coalesce(t.debit_card_payment_flag, 0)::int as debit_card_payment_flag,
           (v.order_item_value_total = 0)::int as payment_order_value_zero_flag,
           coalesce(r.payment_type, '(missing)') as primary_payment_type
    from cohort_orders o join order_values v using (source_run_id, order_id)
    left join payment_totals t using (source_run_id, order_id)
    left join payment_hhi h using (source_run_id, order_id)
    left join ranked_types r on r.source_run_id = o.source_run_id and r.order_id = o.order_id and r.type_rank = 1
)
select c.source_run_id, c.product_item_id, f.payment_type_count, f.payment_installments_mean,
       f.installment_amount, f.payment_to_order_value_ratio, f.credit_card_payment_share,
       f.voucher_payment_share, f.payment_type_hhi, f.split_payment_flag,
       f.mixed_payment_type_flag, f.credit_card_payment_flag, f.boleto_payment_flag,
       f.voucher_payment_flag, f.debit_card_payment_flag, f.payment_order_value_zero_flag,
       f.primary_payment_type, 'p5-payment-behavior-v1' as payment_behavior_version
from {{ ref('int_p4_cohort') }} c join order_features f using (source_run_id, order_id)
