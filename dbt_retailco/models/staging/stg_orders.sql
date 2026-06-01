-- stg_orders.sql

with source as (
    select * from {{ source('raw', 'orders') }}
),

staged as (
    select
        id                                          as order_id,
        data->>'customerId'                         as customer_id,
        data->>'storeId'                            as store_id,
        data->>'employeeId'                         as employee_id,
        data->>'status'                             as status,
        (data->>'orderedAt')::timestamptz           as ordered_at,
        (data->>'paidAt')::timestamptz              as paid_at,
        (data->>'shippedAt')::timestamptz           as shipped_at,
        (data->>'deliveredAt')::timestamptz         as delivered_at,
        (data->>'cancelledAt')::timestamptz         as cancelled_at,
        (data->>'totalAmount')::numeric             as total_amount,
        (data->>'isDeleted')::boolean               as is_deleted,
        updated_at,
        extracted_at
    from source
)

select * from staged
