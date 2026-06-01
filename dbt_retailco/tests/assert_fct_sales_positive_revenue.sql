-- tests/assert_fct_sales_positive_revenue.sql
-- Custom test: net_revenue on sales lines should never be negative
-- (refunds are handled in fct_payments, not fct_sales)

select *
from {{ ref('fct_sales') }}
where net_revenue < 0
