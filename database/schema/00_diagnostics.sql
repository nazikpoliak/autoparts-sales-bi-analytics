-- =====================================================================================
-- 00_diagnostics.sql  |  AutoParts Sales & BI Analytics  |  P0-0 read-only diagnostics
-- =====================================================================================
-- PURPOSE   Show the REAL state of the live PostgreSQL database (structure, row counts, duplicates,
--           integrity, dates, returns, prices, statuses) without changing anything.
-- READ-ONLY The script contains only SELECT statements and session SET/RESET. The session is switched to
--           default_transaction_read_only = on, so PostgreSQL itself rejects any write.
-- RUN       Recommended (psql, results in a file; errors in a second file):
--             psql -h <host> -U <user> -d autoparts_bi -P pager=off -f 00_diagnostics.sql -o diagnostics_output.txt 2> diagnostics_errors.txt
--           GUI tools: DBeaver "Execute script" (Alt+X) shows one result tab per statement; in pgAdmin run the
--           statements one by one (each "A..", "B..", "D.." block is one statement).
-- OUTPUT    Sections A and B return the same 5 columns: check_id, check_name, value, expected, status.
--           status: OK | PROBLEM | WARN | BELOW_TARGET | DIFFERS | OUT_OF_RANGE | INFO | NO_DATA | MISSING_* | EXTRA_* | *_DIFF
--           Section D returns detail rows. Full explanation of every check (Ukrainian): 00_diagnostics_guide.md
-- SCHEMA    Section A compares the live structure with 01_schema.sql. Section B/D use the column names of
--           01_schema.sql. If A shows a missing table/column, the dependent B/D statement fails with an error
--           (it is written to diagnostics_errors.txt): send both files back.
-- TABLES    Names are not schema-qualified: they resolve through search_path (normally public). A0.2 shows
--           in which schemas the tables were found.
-- =====================================================================================

SET client_encoding = 'UTF8';
SET default_transaction_read_only = on;
SET statement_timeout = '300s';


-- =====================================================================================
-- A0. Environment
-- =====================================================================================
SELECT 'A0.1' AS check_id, 'Database / server' AS check_name,
       current_database() || ' / ' || split_part(version(), ' on ', 1) AS value,
       'autoparts_bi' AS expected,
       CASE WHEN current_database() = 'autoparts_bi' THEN 'OK' ELSE 'CHECK_DB_NAME' END AS status
UNION ALL
SELECT 'A0.2', 'Schemas that contain tables named orders / customers',
       COALESCE(string_agg(DISTINCT table_schema, ', '), 'NONE'), 'public',
       CASE WHEN count(*) = 0 THEN 'PROBLEM' ELSE 'INFO' END
FROM information_schema.tables WHERE table_name IN ('orders', 'customers')
UNION ALL
SELECT 'A0.3', 'Current search_path', current_setting('search_path'), 'includes the schema from A0.2', 'INFO'
UNION ALL
SELECT 'A0.4', 'Session is read-only', current_setting('default_transaction_read_only'), 'on',
       CASE WHEN current_setting('default_transaction_read_only') = 'on' THEN 'OK' ELSE 'PROBLEM' END
ORDER BY 1;


-- =====================================================================================
-- A1. The 18 expected tables exist (and which tables are extra)
-- =====================================================================================
WITH expected(tbl) AS (VALUES
  ('regions'),
  ('cities'),
  ('customer_types'),
  ('customers'),
  ('salespersons'),
  ('sales_channels'),
  ('order_statuses'),
  ('brands'),
  ('categories'),
  ('subcategories'),
  ('suppliers'),
  ('product_statuses'),
  ('products'),
  ('orders'),
  ('order_items'),
  ('return_reasons'),
  ('returns'),
  ('return_items')
), actual AS (
  SELECT n.nspname AS sch, c.relname AS tbl
  FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
  WHERE c.relkind IN ('r', 'p')
    AND n.nspname NOT IN ('pg_catalog', 'information_schema') AND n.nspname NOT LIKE 'pg_toast%'
)
SELECT 'A1' AS check_id,
       COALESCE(e.tbl, a.tbl) AS check_name,
       COALESCE(a.sch || '.' || a.tbl, 'MISSING') AS value,
       'present' AS expected,
       CASE WHEN e.tbl IS NULL THEN 'EXTRA_TABLE' WHEN a.tbl IS NULL THEN 'MISSING_TABLE' ELSE 'OK' END AS status
FROM expected e FULL JOIN actual a ON a.tbl = e.tbl
ORDER BY (CASE WHEN e.tbl IS NULL THEN 2 WHEN a.tbl IS NULL THEN 0 ELSE 1 END), 2;


-- =====================================================================================
-- A2. Columns, types, nullability and identity versus 01_schema.sql (only deviations + a summary row)
--     expected list = column dump of 01_schema.sql loaded into a scratch database (89 columns)
-- =====================================================================================
WITH expected(tbl, col, typ, is_nullable, identity) AS (VALUES
('brands','brand_id','integer','NO','a'),
('brands','brand_name','character varying(100)','NO',''),
('categories','category_id','integer','NO','a'),
('categories','category_name','character varying(100)','NO',''),
('cities','city_id','integer','NO','a'),
('cities','region_id','integer','NO',''),
('cities','city_name','character varying(100)','NO',''),
('customer_types','customer_type_id','integer','NO','a'),
('customer_types','type_name','character varying(50)','NO',''),
('customers','customer_id','integer','NO','a'),
('customers','customer_type_id','integer','NO',''),
('customers','city_id','integer','YES',''),
('customers','customer_name','character varying(200)','NO',''),
('customers','tax_id','character varying(50)','YES',''),
('customers','phone','character varying(50)','YES',''),
('customers','email','character varying(150)','YES',''),
('customers','address','character varying(255)','YES',''),
('customers','registration_date','date','YES',''),
('customers','is_active','boolean','NO',''),
('order_items','order_item_id','bigint','NO','a'),
('order_items','order_id','bigint','NO',''),
('order_items','product_id','integer','NO',''),
('order_items','quantity','numeric(12,3)','NO',''),
('order_items','unit_sale_price','numeric(12,2)','NO',''),
('order_items','unit_cost','numeric(12,2)','NO',''),
('order_items','discount_amount','numeric(12,2)','NO',''),
('order_statuses','order_status_id','integer','NO','a'),
('order_statuses','status_name','character varying(50)','NO',''),
('orders','order_id','bigint','NO','a'),
('orders','customer_id','integer','NO',''),
('orders','salesperson_id','integer','YES',''),
('orders','sales_channel_id','integer','NO',''),
('orders','order_status_id','integer','NO',''),
('orders','order_date','timestamp without time zone','NO',''),
('orders','customer_reference','character varying(100)','YES',''),
('orders','notes','text','YES',''),
('product_statuses','product_status_id','integer','NO','a'),
('product_statuses','status_name','character varying(50)','NO',''),
('products','product_id','integer','NO','a'),
('products','subcategory_id','integer','NO',''),
('products','brand_id','integer','NO',''),
('products','supplier_id','integer','NO',''),
('products','product_status_id','integer','NO',''),
('products','sku','character varying(100)','NO',''),
('products','product_name','character varying(255)','NO',''),
('products','description','text','YES',''),
('products','unit_of_measure','character varying(20)','NO',''),
('products','purchase_price','numeric(12,2)','NO',''),
('products','standard_sale_price','numeric(12,2)','NO',''),
('products','weight_kg','numeric(10,3)','YES',''),
('products','created_at','timestamp without time zone','NO',''),
('regions','region_id','integer','NO','a'),
('regions','region_name','character varying(100)','NO',''),
('return_items','return_item_id','bigint','NO','a'),
('return_items','return_id','bigint','NO',''),
('return_items','order_item_id','bigint','NO',''),
('return_items','product_id','integer','NO',''),
('return_items','quantity','numeric(12,3)','NO',''),
('return_items','refund_unit_price','numeric(12,2)','NO',''),
('return_reasons','return_reason_id','integer','NO','a'),
('return_reasons','reason_name','character varying(150)','NO',''),
('return_reasons','description','text','YES',''),
('return_reasons','is_active','boolean','NO',''),
('returns','return_id','bigint','NO','a'),
('returns','order_id','bigint','NO',''),
('returns','customer_id','integer','NO',''),
('returns','return_reason_id','integer','NO',''),
('returns','return_date','timestamp without time zone','NO',''),
('returns','notes','text','YES',''),
('sales_channels','sales_channel_id','integer','NO','a'),
('sales_channels','channel_name','character varying(50)','NO',''),
('salespersons','salesperson_id','integer','NO','a'),
('salespersons','region_id','integer','YES',''),
('salespersons','first_name','character varying(100)','NO',''),
('salespersons','last_name','character varying(100)','NO',''),
('salespersons','email','character varying(150)','YES',''),
('salespersons','phone','character varying(50)','YES',''),
('salespersons','hire_date','date','YES',''),
('salespersons','is_active','boolean','NO',''),
('subcategories','subcategory_id','integer','NO','a'),
('subcategories','category_id','integer','NO',''),
('subcategories','subcategory_name','character varying(100)','NO',''),
('suppliers','supplier_id','integer','NO','a'),
('suppliers','supplier_name','character varying(200)','NO',''),
('suppliers','contact_name','character varying(150)','YES',''),
('suppliers','phone','character varying(50)','YES',''),
('suppliers','email','character varying(150)','YES',''),
('suppliers','country','character varying(100)','YES',''),
('suppliers','is_active','boolean','NO','')
), actual AS (
  SELECT c.relname AS tbl, a.attname AS col, format_type(a.atttypid, a.atttypmod) AS typ,
         CASE WHEN a.attnotnull THEN 'NO' ELSE 'YES' END AS is_nullable, a.attidentity::text AS identity
  FROM pg_attribute a JOIN pg_class c ON c.oid = a.attrelid JOIN pg_namespace n ON n.oid = c.relnamespace
  WHERE c.relkind IN ('r', 'p') AND a.attnum > 0 AND NOT a.attisdropped
    AND n.nspname NOT IN ('pg_catalog', 'information_schema') AND n.nspname NOT LIKE 'pg_toast%'
    AND c.relname IN (SELECT DISTINCT tbl FROM expected)
), diff AS (
  SELECT COALESCE(e.tbl, a.tbl) AS tbl, COALESCE(e.col, a.col) AS col,
         CASE WHEN e.col IS NULL THEN 'EXTRA_COLUMN'
              WHEN a.col IS NULL THEN 'MISSING_COLUMN'
              WHEN e.typ <> a.typ THEN 'TYPE_DIFF'
              WHEN e.is_nullable <> a.is_nullable THEN 'NULLABILITY_DIFF'
              WHEN e.identity <> a.identity THEN 'IDENTITY_DIFF' END AS status,
         COALESCE(a.typ || ' / nullable=' || a.is_nullable, 'absent') AS actual_def,
         COALESCE(e.typ || ' / nullable=' || e.is_nullable, 'absent') AS expected_def
  FROM expected e FULL JOIN actual a ON a.tbl = e.tbl AND a.col = e.col
  WHERE e.col IS NULL OR a.col IS NULL OR e.typ <> a.typ OR e.is_nullable <> a.is_nullable OR e.identity <> a.identity
)
SELECT 'A2.0' AS check_id, 'Columns that deviate from 01_schema.sql' AS check_name, count(*)::text AS value, '0' AS expected,
       CASE WHEN count(*) = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM diff
UNION ALL
SELECT 'A2.1', tbl || '.' || col || ' (actual: ' || actual_def || ')', status, expected_def, status FROM diff
ORDER BY 1, 2;


-- =====================================================================================
-- A3. Constraints (PK / FK / UNIQUE / CHECK) versus 01_schema.sql: by name, type and definition
--     expected list = constraint dump of 01_schema.sql (62 constraints)
-- =====================================================================================
WITH expected(tbl, name, typ, def) AS (VALUES
('brands','brands_brand_name_key','u','UNIQUE (brand_name)'),
('brands','brands_pkey','p','PRIMARY KEY (brand_id)'),
('categories','categories_category_name_key','u','UNIQUE (category_name)'),
('categories','categories_pkey','p','PRIMARY KEY (category_id)'),
('cities','cities_pkey','p','PRIMARY KEY (city_id)'),
('cities','fk_cities_region','f','FOREIGN KEY (region_id) REFERENCES regions(region_id)'),
('cities','uq_cities_region_name','u','UNIQUE (region_id, city_name)'),
('customer_types','customer_types_pkey','p','PRIMARY KEY (customer_type_id)'),
('customer_types','customer_types_type_name_key','u','UNIQUE (type_name)'),
('customers','customers_pkey','p','PRIMARY KEY (customer_id)'),
('customers','fk_customers_city','f','FOREIGN KEY (city_id) REFERENCES cities(city_id)'),
('customers','fk_customers_type','f','FOREIGN KEY (customer_type_id) REFERENCES customer_types(customer_type_id)'),
('customers','uq_customers_tax_id','u','UNIQUE (tax_id)'),
('order_items','chk_order_items_cost','c','CHECK ((unit_cost >= (0)::numeric))'),
('order_items','chk_order_items_discount','c','CHECK ((discount_amount >= (0)::numeric))'),
('order_items','chk_order_items_quantity','c','CHECK ((quantity > (0)::numeric))'),
('order_items','chk_order_items_sale_price','c','CHECK ((unit_sale_price >= (0)::numeric))'),
('order_items','fk_order_items_order','f','FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE'),
('order_items','fk_order_items_product','f','FOREIGN KEY (product_id) REFERENCES products(product_id)'),
('order_items','order_items_pkey','p','PRIMARY KEY (order_item_id)'),
('order_statuses','order_statuses_pkey','p','PRIMARY KEY (order_status_id)'),
('order_statuses','order_statuses_status_name_key','u','UNIQUE (status_name)'),
('orders','fk_orders_channel','f','FOREIGN KEY (sales_channel_id) REFERENCES sales_channels(sales_channel_id)'),
('orders','fk_orders_customer','f','FOREIGN KEY (customer_id) REFERENCES customers(customer_id)'),
('orders','fk_orders_salesperson','f','FOREIGN KEY (salesperson_id) REFERENCES salespersons(salesperson_id)'),
('orders','fk_orders_status','f','FOREIGN KEY (order_status_id) REFERENCES order_statuses(order_status_id)'),
('orders','orders_pkey','p','PRIMARY KEY (order_id)'),
('product_statuses','product_statuses_pkey','p','PRIMARY KEY (product_status_id)'),
('product_statuses','product_statuses_status_name_key','u','UNIQUE (status_name)'),
('products','chk_products_purchase_price','c','CHECK ((purchase_price >= (0)::numeric))'),
('products','chk_products_sale_price','c','CHECK ((standard_sale_price >= (0)::numeric))'),
('products','chk_products_weight','c','CHECK (((weight_kg IS NULL) OR (weight_kg >= (0)::numeric)))'),
('products','fk_products_brand','f','FOREIGN KEY (brand_id) REFERENCES brands(brand_id)'),
('products','fk_products_status','f','FOREIGN KEY (product_status_id) REFERENCES product_statuses(product_status_id)'),
('products','fk_products_subcategory','f','FOREIGN KEY (subcategory_id) REFERENCES subcategories(subcategory_id)'),
('products','fk_products_supplier','f','FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)'),
('products','products_pkey','p','PRIMARY KEY (product_id)'),
('products','products_sku_key','u','UNIQUE (sku)'),
('regions','regions_pkey','p','PRIMARY KEY (region_id)'),
('regions','regions_region_name_key','u','UNIQUE (region_name)'),
('return_items','chk_return_items_quantity','c','CHECK ((quantity > (0)::numeric))'),
('return_items','chk_return_items_refund_price','c','CHECK ((refund_unit_price >= (0)::numeric))'),
('return_items','fk_return_items_order_item','f','FOREIGN KEY (order_item_id) REFERENCES order_items(order_item_id)'),
('return_items','fk_return_items_product','f','FOREIGN KEY (product_id) REFERENCES products(product_id)'),
('return_items','fk_return_items_return','f','FOREIGN KEY (return_id) REFERENCES returns(return_id) ON DELETE CASCADE'),
('return_items','return_items_pkey','p','PRIMARY KEY (return_item_id)'),
('return_items','uq_return_items_return_order_item','u','UNIQUE (return_id, order_item_id)'),
('return_reasons','return_reasons_pkey','p','PRIMARY KEY (return_reason_id)'),
('return_reasons','return_reasons_reason_name_key','u','UNIQUE (reason_name)'),
('returns','fk_returns_customer','f','FOREIGN KEY (customer_id) REFERENCES customers(customer_id)'),
('returns','fk_returns_order','f','FOREIGN KEY (order_id) REFERENCES orders(order_id)'),
('returns','fk_returns_reason','f','FOREIGN KEY (return_reason_id) REFERENCES return_reasons(return_reason_id)'),
('returns','returns_pkey','p','PRIMARY KEY (return_id)'),
('sales_channels','sales_channels_channel_name_key','u','UNIQUE (channel_name)'),
('sales_channels','sales_channels_pkey','p','PRIMARY KEY (sales_channel_id)'),
('salespersons','fk_salespersons_region','f','FOREIGN KEY (region_id) REFERENCES regions(region_id)'),
('salespersons','salespersons_pkey','p','PRIMARY KEY (salesperson_id)'),
('subcategories','fk_subcategories_category','f','FOREIGN KEY (category_id) REFERENCES categories(category_id)'),
('subcategories','subcategories_pkey','p','PRIMARY KEY (subcategory_id)'),
('subcategories','uq_subcategories_category_name','u','UNIQUE (category_id, subcategory_name)'),
('suppliers','suppliers_pkey','p','PRIMARY KEY (supplier_id)'),
('suppliers','suppliers_supplier_name_key','u','UNIQUE (supplier_name)')
), actual AS (
  SELECT cl.relname AS tbl, co.conname AS name, co.contype::text AS typ, pg_get_constraintdef(co.oid) AS def
  FROM pg_constraint co JOIN pg_class cl ON cl.oid = co.conrelid JOIN pg_namespace n ON n.oid = cl.relnamespace
  WHERE co.contype IN ('p', 'f', 'u', 'c') AND n.nspname NOT IN ('pg_catalog', 'information_schema')
    AND cl.relname IN (SELECT DISTINCT tbl FROM expected)
), diff AS (
  SELECT COALESCE(e.tbl, a.tbl) AS tbl, COALESCE(e.name, a.name) AS name,
         CASE WHEN e.name IS NULL THEN 'EXTRA_CONSTRAINT'
              WHEN a.name IS NULL THEN 'MISSING_CONSTRAINT'
              WHEN e.typ <> a.typ THEN 'TYPE_DIFF' ELSE 'DEFINITION_DIFF' END AS status,
         COALESCE(a.def, 'absent') AS actual_def, COALESCE(e.def, 'absent') AS expected_def
  FROM expected e FULL JOIN actual a ON a.tbl = e.tbl AND a.name = e.name
  WHERE e.name IS NULL OR a.name IS NULL OR e.typ <> a.typ OR e.def <> a.def
)
SELECT 'A3.0' AS check_id, 'Constraints that deviate from 01_schema.sql' AS check_name, count(*)::text AS value, '0' AS expected,
       CASE WHEN count(*) = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM diff
UNION ALL
SELECT 'A3.1', tbl || '.' || name || ' (actual: ' || actual_def || ')', status, expected_def, status FROM diff
ORDER BY 1, 2;


-- =====================================================================================
-- A4. Indexes versus 01_schema.sql (by name; 55 expected including PK/UNIQUE indexes)
-- =====================================================================================
WITH expected(tbl, idx) AS (VALUES
('brands','brands_brand_name_key'),
('brands','brands_pkey'),
('categories','categories_category_name_key'),
('categories','categories_pkey'),
('cities','cities_pkey'),
('cities','idx_cities_region_id'),
('cities','uq_cities_region_name'),
('customer_types','customer_types_pkey'),
('customer_types','customer_types_type_name_key'),
('customers','customers_pkey'),
('customers','idx_customers_city_id'),
('customers','idx_customers_customer_type_id'),
('customers','uq_customers_tax_id'),
('order_items','idx_order_items_order_id'),
('order_items','idx_order_items_product_id'),
('order_items','order_items_pkey'),
('order_statuses','order_statuses_pkey'),
('order_statuses','order_statuses_status_name_key'),
('orders','idx_orders_customer_id'),
('orders','idx_orders_order_date'),
('orders','idx_orders_sales_channel_id'),
('orders','idx_orders_salesperson_id'),
('orders','idx_orders_status_id'),
('orders','orders_pkey'),
('product_statuses','product_statuses_pkey'),
('product_statuses','product_statuses_status_name_key'),
('products','idx_products_brand_id'),
('products','idx_products_status_id'),
('products','idx_products_subcategory_id'),
('products','idx_products_supplier_id'),
('products','products_pkey'),
('products','products_sku_key'),
('regions','regions_pkey'),
('regions','regions_region_name_key'),
('return_items','idx_return_items_order_item_id'),
('return_items','idx_return_items_product_id'),
('return_items','idx_return_items_return_id'),
('return_items','return_items_pkey'),
('return_items','uq_return_items_return_order_item'),
('return_reasons','return_reasons_pkey'),
('return_reasons','return_reasons_reason_name_key'),
('returns','idx_returns_customer_id'),
('returns','idx_returns_order_id'),
('returns','idx_returns_return_date'),
('returns','idx_returns_return_reason_id'),
('returns','returns_pkey'),
('sales_channels','sales_channels_channel_name_key'),
('sales_channels','sales_channels_pkey'),
('salespersons','idx_salespersons_region_id'),
('salespersons','salespersons_pkey'),
('subcategories','idx_subcategories_category_id'),
('subcategories','subcategories_pkey'),
('subcategories','uq_subcategories_category_name'),
('suppliers','suppliers_pkey'),
('suppliers','suppliers_supplier_name_key')
), actual AS (
  SELECT tablename AS tbl, indexname AS idx FROM pg_indexes
  WHERE schemaname NOT IN ('pg_catalog', 'information_schema') AND tablename IN (SELECT DISTINCT tbl FROM expected)
), diff AS (
  SELECT COALESCE(e.tbl, a.tbl) AS tbl, COALESCE(e.idx, a.idx) AS idx,
         CASE WHEN e.idx IS NULL THEN 'EXTRA_INDEX' ELSE 'MISSING_INDEX' END AS status
  FROM expected e FULL JOIN actual a ON a.tbl = e.tbl AND a.idx = e.idx
  WHERE e.idx IS NULL OR a.idx IS NULL
)
SELECT 'A4.0' AS check_id, 'Indexes that deviate from 01_schema.sql' AS check_name, count(*)::text AS value, '0' AS expected,
       CASE WHEN count(*) = 0 THEN 'OK' ELSE 'WARN' END AS status
FROM diff
UNION ALL
SELECT 'A4.1', tbl || '.' || idx, status, 'see 01_schema.sql', status FROM diff
ORDER BY 1, 2;


-- =====================================================================================
-- A5. Columns that exist ONLY in the ERD image (not in 01_schema.sql): does the live DB follow the ERD?
--     PRESENT_IN_DB = the live DB was built from the ERD design, not from 01_schema.sql.
-- =====================================================================================
WITH erd_only(tbl, col) AS (VALUES
  ('customers','customer_code'),
  ('customers','salesperson_id'),
  ('customers','status'),
  ('customers','created_at'),
  ('salespersons','employee_code'),
  ('salespersons','status'),
  ('brands','country'),
  ('brands','status'),
  ('suppliers','status'),
  ('products','unit_cost'),
  ('products','list_price'),
  ('orders','order_number'),
  ('orders','currency'),
  ('orders','created_at'),
  ('order_items','unit_price'),
  ('order_items','discount_pct'),
  ('returns','return_number'),
  ('returns','status'),
  ('returns','created_at'),
  ('return_items','unit_price')
)
SELECT 'A5.1' AS check_id, e.tbl || '.' || e.col AS check_name,
       CASE WHEN a.attname IS NULL THEN 'absent' ELSE 'PRESENT_IN_DB' END AS value, 'absent' AS expected,
       CASE WHEN a.attname IS NULL THEN 'OK' ELSE 'ERD_COLUMN_PRESENT' END AS status
FROM erd_only e
LEFT JOIN (SELECT c.relname, a.attname FROM pg_attribute a JOIN pg_class c ON c.oid = a.attrelid
           JOIN pg_namespace n ON n.oid = c.relnamespace
           WHERE c.relkind IN ('r', 'p') AND a.attnum > 0 AND NOT a.attisdropped
             AND n.nspname NOT IN ('pg_catalog', 'information_schema')) a ON a.relname = e.tbl AND a.attname = e.col
ORDER BY 3 DESC, 2;


-- =====================================================================================
-- A6. Checks that CANNOT be performed with the schema of 01_schema.sql (informational list)
-- =====================================================================================
SELECT * FROM (VALUES
 ('A6.1', 'Delivery / shipping date versus return date', 'NOT POSSIBLE', 'orders has only order_date; there is no shipped or delivered date', 'N/A'),
 ('A6.2', 'Partially fulfilled orders: shipped quantity', 'NOT POSSIBLE', 'order_items has no shipped_quantity; status "Partially Fulfilled" cannot be verified', 'N/A'),
 ('A6.3', 'Customer owner (account manager) versus order manager', 'NOT POSSIBLE', 'customers has no salesperson_id (only the ERD image shows it); manager is stored per order', 'N/A'),
 ('A6.4', 'Order total versus sum of lines', 'NOT POSSIBLE', 'orders has no stored total; totals are always derived from order_items', 'N/A'),
 ('A6.5', 'Currency consistency', 'NOT POSSIBLE', 'no currency column in the schema (the ERD shows orders.currency)', 'N/A'),
 ('A6.6', 'Price history / price at the date of sale versus product price', 'NOT POSSIBLE', 'products has one price only; B7.16 compares the line price with the current list price', 'N/A'),
 ('A6.7', 'Return status / processing state', 'NOT POSSIBLE', 'returns has no status column (the ERD shows one)', 'N/A'),
 ('A6.8', 'Tax / VAT correctness', 'NOT POSSIBLE', 'no VAT columns; prices are treated as net amounts', 'N/A'),
 ('A6.9', 'Discount percentage as a stored value', 'NOT POSSIBLE', 'the schema stores discount_amount (a LINE total), not a percentage; B7.10 derives the percentage', 'N/A')
) AS t(check_id, check_name, value, expected, status);


-- =====================================================================================
-- B1. Row counts (18 tables)
-- =====================================================================================
-- B1.01 | regions
SELECT 'B1.01' AS check_id, 'regions' AS check_name, v::text AS value, '= 8' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 8 THEN 'OK' ELSE 'DIFFERS' END AS status
FROM (SELECT (SELECT count(*) FROM regions) AS v) q
UNION ALL
-- B1.02 | cities
SELECT 'B1.02' AS check_id, 'cities' AS check_name, v::text AS value, '= 42' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 42 THEN 'OK' ELSE 'DIFFERS' END AS status
FROM (SELECT (SELECT count(*) FROM cities) AS v) q
UNION ALL
-- B1.03 | customer_types
SELECT 'B1.03' AS check_id, 'customer_types' AS check_name, v::text AS value, '= 5' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 5 THEN 'OK' ELSE 'DIFFERS' END AS status
FROM (SELECT (SELECT count(*) FROM customer_types) AS v) q
UNION ALL
-- B1.04 | customers
SELECT 'B1.04' AS check_id, 'customers' AS check_name, v::text AS value, '>= 1000' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v >= 1000 THEN 'OK' ELSE 'BELOW_TARGET' END AS status
FROM (SELECT (SELECT count(*) FROM customers) AS v) q
UNION ALL
-- B1.05 | salespersons
SELECT 'B1.05' AS check_id, 'salespersons' AS check_name, v::text AS value, '= 24' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 24 THEN 'OK' ELSE 'DIFFERS' END AS status
FROM (SELECT (SELECT count(*) FROM salespersons) AS v) q
UNION ALL
-- B1.06 | sales_channels
SELECT 'B1.06' AS check_id, 'sales_channels' AS check_name, v::text AS value, '= 5' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 5 THEN 'OK' ELSE 'DIFFERS' END AS status
FROM (SELECT (SELECT count(*) FROM sales_channels) AS v) q
UNION ALL
-- B1.07 | order_statuses
SELECT 'B1.07' AS check_id, 'order_statuses' AS check_name, v::text AS value, '= 5' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 5 THEN 'OK' ELSE 'DIFFERS' END AS status
FROM (SELECT (SELECT count(*) FROM order_statuses) AS v) q
UNION ALL
-- B1.08 | brands
SELECT 'B1.08' AS check_id, 'brands' AS check_name, v::text AS value, '= 40' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 40 THEN 'OK' ELSE 'DIFFERS' END AS status
FROM (SELECT (SELECT count(*) FROM brands) AS v) q
UNION ALL
-- B1.09 | categories
SELECT 'B1.09' AS check_id, 'categories' AS check_name, v::text AS value, '= 15' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 15 THEN 'OK' ELSE 'DIFFERS' END AS status
FROM (SELECT (SELECT count(*) FROM categories) AS v) q
UNION ALL
-- B1.10 | subcategories
SELECT 'B1.10' AS check_id, 'subcategories' AS check_name, v::text AS value, '= 50' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 50 THEN 'OK' ELSE 'DIFFERS' END AS status
FROM (SELECT (SELECT count(*) FROM subcategories) AS v) q
UNION ALL
-- B1.11 | suppliers
SELECT 'B1.11' AS check_id, 'suppliers' AS check_name, v::text AS value, '= 20' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 20 THEN 'OK' ELSE 'DIFFERS' END AS status
FROM (SELECT (SELECT count(*) FROM suppliers) AS v) q
UNION ALL
-- B1.12 | product_statuses
SELECT 'B1.12' AS check_id, 'product_statuses' AS check_name, v::text AS value, '= 4' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 4 THEN 'OK' ELSE 'DIFFERS' END AS status
FROM (SELECT (SELECT count(*) FROM product_statuses) AS v) q
UNION ALL
-- B1.13 | products
SELECT 'B1.13' AS check_id, 'products' AS check_name, v::text AS value, '>= 5000' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v >= 5000 THEN 'OK' ELSE 'BELOW_TARGET' END AS status
FROM (SELECT (SELECT count(*) FROM products) AS v) q
UNION ALL
-- B1.14 | orders
SELECT 'B1.14' AS check_id, 'orders' AS check_name, v::text AS value, '>= 50000' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v >= 50000 THEN 'OK' ELSE 'BELOW_TARGET' END AS status
FROM (SELECT (SELECT count(*) FROM orders) AS v) q
UNION ALL
-- B1.15 | order_items
SELECT 'B1.15' AS check_id, 'order_items' AS check_name, v::text AS value, '>= 250000' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v >= 250000 THEN 'OK' ELSE 'BELOW_TARGET' END AS status
FROM (SELECT (SELECT count(*) FROM order_items) AS v) q
UNION ALL
-- B1.16 | return_reasons
SELECT 'B1.16' AS check_id, 'return_reasons' AS check_name, v::text AS value, '= 8' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 8 THEN 'OK' ELSE 'DIFFERS' END AS status
FROM (SELECT (SELECT count(*) FROM return_reasons) AS v) q
UNION ALL
-- B1.17 | returns
SELECT 'B1.17' AS check_id, 'returns' AS check_name, v::text AS value, 'info' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' ELSE 'INFO' END AS status
FROM (SELECT (SELECT count(*) FROM returns) AS v) q
UNION ALL
-- B1.18 | return_items
SELECT 'B1.18' AS check_id, 'return_items' AS check_name, v::text AS value, 'info' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' ELSE 'INFO' END AS status
FROM (SELECT (SELECT count(*) FROM return_items) AS v) q
ORDER BY 1;


-- =====================================================================================
-- B2. Duplicates (keys and business keys)
-- =====================================================================================
-- B2.01 | Duplicate business key: regions.region_name
SELECT 'B2.01' AS check_id, 'Duplicate business key: regions.region_name' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT COALESCE(SUM(c-1),0) FROM (SELECT count(*) c FROM regions  GROUP BY region_name HAVING count(*)>1) s) AS v) q
UNION ALL
-- B2.02 | Duplicate business key: cities (region_id, city_name)
SELECT 'B2.02' AS check_id, 'Duplicate business key: cities (region_id, city_name)' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT COALESCE(SUM(c-1),0) FROM (SELECT count(*) c FROM cities  GROUP BY region_id, city_name HAVING count(*)>1) s) AS v) q
UNION ALL
-- B2.03 | Duplicate business key: customer_types.type_name
SELECT 'B2.03' AS check_id, 'Duplicate business key: customer_types.type_name' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT COALESCE(SUM(c-1),0) FROM (SELECT count(*) c FROM customer_types  GROUP BY type_name HAVING count(*)>1) s) AS v) q
UNION ALL
-- B2.04 | Duplicate business key: sales_channels.channel_name
SELECT 'B2.04' AS check_id, 'Duplicate business key: sales_channels.channel_name' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT COALESCE(SUM(c-1),0) FROM (SELECT count(*) c FROM sales_channels  GROUP BY channel_name HAVING count(*)>1) s) AS v) q
UNION ALL
-- B2.05 | Duplicate business key: order_statuses.status_name
SELECT 'B2.05' AS check_id, 'Duplicate business key: order_statuses.status_name' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT COALESCE(SUM(c-1),0) FROM (SELECT count(*) c FROM order_statuses  GROUP BY status_name HAVING count(*)>1) s) AS v) q
UNION ALL
-- B2.06 | Duplicate business key: brands.brand_name
SELECT 'B2.06' AS check_id, 'Duplicate business key: brands.brand_name' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT COALESCE(SUM(c-1),0) FROM (SELECT count(*) c FROM brands  GROUP BY brand_name HAVING count(*)>1) s) AS v) q
UNION ALL
-- B2.07 | Duplicate business key: categories.category_name
SELECT 'B2.07' AS check_id, 'Duplicate business key: categories.category_name' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT COALESCE(SUM(c-1),0) FROM (SELECT count(*) c FROM categories  GROUP BY category_name HAVING count(*)>1) s) AS v) q
UNION ALL
-- B2.08 | Duplicate business key: subcategories (category_id, subcategory_name)
SELECT 'B2.08' AS check_id, 'Duplicate business key: subcategories (category_id, subcategory_name)' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT COALESCE(SUM(c-1),0) FROM (SELECT count(*) c FROM subcategories  GROUP BY category_id, subcategory_name HAVING count(*)>1) s) AS v) q
UNION ALL
-- B2.09 | Duplicate business key: suppliers.supplier_name
SELECT 'B2.09' AS check_id, 'Duplicate business key: suppliers.supplier_name' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT COALESCE(SUM(c-1),0) FROM (SELECT count(*) c FROM suppliers  GROUP BY supplier_name HAVING count(*)>1) s) AS v) q
UNION ALL
-- B2.10 | Duplicate business key: product_statuses.status_name
SELECT 'B2.10' AS check_id, 'Duplicate business key: product_statuses.status_name' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT COALESCE(SUM(c-1),0) FROM (SELECT count(*) c FROM product_statuses  GROUP BY status_name HAVING count(*)>1) s) AS v) q
UNION ALL
-- B2.11 | Duplicate business key: products.sku
SELECT 'B2.11' AS check_id, 'Duplicate business key: products.sku' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT COALESCE(SUM(c-1),0) FROM (SELECT count(*) c FROM products  GROUP BY sku HAVING count(*)>1) s) AS v) q
UNION ALL
-- B2.12 | Duplicate business key: return_reasons.reason_name
SELECT 'B2.12' AS check_id, 'Duplicate business key: return_reasons.reason_name' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT COALESCE(SUM(c-1),0) FROM (SELECT count(*) c FROM return_reasons  GROUP BY reason_name HAVING count(*)>1) s) AS v) q
UNION ALL
-- B2.13 | Duplicate business key: return_items (return_id, order_item_id)
SELECT 'B2.13' AS check_id, 'Duplicate business key: return_items (return_id, order_item_id)' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT COALESCE(SUM(c-1),0) FROM (SELECT count(*) c FROM return_items  GROUP BY return_id, order_item_id HAVING count(*)>1) s) AS v) q
UNION ALL
-- B2.14 | Duplicate business key: customers.tax_id (non-NULL)
SELECT 'B2.14' AS check_id, 'Duplicate business key: customers.tax_id (non-NULL)' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT COALESCE(SUM(c-1),0) FROM (SELECT count(*) c FROM customers WHERE tax_id IS NOT NULL GROUP BY tax_id HAVING count(*)>1) s) AS v) q
UNION ALL
-- B2.15 | Duplicate salespersons (first_name, last_name, hire_date)
SELECT 'B2.15' AS check_id, 'Duplicate salespersons (first_name, last_name, hire_date)' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT COALESCE(SUM(c-1),0) FROM (SELECT count(*) c FROM salespersons  GROUP BY first_name, last_name, hire_date HAVING count(*)>1) s) AS v) q
UNION ALL
-- B2.16 | Soft duplicate: customers (customer_name, city_id)
SELECT 'B2.16' AS check_id, 'Soft duplicate: customers (customer_name, city_id)' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'WARN' END AS status
FROM (SELECT (SELECT COALESCE(SUM(c-1),0) FROM (SELECT count(*) c FROM customers  GROUP BY customer_name, city_id HAVING count(*)>1) s) AS v) q
UNION ALL
-- B2.17 | Soft duplicate: customers.email (non-NULL)
SELECT 'B2.17' AS check_id, 'Soft duplicate: customers.email (non-NULL)' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'WARN' END AS status
FROM (SELECT (SELECT COALESCE(SUM(c-1),0) FROM (SELECT count(*) c FROM customers WHERE email IS NOT NULL GROUP BY email HAVING count(*)>1) s) AS v) q
UNION ALL
-- B2.18 | Soft duplicate: customers.phone (non-NULL)
SELECT 'B2.18' AS check_id, 'Soft duplicate: customers.phone (non-NULL)' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'WARN' END AS status
FROM (SELECT (SELECT COALESCE(SUM(c-1),0) FROM (SELECT count(*) c FROM customers WHERE phone IS NOT NULL GROUP BY phone HAVING count(*)>1) s) AS v) q
UNION ALL
-- B2.19 | Soft duplicate: products.product_name
SELECT 'B2.19' AS check_id, 'Soft duplicate: products.product_name' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'WARN' END AS status
FROM (SELECT (SELECT COALESCE(SUM(c-1),0) FROM (SELECT count(*) c FROM products  GROUP BY product_name HAVING count(*)>1) s) AS v) q
UNION ALL
-- B2.20 | Soft duplicate: order_items (order_id, product_id)
SELECT 'B2.20' AS check_id, 'Soft duplicate: order_items (order_id, product_id)' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'WARN' END AS status
FROM (SELECT (SELECT COALESCE(SUM(c-1),0) FROM (SELECT count(*) c FROM order_items  GROUP BY order_id, product_id HAVING count(*)>1) s) AS v) q
UNION ALL
-- B2.21 | Soft duplicate: orders (customer_id, order_date, sales_channel_id)
SELECT 'B2.21' AS check_id, 'Soft duplicate: orders (customer_id, order_date, sales_channel_id)' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'WARN' END AS status
FROM (SELECT (SELECT COALESCE(SUM(c-1),0) FROM (SELECT count(*) c FROM orders  GROUP BY customer_id, order_date, sales_channel_id HAVING count(*)>1) s) AS v) q
UNION ALL
-- B2.22 | Orders with more than one return (surplus returns)
SELECT 'B2.22' AS check_id, 'Orders with more than one return (surplus returns)' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'WARN' END AS status
FROM (SELECT (SELECT COALESCE(SUM(c-1),0) FROM (SELECT count(*) c FROM returns  GROUP BY order_id HAVING count(*)>1) s) AS v) q
UNION ALL
-- B2.23 | Order items returned in more than one return (surplus return_items)
SELECT 'B2.23' AS check_id, 'Order items returned in more than one return (surplus return_items)' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'WARN' END AS status
FROM (SELECT (SELECT COALESCE(SUM(c-1),0) FROM (SELECT count(*) c FROM return_items  GROUP BY order_item_id HAVING count(*)>1) s) AS v) q
ORDER BY 1;


-- =====================================================================================
-- B3. Referential and logical integrity
-- =====================================================================================
-- B3.01 | Orphan rows: cities.region_id -> regions
SELECT 'B3.01' AS check_id, 'Orphan rows: cities.region_id -> regions' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT count(*) FROM cities c WHERE c.region_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM regions p WHERE p.region_id = c.region_id)) AS v) q
UNION ALL
-- B3.02 | Orphan rows: customers.city_id -> cities
SELECT 'B3.02' AS check_id, 'Orphan rows: customers.city_id -> cities' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT count(*) FROM customers c WHERE c.city_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM cities p WHERE p.city_id = c.city_id)) AS v) q
UNION ALL
-- B3.03 | Orphan rows: customers.customer_type_id -> customer_types
SELECT 'B3.03' AS check_id, 'Orphan rows: customers.customer_type_id -> customer_types' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT count(*) FROM customers c WHERE c.customer_type_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM customer_types p WHERE p.customer_type_id = c.customer_type_id)) AS v) q
UNION ALL
-- B3.04 | Orphan rows: salespersons.region_id -> regions
SELECT 'B3.04' AS check_id, 'Orphan rows: salespersons.region_id -> regions' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT count(*) FROM salespersons c WHERE c.region_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM regions p WHERE p.region_id = c.region_id)) AS v) q
UNION ALL
-- B3.05 | Orphan rows: subcategories.category_id -> categories
SELECT 'B3.05' AS check_id, 'Orphan rows: subcategories.category_id -> categories' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT count(*) FROM subcategories c WHERE c.category_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM categories p WHERE p.category_id = c.category_id)) AS v) q
UNION ALL
-- B3.06 | Orphan rows: orders.customer_id -> customers
SELECT 'B3.06' AS check_id, 'Orphan rows: orders.customer_id -> customers' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT count(*) FROM orders c WHERE c.customer_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM customers p WHERE p.customer_id = c.customer_id)) AS v) q
UNION ALL
-- B3.07 | Orphan rows: orders.salesperson_id -> salespersons
SELECT 'B3.07' AS check_id, 'Orphan rows: orders.salesperson_id -> salespersons' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT count(*) FROM orders c WHERE c.salesperson_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM salespersons p WHERE p.salesperson_id = c.salesperson_id)) AS v) q
UNION ALL
-- B3.08 | Orphan rows: orders.sales_channel_id -> sales_channels
SELECT 'B3.08' AS check_id, 'Orphan rows: orders.sales_channel_id -> sales_channels' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT count(*) FROM orders c WHERE c.sales_channel_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM sales_channels p WHERE p.sales_channel_id = c.sales_channel_id)) AS v) q
UNION ALL
-- B3.09 | Orphan rows: orders.order_status_id -> order_statuses
SELECT 'B3.09' AS check_id, 'Orphan rows: orders.order_status_id -> order_statuses' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT count(*) FROM orders c WHERE c.order_status_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM order_statuses p WHERE p.order_status_id = c.order_status_id)) AS v) q
UNION ALL
-- B3.10 | Orphan rows: order_items.order_id -> orders
SELECT 'B3.10' AS check_id, 'Orphan rows: order_items.order_id -> orders' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT count(*) FROM order_items c WHERE c.order_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM orders p WHERE p.order_id = c.order_id)) AS v) q
UNION ALL
-- B3.11 | Orphan rows: order_items.product_id -> products
SELECT 'B3.11' AS check_id, 'Orphan rows: order_items.product_id -> products' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT count(*) FROM order_items c WHERE c.product_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM products p WHERE p.product_id = c.product_id)) AS v) q
UNION ALL
-- B3.12 | Orphan rows: returns.order_id -> orders
SELECT 'B3.12' AS check_id, 'Orphan rows: returns.order_id -> orders' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT count(*) FROM returns c WHERE c.order_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM orders p WHERE p.order_id = c.order_id)) AS v) q
UNION ALL
-- B3.13 | Orphan rows: returns.customer_id -> customers
SELECT 'B3.13' AS check_id, 'Orphan rows: returns.customer_id -> customers' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT count(*) FROM returns c WHERE c.customer_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM customers p WHERE p.customer_id = c.customer_id)) AS v) q
UNION ALL
-- B3.14 | Orphan rows: returns.return_reason_id -> return_reasons
SELECT 'B3.14' AS check_id, 'Orphan rows: returns.return_reason_id -> return_reasons' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT count(*) FROM returns c WHERE c.return_reason_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM return_reasons p WHERE p.return_reason_id = c.return_reason_id)) AS v) q
UNION ALL
-- B3.15 | Orphan rows: return_items.return_id -> returns
SELECT 'B3.15' AS check_id, 'Orphan rows: return_items.return_id -> returns' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT count(*) FROM return_items c WHERE c.return_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM returns p WHERE p.return_id = c.return_id)) AS v) q
UNION ALL
-- B3.16 | Orphan rows: return_items.order_item_id -> order_items
SELECT 'B3.16' AS check_id, 'Orphan rows: return_items.order_item_id -> order_items' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT count(*) FROM return_items c WHERE c.order_item_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM order_items p WHERE p.order_item_id = c.order_item_id)) AS v) q
UNION ALL
-- B3.17 | Orphan rows: return_items.product_id -> products
SELECT 'B3.17' AS check_id, 'Orphan rows: return_items.product_id -> products' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT count(*) FROM return_items c WHERE c.product_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM products p WHERE p.product_id = c.product_id)) AS v) q
UNION ALL
-- B3.18 | Orphan rows: products.subcategory_id -> subcategories
SELECT 'B3.18' AS check_id, 'Orphan rows: products.subcategory_id -> subcategories' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT count(*) FROM products c WHERE c.subcategory_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM subcategories p WHERE p.subcategory_id = c.subcategory_id)) AS v) q
UNION ALL
-- B3.19 | Orphan rows: products.brand_id -> brands
SELECT 'B3.19' AS check_id, 'Orphan rows: products.brand_id -> brands' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT count(*) FROM products c WHERE c.brand_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM brands p WHERE p.brand_id = c.brand_id)) AS v) q
UNION ALL
-- B3.20 | Orphan rows: products.supplier_id -> suppliers
SELECT 'B3.20' AS check_id, 'Orphan rows: products.supplier_id -> suppliers' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT count(*) FROM products c WHERE c.supplier_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM suppliers p WHERE p.supplier_id = c.supplier_id)) AS v) q
UNION ALL
-- B3.21 | Orphan rows: products.product_status_id -> product_statuses
SELECT 'B3.21' AS check_id, 'Orphan rows: products.product_status_id -> product_statuses' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT count(*) FROM products c WHERE c.product_status_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM product_statuses p WHERE p.product_status_id = c.product_status_id)) AS v) q
UNION ALL
-- B3.22 | Customers without city_id
SELECT 'B3.22' AS check_id, 'Customers without city_id' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'WARN' END AS status
FROM (SELECT (SELECT count(*) FROM customers WHERE city_id IS NULL) AS v) q
UNION ALL
-- B3.23 | Salespersons without region_id
SELECT 'B3.23' AS check_id, 'Salespersons without region_id' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'WARN' END AS status
FROM (SELECT (SELECT count(*) FROM salespersons WHERE region_id IS NULL) AS v) q
UNION ALL
-- B3.24 | Orders without salesperson_id
SELECT 'B3.24' AS check_id, 'Orders without salesperson_id' AS check_name, v::text AS value, 'info' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' ELSE 'INFO' END AS status
FROM (SELECT (SELECT count(*) FROM orders WHERE salesperson_id IS NULL) AS v) q
UNION ALL
-- B3.25 | returns.customer_id differs from the customer of the order
SELECT 'B3.25' AS check_id, 'returns.customer_id differs from the customer of the order' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT count(*) FROM returns r JOIN orders o ON o.order_id = r.order_id WHERE r.customer_id <> o.customer_id) AS v) q
UNION ALL
-- B3.26 | return_items.product_id differs from the product of the order item
SELECT 'B3.26' AS check_id, 'return_items.product_id differs from the product of the order item' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT count(*) FROM return_items ri JOIN order_items oi ON oi.order_item_id = ri.order_item_id WHERE ri.product_id <> oi.product_id) AS v) q
UNION ALL
-- B3.27 | Return line belongs to an order other than the return's order
SELECT 'B3.27' AS check_id, 'Return line belongs to an order other than the return''s order' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT count(*) FROM return_items ri JOIN returns r ON r.return_id = ri.return_id JOIN order_items oi ON oi.order_item_id = ri.order_item_id WHERE oi.order_id <> r.order_id) AS v) q
UNION ALL
-- B3.28 | Orders without order_items
SELECT 'B3.28' AS check_id, 'Orders without order_items' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'WARN' END AS status
FROM (SELECT (SELECT count(*) FROM orders o WHERE NOT EXISTS (SELECT 1 FROM order_items oi WHERE oi.order_id = o.order_id)) AS v) q
UNION ALL
-- B3.29 | Returns without return_items
SELECT 'B3.29' AS check_id, 'Returns without return_items' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'WARN' END AS status
FROM (SELECT (SELECT count(*) FROM returns r WHERE NOT EXISTS (SELECT 1 FROM return_items ri WHERE ri.return_id = r.return_id)) AS v) q
UNION ALL
-- B3.30 | Customers without orders
SELECT 'B3.30' AS check_id, 'Customers without orders' AS check_name, v::text AS value, 'info' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' ELSE 'INFO' END AS status
FROM (SELECT (SELECT count(*) FROM customers c WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id)) AS v) q
UNION ALL
-- B3.31 | Products never sold
SELECT 'B3.31' AS check_id, 'Products never sold' AS check_name, v::text AS value, 'info' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' ELSE 'INFO' END AS status
FROM (SELECT (SELECT count(*) FROM products p WHERE NOT EXISTS (SELECT 1 FROM order_items oi WHERE oi.product_id = p.product_id)) AS v) q
UNION ALL
-- B3.32 | Salespersons without orders
SELECT 'B3.32' AS check_id, 'Salespersons without orders' AS check_name, v::text AS value, 'info' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' ELSE 'INFO' END AS status
FROM (SELECT (SELECT count(*) FROM salespersons s WHERE NOT EXISTS (SELECT 1 FROM orders o WHERE o.salesperson_id = s.salesperson_id)) AS v) q
UNION ALL
-- B3.33 | Orders where salesperson region is comparable to customer region
SELECT 'B3.33' AS check_id, 'Orders where salesperson region is comparable to customer region' AS check_name, v::text AS value, 'info' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' ELSE 'INFO' END AS status
FROM (SELECT (SELECT count(*) FROM orders o JOIN salespersons s ON s.salesperson_id = o.salesperson_id JOIN customers c ON c.customer_id = o.customer_id JOIN cities ci ON ci.city_id = c.city_id WHERE s.region_id IS NOT NULL) AS v) q
UNION ALL
-- B3.34 | Orders where salesperson region differs from customer region
SELECT 'B3.34' AS check_id, 'Orders where salesperson region differs from customer region' AS check_name, v::text AS value, 'info' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' ELSE 'INFO' END AS status
FROM (SELECT (SELECT count(*) FROM orders o JOIN salespersons s ON s.salesperson_id = o.salesperson_id JOIN customers c ON c.customer_id = o.customer_id JOIN cities ci ON ci.city_id = c.city_id WHERE s.region_id IS NOT NULL AND s.region_id <> ci.region_id) AS v) q
UNION ALL
-- B3.35 | Share of orders (%) where salesperson region differs from customer region
SELECT 'B3.35' AS check_id, 'Share of orders (%) where salesperson region differs from customer region' AS check_name, v::text AS value, '<= 50' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v <= 50 THEN 'OK' ELSE 'WARN' END AS status
FROM (SELECT (SELECT round(100.0 * count(*) FILTER (WHERE s.region_id <> ci.region_id) / NULLIF(count(*), 0), 1) FROM orders o JOIN salespersons s ON s.salesperson_id = o.salesperson_id JOIN customers c ON c.customer_id = o.customer_id JOIN cities ci ON ci.city_id = c.city_id WHERE s.region_id IS NOT NULL) AS v) q
ORDER BY 1;


-- =====================================================================================
-- B4. Order dates and customer registration
-- =====================================================================================
-- B4.01 | Orders dated before customer registration
SELECT 'B4.01' AS check_id, 'Orders dated before customer registration' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT count(*) FROM orders o JOIN customers c ON c.customer_id = o.customer_id WHERE c.registration_date IS NOT NULL AND o.order_date::date < c.registration_date) AS v) q
UNION ALL
-- B4.02 | Share of orders (%) dated before customer registration
SELECT 'B4.02' AS check_id, 'Share of orders (%) dated before customer registration' AS check_name, v::text AS value, '<= 0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v <= 0 THEN 'OK' ELSE 'WARN' END AS status
FROM (SELECT (SELECT round(100.0 * count(*) FILTER (WHERE o.order_date::date < c.registration_date) / NULLIF(count(*), 0), 1) FROM orders o JOIN customers c ON c.customer_id = o.customer_id WHERE c.registration_date IS NOT NULL) AS v) q
UNION ALL
-- B4.03 | Customers without registration_date
SELECT 'B4.03' AS check_id, 'Customers without registration_date' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'WARN' END AS status
FROM (SELECT (SELECT count(*) FROM customers WHERE registration_date IS NULL) AS v) q
UNION ALL
-- B4.04 | Orders from customers flagged is_active = false
SELECT 'B4.04' AS check_id, 'Orders from customers flagged is_active = false' AS check_name, v::text AS value, 'info' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' ELSE 'INFO' END AS status
FROM (SELECT (SELECT count(*) FROM orders o JOIN customers c ON c.customer_id = o.customer_id WHERE NOT c.is_active) AS v) q
UNION ALL
-- B4.05 | Orders dated in the future
SELECT 'B4.05' AS check_id, 'Orders dated in the future' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT count(*) FROM orders WHERE order_date > localtimestamp) AS v) q
UNION ALL
-- B4.06 | Order date range
SELECT 'B4.06' AS check_id, 'Order date range' AS check_name, v::text AS value, 'info' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' ELSE 'INFO' END AS status
FROM (SELECT (SELECT min(order_date)::text || ' .. ' || max(order_date)::text FROM orders) AS v) q
UNION ALL
-- B4.07 | Registration date range
SELECT 'B4.07' AS check_id, 'Registration date range' AS check_name, v::text AS value, 'info' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' ELSE 'INFO' END AS status
FROM (SELECT (SELECT min(registration_date)::text || ' .. ' || max(registration_date)::text FROM customers) AS v) q
UNION ALL
-- B4.08 | History length in months
SELECT 'B4.08' AS check_id, 'History length in months' AS check_name, v::text AS value, '24 .. 36' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v BETWEEN 24 AND 36 THEN 'OK' ELSE 'OUT_OF_RANGE' END AS status
FROM (SELECT (SELECT round((extract(epoch FROM max(order_date) - min(order_date)) / 86400 / 30.44)::numeric, 1) FROM orders) AS v) q
UNION ALL
-- B4.09 | Order lines dated before the product was created
SELECT 'B4.09' AS check_id, 'Order lines dated before the product was created' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'WARN' END AS status
FROM (SELECT (SELECT count(*) FROM order_items oi JOIN orders o ON o.order_id = oi.order_id JOIN products p ON p.product_id = oi.product_id WHERE o.order_date < p.created_at) AS v) q
UNION ALL
-- B4.10 | Orders dated before the salesperson was hired
SELECT 'B4.10' AS check_id, 'Orders dated before the salesperson was hired' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT count(*) FROM orders o JOIN salespersons s ON s.salesperson_id = o.salesperson_id WHERE s.hire_date IS NOT NULL AND o.order_date::date < s.hire_date) AS v) q
UNION ALL
-- B4.11 | Customers registered in the future
SELECT 'B4.11' AS check_id, 'Customers registered in the future' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT count(*) FROM customers WHERE registration_date > current_date) AS v) q
ORDER BY 1;


-- =====================================================================================
-- B5. Return dates
-- =====================================================================================
-- B5.01 | Returns dated before the order
SELECT 'B5.01' AS check_id, 'Returns dated before the order' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT count(*) FROM returns r JOIN orders o ON o.order_id = r.order_id WHERE r.return_date < o.order_date) AS v) q
UNION ALL
-- B5.02 | Returns on the same calendar day as the order
SELECT 'B5.02' AS check_id, 'Returns on the same calendar day as the order' AS check_name, v::text AS value, 'info' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' ELSE 'INFO' END AS status
FROM (SELECT (SELECT count(*) FROM returns r JOIN orders o ON o.order_id = r.order_id WHERE r.return_date::date = o.order_date::date) AS v) q
UNION ALL
-- B5.03 | Returns dated in the future
SELECT 'B5.03' AS check_id, 'Returns dated in the future' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT count(*) FROM returns WHERE return_date > localtimestamp) AS v) q
UNION ALL
-- B5.04 | Min days from order to return
SELECT 'B5.04' AS check_id, 'Min days from order to return' AS check_name, v::text AS value, 'info' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' ELSE 'INFO' END AS status
FROM (SELECT (SELECT round(min(extract(epoch FROM r.return_date - o.order_date) / 86400)::numeric, 1) FROM returns r JOIN orders o ON o.order_id = r.order_id) AS v) q
UNION ALL
-- B5.05 | Avg days from order to return
SELECT 'B5.05' AS check_id, 'Avg days from order to return' AS check_name, v::text AS value, 'info' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' ELSE 'INFO' END AS status
FROM (SELECT (SELECT round(avg(extract(epoch FROM r.return_date - o.order_date) / 86400)::numeric, 1) FROM returns r JOIN orders o ON o.order_id = r.order_id) AS v) q
UNION ALL
-- B5.06 | Max days from order to return
SELECT 'B5.06' AS check_id, 'Max days from order to return' AS check_name, v::text AS value, 'info' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' ELSE 'INFO' END AS status
FROM (SELECT (SELECT round(max(extract(epoch FROM r.return_date - o.order_date) / 86400)::numeric, 1) FROM returns r JOIN orders o ON o.order_id = r.order_id) AS v) q
UNION ALL
-- B5.07 | Returns dated before customer registration
SELECT 'B5.07' AS check_id, 'Returns dated before customer registration' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT count(*) FROM returns r JOIN customers c ON c.customer_id = r.customer_id WHERE c.registration_date IS NOT NULL AND r.return_date::date < c.registration_date) AS v) q
UNION ALL
-- B5.08 | Returns of orders that are not Completed
SELECT 'B5.08' AS check_id, 'Returns of orders that are not Completed' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'WARN' END AS status
FROM (SELECT (SELECT count(*) FROM returns r JOIN orders o ON o.order_id = r.order_id JOIN order_statuses s ON s.order_status_id = o.order_status_id WHERE s.status_name <> 'Completed') AS v) q
UNION ALL
-- B5.09 | Return headers per 100 orders (%)
SELECT 'B5.09' AS check_id, 'Return headers per 100 orders (%)' AS check_name, v::text AS value, 'info' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' ELSE 'INFO' END AS status
FROM (SELECT (SELECT round(100.0 * (SELECT count(*) FROM returns) / NULLIF((SELECT count(*) FROM orders), 0), 2)) AS v) q
ORDER BY 1;


-- =====================================================================================
-- B6. Returned vs sold quantity and refund amounts
-- =====================================================================================
-- B6.01 | Order items with returned quantity above sold quantity
SELECT 'B6.01' AS check_id, 'Order items with returned quantity above sold quantity' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT count(*) FROM (SELECT 1 FROM order_items oi JOIN return_items ri ON ri.order_item_id = oi.order_item_id GROUP BY oi.order_item_id, oi.quantity HAVING sum(ri.quantity) > oi.quantity) s) AS v) q
UNION ALL
-- B6.02 | Surplus returned quantity (units)
SELECT 'B6.02' AS check_id, 'Surplus returned quantity (units)' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT COALESCE(sum(x), 0) FROM (SELECT sum(ri.quantity) - oi.quantity AS x FROM order_items oi JOIN return_items ri ON ri.order_item_id = oi.order_item_id GROUP BY oi.order_item_id, oi.quantity HAVING sum(ri.quantity) > oi.quantity) s) AS v) q
UNION ALL
-- B6.03 | Items fully returned
SELECT 'B6.03' AS check_id, 'Items fully returned' AS check_name, v::text AS value, 'info' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' ELSE 'INFO' END AS status
FROM (SELECT (SELECT count(*) FROM (SELECT 1 FROM order_items oi JOIN return_items ri ON ri.order_item_id = oi.order_item_id GROUP BY oi.order_item_id, oi.quantity HAVING sum(ri.quantity) = oi.quantity) s) AS v) q
UNION ALL
-- B6.04 | Items partially returned
SELECT 'B6.04' AS check_id, 'Items partially returned' AS check_name, v::text AS value, 'info' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' ELSE 'INFO' END AS status
FROM (SELECT (SELECT count(*) FROM (SELECT 1 FROM order_items oi JOIN return_items ri ON ri.order_item_id = oi.order_item_id GROUP BY oi.order_item_id, oi.quantity HAVING sum(ri.quantity) < oi.quantity) s) AS v) q
UNION ALL
-- B6.05 | Single return line larger than the sold line
SELECT 'B6.05' AS check_id, 'Single return line larger than the sold line' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT count(*) FROM return_items ri JOIN order_items oi ON oi.order_item_id = ri.order_item_id WHERE ri.quantity > oi.quantity) AS v) q
UNION ALL
-- B6.06 | Refund price above the sale price
SELECT 'B6.06' AS check_id, 'Refund price above the sale price' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT count(*) FROM return_items ri JOIN order_items oi ON oi.order_item_id = ri.order_item_id WHERE ri.refund_unit_price > oi.unit_sale_price + 0.005) AS v) q
UNION ALL
-- B6.07 | Refund above the price actually paid (after discount)
SELECT 'B6.07' AS check_id, 'Refund above the price actually paid (after discount)' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT count(*) FROM return_items ri JOIN order_items oi ON oi.order_item_id = ri.order_item_id WHERE ri.refund_unit_price > (oi.unit_sale_price * oi.quantity - oi.discount_amount) / oi.quantity + 0.01) AS v) q
UNION ALL
-- B6.08 | Total refund overstatement
SELECT 'B6.08' AS check_id, 'Total refund overstatement' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT round(COALESCE(sum((ri.refund_unit_price - (oi.unit_sale_price * oi.quantity - oi.discount_amount) / oi.quantity) * ri.quantity), 0), 2) FROM return_items ri JOIN order_items oi ON oi.order_item_id = ri.order_item_id WHERE ri.refund_unit_price > (oi.unit_sale_price * oi.quantity - oi.discount_amount) / oi.quantity + 0.01) AS v) q
ORDER BY 1;


-- =====================================================================================
-- B7. Prices, costs, quantities, discounts
-- =====================================================================================
-- B7.01 | Order lines with quantity <= 0
SELECT 'B7.01' AS check_id, 'Order lines with quantity <= 0' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT count(*) FROM order_items WHERE quantity <= 0) AS v) q
UNION ALL
-- B7.02 | Order lines with negative unit_sale_price
SELECT 'B7.02' AS check_id, 'Order lines with negative unit_sale_price' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT count(*) FROM order_items WHERE unit_sale_price < 0) AS v) q
UNION ALL
-- B7.03 | Order lines with negative unit_cost
SELECT 'B7.03' AS check_id, 'Order lines with negative unit_cost' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT count(*) FROM order_items WHERE unit_cost < 0) AS v) q
UNION ALL
-- B7.04 | Order lines with negative discount_amount
SELECT 'B7.04' AS check_id, 'Order lines with negative discount_amount' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT count(*) FROM order_items WHERE discount_amount < 0) AS v) q
UNION ALL
-- B7.05 | Order lines with unit_sale_price = 0
SELECT 'B7.05' AS check_id, 'Order lines with unit_sale_price = 0' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'WARN' END AS status
FROM (SELECT (SELECT count(*) FROM order_items WHERE unit_sale_price = 0) AS v) q
UNION ALL
-- B7.06 | Order lines with unit_cost = 0
SELECT 'B7.06' AS check_id, 'Order lines with unit_cost = 0' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'WARN' END AS status
FROM (SELECT (SELECT count(*) FROM order_items WHERE unit_cost = 0) AS v) q
UNION ALL
-- B7.07 | Discount larger than the line amount
SELECT 'B7.07' AS check_id, 'Discount larger than the line amount' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT count(*) FROM order_items oi WHERE oi.discount_amount > (oi.unit_sale_price * oi.quantity)) AS v) q
UNION ALL
-- B7.08 | Discount equal to 100% of the line
SELECT 'B7.08' AS check_id, 'Discount equal to 100% of the line' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'WARN' END AS status
FROM (SELECT (SELECT count(*) FROM order_items oi WHERE oi.discount_amount > 0 AND oi.discount_amount = (oi.unit_sale_price * oi.quantity)) AS v) q
UNION ALL
-- B7.09 | Lines with a discount (%)
SELECT 'B7.09' AS check_id, 'Lines with a discount (%)' AS check_name, v::text AS value, 'info' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' ELSE 'INFO' END AS status
FROM (SELECT (SELECT round(100.0 * count(*) FILTER (WHERE discount_amount > 0) / NULLIF(count(*), 0), 1) FROM order_items) AS v) q
UNION ALL
-- B7.10 | Avg discount among discounted lines (% of line amount)
SELECT 'B7.10' AS check_id, 'Avg discount among discounted lines (% of line amount)' AS check_name, v::text AS value, 'info' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' ELSE 'INFO' END AS status
FROM (SELECT (SELECT round(avg(100.0 * discount_amount / NULLIF(unit_sale_price * quantity, 0)), 2) FROM order_items WHERE discount_amount > 0) AS v) q
UNION ALL
-- B7.11 | Max discount (% of line amount)
SELECT 'B7.11' AS check_id, 'Max discount (% of line amount)' AS check_name, v::text AS value, 'info' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' ELSE 'INFO' END AS status
FROM (SELECT (SELECT round(max(100.0 * discount_amount / NULLIF(unit_sale_price * quantity, 0)), 2) FROM order_items) AS v) q
UNION ALL
-- B7.12 | Lines sold below cost (unit_sale_price < unit_cost)
SELECT 'B7.12' AS check_id, 'Lines sold below cost (unit_sale_price < unit_cost)' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'WARN' END AS status
FROM (SELECT (SELECT count(*) FROM order_items WHERE unit_sale_price < unit_cost) AS v) q
UNION ALL
-- B7.13 | Products with purchase_price <= 0
SELECT 'B7.13' AS check_id, 'Products with purchase_price <= 0' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'WARN' END AS status
FROM (SELECT (SELECT count(*) FROM products WHERE purchase_price <= 0) AS v) q
UNION ALL
-- B7.14 | Products with standard_sale_price <= 0
SELECT 'B7.14' AS check_id, 'Products with standard_sale_price <= 0' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'WARN' END AS status
FROM (SELECT (SELECT count(*) FROM products WHERE standard_sale_price <= 0) AS v) q
UNION ALL
-- B7.15 | Products with standard_sale_price below purchase_price
SELECT 'B7.15' AS check_id, 'Products with standard_sale_price below purchase_price' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'WARN' END AS status
FROM (SELECT (SELECT count(*) FROM products WHERE standard_sale_price < purchase_price) AS v) q
UNION ALL
-- B7.16 | Lines with price deviating >10% from the product standard price
SELECT 'B7.16' AS check_id, 'Lines with price deviating >10% from the product standard price' AS check_name, v::text AS value, 'info' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' ELSE 'INFO' END AS status
FROM (SELECT (SELECT count(*) FROM order_items oi JOIN products p ON p.product_id = oi.product_id WHERE p.standard_sale_price > 0 AND abs(oi.unit_sale_price / p.standard_sale_price - 1) > 0.10) AS v) q
UNION ALL
-- B7.17 | Lines with unit_cost deviating >5% from the product purchase price
SELECT 'B7.17' AS check_id, 'Lines with unit_cost deviating >5% from the product purchase price' AS check_name, v::text AS value, 'info' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' ELSE 'INFO' END AS status
FROM (SELECT (SELECT count(*) FROM order_items oi JOIN products p ON p.product_id = oi.product_id WHERE p.purchase_price > 0 AND abs(oi.unit_cost / p.purchase_price - 1) > 0.05) AS v) q
UNION ALL
-- B7.18 | Order lines with fractional quantity
SELECT 'B7.18' AS check_id, 'Order lines with fractional quantity' AS check_name, v::text AS value, 'info' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' ELSE 'INFO' END AS status
FROM (SELECT (SELECT count(*) FROM order_items WHERE quantity <> trunc(quantity)) AS v) q
UNION ALL
-- B7.19 | Return lines with quantity <= 0 or negative refund
SELECT 'B7.19' AS check_id, 'Return lines with quantity <= 0 or negative refund' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT count(*) FROM return_items WHERE quantity <= 0 OR refund_unit_price < 0) AS v) q
UNION ALL
-- B7.20 | Return lines with refund_unit_price = 0
SELECT 'B7.20' AS check_id, 'Return lines with refund_unit_price = 0' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'WARN' END AS status
FROM (SELECT (SELECT count(*) FROM return_items WHERE refund_unit_price = 0) AS v) q
ORDER BY 1;


-- =====================================================================================
-- B8. Order statuses
-- =====================================================================================
-- B8.01 | Order statuses outside the expected list
SELECT 'B8.01' AS check_id, 'Order statuses outside the expected list' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'WARN' END AS status
FROM (SELECT (SELECT count(*) FROM order_statuses WHERE status_name NOT IN ('Completed','Processing','Cancelled','On Hold','Partially Fulfilled')) AS v) q
UNION ALL
-- B8.02 | Expected statuses missing in order_statuses
SELECT 'B8.02' AS check_id, 'Expected statuses missing in order_statuses' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'PROBLEM' END AS status
FROM (SELECT (SELECT 5 - count(*) FROM order_statuses WHERE status_name IN ('Completed','Processing','Cancelled','On Hold','Partially Fulfilled')) AS v) q
UNION ALL
-- B8.03 | Completed orders (%)
SELECT 'B8.03' AS check_id, 'Completed orders (%)' AS check_name, v::text AS value, 'info' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' ELSE 'INFO' END AS status
FROM (SELECT (SELECT round(100.0 * count(*) FILTER (WHERE s.status_name = 'Completed') / NULLIF(count(*), 0), 1) FROM orders o JOIN order_statuses s ON s.order_status_id = o.order_status_id) AS v) q
UNION ALL
-- B8.04 | Cancelled orders (%)
SELECT 'B8.04' AS check_id, 'Cancelled orders (%)' AS check_name, v::text AS value, 'info' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' ELSE 'INFO' END AS status
FROM (SELECT (SELECT round(100.0 * count(*) FILTER (WHERE s.status_name = 'Cancelled') / NULLIF(count(*), 0), 1) FROM orders o JOIN order_statuses s ON s.order_status_id = o.order_status_id) AS v) q
UNION ALL
-- B8.05 | Non-final orders (%)
SELECT 'B8.05' AS check_id, 'Non-final orders (%)' AS check_name, v::text AS value, 'info' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' ELSE 'INFO' END AS status
FROM (SELECT (SELECT round(100.0 * count(*) FILTER (WHERE s.status_name IN ('Processing','On Hold','Partially Fulfilled')) / NULLIF(count(*), 0), 1) FROM orders o JOIN order_statuses s ON s.order_status_id = o.order_status_id) AS v) q
UNION ALL
-- B8.06 | Non-final orders older than 90 days
SELECT 'B8.06' AS check_id, 'Non-final orders older than 90 days' AS check_name, v::text AS value, '0' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' WHEN v = 0 THEN 'OK' ELSE 'WARN' END AS status
FROM (SELECT (SELECT count(*) FROM orders o JOIN order_statuses s ON s.order_status_id = o.order_status_id WHERE s.status_name IN ('Processing','On Hold','Partially Fulfilled') AND o.order_date < localtimestamp - interval '90 days') AS v) q
UNION ALL
-- B8.07 | Order lines of products that are not Active (%)
SELECT 'B8.07' AS check_id, 'Order lines of products that are not Active (%)' AS check_name, v::text AS value, 'info' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' ELSE 'INFO' END AS status
FROM (SELECT (SELECT round(100.0 * count(*) FILTER (WHERE ps.status_name <> 'Active') / NULLIF(count(*), 0), 1) FROM order_items oi JOIN products p ON p.product_id = oi.product_id JOIN product_statuses ps ON ps.product_status_id = p.product_status_id) AS v) q
UNION ALL
-- B8.08 | Inactive customers (%)
SELECT 'B8.08' AS check_id, 'Inactive customers (%)' AS check_name, v::text AS value, 'info' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' ELSE 'INFO' END AS status
FROM (SELECT (SELECT round(100.0 * count(*) FILTER (WHERE NOT is_active) / NULLIF(count(*), 0), 1) FROM customers) AS v) q
ORDER BY 1;


-- =====================================================================================
-- B9. Financial baseline (quantifies findings C1-C4)
-- =====================================================================================
-- B9.01 | Gross revenue, all statuses
SELECT 'B9.01' AS check_id, 'Gross revenue, all statuses' AS check_name, v::text AS value, 'info' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' ELSE 'INFO' END AS status
FROM (SELECT (SELECT round(sum(oi.quantity * oi.unit_sale_price), 2) FROM order_items oi) AS v) q
UNION ALL
-- B9.02 | Total discounts, all statuses
SELECT 'B9.02' AS check_id, 'Total discounts, all statuses' AS check_name, v::text AS value, 'info' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' ELSE 'INFO' END AS status
FROM (SELECT (SELECT round(sum(discount_amount), 2) FROM order_items) AS v) q
UNION ALL
-- B9.03 | Gross revenue, Completed only
SELECT 'B9.03' AS check_id, 'Gross revenue, Completed only' AS check_name, v::text AS value, 'info' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' ELSE 'INFO' END AS status
FROM (SELECT (SELECT round(sum(oi.quantity * oi.unit_sale_price), 2) FROM order_items oi JOIN orders o ON o.order_id = oi.order_id JOIN order_statuses s ON s.order_status_id = o.order_status_id WHERE s.status_name = 'Completed') AS v) q
UNION ALL
-- B9.04 | Net revenue, Completed only (after discounts, before returns)
SELECT 'B9.04' AS check_id, 'Net revenue, Completed only (after discounts, before returns)' AS check_name, v::text AS value, 'info' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' ELSE 'INFO' END AS status
FROM (SELECT (SELECT round(sum(oi.quantity * oi.unit_sale_price) - sum(oi.discount_amount), 2) FROM order_items oi JOIN orders o ON o.order_id = oi.order_id JOIN order_statuses s ON s.order_status_id = o.order_status_id WHERE s.status_name = 'Completed') AS v) q
UNION ALL
-- B9.05 | Overstatement of current 'revenue' vs net Completed (%)
SELECT 'B9.05' AS check_id, 'Overstatement of current ''revenue'' vs net Completed (%)' AS check_name, v::text AS value, 'info' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' ELSE 'INFO' END AS status
FROM (SELECT (SELECT round(100.0 * ((SELECT sum(oi.quantity * oi.unit_sale_price) FROM order_items oi) / NULLIF((SELECT sum(oi.quantity * oi.unit_sale_price) - sum(oi.discount_amount) FROM order_items oi JOIN orders o ON o.order_id = oi.order_id JOIN order_statuses s ON s.order_status_id = o.order_status_id WHERE s.status_name = 'Completed'), 0) - 1), 1)) AS v) q
UNION ALL
-- B9.06 | Total refunds
SELECT 'B9.06' AS check_id, 'Total refunds' AS check_name, v::text AS value, 'info' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' ELSE 'INFO' END AS status
FROM (SELECT (SELECT round(COALESCE(sum(quantity * refund_unit_price), 0), 2) FROM return_items) AS v) q
UNION ALL
-- B9.07 | Refunds as % of net revenue (Completed)
SELECT 'B9.07' AS check_id, 'Refunds as % of net revenue (Completed)' AS check_name, v::text AS value, 'info' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' ELSE 'INFO' END AS status
FROM (SELECT (SELECT round(100.0 * (SELECT sum(quantity * refund_unit_price) FROM return_items) / NULLIF((SELECT sum(oi.quantity * oi.unit_sale_price) - sum(oi.discount_amount) FROM order_items oi JOIN orders o ON o.order_id = oi.order_id JOIN order_statuses s ON s.order_status_id = o.order_status_id WHERE s.status_name = 'Completed'), 0), 2)) AS v) q
UNION ALL
-- B9.08 | Gross margin %, Completed, after discounts, before returns
SELECT 'B9.08' AS check_id, 'Gross margin %, Completed, after discounts, before returns' AS check_name, v::text AS value, 'info' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' ELSE 'INFO' END AS status
FROM (SELECT (SELECT round(100.0 * (sum(oi.quantity * oi.unit_sale_price) - sum(oi.discount_amount) - sum(oi.quantity * oi.unit_cost)) / NULLIF(sum(oi.quantity * oi.unit_sale_price) - sum(oi.discount_amount), 0), 2) FROM order_items oi JOIN orders o ON o.order_id = oi.order_id JOIN order_statuses s ON s.order_status_id = o.order_status_id WHERE s.status_name = 'Completed') AS v) q
ORDER BY 1;


-- =====================================================================================
-- B10. Distribution profile (realism of the data)
-- =====================================================================================
-- B10.01 | Products with at least one sale
SELECT 'B10.01' AS check_id, 'Products with at least one sale' AS check_name, v::text AS value, 'info' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' ELSE 'INFO' END AS status
FROM (SELECT (SELECT count(DISTINCT product_id) FROM order_items) AS v) q
UNION ALL
-- B10.02 | Share of sold products that make 80% of gross revenue (%)
SELECT 'B10.02' AS check_id, 'Share of sold products that make 80% of gross revenue (%)' AS check_name, v::text AS value, 'info' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' ELSE 'INFO' END AS status
FROM (SELECT (SELECT round(100.0 * count(*) FILTER (WHERE cb < 0.8 * tot) / NULLIF(count(*), 0), 1) FROM (SELECT COALESCE(sum(rev) OVER (ORDER BY rev DESC, k ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING), 0) AS cb, sum(rev) OVER () AS tot FROM (SELECT product_id AS k, sum(quantity * unit_sale_price) AS rev FROM order_items GROUP BY product_id) p) r) AS v) q
UNION ALL
-- B10.03 | Share of buying customers that make 80% of gross revenue (%)
SELECT 'B10.03' AS check_id, 'Share of buying customers that make 80% of gross revenue (%)' AS check_name, v::text AS value, 'info' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' ELSE 'INFO' END AS status
FROM (SELECT (SELECT round(100.0 * count(*) FILTER (WHERE cb < 0.8 * tot) / NULLIF(count(*), 0), 1) FROM (SELECT COALESCE(sum(rev) OVER (ORDER BY rev DESC, k ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING), 0) AS cb, sum(rev) OVER () AS tot FROM (SELECT o.customer_id AS k, sum(oi.quantity * oi.unit_sale_price) AS rev FROM order_items oi JOIN orders o ON o.order_id = oi.order_id GROUP BY o.customer_id) p) r) AS v) q
UNION ALL
-- B10.04 | Top 10 brands: share of gross revenue (%)
SELECT 'B10.04' AS check_id, 'Top 10 brands: share of gross revenue (%)' AS check_name, v::text AS value, 'info' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' ELSE 'INFO' END AS status
FROM (SELECT (SELECT round(100.0 * sum(rev) / NULLIF((SELECT sum(quantity * unit_sale_price) FROM order_items), 0), 1) FROM (SELECT sum(oi.quantity * oi.unit_sale_price) AS rev FROM order_items oi JOIN products p ON p.product_id = oi.product_id GROUP BY p.brand_id ORDER BY 1 DESC LIMIT 10) t) AS v) q
UNION ALL
-- B10.05 | Lowest brand margin (%)
SELECT 'B10.05' AS check_id, 'Lowest brand margin (%)' AS check_name, v::text AS value, 'info' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' ELSE 'INFO' END AS status
FROM (SELECT (SELECT round(min(100.0 * prof / NULLIF(rev, 0)), 1) FROM (SELECT sum(oi.quantity * oi.unit_sale_price) AS rev, sum(oi.quantity * (oi.unit_sale_price - oi.unit_cost)) AS prof FROM order_items oi JOIN products p ON p.product_id = oi.product_id GROUP BY p.brand_id) t) AS v) q
UNION ALL
-- B10.06 | Highest brand margin (%)
SELECT 'B10.06' AS check_id, 'Highest brand margin (%)' AS check_name, v::text AS value, 'info' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' ELSE 'INFO' END AS status
FROM (SELECT (SELECT round(max(100.0 * prof / NULLIF(rev, 0)), 1) FROM (SELECT sum(oi.quantity * oi.unit_sale_price) AS rev, sum(oi.quantity * (oi.unit_sale_price - oi.unit_cost)) AS prof FROM order_items oi JOIN products p ON p.product_id = oi.product_id GROUP BY p.brand_id) t) AS v) q
UNION ALL
-- B10.07 | Seasonality: busiest month orders / quietest full month orders
SELECT 'B10.07' AS check_id, 'Seasonality: busiest month orders / quietest full month orders' AS check_name, v::text AS value, 'info' AS expected, CASE WHEN v IS NULL THEN 'NO_DATA' ELSE 'INFO' END AS status
FROM (SELECT (SELECT round(max(n)::numeric / NULLIF(min(n), 0), 2) FROM (SELECT date_trunc('month', order_date) AS m, count(*) AS n FROM orders GROUP BY 1) t WHERE m > (SELECT date_trunc('month', min(order_date)) FROM orders) AND m < (SELECT date_trunc('month', max(order_date)) FROM orders)) AS v) q
ORDER BY 1;


-- =====================================================================================
-- D1. Top 20 order lines with returned quantity above sold quantity (empty = none)
-- =====================================================================================
SELECT oi.order_item_id, oi.order_id, oi.product_id, oi.quantity AS sold_qty,
       sum(ri.quantity) AS returned_qty, count(*) AS return_lines, count(DISTINCT ri.return_id) AS returns
FROM order_items oi JOIN return_items ri ON ri.order_item_id = oi.order_item_id
GROUP BY oi.order_item_id, oi.order_id, oi.product_id, oi.quantity
HAVING sum(ri.quantity) > oi.quantity
ORDER BY sum(ri.quantity) - oi.quantity DESC, oi.order_item_id
LIMIT 20;

-- =====================================================================================
-- D2. Duplicate salespersons (empty = none)
-- =====================================================================================
SELECT first_name, last_name, hire_date, count(*) AS copies, min(salesperson_id) AS first_id, max(salesperson_id) AS last_id
FROM salespersons
GROUP BY first_name, last_name, hire_date
HAVING count(*) > 1
ORDER BY copies DESC, last_name, first_name;

-- =====================================================================================
-- D3. 20 largest gaps: order placed before the customer registration date (empty = none)
-- =====================================================================================
SELECT o.order_id, o.customer_id, c.registration_date, o.order_date::date AS order_date,
       (c.registration_date - o.order_date::date) AS days_before_registration
FROM orders o JOIN customers c ON c.customer_id = o.customer_id
WHERE c.registration_date IS NOT NULL AND o.order_date::date < c.registration_date
ORDER BY days_before_registration DESC, o.order_id
LIMIT 20;

-- =====================================================================================
-- D4. Order status distribution (orders, lines, gross and net revenue)
-- =====================================================================================
SELECT s.status_name,
       count(DISTINCT o.order_id) AS orders,
       round(100.0 * count(DISTINCT o.order_id) / NULLIF(sum(count(DISTINCT o.order_id)) OVER (), 0), 1) AS pct_orders,
       count(oi.order_item_id) AS lines,
       round(COALESCE(sum(oi.quantity * oi.unit_sale_price), 0), 2) AS gross_revenue,
       round(COALESCE(sum(oi.quantity * oi.unit_sale_price - oi.discount_amount), 0), 2) AS net_of_discount_revenue
FROM order_statuses s
LEFT JOIN orders o ON o.order_status_id = s.order_status_id
LEFT JOIN order_items oi ON oi.order_id = o.order_id
GROUP BY s.status_name
ORDER BY orders DESC;

-- =====================================================================================
-- D5. Product status distribution and order lines sold per product status
-- =====================================================================================
SELECT ps.status_name AS product_status,
       count(DISTINCT p.product_id) AS products,
       count(oi.order_item_id) AS order_lines,
       round(COALESCE(sum(oi.quantity * oi.unit_sale_price), 0), 2) AS gross_revenue
FROM product_statuses ps
LEFT JOIN products p ON p.product_status_id = ps.product_status_id
LEFT JOIN order_items oi ON oi.product_id = p.product_id
GROUP BY ps.status_name
ORDER BY products DESC;

-- =====================================================================================
-- D6. Monthly profile: orders, lines, gross revenue, returns (seasonality and volume)
-- =====================================================================================
SELECT to_char(m.month, 'YYYY-MM') AS month,
       m.orders, m.lines, m.gross_revenue,
       COALESCE(r.returns, 0) AS returns_dated_in_month
FROM (SELECT date_trunc('month', o.order_date) AS month, count(DISTINCT o.order_id) AS orders,
             count(oi.order_item_id) AS lines, round(COALESCE(sum(oi.quantity * oi.unit_sale_price), 0), 2) AS gross_revenue
      FROM orders o LEFT JOIN order_items oi ON oi.order_id = o.order_id GROUP BY 1) m
LEFT JOIN (SELECT date_trunc('month', return_date) AS month, count(*) AS returns FROM returns GROUP BY 1) r ON r.month = m.month
ORDER BY m.month;

-- =====================================================================================
-- D7. Customers: orders per customer type (does behavior differ by type?)
-- =====================================================================================
SELECT ct.type_name, count(DISTINCT c.customer_id) AS customers,
       count(DISTINCT o.order_id) AS orders,
       round(count(DISTINCT o.order_id)::numeric / NULLIF(count(DISTINCT c.customer_id), 0), 1) AS orders_per_customer,
       round(COALESCE(sum(oi.quantity * oi.unit_sale_price), 0) / NULLIF(count(DISTINCT o.order_id), 0), 2) AS avg_gross_order_value
FROM customer_types ct
LEFT JOIN customers c ON c.customer_type_id = ct.customer_type_id
LEFT JOIN orders o ON o.customer_id = c.customer_id
LEFT JOIN order_items oi ON oi.order_id = o.order_id
GROUP BY ct.type_name
ORDER BY customers DESC;

-- =====================================================================================
RESET default_transaction_read_only;
RESET statement_timeout;