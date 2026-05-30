-- stg_stores.sql

with source as (
    select * from {{ source('raw', 'stores') }}
),

staged as (
    select
        id                                      as store_id,
        data->>'name'                           as store_name,
        data->>'city'                           as city,
        data->>'state'                          as state,
        data->>'region'                         as region,
        data->>'storeType'                      as store_type,
        (data->>'openedDate')::date             as opened_date,
        (data->>'isDeleted')::boolean           as is_deleted,
        updated_at,
        extracted_at
    from source
)

select * from staged
