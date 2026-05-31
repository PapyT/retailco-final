-- fct_payments.sql
-- Grain: one row per payment event
-- Excludes flagged (zero or unexplained negative) payments

{{ config(materialized='table') }}

with payments as (
    select * from {{ ref('stg_payments') }}
    -- exclude flagged payments — they go to flagged_payments table
    where is_flagged = false
),

dim_customer as (
    select customer_key, customer_id
    from {{ ref('dim_customer') }}
    where is_current = true
),

dim_store as (
    select store_key, store_id
    from {{ ref('dim_store') }}
),

dim_payment_method as (
    select payment_method_key, payment_method_id
    from {{ ref('dim_payment_method') }}
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['p.payment_id']) }}
                                                    as payment_key,

        -- dimension foreign keys
        to_char(coalesce(p.updated_at, p.extracted_at)::timestamp::date, 'YYYYMMDD')::integer as date_key,
        coalesce(dc.customer_key, 'unknown')         as customer_key,
        coalesce(ds.store_key,    'unknown')         as store_key,
        coalesce(pm.payment_method_key, 'unknown')   as payment_method_key,

        -- natural keys
        p.payment_id,
        p.order_id,

        -- measures
        p.amount_paid,
        p.currency,
        p.status,
        p.payment_type,
        p.is_refund,
        p.payment_classification

    from payments p
    left join dim_customer dc
        on p.customer_id = dc.customer_id
    left join dim_store ds
        on p.store_id = ds.store_id
    left join dim_payment_method pm
        on p.payment_method_id = pm.payment_method_id
)

select * from final
