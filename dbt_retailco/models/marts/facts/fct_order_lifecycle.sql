-- fct_order_lifecycle.sql
-- Grain: one row per order
-- Accumulating snapshot: status timestamps fill in as the order progresses

{{ config(materialized='table') }}

with orders as (
    select * from {{ ref('stg_orders') }}
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

dim_employee as (
    select employee_key, employee_id
    from {{ ref('dim_employee') }}
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['o.order_id']) }}
                                                        as lifecycle_key,

        -- natural key
        o.order_id,

        -- dimension foreign keys
        coalesce(dc.customer_key,  'unknown')           as customer_key,
        coalesce(ds.store_key,     'unknown')           as store_key,
        coalesce(de.employee_key,  'unknown')           as employee_key,

        -- milestone date keys (NULL until that status is reached)
        to_char(o.ordered_at,   'YYYYMMDD')::integer    as created_date_key,
        to_char(o.paid_at,      'YYYYMMDD')::integer    as paid_date_key,
        to_char(o.shipped_at,   'YYYYMMDD')::integer    as shipped_date_key,
        to_char(o.delivered_at, 'YYYYMMDD')::integer    as delivered_date_key,
        to_char(o.cancelled_at, 'YYYYMMDD')::integer    as cancelled_date_key,

        -- current status
        o.status                                        as current_status,
        o.is_deleted                                    as is_cancelled,

        -- measures
        o.total_amount                                  as order_total,

        -- lag metrics (NULL until both timestamps exist)
        extract(epoch from (o.delivered_at - o.ordered_at))
            / 86400                                     as days_to_deliver,
        extract(epoch from (o.paid_at - o.ordered_at))
            / 3600                                      as hours_to_pay,
        extract(epoch from (o.shipped_at - o.paid_at))
            / 86400                                     as days_to_ship

    from orders o
    left join dim_customer dc  on o.customer_id  = dc.customer_id
    left join dim_store ds     on o.store_id     = ds.store_id
    left join dim_employee de  on o.employee_id  = de.employee_id
)

select * from final
