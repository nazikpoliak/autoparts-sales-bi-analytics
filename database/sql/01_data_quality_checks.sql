CREATE TABLE IF NOT EXISTS dq_results (
    check_id SERIAL PRIMARY KEY,
    check_name VARCHAR(150) NOT NULL,
    severity VARCHAR(20) NOT NULL, -- 'CRITICAL', 'HIGH', 'MEDIUM'
    failed_rows INT NOT NULL,
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

TRUNCATE TABLE dq_results RESTART IDENTITY;

INSERT INTO dq_results (check_name, severity, failed_rows)
SELECT 
    'Orders before customer registration date',
    'CRITICAL',
    COUNT(*)
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.order_date < c.registration_date;


INSERT INTO dq_results (check_name, severity, failed_rows)
SELECT 
    'Orders without any order items (orphaned orders)',
    'HIGH',
    COUNT(*)
FROM orders o
LEFT JOIN order_items oi ON o.order_id = oi.order_id
WHERE oi.order_item_id IS NULL;

INSERT INTO dq_results (check_name, severity, failed_rows)
SELECT 
    'Return date earlier than order date',
    'CRITICAL',
    COUNT(*)
FROM returns r
JOIN orders o ON r.order_id = o.order_id
WHERE r.return_date < o.order_date;


INSERT INTO dq_results (check_name, severity, failed_rows)
SELECT 
    'Return quantity exceeds ordered quantity',
    'HIGH',
    COUNT(*)
FROM return_items ri
JOIN order_items oi ON ri.order_item_id = oi.order_item_id
WHERE ri.quantity > oi.quantity;


INSERT INTO dq_results (check_name, severity, failed_rows)
SELECT 
    'Discount amount exceeds line gross amount',
    'MEDIUM',
    COUNT(*)
FROM order_items
WHERE discount_amount > (quantity * unit_sale_price);


SELECT 
    check_name,
    severity,
    failed_rows,
    CASE 
        WHEN failed_rows = 0 THEN 'PASS'
        WHEN severity = 'CRITICAL' THEN 'FAIL (CRITICAL)'
        ELSE 'WARNING'
    END as status
FROM dq_results
ORDER BY 
    CASE severity 
        WHEN 'CRITICAL' THEN 1 
        WHEN 'HIGH' THEN 2 
        else 3 
    end, 
    failed_rows DESC;