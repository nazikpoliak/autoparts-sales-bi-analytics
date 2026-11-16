# AutoParts Sales & BI Analytics

An end-to-end Data Analytics and Business Intelligence project focused on automotive parts distribution. The project demonstrates the complete analytical lifecycle, from relational database design and data generation to SQL analysis, Python EDA, Power BI dashboards, and actionable business recommendations.

## 1. Project Overview

**Industry:** Automotive Parts Distribution  
**Project Type:** End-to-End Data Analytics / Business Intelligence  
**Database:** PostgreSQL  
**Tools:** SQL, Python, Pandas, NumPy, Matplotlib, Seaborn, Power BI, DAX

### Business Objective

Build a unified analytical solution that enables management to evaluate sales performance, profitability, customer value, product performance, pricing effectiveness, and regional growth.

The project aims to transform transactional data into actionable business insights and demonstrate practical Data Analyst / BI Analyst skills.

## 2. Business Context

The company is a B2B automotive parts distributor serving independent workshops, retail parts stores, fleet operators, service stations, and regional distributors.

Management needs better visibility into:

- Revenue, gross profit, and margin trends.
- Product, brand, and category performance.
- Customer value, retention, and inactivity.
- Pricing effectiveness and discount impact.
- Sales representative performance.
- Regional performance and revenue concentration.
- Commercial risks and growth opportunities.

## 3. Project Scope

The solution covers six core analytical domains:

| Domain | Key Areas |
|---|---|
| Sales Analytics | Revenue, profit, orders, units sold, AOV, ASP, growth trends |
| Product Analytics | SKU, categories, brands, product performance, profitability |
| Customer Analytics | Customer value, purchase frequency, activity, segmentation |
| Pricing Analytics | Discounts, selling prices, margins, pricing opportunities |
| Sales Performance | Sales representatives, customer portfolios, regional comparisons |
| Advanced Analytics | ABC/XYZ, RFM, concentration risk, profitability matrix |

## 4. Dataset

The project uses synthetically generated transactional data designed to simulate a realistic automotive parts distributor.

**Target dataset specifications:**

- 250,000+ sales order lines.
- 50,000+ sales orders.
- 5,000+ products.
- 1,000+ customers.
- 30+ brands.
- 15+ categories and 30+ subcategories.
- 20+ sales representatives.
- 24–36 months of historical data.

The dataset includes customers, products, brands, categories, suppliers, sales representatives, regions, orders, order lines, pricing, discounts, costs, and returns.

Synthetic data is used to demonstrate analytical methods without exposing real business information.

## 5. Technical Approach

The project follows an end-to-end analytical workflow:

**Data Generation → PostgreSQL → Data Quality → SQL Analytics → Python EDA → Star Schema → Power BI → Business Insights**

### PostgreSQL
- Design a normalized relational database.
- Implement primary keys, foreign keys, constraints, and indexes.
- Generate and validate transactional data.
- Maintain referential integrity.

### SQL Analytics
Develop 30–50 analytical queries covering:

- Sales and profitability.
- Product and brand performance.
- Customer behavior and segmentation.
- Pricing and discount analysis.
- Sales representative and regional performance.
- Advanced analytics using CTEs, subqueries, and window functions.

### Python
Use Pandas, NumPy, Matplotlib, and Seaborn for:

- Synthetic data generation.
- Data quality validation.
- Exploratory data analysis.
- Statistical exploration.
- Business-oriented visualizations.

### Power BI
Build a dimensional model using a Star Schema, supported by documented DAX measures and interactive dashboards.

## 6. Key Performance Indicators

The analytical model includes the following KPIs:

| KPI | Definition |
|---|---|
| Revenue | Net sales after discounts and returns |
| Gross Profit | Net revenue minus cost of goods sold |
| Gross Margin % | Gross profit divided by net revenue |
| Orders | Number of unique sales orders |
| Customers | Number of unique purchasing customers |
| Units Sold | Units sold adjusted for returns |
| Average Order Value | Revenue divided by orders |
| Average Selling Price | Revenue divided by net units sold |
| Revenue Growth | Month-over-month and year-over-year changes |
| Discount % | Discount relative to list price |

KPI definitions and calculation rules will be documented to ensure consistency across SQL, Python, and Power BI.

## 7. Advanced Analytics

### ABC Analysis
Classify products by cumulative revenue contribution:

- **A:** Top 80%.
- **B:** Next 15%.
- **C:** Remaining 5%.

### XYZ Analysis
Classify products by monthly demand variability using the coefficient of variation (CV).

Thresholds will be documented and validated against the generated dataset.

### ABC/XYZ Matrix
Combine revenue importance and demand stability to identify strategic products, stable core items, and high-variability products.

### RFM Analysis
Segment customers by:

- **Recency:** Time since the last purchase.
- **Frequency:** Number of purchases.
- **Monetary:** Revenue generated.

Potential segments include Champions, Loyal Customers, Potential Loyalists, At Risk, Lost, and New Customers.

### Product Profitability Matrix
Classify products by revenue and gross margin to identify:

- High-revenue, high-margin products.
- High-revenue, low-margin products.
- Low-revenue, high-margin growth opportunities.
- Low-revenue, low-margin products for portfolio review.

Additional analyses cover discount effectiveness, revenue concentration, customer concentration, and pricing opportunities.

## 8. Power BI Dashboard

The dashboard consists of four analytical pages.

| Page | Focus |
|---|---|
| Executive Overview | Revenue, profit, margins, trends, and overall performance |
| Product & Brand | Product rankings, categories, brands, ABC classification, profitability |
| Customer Analytics | Customer value, RFM segments, activity, and concentration |
| Pricing & Profitability | Discounts, margins, pricing opportunities, and low-margin products |

The dashboard will include interactive filters, KPI cards, trend charts, rankings, and decision-oriented visualizations.

## 9. Business Insights & Recommendations

The final analysis will deliver 8–12 evidence-based business insights.

Each insight will include:

1. **Finding** — What happened?
2. **Evidence** — What data supports the finding?
3. **Business Impact** — Why does it matter?
4. **Recommendation** — What action should be taken?

Recommendations will focus on pricing optimization, product portfolio management, customer retention, sales performance, brand profitability, and regional opportunities.

All quantitative findings will be calculated from the generated dataset rather than invented in advance.

## 10. Deliverables

- PostgreSQL relational database and ERD.
- Synthetic transactional dataset.
- Data quality validation.
- SQL analytical query library.
- Python notebooks for generation and EDA.
- Star Schema and data model documentation.
- Interactive Power BI dashboard with DAX measures.
- ABC/XYZ, RFM, and profitability analyses.
- Business insights and actionable recommendations.
- Technical documentation and final presentation.

## 11. Success Criteria

The project is complete when:

- The relational database and analytical data model are implemented.
- The dataset meets the defined volume requirements.
- Data quality checks are completed and documented.
- SQL analyses cover the core business questions.
- Python EDA and statistical exploration are completed.
- All four Power BI dashboard pages are implemented and validated.
- Advanced analytical methods are documented.
- Business insights and recommendations are supported by data.
- The repository is organized and ready for portfolio presentation.

## 12. Future Enhancements

Potential extensions include sales forecasting, machine learning, automated data pipelines, and additional profitability optimization models.

---

**Project Status:** In Development
