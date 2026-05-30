-- dim_date.sql
-- Generates a date spine covering 2023-01-01 to 2026-12-31
-- Includes Nigerian public holidays

{{ config(materialized='table') }}

with date_spine as (
    select generate_series(
        '2023-01-01'::date,
        '2026-12-31'::date,
        '1 day'::interval
    )::date as full_date
),

nigerian_holidays as (
    select * from (values
        ('2023-01-01'::date, 'New Year''s Day'),
        ('2023-01-02'::date, 'New Year Holiday'),
        ('2023-04-07'::date, 'Good Friday'),
        ('2023-04-10'::date, 'Easter Monday'),
        ('2023-04-21'::date, 'Eid al-Fitr'),
        ('2023-05-01'::date, 'Workers Day'),
        ('2023-06-12'::date, 'Democracy Day'),
        ('2023-06-28'::date, 'Eid al-Adha'),
        ('2023-10-01'::date, 'Independence Day'),
        ('2023-12-25'::date, 'Christmas Day'),
        ('2023-12-26'::date, 'Boxing Day'),
        ('2024-01-01'::date, 'New Year''s Day'),
        ('2024-03-29'::date, 'Good Friday'),
        ('2024-04-01'::date, 'Easter Monday'),
        ('2024-04-10'::date, 'Eid al-Fitr'),
        ('2024-05-01'::date, 'Workers Day'),
        ('2024-06-12'::date, 'Democracy Day'),
        ('2024-06-17'::date, 'Eid al-Adha'),
        ('2024-10-01'::date, 'Independence Day'),
        ('2024-12-25'::date, 'Christmas Day'),
        ('2024-12-26'::date, 'Boxing Day'),
        ('2025-01-01'::date, 'New Year''s Day'),
        ('2025-03-31'::date, 'Eid al-Fitr'),
        ('2025-04-18'::date, 'Good Friday'),
        ('2025-04-21'::date, 'Easter Monday'),
        ('2025-05-01'::date, 'Workers Day'),
        ('2025-06-06'::date, 'Eid al-Adha'),
        ('2025-06-12'::date, 'Democracy Day'),
        ('2025-10-01'::date, 'Independence Day'),
        ('2025-12-25'::date, 'Christmas Day'),
        ('2025-12-26'::date, 'Boxing Day'),
        ('2026-01-01'::date, 'New Year''s Day'),
        ('2026-03-20'::date, 'Eid al-Fitr'),
        ('2026-04-03'::date, 'Good Friday'),
        ('2026-04-06'::date, 'Easter Monday'),
        ('2026-05-01'::date, 'Workers Day'),
        ('2026-05-27'::date, 'Eid al-Adha'),
        ('2026-06-12'::date, 'Democracy Day'),
        ('2026-10-01'::date, 'Independence Day'),
        ('2026-12-25'::date, 'Christmas Day'),
        ('2026-12-26'::date, 'Boxing Day')
    ) as h(holiday_date, holiday_name)
),

final as (
    select
        -- surrogate key as integer YYYYMMDD
        to_char(d.full_date, 'YYYYMMDD')::integer   as date_key,
        d.full_date,
        extract(year  from d.full_date)::integer    as year,
        extract(quarter from d.full_date)::integer  as quarter,
        extract(month from d.full_date)::integer    as month,
        to_char(d.full_date, 'Month')               as month_name,
        extract(week  from d.full_date)::integer    as week,
        extract(dow   from d.full_date)::integer    as day_of_week,
        to_char(d.full_date, 'Day')                 as day_name,
        extract(day   from d.full_date)::integer    as day_of_month,
        extract(doy   from d.full_date)::integer    as day_of_year,
        -- weekend: Saturday (6) or Sunday (0)
        extract(dow from d.full_date) in (0, 6)     as is_weekend,
        h.holiday_name is not null                  as is_public_holiday,
        h.holiday_name                              as holiday_name,
        -- quarter label e.g. 'Q1 2024'
        'Q' || extract(quarter from d.full_date)::text
            || ' ' || extract(year from d.full_date)::text
                                                    as quarter_label,
        -- month label e.g. '2024-01'
        to_char(d.full_date, 'YYYY-MM')             as month_label
    from date_spine d
    left join nigerian_holidays h
        on d.full_date = h.holiday_date
)

select * from final
