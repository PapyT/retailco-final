-- stg_employees.sql

with source as (
    select * from {{ source('raw', 'employees') }}
),

staged as (
    select
        id                                      as employee_id,
        data->>'firstName'                      as first_name,
        data->>'lastName'                       as last_name,
        (data->>'firstName') || ' ' ||
        (data->>'lastName')                     as full_name,
        data->>'role'                           as role,
        data->>'department'                     as department,
        data->>'storeId'                        as store_id,
        (data->>'isDeleted')::boolean           as is_deleted,
        updated_at,
        extracted_at
    from source
)

select * from staged
