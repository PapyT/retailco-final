-- dim_store.sql

{{ config(materialized='table') }}

with staged as (
    select * from {{ ref('stg_stores') }}
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['store_id']) }}
                                            as store_key,
        store_id,
        store_name,
        city,
        state,
        region,
        store_type,
        opened_date,
        is_deleted
    from staged
)

select * from final
