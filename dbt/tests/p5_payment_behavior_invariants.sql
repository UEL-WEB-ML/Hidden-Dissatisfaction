select source_run_id, product_item_id from {{ ref('int_p5_payment_behavior') }}
where payment_type_count < 0 or payment_installments_mean < 0 or installment_amount < 0
   or payment_to_order_value_ratio < 0 or credit_card_payment_share not between 0 and 1
   or voucher_payment_share not between 0 and 1 or payment_type_hhi < 0 or payment_type_hhi > 1
   or split_payment_flag not in (0, 1) or mixed_payment_type_flag not in (0, 1)
   or credit_card_payment_flag not in (0, 1) or boleto_payment_flag not in (0, 1)
   or voucher_payment_flag not in (0, 1) or debit_card_payment_flag not in (0, 1)
   or payment_order_value_zero_flag not in (0, 1) or primary_payment_type is null
