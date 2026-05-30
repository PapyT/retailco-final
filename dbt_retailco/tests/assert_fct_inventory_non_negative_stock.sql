-- tests/assert_fct_inventory_non_negative_stock.sql
-- Custom test: quantity_on_hand should not go negative
-- Negative stock indicates a data quality issue upstream

select *
from {{ ref('fct_inventory_daily') }}
where quantity_on_hand < 0
