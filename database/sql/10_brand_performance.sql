-- 10_brand_performance.sql   (Task 4: brands)
-- Question: which brands hold the main share of sales and where is the margin weak?
-- Grain: one row per brand (all brands, also those without sales).
-- Definitions: docs/metrics.md. A refund belongs to the brand of the RETURNED PRODUCT (return_items.product_id).
--   * share_of_net_pct  = brand net_revenue / company net_revenue
--   * revenue_rank      = rank by net_revenue (1 = biggest); margin_rank = rank by net_margin_pct (1 = best)
--   * margin_vs_company_pp = brand margin % minus company margin %, in percentage points (negative = weak margin)
-- Pitfall (fan-out): sales and refunds are aggregated per product in separate CTEs, then joined by product_id.
-- Pitfall (ties): rank() leaves gaps after ties; the final order_by has a tie-breaker (brand_name) for a stable result.

with product_sales as (
    select oi.product_id,
           sum(oi.quantity * oi.unit_sale_price - oi.discount_amount) as gross,
           sum(oi.quantity * oi.unit_cost)                            as cogs
    from orders o
    join order_items    oi on oi.order_id = o.order_id
    join order_statuses os on os.order_status_id = o.order_status_id
    where os.status_name = 'Completed'
    group by oi.product_id
),
product_refunds as (
    select ri.product_id,
           sum(ri.quantity * ri.refund_unit_price) as refunds,
           sum(ri.quantity * oi.unit_cost)         as returned_cogs
    from return_items ri
    join order_items oi on oi.order_item_id = ri.order_item_id
    group by ri.product_id
),
brand_totals as (
    select b.brand_id,
           b.brand_name,
           count(p.product_id)                                           as skus_in_catalog,
           count(ps.product_id)                                          as skus_sold,
           coalesce(sum(ps.gross), 0)                                    as gross,
           coalesce(sum(pr.refunds), 0)                                  as refunds,
           coalesce(sum(ps.cogs), 0) - coalesce(sum(pr.returned_cogs), 0) as net_cogs
    from brands b
    left join products        p  on p.brand_id    = b.brand_id
    left join product_sales   ps on ps.product_id = p.product_id
    left join product_refunds pr on pr.product_id = p.product_id
    group by b.brand_id, b.brand_name
),
brand_metrics as (
    select brand_name,
           skus_in_catalog,
           skus_sold,
           gross - refunds                                               as net_revenue,
           gross - refunds - net_cogs                                    as net_margin,
           100 * (gross - refunds - net_cogs) / nullif(gross - refunds, 0) as net_margin_pct
    from brand_totals
)
select
    brand_name,
    skus_in_catalog,
    skus_sold,
    round(net_revenue, 2)                                                as net_revenue,
    round(net_margin, 2)                                                 as net_margin,
    round(net_margin_pct, 2)                                             as net_margin_pct,
    round(100 * net_revenue / nullif(sum(net_revenue) over (), 0), 2)    as share_of_net_pct,
    round(100 * sum(net_revenue) over (order by net_revenue desc, brand_name)
              / nullif(sum(net_revenue) over (), 0), 2)                  as cumulative_share_pct,
    rank() over (order by net_revenue desc)                              as revenue_rank,
    rank() over (order by net_margin_pct desc nulls last)                as margin_rank,
    round(net_margin_pct - 100 * sum(net_margin) over () / nullif(sum(net_revenue) over (), 0), 2) as margin_vs_company_pp
from brand_metrics
order by net_revenue desc, brand_name;

-- ===================== CHECKS =====================
-- Check 1: sum of brand net_revenue = net_revenue of 08_kpi_snapshot.sql (1223572558.80 on the reference run).
--   Add after the CTEs:  select round(sum(net_revenue), 2) from brand_metrics;
-- Check 2: top-5 by hand: run the final select, then compare with
--   select brand_name, round(net_revenue, 2) from brand_metrics order by net_revenue desc limit 5;
-- Check 3: number of brands = count(*) from brands (40 on the reference run); brands without sales are present with zeros.
-- Check 4: cumulative_share_pct of the last row = 100.00; the share column sums to 100 (±0.01 from rounding).
-- Check 5: brand and category totals are two views of the same net_revenue (compare with 09 check 1).