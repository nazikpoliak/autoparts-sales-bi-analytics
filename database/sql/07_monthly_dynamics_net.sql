-- 07_monthly_dynamics_net.sql
-- Question: how do gross revenue, refunds, net revenue and net margin change month by month?
-- Grain of the result: one row per calendar month of the period.
-- Definitions: see docs/metrics.md (gross by order_date, refunds by return_date, Completed orders only).
-- Pitfall: aggregate orders and returns SEPARATELY at their own grain, then join by month (fan-out).
-- Checks (below the query):
--   1. sum(gross) over all months = total gross from a single query on the whole DB
--   2. sum(refunds) over all months = total refunds
--   3. net = gross - refunds in every row
--   4. number of months = 30 (validate REAL07)

with gross as (
    select
        date_trunc('month', o.order_date)::date as month,
        round(sum(oi.quantity * oi.unit_sale_price - oi.discount_amount), 2) as gross,
        round(sum(oi.quantity * oi.unit_cost), 2) as cogs
    from orders o
    join order_items oi on o.order_id = oi.order_id
    join order_statuses os on o.order_status_id = os.order_status_id
    where os.status_name = 'Completed'
    group by 1
),
refunds as (
    select
        date_trunc('month', r.return_date)::date as month,
        round(sum(ri.refund_unit_price * ri.quantity), 2) as refunds,
        round(sum(ri.quantity * oi.unit_cost), 2) as returned_cogs
    from returns r
    join return_items ri on r.return_id = ri.return_id
    join order_items oi on oi.order_item_id = ri.order_item_id
    group by 1
)
select
    g.month,
    g.gross,
    coalesce(r.refunds, 0) as refunds,
    g.cogs - coalesce(r.returned_cogs, 0) as net_cogs,
    round((g.gross - coalesce(r.refunds, 0)) - (g.cogs - coalesce(r.returned_cogs, 0)), 2) as net_margin,
    case when ((g.gross - coalesce(r.refunds, 0)) * 100) = 0 then null else round(((g.gross - coalesce(r.refunds, 0)) - (g.cogs - coalesce(r.returned_cogs, 0))) / (g.gross - coalesce(r.refunds, 0)) * 100, 2) end as net_margin_pct
from gross g
left join refunds r on g.month = r.month
order by g.month;