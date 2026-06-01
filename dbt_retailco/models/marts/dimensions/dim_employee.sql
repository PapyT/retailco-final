-- dim_employee.sql

{{ config(materialized='table') }}

with staged as (
    select * from {{ ref('stg_employees') }}
),

stores as (
    select store_key, store_id from {{ ref('dim_store') }}
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['e.employee_id']) }}
                                            as employee_key,
        e.employee_id,
        e.first_name,
        e.last_name,
        e.full_name,
        e.role,
        e.department,
        e.store_id,
        s.store_key,
        e.is_deleted
    from staged e
    left join stores s on e.store_id = s.store_id
)

select * from final
