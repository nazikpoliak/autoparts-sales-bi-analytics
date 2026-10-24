select
    count(distinct o.order_id) AS total_orders,
    sum(oi.quantity) as total_items_sold,
    round(sum(oi.unit_sale_price * oi.quantity), 2) as total_revenue,
    round(sum(oi.unit_cost * oi.quantity), 2) as total_cost,
    round(sum(oi.unit_sale_price * oi.quantity) - sum(oi.unit_cost * oi.quantity), 2) as total_profit,
    round(sum(oi.unit_sale_price * oi.quantity) - sum(oi.unit_cost * oi.quantity), 2) / nullif(sum(oi.unit_sale_price * oi.quantity), 0) * 100 as profit_margin_percentage,
    round(sum(oi.unit_sale_price * oi.quantity) / count(distinct o.order_id), 2) as average_order_value
from orders o
join order_items oi on o.order_id = oi.order_id
join products p on oi.product_id = p.product_id;

select
    date_trunc('month', o.order_date)::date as sales_month,
    count(distinct o.order_id) AS monthly_orders,
    round(sum(oi.unit_sale_price * oi.quantity), 2) as monthly_revenue,
    round(sum(oi.unit_cost * oi.quantity), 2) as monthly_cost,
    round(sum(oi.unit_sale_price * oi.quantity) - sum(oi.unit_cost * oi.quantity), 2) as monthly_profit,
    round(sum(oi.unit_sale_price * oi.quantity) / count(distinct o.order_id), 2) as monthly_average_order_value
from orders o
join order_items oi on o.order_id = oi.order_id
join products p on oi.product_id = p.product_id
group by sales_month
order by sales_month;