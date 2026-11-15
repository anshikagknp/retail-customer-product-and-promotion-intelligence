# Analytical Limitations and Data Constraints

**Project**: Retail Customer, Product & Promotion Intelligence  
**Dataset**: dunnhumby – The Complete Journey  

This document outlines the analytical boundaries, data constraints, and observational limitations inherent in the dataset.

---

## 1. Lack of Calendar Dates (Index Time Only)
- **Constraint**: Transaction timing is indexed by sequential `DAY` (1 to 711) and `WEEK_NO` (1 to 102), without calendar timestamps (day of week, month, year, or statutory holidays).
- **Analytical Impact**: 
  - Day-of-week shopping patterns (e.g., Saturday grocery rush vs. Tuesday lull) cannot be determined directly without external anchoring.
  - While seasonal annual peaks are evident in Weeks 48–52 and 99–102 (holiday pantry stocking), specific holiday promotions (e.g. Thanksgiving vs. Christmas vs. Super Bowl) cannot be disambiguated with certainty.

---

## 2. Revenue vs. Margin / Profit
- **Constraint**: `SALES_VALUE` represents gross dollars received by the retailer. The dataset does not provide **Cost of Goods Sold (COGS)** or product margin percentages.
- **Analytical Impact**:
  - The highest revenue products (e.g., fluid milk, gasoline, soft drinks) are not necessarily the highest profit contributors. In grocery retail, staples often serve as low-margin "loss leaders" to drive foot traffic.
  - Financial insights in this project are strictly framed around **revenue, volume, basket value, and discount depth**, avoiding unsupported profit claims.

---

## 3. Frequent Shopper Selection Bias
- **Constraint**: As stated in the official dunnhumby User Guide, the 2,500 panel households were deliberately selected from a cohort of **frequent shoppers**.
- **Analytical Impact**:
  - The sample exhibits higher overall shopping trip frequency (averaging 110 trips over 2 years, or ~1.1 trips/week) than the broader US consumer population.
  - Findings regarding customer retention and loyalty apply specifically to engaged retail panel households, not casual or one-time drive-by shoppers.

---

## 4. Incomplete Demographic Coverage
- **Constraint**: Demographic profiling is available for **801 out of 2,500 households (32.0%)**.
- **Analytical Impact**:
  - While these 801 households generate 55.8% of total revenue, non-profiled households (68.0%) may differ systematically in age, income, or family composition.
  - All demographic findings are transparently reported as representing the *profiled subpopulation*, rather than imputed across the entire 2,500 household universe.

---

## 5. Promotional Correlation vs. True Causality
- **Constraint**: `causal_data.csv` (circular feature ads, in-store end-caps, shelf-talkers) was excluded from the project per user instructions.
- **Analytical Impact**:
  - Coupon-redeeming households spend 115% more ($5,785 vs $2,684) and shop twice as often (194 trips vs 93 trips) compared to non-redeemers.
  - However, **correlation must not be mistaken for causation**: highly engaged shoppers who visit the store twice a week naturally encounter more coupons and have more opportunities to redeem them. Without randomized control groups (A/B testing) or in-store display logs, claiming that coupons *caused* the higher spend would be methodologically unsound.

---

## 6. Type A Campaign Personalized Pool Caveat
- **Constraint**: In Type A campaigns, customers received a personalized selection of 16 coupons chosen from the overall campaign coupon pool based on their historical purchasing behavior. The database records the total coupon pool for the campaign, but does not identify the specific 16 coupons received by each individual household.
- **Analytical Impact**:
  - Coupon redemption rates for Type A campaigns can be measured at the household and campaign level, but coupon-level distribution denominators (exact count of coupons delivered per household) are unavailable for Type A offers.

