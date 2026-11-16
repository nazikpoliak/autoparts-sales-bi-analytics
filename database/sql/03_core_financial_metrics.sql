select
    count(distinct o.order_id) AS total_completed_orders,
    round(sum(oi.quantity - coalesce(ri.quantity, 0)), 0) as total_items_sold,
    round(sum(oi.quantity * oi.unit_sale_price - oi.discount_amount), 2) as total_revenue,
    round(sum(oi.unit_cost * oi.quantity), 2) as total_cost,
    round(sum(oi.quantity * oi.unit_sale_price - oi.discount_amount) - sum(oi.unit_cost * oi.quantity), 2) as total_profit,
    round(sum(oi.quantity * oi.unit_sale_price - oi.discount_amount) - sum(oi.unit_cost * oi.quantity), 2) / nullif(sum(oi.quantity * oi.unit_sale_price - oi.discount_amount), 2) * 100 as profit_margin_percentage,
    round(sum(oi.quantity * oi.unit_sale_price - oi.discount_amount) / count(distinct o.order_id), 2) as average_order_value,
    count(ri.return_item_id) as total_returned_items,
    round(sum(ri.quantity * ri.refund_unit_price - oi.discount_amount), 2) as total_refunds
from orders o
join order_statuses os on os.order_status_id = o.order_status_id
join order_items oi on o.order_id = oi.order_id
join products p on oi.product_id = p.product_id
left join return_items ri on oi.order_item_id = ri.order_item_id
where os.status_name = 'Completed';

select
    date_trunc('month', o.order_date)::date as sales_month,
    count(distinct o.order_id) AS monthly_orders,
    round(sum(oi.quantity * oi.unit_sale_price - oi.discount_amount), 2) as monthly_revenue,
    round(sum(oi.unit_cost * oi.quantity), 2) as monthly_cost,
    round(sum(oi.quantity * oi.unit_sale_price - oi.discount_amount) - sum(oi.unit_cost * oi.quantity), 2) as monthly_profit,
    round(sum(oi.quantity * oi.unit_sale_price - oi.discount_amount) / count(distinct o.order_id), 2) as monthly_average_order_value,
    round(sum(ri.quantity * ri.refund_unit_price - oi.discount_amount), 2) as monthly_refunds
from orders o
join order_statuses os on os.order_status_id = o.order_status_id
join order_items oi on o.order_id = oi.order_id
join products p on oi.product_id = p.product_id
left join return_items ri on oi.order_item_id = ri.order_item_id
where os.status_name = 'Completed'
group by sales_month
order by sales_month;