-- 09_category_performance.sql   (Task 3: categories and subcategories)
-- Question: which product groups bring revenue and profit, and where is the margin weak?
-- Grain: query A = one row per category, query B = one row per subcategory.
-- Definitions: docs/metrics.md. A refund belongs to the category of the RETURNED PRODUCT (return_items.product_id).
--   * net_revenue  = gross - refunds,  net_margin = net_revenue - (cogs - returned_cogs)
--   * share        = net_revenue of the group / net_revenue of the whole company
--   * skus_in_catalog = products in the group;  skus_sold = products with at least one Completed sale
-- Pitfall (fan-out): sales and refunds are aggregated per PRODUCT in separate CTEs, then joined to the product list by product_id.
-- Pitfall (dropped groups): the dimensions are the LEFT side, so a category without sales still appears with zeros.

-- ---------- Query A: categories ----------
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
category_totals as (
    select c.category_id,
           c.category_name,
           count(p.product_id)                                           as skus_in_catalog,
           count(ps.product_id)                                          as skus_sold,
           coalesce(sum(ps.gross), 0)                                    as gross,
           coalesce(sum(pr.refunds), 0)                                  as refunds,
           coalesce(sum(ps.cogs), 0) - coalesce(sum(pr.returned_cogs), 0) as net_cogs
    from categories c
    left join subcategories  sc on sc.category_id    = c.category_id
    left join products       p  on p.subcategory_id  = sc.subcategory_id
    left join product_sales  ps on ps.product_id     = p.product_id
    left join product_refunds pr on pr.product_id    = p.product_id
    group by c.category_id, c.category_name
)
select
    category_name,
    skus_in_catalog,
    skus_sold,
    round(gross, 2)                                                      as gross,
    round(refunds, 2)                                                    as refunds,
    round(gross - refunds, 2)                                            as net_revenue,
    round(gross - refunds - net_cogs, 2)                                 as net_margin,
    round(100 * (gross - refunds - net_cogs) / nullif(gross - refunds, 0), 2) as net_margin_pct,
    round(100 * (gross - refunds) / nullif(sum(gross - refunds) over (), 0), 2) as share_of_net_pct
from category_totals
order by gross - refunds desc;

-- ---------- Query B: subcategories (share of the category and of the company) ----------
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
sub_totals as (
    select c.category_name,
           sc.subcategory_id,
           sc.subcategory_name,
           count(p.product_id)                                           as skus_in_catalog,
           count(ps.product_id)                                          as skus_sold,
           coalesce(sum(ps.gross), 0)                                    as gross,
           coalesce(sum(pr.refunds), 0)                                  as refunds,
           coalesce(sum(ps.cogs), 0) - coalesce(sum(pr.returned_cogs), 0) as net_cogs
    from subcategories sc
    join categories c on c.category_id = sc.category_id
    left join products        p  on p.subcategory_id = sc.subcategory_id
    left join product_sales   ps on ps.product_id    = p.product_id
    left join product_refunds pr on pr.product_id    = p.product_id
    group by c.category_name, sc.subcategory_id, sc.subcategory_name
)
select
    category_name,
    subcategory_name,
    skus_in_catalog,
    skus_sold,
    round(gross - refunds, 2)                                            as net_revenue,
    round(gross - refunds - net_cogs, 2)                                 as net_margin,
    round(100 * (gross - refunds - net_cogs) / nullif(gross - refunds, 0), 2) as net_margin_pct,
    round(100 * (gross - refunds) / nullif(sum(gross - refunds) over (partition by category_name), 0), 2) as share_of_category_pct,
    round(100 * (gross - refunds) / nullif(sum(gross - refunds) over (), 0), 2) as share_of_net_pct
from sub_totals
order by category_name, gross - refunds desc;

-- ===================== CHECKS =====================
-- Check 1: sum of category net_revenue = net_revenue of 08_kpi_snapshot.sql (1223572558.80 on the reference run).
--   Add:  select round(sum(gross - refunds), 2) from category_totals;   after the CTEs of query A.
-- Check 2: sum of subcategory net_revenue inside each category = that category's net_revenue.
--   Add the query below after the CTEs of query B and compare with query A; diff must be 0.
--   select category_name, round(sum(gross - refunds), 2) from sub_totals group by 1 order by 1;
-- Check 3: skus_in_catalog summed over categories = count(*) from products (10000 on the reference run).
-- Check 4: every refunded product has a sale (otherwise refunds would belong to a product with no gross); must be 0:
select count(*) as refunded_products_without_sales
from (select distinct product_id from return_items) r
where r.product_id not in (
    select oi.product_id
    from order_items oi
    join orders o on o.order_id = oi.order_id
    join order_statuses os on os.order_status_id = o.order_status_id
    where os.status_name = 'Completed');