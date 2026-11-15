-- Household summary metrics and purchase cadence
SELECT 
    b.household_key,
    COUNT(b.basket_id) AS total_baskets,
    SUM(b.basket_sales) AS total_sales,
    SUM(b.basket_net_spend) AS total_customer_net_spend,
    SUM(b.total_quantity) AS total_units_purchased,
    ROUND(AVG(b.basket_sales), 2) AS avg_basket_value,
    ROUND(AVG(b.line_item_count), 1) AS avg_items_per_basket,
    MIN(b.day) AS first_shopping_day,
    MAX(b.day) AS last_shopping_day,
    (MAX(b.day) - MIN(b.day) + 1) AS active_span_days,
    ROUND(COUNT(b.basket_id)::NUMERIC / NULLIF((MAX(b.day) - MIN(b.day) + 1) / 7.0, 0), 2) AS visits_per_week
FROM baskets b
GROUP BY b.household_key
ORDER BY total_sales DESC;

-- Pareto 80/20 revenue contribution by spend decile
WITH customer_totals AS (
    SELECT 
        household_key,
        SUM(basket_sales) AS total_spend,
        COUNT(basket_id) AS trip_count
    FROM baskets
    GROUP BY household_key
),
ranked_customers AS (
    SELECT 
        household_key,
        total_spend,
        trip_count,
        NTILE(10) OVER (ORDER BY total_spend DESC) AS spend_decile,
        ROW_NUMBER() OVER (ORDER BY total_spend DESC) AS customer_rank,
        COUNT(*) OVER () AS total_households,
        SUM(total_spend) OVER (ORDER BY total_spend DESC ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS cumulative_spend,
        SUM(total_spend) OVER () AS overall_spend
    FROM customer_totals
)
SELECT 
    spend_decile,
    COUNT(household_key) AS households_in_decile,
    ROUND(MIN(total_spend), 2) AS min_household_spend,
    ROUND(MAX(total_spend), 2) AS max_household_spend,
    ROUND(SUM(total_spend), 2) AS decile_total_spend,
    ROUND(AVG(total_spend), 2) AS decile_avg_spend,
    ROUND((SUM(total_spend) / MAX(overall_spend) * 100), 2) AS decile_share_pct,
    ROUND((MAX(cumulative_spend) / MAX(overall_spend) * 100), 2) AS cumulative_share_pct
FROM ranked_customers
GROUP BY spend_decile
ORDER BY spend_decile;

-- RFM segmentation using quartile rankings
WITH rfm_base AS (
    SELECT 
        household_key,
        (711 - MAX(day)) AS recency_days,
        COUNT(basket_id) AS frequency_trips,
        SUM(basket_sales) AS monetary_spend,
        ROUND(AVG(basket_sales), 2) AS avg_basket_value
    FROM baskets
    GROUP BY household_key
),
rfm_scores AS (
    SELECT 
        household_key,
        recency_days,
        frequency_trips,
        monetary_spend,
        avg_basket_value,
        NTILE(4) OVER (ORDER BY recency_days DESC) AS r_score,
        NTILE(4) OVER (ORDER BY frequency_trips ASC) AS f_score,
        NTILE(4) OVER (ORDER BY monetary_spend ASC) AS m_score
    FROM rfm_base
),
rfm_segments AS (
    SELECT 
        household_key,
        recency_days,
        frequency_trips,
        monetary_spend,
        avg_basket_value,
        r_score,
        f_score,
        m_score,
        (r_score::TEXT || f_score::TEXT || m_score::TEXT) AS rfm_cell,
        CASE 
            WHEN r_score >= 3 AND f_score >= 3 AND m_score >= 3 THEN 'Champions / Core Loyal'
            WHEN r_score >= 3 AND (f_score >= 2 OR m_score >= 2) THEN 'Active / Potential Loyalists'
            WHEN r_score <= 2 AND f_score >= 3 AND m_score >= 3 THEN 'At Risk High-Value'
            WHEN r_score <= 2 AND (f_score >= 2 OR m_score >= 2) THEN 'Needs Attention / Lapsing'
            WHEN r_score >= 3 AND f_score = 1 THEN 'Recent New / Occasional'
            ELSE 'Lapsed / Hibernating'
        END AS customer_segment
    FROM rfm_scores
)
SELECT 
    customer_segment,
    COUNT(household_key) AS household_count,
    ROUND(COUNT(household_key)::NUMERIC / (SELECT COUNT(*) FROM rfm_segments) * 100, 1) AS household_pct,
    ROUND(SUM(monetary_spend), 2) AS segment_revenue,
    ROUND(SUM(monetary_spend) / (SELECT SUM(monetary_spend) FROM rfm_segments) * 100, 1) AS revenue_share_pct,
    ROUND(AVG(monetary_spend), 2) AS avg_spend_per_hh,
    ROUND(AVG(frequency_trips), 1) AS avg_trips_per_hh,
    ROUND(AVG(recency_days), 1) AS avg_recency_days,
    ROUND(AVG(avg_basket_value), 2) AS avg_basket_value
FROM rfm_segments
GROUP BY customer_segment
ORDER BY segment_revenue DESC;

-- Inter-purchase interval in days between consecutive trips
WITH visit_intervals AS (
    SELECT 
        household_key,
        basket_id,
        day,
        LAG(day) OVER (PARTITION BY household_key ORDER BY day) AS prev_visit_day,
        (day - LAG(day) OVER (PARTITION BY household_key ORDER BY day)) AS days_between_visits
    FROM baskets
)
SELECT 
    household_key,
    COUNT(basket_id) AS total_visits,
    ROUND(AVG(days_between_visits), 1) AS avg_intervisit_days,
    MIN(days_between_visits) AS min_gap_days,
    MAX(days_between_visits) AS max_gap_days,
    ROUND(STDDEV(days_between_visits), 1) AS cadence_consistency_stddev
FROM visit_intervals
WHERE prev_visit_day IS NOT NULL
GROUP BY household_key
HAVING COUNT(basket_id) >= 10
ORDER BY total_visits DESC
LIMIT 20;

-- Demographic comparisons for profiled households
SELECT 
    COALESCE(d.classification_3, 'Unprofiled') AS income_tier,
    COALESCE(d.homeowner_desc, 'Unprofiled') AS homeowner_status,
    COUNT(DISTINCT b.household_key) AS profiled_households,
    COUNT(b.basket_id) AS total_baskets,
    ROUND(SUM(b.basket_sales), 2) AS total_sales,
    ROUND(AVG(b.basket_sales), 2) AS avg_spend_per_basket,
    ROUND(SUM(b.basket_sales) / COUNT(DISTINCT b.household_key), 2) AS avg_sales_per_household,
    ROUND(COUNT(b.basket_id)::NUMERIC / COUNT(DISTINCT b.household_key), 1) AS avg_baskets_per_household
FROM baskets b
LEFT JOIN demographics d ON b.household_key = d.household_key
GROUP BY d.classification_3, d.homeowner_desc
ORDER BY total_sales DESC;

-- Inactive high-value households for churn prevention
SELECT 
    b.household_key,
    ROUND(SUM(b.basket_sales), 2) AS lifetime_spend,
    COUNT(b.basket_id) AS total_visits,
    MAX(b.day) AS last_shopping_day,
    (711 - MAX(b.day)) AS days_inactive,
    ROUND(AVG(b.basket_sales), 2) AS historical_avg_basket,
    d.classification_1 AS age_group,
    d.classification_3 AS income_tier,
    d.homeowner_desc
FROM baskets b
LEFT JOIN demographics d ON b.household_key = d.household_key
GROUP BY b.household_key, d.classification_1, d.classification_3, d.homeowner_desc
HAVING SUM(b.basket_sales) >= 4000.00 AND (711 - MAX(b.day)) >= 45
ORDER BY lifetime_spend DESC;
