-- tests/assert_fct_order_lifecycle_one_row_per_order.sql
-- Custom test: each order_id must appear exactly once in fct_order_lifecycle

select order_id, count(*) as row_count
from {{ ref('fct_order_lifecycle') }}
group by order_id
having count(*) > 1
