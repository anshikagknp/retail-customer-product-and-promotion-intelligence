DROP TABLE IF EXISTS coupon_redemptions CASCADE;
DROP TABLE IF EXISTS coupons CASCADE;
DROP TABLE IF EXISTS campaign_households CASCADE;
DROP TABLE IF EXISTS campaigns CASCADE;
DROP TABLE IF EXISTS transactions CASCADE;
DROP TABLE IF EXISTS baskets CASCADE;
DROP TABLE IF EXISTS demographics CASCADE;
DROP TABLE IF EXISTS products CASCADE;

-- Profiled subset of households
CREATE TABLE demographics (
    classification_1    VARCHAR(50),
    classification_2    VARCHAR(50),
    classification_3    VARCHAR(50),
    homeowner_desc      VARCHAR(50),
    classification_5    VARCHAR(50),
    classification_4    VARCHAR(50),
    kid_category_desc   VARCHAR(50),
    household_key       INT PRIMARY KEY
);

-- Product catalog master
CREATE TABLE products (
    product_id            INT PRIMARY KEY,
    manufacturer          INT NOT NULL,
    department            VARCHAR(100) NOT NULL,
    brand                 VARCHAR(50) NOT NULL,
    commodity_desc        VARCHAR(100) NOT NULL,
    sub_commodity_desc    VARCHAR(100) NOT NULL,
    curr_size_of_product  VARCHAR(50)
);

-- Campaign descriptions
CREATE TABLE campaigns (
    description    VARCHAR(50) NOT NULL,
    campaign       INT PRIMARY KEY,
    start_day      INT NOT NULL,
    end_day        INT NOT NULL,
    duration_days  INT NOT NULL
);

-- Targeted households per campaign
CREATE TABLE campaign_households (
    description    VARCHAR(50) NOT NULL,
    household_key  INT NOT NULL,
    campaign       INT NOT NULL REFERENCES campaigns(campaign),
    PRIMARY KEY (campaign, household_key)
);

-- Coupon to product mappings
CREATE TABLE coupons (
    coupon_upc  BIGINT NOT NULL,
    product_id  INT NOT NULL REFERENCES products(product_id),
    campaign    INT NOT NULL REFERENCES campaigns(campaign),
    PRIMARY KEY (coupon_upc, product_id, campaign)
);

-- Coupon redemptions log
CREATE TABLE coupon_redemptions (
    household_key  INT NOT NULL,
    day            INT NOT NULL,
    coupon_upc     BIGINT NOT NULL,
    campaign       INT NOT NULL REFERENCES campaigns(campaign)
);

-- Basket level shopping trips
CREATE TABLE baskets (
    basket_id               BIGINT PRIMARY KEY,
    household_key           INT NOT NULL,
    day                     INT NOT NULL,
    week_no                 INT NOT NULL,
    store_id                INT NOT NULL,
    trans_time              INT NOT NULL,
    line_item_count         INT NOT NULL,
    distinct_product_count  INT NOT NULL,
    total_quantity          INT NOT NULL,
    basket_sales            NUMERIC(10,2) NOT NULL,
    basket_net_spend        NUMERIC(10,2) NOT NULL,
    retail_disc_amount      NUMERIC(10,2) NOT NULL,
    coupon_disc_amount      NUMERIC(10,2) NOT NULL,
    coupon_match_amount     NUMERIC(10,2) NOT NULL,
    total_discount_amount   NUMERIC(10,2) NOT NULL,
    has_coupon_used         BOOLEAN NOT NULL,
    has_retail_disc_used    BOOLEAN NOT NULL,
    avg_line_item_value     NUMERIC(10,2) NOT NULL,
    discount_rate_pct       NUMERIC(5,2) NOT NULL
);

-- Transaction product line items
CREATE TABLE transactions (
    household_key       INT NOT NULL,
    basket_id           BIGINT NOT NULL,
    day                 INT NOT NULL,
    product_id          INT NOT NULL REFERENCES products(product_id),
    quantity            INT NOT NULL,
    sales_value         NUMERIC(10,2) NOT NULL,
    store_id            INT NOT NULL,
    retail_disc         NUMERIC(10,2) NOT NULL,
    trans_time          INT NOT NULL,
    week_no             INT NOT NULL,
    coupon_disc         NUMERIC(10,2) NOT NULL,
    coupon_match_disc   NUMERIC(10,2) NOT NULL,
    total_disc          NUMERIC(10,2) NOT NULL,
    discount_amount     NUMERIC(10,2) NOT NULL,
    retail_disc_amount  NUMERIC(10,2) NOT NULL,
    coupon_disc_amount  NUMERIC(10,2) NOT NULL,
    coupon_match_amount NUMERIC(10,2) NOT NULL,
    net_customer_spend  NUMERIC(10,2) NOT NULL,
    unit_shelf_price    NUMERIC(10,4),
    unit_realized_price NUMERIC(10,4),
    is_zero_quantity    BOOLEAN NOT NULL,
    is_zero_sales       BOOLEAN NOT NULL,
    has_coupon          BOOLEAN NOT NULL,
    has_retail_disc     BOOLEAN NOT NULL
);

-- Analytical indexes
CREATE INDEX idx_transactions_household ON transactions(household_key);
CREATE INDEX idx_transactions_product   ON transactions(product_id);
CREATE INDEX idx_transactions_basket    ON transactions(basket_id);
CREATE INDEX idx_transactions_day_week  ON transactions(day, week_no);
CREATE INDEX idx_products_dept_brand    ON products(department, brand);
CREATE INDEX idx_products_commodity     ON products(commodity_desc);
CREATE INDEX idx_baskets_household      ON baskets(household_key);
CREATE INDEX idx_baskets_day_week       ON baskets(day, week_no);
CREATE INDEX idx_redemptions_camp_hh    ON coupon_redemptions(campaign, household_key);

-- Data loading commands
-- \copy demographics FROM 'data/processed/cleaned_demographics.csv' WITH (FORMAT csv, HEADER true);
-- \copy products FROM 'data/processed/cleaned_products.csv' WITH (FORMAT csv, HEADER true);
-- \copy campaigns FROM 'data/processed/cleaned_campaigns.csv' WITH (FORMAT csv, HEADER true);
-- \copy campaign_households FROM 'data/processed/cleaned_campaign_households.csv' WITH (FORMAT csv, HEADER true);
-- \copy coupons FROM 'data/processed/cleaned_coupons.csv' WITH (FORMAT csv, HEADER true);
-- \copy coupon_redemptions FROM 'data/processed/cleaned_coupon_redemptions.csv' WITH (FORMAT csv, HEADER true);
-- \copy baskets FROM 'data/processed/baskets.csv' WITH (FORMAT csv, HEADER true);
-- \copy transactions FROM 'data/processed/cleaned_transactions.csv' WITH (FORMAT csv, HEADER true);
