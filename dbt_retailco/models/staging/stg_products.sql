-- stg_products.sql
-- Casts price strings to numeric, renames to snake_case

with source as (
    select * from {{ source('raw', 'products') }}
),

staged as (
    select
        id                                          as product_id,
        data->>'sku'                                as sku,
        data->>'name'                               as product_name,
        data->>'category'                           as category,
        data->>'subcategory'                        as subcategory,
        (data->>'costPrice')::numeric               as cost_price,
        (data->>'sellingPrice')::numeric            as selling_price,
        data->>'supplierId'                         as supplier_id,
        (data->>'effectiveFrom')::timestamptz       as effective_from,
        (data->>'isDeleted')::boolean               as is_deleted,
        updated_at,
        extracted_at
    from source
)

select * from staged
