-- stg_inventory_movements.sql

with source as (
    select * from {{ source('raw', 'inventory_movements') }}
),

staged as (
    select
        id                                          as movement_id,
        data->>'productId'                          as product_id,
        data->>'storeId'                            as store_id,
        data->>'movementType'                       as movement_type,
        (data->>'quantity')::integer                as quantity,
        -- positive = inbound (restock/return), negative = outbound (sale/adjustment)
        case
            when (data->>'quantity')::integer > 0 then 'inbound'
            else 'outbound'
        end                                         as direction,
        (data->>'movedAt')::timestamptz             as moved_at,
        updated_at,
        extracted_at
    from source
)

select * from staged
