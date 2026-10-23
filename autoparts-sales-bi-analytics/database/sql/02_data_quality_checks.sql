select count(*)
from orders o
left join customers c on o.customer_id = c.customer_id
where c.customer_id is null;