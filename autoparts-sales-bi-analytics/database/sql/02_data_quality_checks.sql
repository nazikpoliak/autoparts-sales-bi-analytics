select
    'Orders without valid customer' AS check_name,
    COUNT(*) AS orphan_count
from orders o
left join customers c on o.customer_id = c.customer_id
where c.customer_id is null;



select
    'Order items without valid order or product' AS check_name,
    COUNT(*) AS orphan_count
from order_items oi
left join orders o on oi.order_id = o.order_id
left join products p on oi.product_id = p.product_id
where o.order_id is null or p.product_id is null;



select
    'Returns without valid order' AS check_name,
    COUNT(*) AS orphan_count
from returns r
left join orders o on r.order_id = o.order_id
where o.order_id is null;



select
    'Order items with invalid price or quantity' AS check_name,
    COUNT(*) AS invalid_count
from order_items
where unit_sale_price <= 0 or quantity <= 0;



select 'Total Customers' AS check_name, COUNT(*)::TEXT AS value FROM customers
union all
select 'Total Orders' AS check_name, COUNT(*)::TEXT AS value FROM orders
union all
select 'Total Products' AS check_name, COUNT(*)::TEXT AS value FROM products
union all
select 'Total Order Items' AS check_name, COUNT(*)::TEXT AS value FROM order_items
union all
select 'Total Returns' AS check_name, COUNT(*)::TEXT AS value FROM returns;