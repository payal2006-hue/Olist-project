-- ============================================================
-- Olist E-Commerce Analytics
-- PostgreSQL Database Schema
-- ============================================================

-- ============================================================
-- 1. CUSTOMERS
-- ============================================================

CREATE TABLE customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    customer_unique_id VARCHAR(50) NOT NULL,
    customer_zip_code_prefix INTEGER,
    customer_city VARCHAR(100),
    customer_state VARCHAR(10)
);


-- ============================================================
-- 2. SELLERS
-- ============================================================

CREATE TABLE sellers (
    seller_id VARCHAR(50) PRIMARY KEY,
    seller_zip_code_prefix INTEGER,
    seller_city VARCHAR(100),
    seller_state VARCHAR(10)
);


-- ============================================================
-- 3. PRODUCTS
-- ============================================================

CREATE TABLE products (
    product_id VARCHAR(50) PRIMARY KEY,
    product_category_name VARCHAR(100),
    product_name_lenght INTEGER,
    product_description_lenght INTEGER,
    product_photos_qty INTEGER,
    product_weight_g NUMERIC(10, 2),
    product_length_cm NUMERIC(10, 2),
    product_height_cm NUMERIC(10, 2),
    product_width_cm NUMERIC(10, 2)
);


-- ============================================================
-- 4. ORDERS
-- ============================================================

CREATE TABLE orders (
    order_id VARCHAR(50) PRIMARY KEY,

    customer_id VARCHAR(50) NOT NULL,

    order_status VARCHAR(30) NOT NULL,

    order_purchase_timestamp TIMESTAMP NOT NULL,
    order_approved_at TIMESTAMP,
    order_delivered_carrier_date TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP,

    CONSTRAINT fk_orders_customer
        FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id)
);


-- ============================================================
-- 5. ORDER ITEMS
-- ============================================================

CREATE TABLE order_items (
    order_id VARCHAR(50) NOT NULL,
    order_item_id INTEGER NOT NULL,

    product_id VARCHAR(50) NOT NULL,
    seller_id VARCHAR(50) NOT NULL,

    shipping_limit_date TIMESTAMP,

    price NUMERIC(12, 2) NOT NULL,
    freight_value NUMERIC(12, 2) NOT NULL,

    CONSTRAINT pk_order_items
        PRIMARY KEY (order_id, order_item_id),

    CONSTRAINT fk_order_items_order
        FOREIGN KEY (order_id)
        REFERENCES orders(order_id),

    CONSTRAINT fk_order_items_product
        FOREIGN KEY (product_id)
        REFERENCES products(product_id),

    CONSTRAINT fk_order_items_seller
        FOREIGN KEY (seller_id)
        REFERENCES sellers(seller_id),

    CONSTRAINT chk_order_items_price
        CHECK (price >= 0),

    CONSTRAINT chk_order_items_freight
        CHECK (freight_value >= 0)
);


-- ============================================================
-- 6. PAYMENTS
-- ============================================================

CREATE TABLE payments (
    order_id VARCHAR(50) NOT NULL,
    payment_sequential INTEGER NOT NULL,

    payment_type VARCHAR(30) NOT NULL,
    payment_installments INTEGER NOT NULL,
    payment_value NUMERIC(12, 2) NOT NULL,

    CONSTRAINT pk_payments
        PRIMARY KEY (order_id, payment_sequential),

    CONSTRAINT fk_payments_order
        FOREIGN KEY (order_id)
        REFERENCES orders(order_id),

    CONSTRAINT chk_payment_installments
        CHECK (payment_installments > 0),

    CONSTRAINT chk_payment_value
        CHECK (payment_value >= 0)
);


-- ============================================================
-- 7. REVIEWS
-- ============================================================

CREATE TABLE reviews (
    review_id VARCHAR(50) PRIMARY KEY,

    order_id VARCHAR(50) NOT NULL,

    review_score INTEGER NOT NULL,

    review_comment_title TEXT,
    review_comment_message TEXT,

    review_creation_date TIMESTAMP,
    review_answer_timestamp TIMESTAMP,

    CONSTRAINT fk_reviews_order
        FOREIGN KEY (order_id)
        REFERENCES orders(order_id),

    CONSTRAINT chk_review_score
        CHECK (review_score BETWEEN 1 AND 5)
);


-- ============================================================
-- 8. CATEGORY TRANSLATION
-- Lookup/reference table
-- ============================================================

CREATE TABLE category_translation (
    product_category_name VARCHAR(100) PRIMARY KEY,
    product_category_name_english VARCHAR(100) NOT NULL
);


-- ============================================================
-- INDEXES
-- ============================================================

-- Orders
CREATE INDEX idx_orders_customer_id
    ON orders(customer_id);

CREATE INDEX idx_orders_purchase_timestamp
    ON orders(order_purchase_timestamp);

CREATE INDEX idx_orders_status
    ON orders(order_status);

CREATE INDEX idx_orders_estimated_delivery
    ON orders(order_estimated_delivery_date);

CREATE INDEX idx_orders_delivered_customer
    ON orders(order_delivered_customer_date);


-- Order items
CREATE INDEX idx_order_items_product_id
    ON order_items(product_id);

CREATE INDEX idx_order_items_seller_id
    ON order_items(seller_id);


-- Payments
CREATE INDEX idx_payments_order_id
    ON payments(order_id);


-- Reviews
CREATE INDEX idx_reviews_order_id
    ON reviews(order_id);


-- Products
CREATE INDEX idx_products_category
    ON products(product_category_name);


-- Customers
CREATE INDEX idx_customers_state
    ON customers(customer_state);


-- Sellers
CREATE INDEX idx_sellers_state
    ON sellers(seller_state);