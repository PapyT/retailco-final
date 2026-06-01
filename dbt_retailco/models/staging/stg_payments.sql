-- stg_payments.sql
-- Classifies payments into: normal, refund, flagged (zero or unexplained negative)

with source as (
    select * from {{ source('raw', 'payments') }}
),

staged as (
    select
        id                                          as payment_id,
        data->>'orderId'                            as order_id,
        data->>'customerId'                         as customer_id,
        data->>'storeId'                            as store_id,
        data->>'paymentMethodId'                    as payment_method_id,
        (data->>'amountPaid')::numeric              as amount_paid,
        data->>'currency'                           as currency,
        data->>'status'                             as status,
        data->>'paymentType'                        as payment_type,

        -- Classify the payment
        case
            when (data->>'amountPaid')::numeric > 0
                then 'payment'
            when (data->>'amountPaid')::numeric < 0
                 and lower(data->>'paymentType') = 'refund'
                then 'refund'
            when (data->>'amountPaid')::numeric = 0
                then 'flagged_zero'
            else 'flagged_unexplained_negative'
        end                                         as payment_classification,

        -- Convenience booleans
        (data->>'amountPaid')::numeric < 0
            and lower(data->>'paymentType') = 'refund'
                                                    as is_refund,

        (data->>'amountPaid')::numeric = 0
            or (
                (data->>'amountPaid')::numeric < 0
                and lower(data->>'paymentType') != 'refund'
            )                                       as is_flagged,

        updated_at,
        extracted_at
    from source
)

select * from staged
