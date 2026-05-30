-- stg_customers.sql
-- Casts columns, renames to snake_case, keeps soft-deleted rows for SCD2 history

with source as (
    select * from {{ source('raw', 'customers') }}
),

staged as (
    select
        id                                      as customer_id,
        data->>'firstName'                      as first_name,
        data->>'lastName'                       as last_name,
        (data->>'firstName') || ' ' ||
        (data->>'lastName')                     as full_name,
        data->>'email'                          as email,
        data->>'phone'                          as phone,
        data->>'segment'                        as segment,
        data->>'tier'                           as tier,
        data->>'city'                           as city,
        data->>'state'                          as state,
        data->>'address'                        as address,
        (data->>'isDeleted')::boolean           as is_deleted,
        (data->>'effectiveFrom')::timestamptz   as effective_from,
        updated_at,
        extracted_at
    from source
)

select * from staged
