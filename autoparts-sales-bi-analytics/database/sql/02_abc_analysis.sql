with gross_product_sales as (
    select 
        p.product_id,
        p.product_name,
        sum(oi.quantity * oi.unit_sale_price - oi.discount_amount) as product_revenue
    from order_items oi
    join products p on oi.product_id = p.product_id
    join orders o on oi.order_id = o.order_id
    join order_statuses os on o.order_status_id = os.order_status_id
    left join return_items ri on oi.order_item_id = ri.order_item_id
    where os.status_name = 'Completed'
    group by p.product_id, p.product_name
),

product_refund as (
    select 
        oi.product_id,
        sum(ri.quantity * ri.refund_unit_price) as product_refund
    from return_items ri
    join order_items oi on ri.order_item_id = oi.order_item_id
    group by oi.product_id
),

net_product_sales as (
    select 
        ps.product_id,
        ps.product_name,
        ps.product_revenue - coalesce(pr.product_refund, 0) - oi.discount_amount as product_revenue
    from gross_product_sales ps
    left join product_refund pr on ps.product_id = pr.product_id
    join order_items oi on ps.product_id = oi.product_id
),

cumulative_calc as (
    select 
        product_id,
        product_name,
        product_revenue,
        sum(product_revenue) over (order by product_revenue desc) as running_total,
        sum(product_revenue) over () as grand_total
    from net_product_sales
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