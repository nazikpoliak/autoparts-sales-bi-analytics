select
    c.customer_name,
    count(distinct o.order_id) as total_orders,
    sum(oi.quantity) as total_quantity_purchased,
    round(sum(oi.quantity * oi.unit_sale_price), 2) as total_spent
from customers c
join orders o on c.customer_id = o.customer_id
join order_items oi on o.order_id = oi.order_id
group by c.customer_id, c.customer_name
order by total_spent desc
limit 10;



select
    c.city_name,
    count(distinct o.order_id) as total_orders,
    sum(oi.quantity) as total_quantity_purchased,
    round(sum(oi.quantity * oi.unit_sale_price), 2) as total_spent
from cities c
join customers cu on c.city_id = cu.city_id
join orders o on cu.customer_id = o.customer_id
join order_items oi on o.order_id = oi.order_id
group by c.city_id, c.city_name
order by total_spent desc
limit 10;