with rfm_raw as (
    select
        c.customer_id,
        c.customer_name,
        current_date - max(o.order_date) as recency,
        count(distinct o.order_id) as frequency,
        sum(oi.quantity * oi.unit_sale_price) as monetary
    from customers c
    left join orders o on c.customer_id = o.customer_id
    left join order_items oi on o.order_id = oi.order_id
    group by c.customer_id, c.customer_name
), 
rfm_scores as (
    select
        customer_id,
        customer_name,
        recency,
        frequency,
        monetary,
        ntile(5) over (order by recency) as recency_score,
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