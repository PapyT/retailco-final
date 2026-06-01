{% snapshot snap_customers %}

{{
    config(
        target_schema='snapshots',
        unique_key='id',
        strategy='timestamp',
        updated_at='updated_at',
        invalidate_hard_deletes=True
    )
}}

select
    id,
    data->>'firstName'         as first_name,
    data->>'lastName'          as last_name,
    data->>'email'             as email,
    data->>'phone'             as phone,
    data->>'segment'           as segment,
    data->>'tier'              as tier,
    data->>'city'              as city,
    data->>'state'             as state,
    data->>'address'           as address,
    (data->>'isDeleted')::boolean as is_deleted,
    data->>'effectiveFrom'     as effective_from,
    (updated_at at time zone 'UTC') as updated_at
from {{ source('raw', 'customers') }}

{% endsnapshot %}
