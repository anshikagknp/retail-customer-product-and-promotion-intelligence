-- Department performance and storewide penetration
WITH dept_stats AS (
    SELECT 
        p.department,
        COUNT(t.product_id) AS transaction_lines,
        COUNT(DISTINCT t.basket_id) AS unique_baskets,
        COUNT(DISTINCT t.product_id) AS active_products,
        SUM(t.quantity) AS total_quantity,
        SUM(t.sales_value) AS department_sales,
        SUM(t.retail_disc_amount) AS total_retail_discounts
    FROM transactions t
    JOIN products p ON t.product_id = p.product_id
    GROUP BY p.department
),
overall_totals AS (
    SELECT 
        SUM(sales_value) AS grand_total_sales,
        COUNT(DISTINCT basket_id) AS grand_total_baskets
    FROM transactions
)
SELECT 
    d.department,
    ROUND(d.department_sales, 2) AS total_sales,
    ROUND((d.department_sales / o.grand_total_sales * 100), 2) AS sales_share_pct,
    d.transaction_lines,
    d.unique_baskets,
    ROUND((d.unique_baskets::NUMERIC / o.grand_total_baskets * 100), 1) AS basket_penetration_pct,
    d.total_quantity,
    d.active_products,
    ROUND(d.total_retail_discounts, 2) AS total_retail_discounts,
    DENSE_RANK() OVER (ORDER BY d.department_sales DESC) AS revenue_rank
FROM dept_stats d
CROSS JOIN overall_totals o
ORDER BY d.department_sales DESC;

-- National brand versus private label split by department
SELECT 
    p.department,
    ROUND(SUM(CASE WHEN p.brand = 'Private' THEN t.sales_value ELSE 0 END), 2) AS private_label_sales,
    ROUND(SUM(CASE WHEN p.brand = 'National' THEN t.sales_value ELSE 0 END), 2) AS national_brand_sales,
    ROUND(SUM(t.sales_value), 2) AS total_department_sales,
    ROUND(
        (SUM(CASE WHEN p.brand = 'Private' THEN t.sales_value ELSE 0 END) / NULLIF(SUM(t.sales_value), 0) * 100), 2
    ) AS private_label_share_pct,
    ROUND(
        AVG(CASE WHEN p.brand = 'Private' AND t.quantity > 0 THEN t.unit_realized_price END), 2
    ) AS avg_private_unit_price,
    ROUND(
        AVG(CASE WHEN p.brand = 'National' AND t.quantity > 0 THEN t.unit_realized_price END), 2
    ) AS avg_national_unit_price
FROM transactions t
JOIN products p ON t.product_id = p.product_id
GROUP BY p.department
HAVING SUM(t.sales_value) >= 50000.00
ORDER BY total_department_sales DESC;

-- Top 5 revenue products per department
WITH product_dept_sales AS (
    SELECT 
        p.department,
        p.product_id,
        p.commodity_desc,
        p.sub_commodity_desc,
        p.brand,
        p.curr_size_of_product,
        SUM(t.sales_value) AS product_sales,
        SUM(t.quantity) AS product_quantity,
        COUNT(DISTINCT t.household_key) AS purchasing_households,
        ROW_NUMBER() OVER (PARTITION BY p.department ORDER BY SUM(t.sales_value) DESC) AS rank_in_dept
    FROM transactions t
    JOIN products p ON t.product_id = p.product_id
    GROUP BY p.department, p.product_id, p.commodity_desc, p.sub_commodity_desc, p.brand, p.curr_size_of_product
)
SELECT 
    department,
    rank_in_dept,
    product_id,
    commodity_desc,
    sub_commodity_desc,
    brand,
    curr_size_of_product,
    ROUND(product_sales, 2) AS total_sales,
    product_quantity,
    purchasing_households
FROM product_dept_sales
WHERE rank_in_dept <= 5
ORDER BY department, rank_in_dept;

-- Top 20 revenue products storewide
SELECT 
    t.product_id,
    p.department,
    p.commodity_desc,
    p.sub_commodity_desc,
    p.brand,
    p.curr_size_of_product,
    ROUND(SUM(t.sales_value), 2) AS total_sales,
    SUM(t.quantity) AS total_quantity,
    COUNT(DISTINCT t.basket_id) AS basket_count,
    COUNT(DISTINCT t.household_key) AS purchasing_households,
    CASE 
        WHEN p.commodity_desc LIKE '%GASOLINE%' OR p.sub_commodity_desc LIKE '%GASOLINE%' THEN 'Fuel / Gas Station'
        ELSE 'In-Store Retail Item'
    END AS item_category_type
FROM transactions t
JOIN products p ON t.product_id = p.product_id
GROUP BY t.product_id, p.department, p.commodity_desc, p.sub_commodity_desc, p.brand, p.curr_size_of_product
ORDER BY total_sales DESC
LIMIT 20;

-- Product sales velocity tiers and long-tail distribution
WITH product_lifetime_revenue AS (
    SELECT 
        p.product_id,
        COALESCE(SUM(t.sales_value), 0.00) AS lifetime_sales,
        COALESCE(SUM(t.quantity), 0) AS lifetime_units
    FROM products p
    LEFT JOIN transactions t ON p.product_id = t.product_id
    GROUP BY p.product_id
),
revenue_tiers AS (
    SELECT 
        product_id,
        lifetime_sales,
        lifetime_units,
        CASE 
            WHEN lifetime_sales = 0 THEN '1. Inactive / Zero Sales'
            WHEN lifetime_sales < 50.00 THEN '2. Very Low Velocity (< $50)'
            WHEN lifetime_sales < 250.00 THEN '3. Low Velocity ($50 - $250)'
            WHEN lifetime_sales < 1000.00 THEN '4. Moderate Velocity ($250 - $1,000)'
            WHEN lifetime_sales < 5000.00 THEN '5. High Velocity ($1,000 - $5,000)'
            ELSE '6. Core Hero Products (> $5,000)'
        END AS velocity_tier
    FROM product_lifetime_revenue
)
SELECT 
    velocity_tier,
    COUNT(product_id) AS sku_count,
    ROUND(COUNT(product_id)::NUMERIC / (SELECT COUNT(*) FROM products) * 100, 2) AS sku_share_pct,
    ROUND(SUM(lifetime_sales), 2) AS tier_total_sales,
    ROUND(SUM(lifetime_sales) / (SELECT SUM(lifetime_sales) FROM revenue_tiers) * 100, 2) AS sales_share_pct,
    SUM(lifetime_units) AS tier_units_sold
FROM revenue_tiers
GROUP BY velocity_tier
ORDER BY velocity_tier;

-- Weekly sales trend and 4-week rolling moving average
WITH weekly_summary AS (
    SELECT 
        week_no,
        COUNT(DISTINCT basket_id) AS weekly_baskets,
        COUNT(DISTINCT household_key) AS active_households,
        SUM(quantity) AS weekly_quantity,
        SUM(sales_value) AS weekly_sales,
        SUM(retail_disc_amount) AS weekly_retail_discounts
    FROM transactions
    GROUP BY week_no
)
SELECT 
    week_no,
    weekly_baskets,
    active_households,
    ROUND(weekly_sales, 2) AS weekly_sales,
    ROUND(
        AVG(weekly_sales) OVER (ORDER BY week_no ROWS BETWEEN 3 PRECEDING AND CURRENT ROW), 2
    ) AS sales_4week_moving_avg,
    ROUND(weekly_retail_discounts, 2) AS weekly_retail_discounts,
    ROUND(
        (weekly_sales - LAG(weekly_sales) OVER (ORDER BY week_no)) / NULLIF(LAG(weekly_sales) OVER (ORDER BY week_no), 0) * 100, 1
    ) AS wow_sales_growth_pct
FROM weekly_summary
ORDER BY week_no;
