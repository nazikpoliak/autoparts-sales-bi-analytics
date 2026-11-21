# Metrics glossary

Scope: only Completed orders count as sales. Cancelled/unfinished orders are excluded from all revenue metrics.

| Metric | Definition | Date axis |
|---|---|---|
| Gross revenue | sum(quantity * unit price) - line discounts, Completed orders | order_date |
| Refunds | sum(refund_quantity * refund_unit_price) | return_date |
| Net revenue | Gross revenue - Refunds | gross by order_date, refunds by return_date |
| COGS (gross) | sum(quantity * unit cost at sale) | order_date |
| Returned COGS | sum(returned quantity * unit cost at sale) | return_date |
| Net margin | Net revenue - (COGS - Returned COGS) | as above |
| Return rate | orders with a return / Completed orders, by ORDER COHORT month | order_date of the original order |

Assumptions
1. Returned goods are restocked at the original cost (no write-offs).
2. Return attribution is cash-basis: a refund belongs to the month it is paid, not to the month of the sale.
3. Return rate of the last 1-2 months of the period is understated (returns not yet occurred) and must not be interpreted.
4. Data is synthetic (seed 42, end-date: 21.10.2026).