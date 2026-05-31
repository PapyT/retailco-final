-- tests/assert_fct_inventory_non_negative_stock.sql
-- Warns (does not fail) when stock goes negative
-- This is expected when movements start mid-history without opening balances

{{ config(severity='warn') }}

select *
from {{ ref('fct_inventory_daily') }}
where quantity_on_hand < 0