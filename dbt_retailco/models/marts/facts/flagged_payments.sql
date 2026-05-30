-- flagged_payments.sql
-- Data quality artifact: isolates anomalous payments
-- Zero amounts and unexplained negatives land here
-- NOT a fact table — no dimension FK relationships

{{ config(materialized='table', schema='marts') }}

with payments as (
    select * from {{ ref('stg_payments') }}
    where is_flagged = true
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['payment_id']) }}
                                            as flagged_key,
        payment_id,
        order_id,
        customer_id,
        store_id,
        payment_method_id,
        amount_paid,
        currency,
        status,
        payment_type,
        payment_classification              as flag_reason,
        updated_at                          as flagged_at
    from payments
)

select * from final
