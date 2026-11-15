-- Promotional discount composition across all shopping baskets
SELECT 
    COUNT(basket_id) AS total_baskets,
    ROUND(SUM(basket_sales), 2) AS total_sales_value,
    ROUND(SUM(basket_net_spend), 2) AS customer_net_spend,
    ROUND(SUM(retail_disc_amount), 2) AS loyalty_card_discounts,
    ROUND(SUM(coupon_disc_amount), 2) AS manufacturer_coupon_discounts,
    ROUND(SUM(coupon_match_amount), 2) AS retailer_match_discounts,
    ROUND(SUM(total_discount_amount), 2) AS total_promotional_discounts,
    ROUND((SUM(retail_disc_amount) / SUM(total_discount_amount) * 100), 1) AS loyalty_share_of_discounts_pct,
    ROUND((SUM(coupon_disc_amount) / SUM(total_discount_amount) * 100), 1) AS coupon_share_of_discounts_pct,
    ROUND((SUM(total_discount_amount) / SUM(basket_sales) * 100), 2) AS discount_to_sales_ratio_pct
FROM baskets;

-- Campaign targeting, redemption count, and participation rate
WITH targeting AS (
    SELECT 
        campaign,
        COUNT(DISTINCT household_key) AS targeted_households
    FROM campaign_households
    GROUP BY campaign
),
redemptions AS (
    SELECT 
        campaign,
        COUNT(*) AS total_redemptions,
        COUNT(DISTINCT household_key) AS unique_redeeming_households,
        COUNT(DISTINCT coupon_upc) AS unique_coupons_redeemed
    FROM coupon_redemptions
    GROUP BY campaign
)
SELECT 
    c.campaign,
    c.description AS campaign_type,
    c.start_day,
    c.end_day,
    c.duration_days,
    COALESCE(t.targeted_households, 0) AS targeted_households,
    COALESCE(r.total_redemptions, 0) AS total_redemptions,
    COALESCE(r.unique_redeeming_households, 0) AS redeeming_households,
    ROUND(
        (COALESCE(r.unique_redeeming_households, 0)::NUMERIC / NULLIF(t.targeted_households, 0) * 100), 2
    ) AS household_participation_rate_pct,
    ROUND(
        (COALESCE(r.total_redemptions, 0)::NUMERIC / NULLIF(r.unique_redeeming_households, 0)), 2
    ) AS redemptions_per_active_redeemer
FROM campaigns c
LEFT JOIN targeting t ON c.campaign = t.campaign
LEFT JOIN redemptions r ON c.campaign = r.campaign
ORDER BY total_redemptions DESC;

-- Campaign performance grouped by campaign type
WITH campaign_metrics AS (
    SELECT 
        c.description AS campaign_type,
        c.campaign,
        c.duration_days,
        COUNT(DISTINCT ch.household_key) AS targeted_households,
        COUNT(cr.coupon_upc) AS total_redemptions,
        COUNT(DISTINCT cr.household_key) AS unique_redeeming_households
    FROM campaigns c
    LEFT JOIN campaign_households ch ON c.campaign = ch.campaign
    LEFT JOIN coupon_redemptions cr ON c.campaign = cr.campaign
    GROUP BY c.description, c.campaign, c.duration_days
)
SELECT 
    campaign_type,
    COUNT(campaign) AS total_campaigns,
    ROUND(AVG(duration_days), 1) AS avg_duration_days,
    SUM(targeted_households) AS total_targeting_instances,
    SUM(total_redemptions) AS total_coupon_redemptions,
    SUM(unique_redeeming_households) AS total_active_redeemers,
    ROUND(
        (SUM(unique_redeeming_households)::NUMERIC / NULLIF(SUM(targeted_households), 0) * 100), 2
    ) AS overall_household_redemption_rate_pct,
    ROUND(
        (SUM(total_redemptions)::NUMERIC / NULLIF(SUM(unique_redeeming_households), 0)), 2
    ) AS avg_redemptions_per_redeemer
FROM campaign_metrics
GROUP BY campaign_type
ORDER BY total_coupon_redemptions DESC;

-- Customer comparison: coupon redeemers versus non-redeemers
WITH redeemer_households AS (
    SELECT DISTINCT household_key FROM coupon_redemptions
),
household_kpis AS (
    SELECT 
        b.household_key,
        CASE WHEN r.household_key IS NOT NULL THEN 'Coupon Redeemer' ELSE 'Non-Redeemer' END AS customer_group,
        COUNT(b.basket_id) AS total_baskets,
        SUM(b.basket_sales) AS total_spend,
        SUM(b.total_quantity) AS total_units,
        ROUND(AVG(b.basket_sales), 2) AS avg_basket_value,
        SUM(b.retail_disc_amount) AS total_retail_discounts
    FROM baskets b
    LEFT JOIN redeemer_households r ON b.household_key = r.household_key
    GROUP BY b.household_key, r.household_key
)
SELECT 
    customer_group,
    COUNT(household_key) AS household_count,
    ROUND(COUNT(household_key)::NUMERIC / (SELECT COUNT(*) FROM household_kpis) * 100, 1) AS household_share_pct,
    ROUND(SUM(total_spend), 2) AS group_total_revenue,
    ROUND(SUM(total_spend) / (SELECT SUM(total_spend) FROM household_kpis) * 100, 1) AS revenue_share_pct,
    ROUND(AVG(total_spend), 2) AS mean_household_spend,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_spend)::NUMERIC, 2) AS median_household_spend,
    ROUND(AVG(total_baskets), 1) AS mean_shopping_trips,
    ROUND(PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY total_baskets)::NUMERIC, 1) AS median_shopping_trips,
    ROUND(AVG(avg_basket_value), 2) AS mean_basket_value,
    ROUND(AVG(total_retail_discounts), 2) AS mean_loyalty_savings_per_hh
FROM household_kpis
GROUP BY customer_group
ORDER BY group_total_revenue DESC;

-- Top 15 redeemed coupons and associated product categories
WITH coupon_primary_product AS (
    SELECT 
        c.coupon_upc,
        c.campaign,
        p.department,
        p.commodity_desc,
        ROW_NUMBER() OVER (PARTITION BY c.coupon_upc, c.campaign ORDER BY p.product_id) AS rn
    FROM coupons c
    JOIN products p ON c.product_id = p.product_id
)
SELECT 
    cr.coupon_upc,
    cr.campaign,
    cpp.department,
    cpp.commodity_desc,
    COUNT(*) AS total_redemptions,
    COUNT(DISTINCT cr.household_key) AS redeeming_households,
    MIN(cr.day) AS first_redemption_day,
    MAX(cr.day) AS last_redemption_day
FROM coupon_redemptions cr
JOIN coupon_primary_product cpp ON cr.coupon_upc = cpp.coupon_upc AND cr.campaign = cpp.campaign AND cpp.rn = 1
GROUP BY cr.coupon_upc, cr.campaign, cpp.department, cpp.commodity_desc
ORDER BY total_redemptions DESC
LIMIT 15;

-- Distribution of coupon redemptions across campaign duration intervals
WITH redemption_timeline AS (
    SELECT 
        cr.campaign,
        cr.household_key,
        cr.coupon_upc,
        cr.day AS redemption_day,
        c.start_day,
        c.end_day,
        (cr.day - c.start_day) AS days_from_campaign_start,
        ((cr.day - c.start_day) / 10 + 1) AS interval_bucket
    FROM coupon_redemptions cr
    JOIN campaigns c ON cr.campaign = c.campaign
)
SELECT 
    interval_bucket,
    ((interval_bucket - 1) * 10) || ' to ' || (interval_bucket * 10) || ' days' AS campaign_window_interval,
    COUNT(*) AS redemptions_in_interval,
    ROUND(COUNT(*)::NUMERIC / (SELECT COUNT(*) FROM redemption_timeline) * 100, 1) AS pct_of_all_redemptions
FROM redemption_timeline
GROUP BY interval_bucket
ORDER BY interval_bucket;
