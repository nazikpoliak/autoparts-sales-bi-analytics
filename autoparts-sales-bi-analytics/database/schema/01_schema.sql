CREATE TABLE regions (
    region_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    region_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE cities (
    city_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    region_id INTEGER NOT NULL,
    city_name VARCHAR(100) NOT NULL,
    CONSTRAINT fk_cities_region
        FOREIGN KEY (region_id)
        REFERENCES regions(region_id),
    CONSTRAINT uq_cities_region_name
        UNIQUE (region_id, city_name)
);

CREATE TABLE customer_types (
    customer_type_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    type_name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE customers (
    customer_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_type_id INTEGER NOT NULL,
    city_id INTEGER,
    customer_name VARCHAR(200) NOT NULL,
    tax_id VARCHAR(50),
    phone VARCHAR(50),
    email VARCHAR(150),
    address VARCHAR(255),
    registration_date DATE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT fk_customers_type
        FOREIGN KEY (customer_type_id)
        REFERENCES customer_types(customer_type_id),
    CONSTRAINT fk_customers_city
        FOREIGN KEY (city_id)
        REFERENCES cities(city_id),
    CONSTRAINT uq_customers_tax_id
        UNIQUE (tax_id)
);

CREATE TABLE salespersons (
    salesperson_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    region_id INTEGER,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(150),
    phone VARCHAR(50),
    hire_date DATE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT fk_salespersons_region
        FOREIGN KEY (region_id)
        REFERENCES regions(region_id)
);

CREATE TABLE sales_channels (
    sales_channel_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    channel_name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE order_statuses (
    order_status_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    status_name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE brands (
    brand_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    brand_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE categories (
    category_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE subcategories (
    subcategory_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    category_id INTEGER NOT NULL,
    subcategory_name VARCHAR(100) NOT NULL,
    CONSTRAINT fk_subcategories_category
        FOREIGN KEY (category_id)
        REFERENCES categories(category_id),
    CONSTRAINT uq_subcategories_category_name
        UNIQUE (category_id, subcategory_name)
);

CREATE TABLE suppliers (
    supplier_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    supplier_name VARCHAR(200) NOT NULL UNIQUE,
    contact_name VARCHAR(150),
    phone VARCHAR(50),
    email VARCHAR(150),
    country VARCHAR(100),
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE product_statuses (
    product_status_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    status_name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE products (
    product_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    subcategory_id INTEGER NOT NULL,
    brand_id INTEGER NOT NULL,
    supplier_id INTEGER NOT NULL,
    product_status_id INTEGER NOT NULL,
    sku VARCHAR(100) NOT NULL UNIQUE,
    product_name VARCHAR(255) NOT NULL,
    description TEXT,
    unit_of_measure VARCHAR(20) NOT NULL DEFAULT 'pcs',
    purchase_price NUMERIC(12, 2) NOT NULL,
    standard_sale_price NUMERIC(12, 2) NOT NULL,
    weight_kg NUMERIC(10, 3),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_products_subcategory
        FOREIGN KEY (subcategory_id)
        REFERENCES subcategories(subcategory_id),
    CONSTRAINT fk_products_brand
        FOREIGN KEY (brand_id)
        REFERENCES brands(brand_id),
    CONSTRAINT fk_products_supplier
        FOREIGN KEY (supplier_id)
        REFERENCES suppliers(supplier_id),
    CONSTRAINT fk_products_status
        FOREIGN KEY (product_status_id)
        REFERENCES product_statuses(product_status_id),
    CONSTRAINT chk_products_purchase_price
        CHECK (purchase_price >= 0),
    CONSTRAINT chk_products_sale_price
        CHECK (standard_sale_price >= 0),
    CONSTRAINT chk_products_weight
        CHECK (weight_kg IS NULL OR weight_kg >= 0)
);

CREATE TABLE orders (
    order_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    salesperson_id INTEGER,
    sales_channel_id INTEGER NOT NULL,
    order_status_id INTEGER NOT NULL,
    order_date TIMESTAMP NOT NULL,
    customer_reference VARCHAR(100),
    notes TEXT,
    CONSTRAINT fk_orders_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id),
    CONSTRAINT fk_orders_salesperson
        FOREIGN KEY (salesperson_id)
        REFERENCES salespersons(salesperson_id),
    CONSTRAINT fk_orders_channel
        FOREIGN KEY (sales_channel_id)
        REFERENCES sales_channels(sales_channel_id),
    CONSTRAINT fk_orders_status
        FOREIGN KEY (order_status_id)
        REFERENCES order_statuses(order_status_id)
);

CREATE TABLE order_items (
    order_item_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id BIGINT NOT NULL,
    product_id INTEGER NOT NULL,
    quantity NUMERIC(12, 3) NOT NULL,
    unit_sale_price NUMERIC(12, 2) NOT NULL,
    unit_cost NUMERIC(12, 2) NOT NULL,
    discount_amount NUMERIC(12, 2) NOT NULL DEFAULT 0,
    CONSTRAINT fk_order_items_order
        FOREIGN KEY (order_id)
        REFERENCES orders(order_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_order_items_product
        FOREIGN KEY (product_id)
        REFERENCES products(product_id),
    CONSTRAINT chk_order_items_quantity
        CHECK (quantity > 0),
    CONSTRAINT chk_order_items_sale_price
        CHECK (unit_sale_price >= 0),
    CONSTRAINT chk_order_items_cost
        CHECK (unit_cost >= 0),
    CONSTRAINT chk_order_items_discount
        CHECK (discount_amount >= 0)
);

CREATE TABLE return_reasons (
    return_reason_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    reason_name VARCHAR(150) NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE returns (
    return_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id BIGINT NOT NULL,
    customer_id INTEGER NOT NULL,
    return_reason_id INTEGER NOT NULL,
    return_date TIMESTAMP NOT NULL,
    notes TEXT,
    CONSTRAINT fk_returns_order
        FOREIGN KEY (order_id)
        REFERENCES orders(order_id),
    CONSTRAINT fk_returns_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id),
    CONSTRAINT fk_returns_reason
        FOREIGN KEY (return_reason_id)
        REFERENCES return_reasons(return_reason_id)
);

CREATE TABLE return_items (
    return_item_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    return_id BIGINT NOT NULL,
    order_item_id BIGINT NOT NULL,
    product_id INTEGER NOT NULL,
    quantity NUMERIC(12, 3) NOT NULL,
    refund_unit_price NUMERIC(12, 2) NOT NULL,
    CONSTRAINT fk_return_items_return
        FOREIGN KEY (return_id)
        REFERENCES returns(return_id)
        ON DELETE CASCADE,
    CONSTRAINT fk_return_items_order_item
        FOREIGN KEY (order_item_id)
        REFERENCES order_items(order_item_id),
    CONSTRAINT fk_return_items_product
        FOREIGN KEY (product_id)
        REFERENCES products(product_id),
    CONSTRAINT chk_return_items_quantity
        CHECK (quantity > 0),
    CONSTRAINT chk_return_items_refund_price
        CHECK (refund_unit_price >= 0),
    CONSTRAINT uq_return_items_return_order_item
        UNIQUE (return_id, order_item_id)
);

CREATE INDEX idx_cities_region_id
    ON cities(region_id);

CREATE INDEX idx_customers_city_id
    ON customers(city_id);

CREATE INDEX idx_customers_customer_type_id
    ON customers(customer_type_id);

CREATE INDEX idx_salespersons_region_id
    ON salespersons(region_id);

CREATE INDEX idx_subcategories_category_id
    ON subcategories(category_id);

CREATE INDEX idx_products_subcategory_id
    ON products(subcategory_id);

CREATE INDEX idx_products_brand_id
    ON products(brand_id);

CREATE INDEX idx_products_supplier_id
    ON products(supplier_id);

CREATE INDEX idx_products_status_id
    ON products(product_status_id);

CREATE INDEX idx_orders_customer_id
    ON orders(customer_id);

CREATE INDEX idx_orders_salesperson_id
    ON orders(salesperson_id);

CREATE INDEX idx_orders_sales_channel_id
    ON orders(sales_channel_id);

CREATE INDEX idx_orders_status_id
    ON orders(order_status_id);

CREATE INDEX idx_orders_order_date
    ON orders(order_date);

CREATE INDEX idx_order_items_order_id
    ON order_items(order_id);

CREATE INDEX idx_order_items_product_id
    ON order_items(product_id);

CREATE INDEX idx_returns_order_id
    ON returns(order_id);

CREATE INDEX idx_returns_customer_id
    ON returns(customer_id);

CREATE INDEX idx_returns_return_reason_id
    ON returns(return_reason_id);

CREATE INDEX idx_returns_return_date
    ON returns(return_date);

CREATE INDEX idx_return_items_return_id
    ON return_items(return_id);

CREATE INDEX idx_return_items_order_item_id
    ON return_items(order_item_id);

CREATE INDEX idx_return_items_product_id
    ON return_items(product_id);