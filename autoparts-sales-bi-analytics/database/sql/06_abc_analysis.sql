with product_sales as (
    select 
        p.product_id,
        p.product_name,
        sum(oi.quantity * oi.unit_sale_price) as product_revenue
    from 
        order_items oi
    join 
        products p on oi.product_id = p.product_id
    group by 
        p.product_id, p.product_name
),
cumulative_calc as (
    select 
        product_id,
        product_name,
        product_revenue,
        sum(product_revenue) over (order by product_revenue desc) as running_total,
        sum(product_revenue) over () as grand_total
    from product_sales
),
percentage_calc as (
    select
        product_id,
        product_name,
        product_revenue,
        (running_total * 100.0 / grand_total) as cum_percentage
    from cumulative_calc
)

select
    product_name,
    product_revenue,
    round(cum_percentage, 2) as cumulative_pct,
    case 
        when cum_percentage <= 80 then 'A'
        when cum_percentage <= 95 then 'B'
        else 'C'
    end as abc_class
from percentage_calc
order by product_revenue desc;