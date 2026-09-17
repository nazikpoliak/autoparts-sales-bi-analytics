# AutoParts Sales & BI Analytics — Business Requirements

# 1. Project Overview

**Project Name:** AutoParts Sales & BI Analytics

**Industry:** Automotive Parts Distribution

**Project Type:** End-to-End Data Analytics / Business Intelligence Portfolio Project

**Primary Goal:**

Build a realistic end-to-end analytical solution for an automotive parts distributor that provides management with a unified view of:

* Sales performance
* Revenue and profitability
* Products and brands
* Categories and subcategories
* Customer behavior and value
* Pricing and discounts
* Sales team performance
* Geographic performance
* Business opportunities and risks

The project should demonstrate practical Data Analyst / BI Analyst capabilities across the full analytical lifecycle:

**Data → Database → SQL → Python → Data Modeling → Power BI → Business Insights → Recommendations**


# 2. Business Context

The company is an automotive parts distributor selling spare parts to B2B customers.

Typical customers include:

* Independent automotive workshops
* Retail automotive parts stores
* Fleet companies
* Service stations
* Corporate customers
* Regional distributors

The company sells products from multiple automotive brands across different product categories and subcategories.

The business generates transactional data containing:

* Sales orders
* Order lines
* Products
* Brands
* Categories
* Customers
* Sales representatives
* Regions
* Prices
* Discounts
* Product costs
* Revenue
* Gross profit

The company currently needs a unified analytical solution that allows management and commercial teams to understand what is happening in the business and where improvement opportunities exist.



# 3. Business Problem

The company has limited visibility into overall commercial performance.

Management needs answers to questions such as:

* How much revenue are we generating?
* Is revenue growing?
* Which products generate the most revenue?
* Which products generate the most profit?
* Which products have poor margins?
* Which brands are the most profitable?
* Which customers generate the most value?
* Which customers are becoming inactive?
* Where are discounts reducing profitability?
* Which sales representatives perform best?
* Which regions are growing?
* Which products have high revenue but low margins?
* Which products should receive commercial attention?
* Where are pricing opportunities?
* Which customers or products create concentration risk?

The project should create a **single source of analytical truth** for these questions.



# 4. Project Objectives

The project should achieve the following objectives:

1. Build a PostgreSQL relational database.
2. Create a realistic automotive parts sales dataset.
3. Implement a structured data model with proper relationships.
4. Perform data quality validation.
5. Analyze business performance using SQL.
6. Perform exploratory and statistical analysis using Python.
7. Build an analytical Star Schema.
8. Create a Power BI semantic model.
9. Develop DAX measures for core KPIs.
10. Build an interactive Power BI dashboard.
11. Perform advanced business analysis.
12. Identify actionable business insights.
13. Provide practical recommendations.
14. Package the project as a professional GitHub portfolio project.



# 5. Stakeholders

## Executive Management

Main interests:

* Revenue
* Profitability
* Growth
* Customer value
* Business risks
* Overall performance

## Sales / Commercial Director

Main interests:

* Sales performance
* Sales representatives
* Customers
* Discounts
* Pricing
* Regions
* Product performance

## Product Managers

Main interests:

* Product performance
* Brands
* Categories
* Margins
* ABC/XYZ classification
* Portfolio opportunities

## Sales Managers

Main interests:

* Sales representatives
* Customer performance
* Revenue
* Profitability
* Sales targets
* Customer activity

## Data Analyst

Responsibilities:

* Data preparation
* SQL analysis
* Python analysis
* KPI development
* Data modeling
* Power BI
* Business insights
* Recommendations



# 6. Scope

## 6.1 Sales Analytics

Analyze:

* Orders
* Order lines
* Units sold
* Revenue
* Discounts
* Costs
* Gross profit
* Gross margin
* Average order value
* Average selling price
* Sales trends
* Growth



## 6.2 Product Analytics

Analyze:

* SKU
* Product
* Category
* Subcategory
* Brand
* Supplier
* Product status
* Revenue
* Units sold
* Profit
* Margin
* Product trends



## 6.3 Customer Analytics

Analyze:

* Customer
* Customer type
* Region
* City
* Sales representative
* Customer activity
* Customer revenue
* Customer profit
* Purchase frequency
* Recency
* Customer value
* Customer segmentation



## 6.4 Sales Organization Analytics

Analyze:

* Sales representatives
* Revenue
* Gross profit
* Gross margin
* Number of customers
* Number of orders
* Average order value
* High-value customers



## 6.5 Geographic Analytics

Analyze:

* Region
* City
* Revenue
* Gross profit
* Margin
* Customer count
* Sales trends



## 6.6 Pricing Analytics

Analyze:

* List price
* Selling price
* Cost
* Discount
* Discount amount
* Revenue
* Gross profit
* Gross margin
* Price anomalies
* Discount profitability



## 6.7 Advanced Analytics

The project should include:

* ABC analysis
* XYZ analysis
* ABC/XYZ matrix
* RFM analysis
* Customer segmentation
* Product profitability matrix
* Discount vs. margin analysis
* Revenue concentration
* Customer concentration
* Product concentration
* Business opportunity identification



# 7. Out of Scope

The following areas are outside the initial project scope:

* Full ERP implementation
* Procurement optimization
* Warehouse management
* Real-time data streaming
* Production planning
* Accounting
* Tax reporting
* Payroll
* Marketing attribution
* Automated production deployment
* Machine Learning forecasting

Forecasting and ML may be implemented as future project extensions.



# 8. Business Processes

## 8.1 Customer Management

Each customer should contain information such as:

* Customer ID
* Customer name
* Customer type
* Region
* City
* Registration date
* Assigned sales representative
* Customer status



## 8.2 Product Management

Each product should contain:

* Product ID
* SKU
* Product name
* Category
* Subcategory
* Brand
* Supplier
* Cost
* List price
* Product status



## 8.3 Sales Order

Each order should contain:

* Order ID
* Order date
* Customer
* Sales representative
* Sales channel
* Order status



## 8.4 Sales Order Lines

Each order line should contain:

* Order ID
* Product ID
* Quantity
* Unit price
* Discount
* Cost
* Revenue
* Gross profit

Returns should be represented separately or through an appropriate transaction type so that net sales are calculated correctly.



# 9. Data Volume Requirements

The project should contain a realistic dataset with approximately:

* **250,000+ sales/order-line records**
* **50,000+ orders**
* **5,000+ products**
* **1,000+ customers**
* **30+ brands**
* **15+ categories**
* **30+ subcategories**
* **20+ sales representatives**
* **24–36 months of historical data**

The dataset should contain enough complexity to make the analysis realistic.



# 10. Core KPIs

## Revenue

Revenue should represent net sales after discounts and returns.

Conceptually:

`Revenue = Quantity × Unit Price × (1 - Discount) - Returns`

The exact implementation should be documented.



## Units Sold

Total units sold adjusted for returns.



## Orders

Number of unique sales orders.



## Customers

Number of unique customers with transactions in the selected period.



## Average Order Value

`AOV = Revenue / Orders`



## Average Selling Price

`ASP = Revenue / Units Sold`



## Gross Profit

`Gross Profit = Revenue - COGS`



## Gross Margin %

`Gross Margin % = Gross Profit / Revenue`



## Discount %

The project should use a clearly documented discount definition.

One possible definition:

`Discount % = (List Price - Selling Price) / List Price`

The implementation should avoid double-counting discounts.



# 11. Business Questions

The analytical solution should answer at least the following questions.

## 11.1 Sales Performance

1. What is total revenue?
2. What is total gross profit?
3. What is gross margin?
4. How does revenue change over time?
5. How does profit change over time?
6. What are the monthly and quarterly trends?
7. What is YoY growth?
8. What is MoM growth?
9. What is the average order value?
10. What is the average selling price?
11. How many active customers do we have?



## 11.2 Product Performance

12. Which products generate the most revenue?
13. Which products generate the most profit?
14. Which products have the highest margins?
15. Which products generate high revenue but low margins?
16. Which products generate low revenue but high margins?
17. Which categories perform best?
18. Which brands perform best?
19. Which products are declining?
20. Which products should receive commercial attention?



## 11.3 Customer Performance

21. Which customers generate the most revenue?
22. Which customers generate the most profit?
23. Which customers purchase most frequently?
24. Which customers have become inactive?
25. Which customers are at risk?
26. Which customers have the highest lifetime/value potential?
27. How concentrated is revenue among the largest customers?
28. How does customer value differ by customer segment?



## 11.4 Pricing

29. What is the average discount?
30. How does discount level relate to margin?
31. Which products receive the highest discounts?
32. Which products have high discounts and low margins?
33. Are there pricing anomalies?
34. Which categories appear underpriced?
35. Where are pricing optimization opportunities?



## 11.5 Sales Organization

36. Which sales representatives generate the most revenue?
37. Which representatives generate the most profit?
38. Which representatives achieve the highest margins?
39. Which representatives manage the most valuable customers?
40. Are there significant performance differences between representatives?



## 11.6 Geography

41. Which regions generate the most revenue?
42. Which regions generate the most profit?
43. How does customer behavior differ between regions?



# 12. Advanced Analytical Requirements

# 12.1 ABC Analysis

ABC classification should primarily use revenue.

A secondary ABC classification may be performed using gross profit.

Initial thresholds:

* A = top 80%
* B = next 15%
* C = remaining 5%

The exact methodology should be documented.



# 12.2 XYZ Analysis

XYZ classification should measure demand variability.

For each product:

`CV = Standard Deviation of Monthly Demand / Average Monthly Demand`

Initial classification:

* X = stable demand
* Y = moderate variability
* Z = high variability

Thresholds should be documented and justified.



# 12.3 ABC/XYZ Matrix

Combine ABC and XYZ classifications:

* AX
* AY
* AZ
* BX
* BY
* BZ
* CX
* CY
* CZ

The analysis should identify:

* Core products
* High-value stable products
* High-value unstable products
* Low-value unstable products
* Stable long-tail products



# 12.4 RFM Analysis

RFM should use:

### Recency

How recently the customer purchased.

### Frequency

How frequently the customer purchases.

### Monetary

How much revenue the customer generates.

Potential segments:

* Champions
* Loyal Customers
* Potential Loyalists
* At Risk
* Lost
* New Customers

The segmentation methodology must be documented.



# 12.5 Product Profitability Matrix

Products should be classified using:

* Revenue
* Gross Margin %

Matrix:

### High Revenue + High Margin

Strategic core products.

### High Revenue + Low Margin

Potential pricing optimization opportunities.

### Low Revenue + High Margin

Potential growth opportunities.

### Low Revenue + Low Margin

Potential portfolio rationalization candidates.



# 13. Pricing Analysis

The analysis should investigate relationships between:

* List price
* Cost
* Selling price
* Discount
* Revenue
* Quantity
* Gross profit
* Gross margin

Important scenarios:

### High Discount + Low Margin

Potential discount abuse or pricing issue.

### High Sales + Low Margin

High-volume products that may require pricing optimization.

### Low Sales + High Margin

Potential growth opportunities.

### High Discount + High Volume

Potentially justified commercial strategy, but should be evaluated for profitability.

Recommendations should not rely solely on correlation.

The analysis should consider:

* Product category
* Brand
* Customer type
* Sales volume
* Customer value
* Competitive positioning where applicable



# 14. Data Quality Requirements

The project should include explicit data quality validation.

Checks should cover:

* Duplicate records
* Missing primary keys
* Missing foreign keys
* Invalid dates
* Invalid quantities
* Invalid prices
* Invalid discounts
* Negative quantities except returns
* Negative margins
* Duplicate orders
* Orphan records
* Inconsistent brands
* Inconsistent categories
* Invalid customer references
* Invalid product references

All identified issues should be documented.



# 15. Database Requirements

The primary database technology is:

**PostgreSQL**

The relational database should include:

* Primary keys
* Foreign keys
* NOT NULL constraints
* UNIQUE constraints
* CHECK constraints
* Referential integrity
* Appropriate data types
* Appropriate indexes

The database should be normalized appropriately for an operational/relational model.



# 16. Analytical Data Model

The analytical layer should use a **Star Schema**.

## Fact Table

### fact_sales

Possible measures:

* Quantity
* Revenue
* Cost
* Gross Profit
* Discount Amount



## Dimensions

### dim_date

* Date
* Day
* Month
* Month Name
* Quarter
* Year
* Week
* Year-Month

### dim_product

* Product
* SKU
* Category
* Subcategory
* Brand
* Supplier
* Status

### dim_customer

* Customer
* Customer Type
* City
* Region
* Registration Date
* Customer Status

### dim_brand

* Brand

### dim_category

* Category
* Subcategory

### dim_salesperson

* Sales Representative

### dim_region

* Region
* City

The final dimensional model should be documented with a Star Schema diagram.



# 17. SQL Requirements

SQL analysis should demonstrate proficiency with:

* SELECT
* WHERE
* GROUP BY
* ORDER BY
* CASE
* INNER JOIN
* LEFT JOIN
* CTEs
* Subqueries
* Date functions
* Conditional aggregation
* Window functions

Window functions should include examples such as:

* RANK
* DENSE_RANK
* LAG
* LEAD
* Running totals
* Moving averages

The SQL layer should contain approximately **30–50 meaningful analytical queries**.

Queries should be organized by business domain rather than as one large script.



# 18. Python Requirements

Python should complement SQL and Power BI rather than unnecessarily duplicate them.

Main technologies:

* Pandas
* NumPy
* Matplotlib
* Seaborn
* Jupyter Notebook

Python should be used for:

* Data generation
* Data quality analysis
* Exploratory Data Analysis
* Statistical exploration
* Supporting calculations
* Business-oriented visualizations



# 19. Power BI Requirements

The Power BI solution should contain four main pages.

# Page 1 — Executive Overview

Include:

* Revenue
* Gross Profit
* Gross Margin %
* Orders
* Customers
* Units Sold
* Revenue trend
* Profit trend
* Category performance
* Brand performance
* Regional performance

Purpose:

Provide management with a high-level overview of business performance.



# Page 2 — Product & Brand

Include:

* Top products by revenue
* Top products by profit
* Top brands
* Category performance
* Revenue vs Margin
* ABC classification
* Product profitability matrix

Purpose:

Identify product portfolio strengths, weaknesses and opportunities.



# Page 3 — Customer

Include:

* Customer ranking
* Revenue by customer
* Profit by customer
* Customer segmentation
* RFM
* Customer activity
* Regional customer analysis

Purpose:

Understand customer value, concentration and retention opportunities.



# Page 4 — Pricing & Profitability

Include:

* Discount vs Margin
* Margin by category
* Margin by brand
* High-discount products
* Low-margin products
* Pricing opportunities
* Profitability analysis

Purpose:

Identify pricing and commercial opportunities.



# 20. DAX Requirements

The Power BI model should contain measures such as:

* Total Revenue
* Total Cost
* Gross Profit
* Gross Margin %
* Total Orders
* Total Customers
* Units Sold
* AOV
* ASP
* Revenue YoY
* YoY %
* Revenue MoM
* MoM %
* Profit YoY
* Customer Revenue
* Customer Profit

Measures should be organized logically and documented where appropriate.



# 21. Dashboard Design Requirements

The dashboard should follow professional BI design principles.

Requirements:

* Clear visual hierarchy
* Consistent KPI definitions
* Minimal unnecessary visuals
* Appropriate chart selection
* Interactive filters
* Clear chart titles
* Consistent formatting
* Business-oriented storytelling
* Decision-oriented visuals

Where useful, implement:

* Drill-down
* Drill-through
* Tooltips
* Slicers
* Conditional formatting

The dashboard should prioritize decision-making rather than visual decoration.



# 22. Business Insights

The final project should produce approximately:

**8–12 significant business insights**

Each insight should follow the structure:

### Finding

What happened?

### Evidence

What data supports the finding?

### Business Impact

Why does it matter?

### Recommendation

What should the business do?

Exact numerical values should be calculated from the actual project dataset.



# 23. Business Recommendations

Recommendations should cover relevant areas such as:

## Pricing

* Optimize discounts
* Identify underpriced products
* Protect high-margin products
* Review high-discount / low-margin combinations

## Product Portfolio

* Prioritize high-value products
* Review low-performing products
* Identify growth opportunities
* Use ABC/XYZ to prioritize products

## Customers

* Retain high-value customers
* Reactivate inactive customers
* Target at-risk customers
* Develop customer segmentation strategies

## Sales Representatives

* Identify top performers
* Analyze performance differences
* Identify opportunities for coaching or portfolio redistribution

## Brands

* Identify strategic brands
* Compare profitability
* Detect brands with strong sales but weak margins

## Geography

* Identify strong and weak regions
* Analyze regional opportunities
* Compare customer behavior across regions

Recommendations should be measurable where possible.



# 24. Technical Deliverables

The project should contain:

* README
* PostgreSQL database scripts
* SQL analytical queries
* Python notebooks
* Raw data
* Processed data
* Power BI dashboard
* Data dictionary
* Data model documentation
* Methodology documentation
* Business insights
* ERD
* Star Schema diagram
* Data pipeline diagram
* Final presentation



# 25. GitHub Repository Structure

```text
autoparts-sales-bi-analytics/
│
├── README.md
├── LICENSE
├── .gitignore
│
├── database/
│   ├── 01_create_database.sql
│   ├── 02_create_tables.sql
│   ├── 03_constraints.sql
│   ├── 04_indexes.sql
│   ├── 05_views.sql
│   └── 06_seed_data.sql
│
├── data/
│   ├── README.md
│   ├── raw/
│   └── processed/
│
├── sql/
│   ├── 01_exploration.sql
│   ├── 02_sales_analysis.sql
│   ├── 03_product_analysis.sql
│   ├── 04_customer_analysis.sql
│   ├── 05_pricing_analysis.sql
│   ├── 06_profitability_analysis.sql
│   └── 07_advanced_analysis.sql
│
├── python/
│   ├── 01_data_generation.ipynb
│   ├── 02_data_quality.ipynb
│   └── 03_eda.ipynb
│
├── powerbi/
│   ├── AutoParts_Sales_Analytics.pbix
│   └── screenshots/
│
├── documentation/
│   ├── business_requirements.md
│   ├── data_dictionary.md
│   ├── data_model.md
│   ├── methodology.md
│   └── business_insights.md
│
├── diagrams/
│   ├── erd.png
│   ├── star_schema.png
│   └── data_pipeline.png
│
└── presentation/
    └── AutoParts_Sales_BI_Analytics.pdf
```



# 26. Success Criteria

The project is considered complete when:

## Database

* [ ] PostgreSQL database implemented
* [ ] Relational model documented
* [ ] PK/FK relationships implemented
* [ ] Constraints implemented
* [ ] Appropriate indexes implemented
* [ ] ERD created

## Data

* [ ] Realistic synthetic dataset created
* [ ] At least 250k sales/order-line records
* [ ] At least 5k products
* [ ] At least 1k customers
* [ ] 24–36 months of data
* [ ] Data quality checks completed

## SQL

* [ ] Core business KPIs calculated
* [ ] Sales analysis completed
* [ ] Product analysis completed
* [ ] Customer analysis completed
* [ ] Pricing analysis completed
* [ ] Profitability analysis completed
* [ ] Window functions demonstrated
* [ ] CTEs demonstrated

## Python

* [ ] Data quality analysis
* [ ] EDA
* [ ] Statistical analysis
* [ ] Business-oriented visualizations

## BI

* [ ] Star Schema created
* [ ] DAX measures created
* [ ] Four Power BI pages completed
* [ ] Interactive filtering implemented
* [ ] Dashboard validated

## Business Analysis

* [ ] ABC analysis
* [ ] XYZ analysis
* [ ] ABC/XYZ matrix
* [ ] RFM analysis
* [ ] Customer segmentation
* [ ] Pricing analysis
* [ ] Profitability matrix
* [ ] 8–12 key insights
* [ ] Actionable recommendations

## Portfolio

* [ ] README completed
* [ ] Repository organized
* [ ] Screenshots included
* [ ] ERD included
* [ ] Data model documented
* [ ] Presentation completed
* [ ] Git history is clean and meaningful
