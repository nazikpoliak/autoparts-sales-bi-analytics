with discount_products as (
    select 
        p.id as product_id,
        d.id as discount_id,
        d.discount_percentage
    from 
        products p
    join 
        discounts d on p.category_id = d.category_id
    where 
        d.start_date <= current_date and d.end_date >= current_date
)
select 
    p.id as product_id,
    p.name as product_name,
    p.price as original_price,
    dp.discount_percentage,
    (p.price * (1 - dp.discount_percentage / 100)) as discounted_price
from 
    products p
left join 
    discount_products dp on p.id = dp.product_id