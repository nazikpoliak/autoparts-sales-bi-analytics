-- 07_monthly_dynamics_net.sql   (Task 2: monthly trend; includes the monthly part of Task 1)
-- Question: are we growing or falling, and how fast? How do gross, refunds, net revenue and net margin change month by month?
-- Grain of the result: one row per calendar month, WITHOUT gaps (calendar built with generate_series).
-- Definitions: docs/metrics.md
--   * only Completed orders are sales
--   * gross + COGS are dated by order_date; refunds + returned COGS are dated by return_date (cash-basis)
--   * AOV = gross revenue / number of Completed orders of the month (before refunds)
--   * MoM / YoY are calculated on gross and on net revenue (gross is not distorted by late returns)
-- Pitfall (fan-out): orders and returns are aggregated SEPARATELY at their own grain, then joined by month.
-- Known artefact: the last 1-2 months have fewer returns (returns not yet happened), so their net is overstated.

with months as (                                   -- calendar: first order month .. last order/return month
    select generate_series(
               date_trunc('month', (select min(order_date) from orders)),
               date_trunc('month', greatest((select max(order_date)  from orders),
                                            (select max(return_date) from returns))),
               interval '1 month')::date as month
),
gross as (                                         -- grain: month of order_date
    select
        date_trunc('month', o.order_date)::date                  as month,
        count(distinct o.order_id)                               as orders,
        sum(oi.quantity * oi.unit_sale_price - oi.discount_amount) as gross,
        sum(oi.quantity * oi.unit_cost)                          as cogs
    from orders o
    join order_items    oi on oi.order_id = o.order_id
    join order_statuses os on os.order_status_id = o.order_status_id
    where os.status_name = 'Completed'
    group by 1
),
refunds as (                                       -- grain: month of return_date
    select
        date_trunc('month', r.return_date)::date                 as month,
        sum(ri.quantity * ri.refund_unit_price)                  as refunds,
        sum(ri.quantity * oi.unit_cost)                          as returned_cogs
    from returns r
    join return_items ri on ri.return_id = r.return_id
    join order_items  oi on oi.order_item_id = ri.order_item_id
    group by 1
),
monthly as (                                       -- one place where net / net_cogs / net_margin are defined
    select
        m.month,
        coalesce(g.orders, 0)                                    as orders,
        coalesce(g.gross, 0)                                     as gross,
        coalesce(r.refunds, 0)                                   as refunds,
        coalesce(g.gross, 0) - coalesce(r.refunds, 0)            as net,
        coalesce(g.cogs, 0) - coalesce(r.returned_cogs, 0)       as net_cogs
    from months m
    left join gross   g on g.month = m.month
    left join refunds r on r.month = m.month
)
select
    month,
    orders,
    round(gross, 2)                                              as gross,
    round(refunds, 2)                                            as refunds,
    round(net, 2)                                                as net,
    round(gross / nullif(orders, 0), 2)                          as aov,
    round(net_cogs, 2)                                           as net_cogs,
    round(net - net_cogs, 2)                                     as net_margin,
    round(100 * (net - net_cogs) / nullif(net, 0), 2)            as net_margin_pct,
    round(100 * (gross / nullif(lag(gross, 1)  over w, 0) - 1), 2) as gross_mom_pct,
    round(100 * (gross / nullif(lag(gross, 12) over w, 0) - 1), 2) as gross_yoy_pct,
    round(100 * (net   / nullif(lag(net,   1)  over w, 0) - 1), 2) as net_mom_pct,
    round(100 * (net   / nullif(lag(net,   12) over w, 0) - 1), 2) as net_yoy_pct
from monthly
window w as (order by month)
order by month;

-- ===================== CHECKS (same CTE chain, different final select; every diff must be 0) =====================
-- If you change the CTEs above, change them here too.
with months as (                                   -- calendar: first order month .. last order/return month
    select generate_series(
               date_trunc('month', (select min(order_date) from orders)),
               date_trunc('month', greatest((select max(order_date)  from orders),
                                            (select max(return_date) from returns))),
               interval '1 month')::date as month
),
gross as (                                         -- grain: month of order_date
    select
        date_trunc('month', o.order_date)::date                  as month,
        count(distinct o.order_id)                               as orders,
        sum(oi.quantity * oi.unit_sale_price - oi.discount_amount) as gross,
        sum(oi.quantity * oi.unit_cost)                          as cogs
    from orders o
    join order_items    oi on oi.order_id = o.order_id
    join order_statuses os on os.order_status_id = o.order_status_id
    where os.status_name = 'Completed'
    group by 1
),
refunds as (                                       -- grain: month of return_date
    select
        date_trunc('month', r.return_date)::date                 as month,
        sum(ri.quantity * ri.refund_unit_price)                  as refunds,
        sum(ri.quantity * oi.unit_cost)                          as returned_cogs
    from returns r
    join return_items ri on ri.return_id = r.return_id
    join order_items  oi on oi.order_item_id = ri.order_item_id
    group by 1
),
monthly as (                                       -- one place where net / net_cogs / net_margin are defined
    select
        m.month,
        coalesce(g.orders, 0)                                    as orders,
        coalesce(g.gross, 0)                                     as gross,
        coalesce(r.refunds, 0)                                   as refunds,
        coalesce(g.gross, 0) - coalesce(r.refunds, 0)            as net,
        coalesce(g.cogs, 0) - coalesce(r.returned_cogs, 0)       as net_cogs
    from months m
    left join gross   g on g.month = m.month
    left join refunds r on r.month = m.month
)
select
    count(*)                                                    as months,                -- expect 30
    sum(gross)   - (select sum(oi.quantity * oi.unit_sale_price - oi.discount_amount)
                      from orders o
                      join order_items oi    on oi.order_id = o.order_id
                      join order_statuses os on os.order_status_id = o.order_status_id
                     where os.status_name = 'Completed')        as diff_gross,            -- check 1
    sum(refunds) - (select sum(quantity * refund_unit_price) from return_items)
                                                                as diff_refunds,          -- check 2
    count(*) filter (where abs(net - (gross - refunds)) > 0.005) as bad_net_rows,         -- check 3
    sum(orders)  - (select count(*) from orders o
                      join order_statuses os on os.order_status_id = o.order_status_id
                     where os.status_name = 'Completed')        as diff_orders,
    sum(net_cogs) - ((select sum(oi.quantity * oi.unit_cost)
                        from orders o
                        join order_items oi    on oi.order_id = o.order_id
                        join order_statuses os on os.order_status_id = o.order_status_id
                       where os.status_name = 'Completed')
                     - (select sum(ri.quantity * oi.unit_cost)
                          from return_items ri
                          join order_items oi on oi.order_item_id = ri.order_item_id))
                                                                as diff_net_cogs
from monthly;