{% snapshot snap_products %}

{{
    config(
        target_schema='snapshots',
        unique_key='id',
        strategy='timestamp',
        updated_at='updated_at',
        invalidate_hard_deletes=True
    )
}}

select
    id,
    data->>'sku'               as sku,
    data->>'name'              as product_name,
    data->>'category'          as category,
    data->>'subcategory'       as subcategory,
    (data->>'costPrice')::numeric   as cost_price,
    (data->>'sellingPrice')::numeric as selling_price,
    data->>'supplierId'        as supplier_id,
    data->>'effectiveFrom'     as effective_from,
    (data->>'isDeleted')::boolean   as is_deleted,
    (updated_at at time zone 'UTC') as updated_at
from {{ source('raw', 'products') }}

{% endsnapshot %}
