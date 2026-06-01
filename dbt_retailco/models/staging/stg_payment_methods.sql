-- stg_payment_methods.sql

with source as (
    select * from {{ source('raw', 'payment_methods') }}
),

staged as (
    select
        id                                      as payment_method_id,
        data->>'name'                           as method_name,
        data->>'provider'                       as provider,
        data->>'type'                           as method_type,
        (data->>'isDigital')::boolean           as is_digital,
        updated_at,
        extracted_at
    from source
)

select * from staged
