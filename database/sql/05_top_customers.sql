with customer_sales_raw as (
    select 
        c.customer_id,
        c.customer_name,
        count(distinct o.order_id) as total_orders,
        sum(oi.quantity) as gross_quantity_purchased,
        sum(oi.quantity * oi.unit_sale_price - oi.discount_amount) as gross_revenue,
        sum(oi.unit_cost * oi.quantity) as total_cost
    from customers c
    join orders o on c.customer_id = o.customer_id
    join order_items oi on o.order_id = oi.order_id
    join order_statuses os on o.order_status_id = os.order_status_id
    where os.status_name = 'Completed'
    group by c.customer_id, c.customer_name
),
customer_refunds_raw as (
    select 
        c.customer_id,
        sum(ri.quantity) as total_returned_quantity,
        sum(ri.quantity * ri.refund_unit_price) as total_refunds
    from customers c
    join orders o on c.customer_id = o.customer_id
    join order_items oi on o.order_id = oi.order_id
    join return_items ri on oi.order_item_id = ri.order_item_id
    group by c.customer_id
)
select
    c.customer_name,
    c.total_orders,
    c.gross_quantity_purchased - coalesce(r.total_returned_quantity, 0) as net_quantity_purchased,
    round(c.gross_revenue - coalesce(r.total_refunds, 0), 2) as net_revenue,
    round((c.gross_revenue - coalesce(r.total_refunds, 0)) - c.total_cost, 2) as net_profit,
    round(((c.gross_revenue - coalesce(r.total_refunds, 0)) - c.total_cost) * 100.0 / nullif(c.gross_revenue - coalesce(r.total_refunds, 0), 0), 2) as customer_margin_pct
from customer_sales_raw c, customer_refunds_raw r
where c.customer_id = r.customer_id
order by net_revenue desc;