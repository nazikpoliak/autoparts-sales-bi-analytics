select
    o.order_date,
    order_item_id,
    product_id,
    quantity,
    unit_sale_price,
    discount_amount,
    unit_cost,
    quantity * unit_sale_price - discount_amount as revenue
from order_items
left join orders o on order_items.order_id = o.order_id;