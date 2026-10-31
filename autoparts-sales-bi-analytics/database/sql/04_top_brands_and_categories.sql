select
    b.brand_name,
    count(distinct p.product_id) as total_skus_in_brand,
    sum(oi.quantity) as total_quantity_sold,
    round(sum(oi.quantity * oi.unit_sale_price - oi.discount_amount), 2) as brand_revenue,
    round(sum((oi.unit_sale_price - oi.unit_cost) * oi.quantity), 2) as brand_profit,
    round(sum((oi.unit_sale_price - oi.unit_cost) * oi.quantity) * 100.0 / nullif(sum(oi.quantity * oi.unit_sale_price - oi.discount_amount), 0), 2) as brand_margin_pct
from order_items oi
join products p on oi.product_id = p.product_id
join brands b on p.brand_id = b.brand_id
group by b.brand_name
order by brand_revenue desc
limit 10;



select
    cat.category_name,
    count(distinct p.product_id) as total_skus_in_category,
    sum(oi.quantity) as total_quantity_sold,
    round(sum(oi.quantity * oi.unit_sale_price - oi.discount_amount), 2) as category_revenue,
    round(sum((oi.unit_sale_price - oi.unit_cost) * oi.quantity), 2) as category_profit,
    round(sum((oi.unit_sale_price - oi.unit_cost) * oi.quantity) * 100.0 / nullif(sum(oi.quantity * oi.unit_sale_price - oi.discount_amount), 0), 2) as category_margin_pct
from order_items oi
join products p on oi.product_id = p.product_id
join subcategories sc on p.subcategory_id = sc.subcategory_id
join categories cat on sc.category_id = cat.category_id
group by cat.category_name
order by category_revenue desc