-- 08_kpi_snapshot.sql   (Task 1: KPI snapshot for the whole period)
-- Question: how much did we earn over the whole period? This is the REFERENCE row: every later query must reconcile to it.
-- Grain of the result: ONE row for the whole DB.
-- Definitions: docs/metrics.md (Completed orders only; refunds and returned COGS are subtracted in full, restock assumed).
--   * AOV          = gross revenue / Completed orders (before refunds)
--   * return_rate  = Completed orders that have a return / Completed orders   (by ORDER, whole period)
--   * refund_share = refunds / gross revenue                                  (by AMOUNT)
-- Pitfall (fan-out): sales lines and return lines are summed in separate CTEs, never joined to each other before aggregation.

with sales as (
    select
        count(distinct o.order_id)                                   as orders,
        sum(oi.quantity * oi.unit_sale_price - oi.discount_amount)   as gross,
        sum(oi.quantity * oi.unit_cost)                              as cogs
    from orders o
    join order_items    oi on oi.order_id = o.order_id
    join order_statuses os on os.order_status_id = o.order_status_id
    where os.status_name = 'Completed'
),
returned as (
    select
        count(distinct r.order_id)                                   as returned_orders,
        sum(ri.quantity * ri.refund_unit_price)                      as refunds,
        sum(ri.quantity * oi.unit_cost)                              as returned_cogs
    from returns r
    join return_items ri on ri.return_id = r.return_id
    join order_items  oi on oi.order_item_id = ri.order_item_id
)
select
    s.orders,
    round(s.gross, 2)                                                as gross_revenue,
    round(coalesce(r.refunds, 0), 2)                                 as refunds,
    round(s.gross - coalesce(r.refunds, 0), 2)                       as net_revenue,
    round(s.cogs - coalesce(r.returned_cogs, 0), 2)                  as net_cogs,
    round((s.gross - coalesce(r.refunds, 0))
        - (s.cogs  - coalesce(r.returned_cogs, 0)), 2)               as net_profit,
    round(100 * ((s.gross - coalesce(r.refunds, 0)) - (s.cogs - coalesce(r.returned_cogs, 0)))
              / nullif(s.gross - coalesce(r.refunds, 0), 0), 2)      as net_margin_pct,
    round(s.gross / nullif(s.orders, 0), 2)                          as aov,
    round(100.0 * coalesce(r.returned_orders, 0) / nullif(s.orders, 0), 2) as return_rate_pct,
    round(100 * coalesce(r.refunds, 0) / nullif(s.gross, 0), 2)      as refund_share_pct
from sales s
cross join returned r;      -- both CTEs return exactly one row

-- ===================== CHECKS =====================

-- Check 1: net = gross - refunds (diff must be 0)
--   compare net_revenue above with gross_revenue - refunds (visible in the same row; rounding to cents only).

-- Check 2: a DIFFERENT calculation path for gross: first per order, then summed (diff must be 0)
select
    (select sum(oi.quantity * oi.unit_sale_price - oi.discount_amount)
       from orders o
       join order_items oi    on oi.order_id = o.order_id
       join order_statuses os on os.order_status_id = o.order_status_id
      where os.status_name = 'Completed')                              as gross_by_lines,
    (select sum(t.order_gross) from (
        select o.order_id, sum(oi.quantity * oi.unit_sale_price - oi.discount_amount) as order_gross
          from orders o
          join order_items oi    on oi.order_id = o.order_id
          join order_statuses os on os.order_status_id = o.order_status_id
         where os.status_name = 'Completed'
         group by o.order_id) t)                                       as gross_by_orders;

-- Check 3: returns exist only for Completed orders (must be 0; same rule as validate RET07)
select count(*) as returns_on_not_completed
from returns r
join orders o          on o.order_id = r.order_id
join order_statuses os on os.order_status_id = o.order_status_id
where os.status_name <> 'Completed';

-- Check 4 (manual check of ONE month, as the plan requires): take any month, e.g. 2026-09.
--   Recompute gross, refunds and margin for that month by hand (spreadsheet or the query below)
--   and compare with the row of 07_monthly_dynamics_net.sql for that month.
select
    round(sum(oi.quantity * oi.unit_sale_price - oi.discount_amount), 2) as gross_2026_09
from orders o
join order_items oi    on oi.order_id = o.order_id
join order_statuses os on os.order_status_id = o.order_status_id
where os.status_name = 'Completed'
  and o.order_date >= date '2026-09-01' and o.order_date < date '2026-10-01';