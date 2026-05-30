-- dim_product.sql
-- Built from the dbt snapshot which handles SCD2 history

{{ config(materialized='table') }}

with snapshot as (
    select * from {{ ref('snap_products') }}
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['id', 'dbt_valid_from']) }}
                                            as product_key,
        id                                  as product_id,
        sku,
        product_name,
        category,
        subcategory,
        cost_price,
        selling_price,
        supplier_id,
        effective_from,
        is_deleted,
        dbt_valid_from                      as valid_from,
        dbt_valid_to                        as valid_to,
        dbt_valid_to is null                as is_current
    from snapshot
)

select * from final