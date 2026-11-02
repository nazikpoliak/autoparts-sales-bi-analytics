with rfm_raw as (
    select
        c.customer_id,
        c.customer_name,
        current_date - max(o.order_date) as recency,
        count(distinct o.order_id ) as frequency,
        sum(oi.quantity * oi.unit_sale_price - oi.discount_amount - coalesce(ri.refund_unit_price, 0)) as monetary
    from customers c
    left join orders o on c.customer_id = o.customer_id
    left join order_items oi on o.order_id = oi.order_id
    left join return_items ri on oi.order_item_id = ri.order_item_id
    join order_statuses os on o.order_status_id = os.order_status_id
    where os.status_name = 'Completed'
    group by c.customer_id, c.customer_name
),

rfm_scores as (
    select
        customer_id,
        customer_name,
        recency,
        frequency,
        monetary,
        ntile(5) over (order by recency desc) as recency_score,
        ntile(5) over (order by frequency desc) as frequency_score,
        ntile(5) over (order by monetary desc) as monetary_score
    from rfm_raw
)

select
    customer_id,
    customer_name,
    recency,
    frequency,
    monetary,
    recency_score,
    frequency_score,
    monetary_score,
    (recency_score + frequency_score + monetary_score) as rfm_total_score
from rfm_scores
order by rfm_total_score desc;