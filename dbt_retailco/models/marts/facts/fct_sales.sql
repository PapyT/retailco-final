-- fct_sales.sql
-- Grain: one row per order line item
-- Excludes soft-deleted orders and order items

{{ config(materialized='table') }}

with order_items as (
    select * from {{ ref('stg_order_items') }}
),

orders as (
    select * from {{ ref('stg_orders') }}
    where is_deleted = false
),

dim_customer as (
    select customer_key, customer_id
    from {{ ref('dim_customer') }}
    where is_current = true
),

dim_product as (
    select product_key, product_id
    from {{ ref('dim_product') }}
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
        -- surrogate key
        {{ dbt_utils.generate_surrogate_key(['oi.order_item_id']) }}
                                                as sales_key,

        -- dimension foreign keys (surrogate)
        to_char(o.ordered_at::timestamp::date, 'YYYYMMDD')::integer as date_key,
        coalesce(dc.customer_key, 'unknown')    as customer_key,
        coalesce(dp.product_key, 'unknown')     as product_key,
        coalesce(ds.store_key,   'unknown')     as store_key,
        coalesce(de.employee_key,'unknown')     as employee_key,

        -- natural keys for reference
        o.order_id,
        oi.order_item_id                        as order_line_id,

        -- measures
        oi.quantity,
        oi.unit_price,
        oi.discount_pct,
        oi.line_total,
        oi.net_revenue

    from order_items oi
    inner join orders o
        on oi.order_id = o.order_id
    left join dim_customer dc
        on o.customer_id = dc.customer_id
    left join dim_product dp
        on oi.product_id = dp.product_id
    left join dim_store ds
        on o.store_id = ds.store_id
    left join dim_employee de
        on o.employee_id = de.employee_id
)

select * from final