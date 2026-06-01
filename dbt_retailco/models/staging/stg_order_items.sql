-- stg_order_items.sql

with source as (
    select * from {{ source('raw', 'order_items') }}
),

staged as (
    select
        id                                              as order_item_id,
        data->>'orderId'                                as order_id,
        data->>'productId'                              as product_id,
        (data->>'quantity')::numeric::integer           as quantity,
        (data->>'unitPrice')::numeric                   as unit_price,
        (data->>'discountPct')::numeric                 as discount_pct,
        (data->>'lineTotal')::numeric                   as line_total,
        (data->>'lineTotal')::numeric *
            (1 - coalesce((data->>'discountPct')::numeric, 0) / 100)
                                                        as net_revenue,
        updated_at,
        extracted_at
    from source
)

select * from staged