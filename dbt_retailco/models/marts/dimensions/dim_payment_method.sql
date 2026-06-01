-- dim_payment_method.sql

{{ config(materialized='table') }}

with staged as (
    select * from {{ ref('stg_payment_methods') }}
),

final as (
    select
        {{ dbt_utils.generate_surrogate_key(['payment_method_id']) }}
                                            as payment_method_key,
        payment_method_id,
        method_name,
        provider,
        method_type,
        is_digital
    from staged
)

select * from final
