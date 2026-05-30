-- dim_customer.sql
{{ config(materialized='table') }}

with snapshot as (
    select * from {{ ref('snap_customers') }}
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['id', 'dbt_valid_from']) }}
                                            as customer_key,
        id                                  as customer_id,
        first_name,
        last_name,
        first_name || ' ' || last_name      as full_name,
        email,
        phone,
        segment,
        tier,
        city,
        state,
        address,
        is_deleted,
        effective_from,
        dbt_valid_from                      as valid_from,
        dbt_valid_to                        as valid_to,
        dbt_valid_to is null                as is_current
    from snapshot
)

select * from final