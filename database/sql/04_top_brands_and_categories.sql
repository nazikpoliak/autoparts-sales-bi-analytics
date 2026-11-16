with brand_financials as (
    select 
        b.brand_name,
        sum(oi.quantity * oi.unit_sale_price - oi.discount_amount) - coalesce(sum(ri.quantity * ri.refund_unit_price), 0) as net_revenue,
        sum(oi.unit_cost * oi.quantity) as total_cost,
        (sum(oi.quantity * oi.unit_sale_price - oi.discount_amount) - coalesce(sum(ri.quantity * ri.refund_unit_price), 0)) 
        - sum(oi.unit_cost * oi.quantity) as net_profit
    from order_items oi
    join products p on oi.product_id = p.product_id
    join brands b on p.brand_id = b.brand_id
    join orders o on oi.order_id = o.order_id
    join order_statuses os on o.order_status_id = os.order_status_id
    left join return_items ri on oi.order_item_id = ri.order_item_id
    where os.status_name = 'Completed'
    group by b.brand_name
)
select 
    brand_name,
    round(net_revenue, 2) as net_revenue,
    round(net_profit, 2) as net_profit,
    round(net_profit * 100.0 / nullif(net_revenue, 0), 2) as brand_margin_pct
from brand_financials
order by net_revenue desc;


with category_sales_raw as (
    select 
        cat.category_id,
        cat.category_name,
        count(distinct p.product_id) as total_skus_in_category,
        sum(oi.quantity) as gross_quantity_sold,
        sum(oi.quantity * oi.unit_sale_price - oi.discount_amount) as gross_revenue,
        sum(oi.unit_cost * oi.quantity) as total_cost
    from order_items oi
    join products p on oi.product_id = p.product_id
    join subcategories sc on p.subcategory_id = sc.subcategory_id
    join categories cat on sc.category_id = cat.category_id
    join orders o on oi.order_id = o.order_id
    join order_statuses os on o.order_status_id = os.order_status_id
    where os.status_name = 'Completed'
    group by cat.category_id, cat.category_name
),
category_refunds_raw as (
    select 
        cat.category_id,
        sum(ri.quantity) as total_returned_quantity,
        sum(ri.quantity * ri.refund_unit_price) as total_refunds
    from return_items ri
    join order_items oi on ri.order_item_id = oi.order_item_id
    join products p on oi.product_id = p.product_id
    join subcategories sc on p.subcategory_id = sc.subcategory_id
    join categories cat on sc.category_id = cat.category_id
    group by cat.category_id
),
net_category_financials as (
    select 
        s.category_name,
        s.total_skus_in_category,
        s.gross_quantity_sold - coalesce(r.total_returned_quantity, 0) as total_quantity_sold,
        s.gross_revenue - coalesce(r.total_refunds, 0) as category_revenue,
        (s.gross_revenue - coalesce(r.total_refunds, 0)) - s.total_cost as category_profit,
        s.gross_revenue - coalesce(r.total_refunds, 0) as net_revenue_for_margin,
        s.total_cost
    from category_sales_raw s
    left join category_refunds_raw r on s.category_id = r.category_id
)
select 
    category_name,
    total_skus_in_category,
    total_quantity_sold,
    round(category_revenue, 2) as category_revenue,
    round(category_profit, 2) as category_profit,
    round(category_profit * 100.0 / nullif(category_revenue, 0), 2) as category_margin_pct
from net_category_financials
order by category_revenue desc;