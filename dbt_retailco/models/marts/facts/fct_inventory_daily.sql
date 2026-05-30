-- fct_inventory_daily.sql
-- Grain: one row per product × store × day
-- Built by aggregating inventory_movements into daily snapshots

{{ config(materialized='table') }}

with movements as (
    select * from {{ ref('stg_inventory_movements') }}
),

-- Aggregate movements to daily grain
daily_movements as (
    select
        product_id,
        store_id,
        moved_at::date                          as movement_date,
        sum(case when direction = 'inbound'  then quantity else 0 end)
                                                as quantity_received,
        sum(case when direction = 'outbound' then abs(quantity) else 0 end)
                                                as quantity_sold,
        sum(quantity)                           as net_movement
    from movements
    group by product_id, store_id, moved_at::date
),

-- Running total (closing stock) using window function
with_running_total as (
    select
        *,
        sum(net_movement) over (
            partition by product_id, store_id
            order by movement_date
            rows between unbounded preceding and current row
        )                                       as quantity_on_hand
    from daily_movements
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

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['m.product_id', 'm.store_id', 'm.movement_date']) }}
                                                as inventory_key,

        -- dimension foreign keys
        to_char(m.movement_date, 'YYYYMMDD')::integer
                                                as date_key,
        coalesce(dp.product_key, 'unknown')     as product_key,
        coalesce(ds.store_key,   'unknown')     as store_key,

        -- measures
        m.quantity_on_hand,
        m.quantity_received,
        m.quantity_sold,
        m.net_movement

    from with_running_total m
    left join dim_product dp on m.product_id = dp.product_id
    left join dim_store ds   on m.store_id   = ds.store_id
)

select * from final
