-- tests/assert_fct_payments_no_flagged.sql
-- Custom test: no flagged payments should exist in fct_payments
-- They must all be in flagged_payments table instead

select *
from {{ ref('fct_payments') }}
where amount_paid = 0
   or (amount_paid < 0 and is_refund = false)
