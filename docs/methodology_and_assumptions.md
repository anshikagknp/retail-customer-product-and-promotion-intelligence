# Methodology and Analytical Assumptions

**Project**: Retail Customer, Product & Promotion Intelligence  
**Dataset**: dunnhumby – The Complete Journey  

This document outlines the analytical methodology, statistical formulas, business rules, and technical assumptions governing the project.

---

## 1. Data Cleaning & Transformation Methodology

### 1.1 Grain Preservation & Transaction Integrity
- **Raw Transaction Grain**: 2,595,732 product line items within shopping baskets.
- **Rule**: Per retail data governance standards, raw transactional records were **never deleted or dropped**.
- **Zero Quantity Audit**: Exactly 14,466 records exhibit `QUANTITY == 0` (with 14,399 having `SALES_VALUE == 0` and 67 having minor positive sales). In retail point-of-sale (POS) systems, these represent zero-dollar price adjustment lines, warranty lines, or register balancing entries. Rather than silently removing them, they are explicitly flagged with `IS_ZERO_QUANTITY` and `IS_ZERO_SALES` to preserve complete audit reconciliation.

### 1.2 Discount Representation & Financial Formulas
In the dunnhumby schema, all discount variables are recorded as negative numbers (representing deductions from shelf price):
- `RETAIL_DISC`: Loyalty card savings (Retailer funded).
- `COUPON_DISC`: Manufacturer coupon deductions (Vendor reimbursed).
- `COUPON_MATCH_DISC`: Retailer match of vendor coupon (Retailer funded).

**Derived Financial Formulas**:
$$\text{Total Discounts Applied} = \text{RETAIL\_DISC} + \text{COUPON\_DISC} + \text{COUPON\_MATCH\_DISC} \quad (\le 0)$$
$$\text{Promotional Discount Dollars Saved} = - (\text{Total Discounts Applied}) \quad (\ge 0)$$
$$\text{Retailer Sales Value} = \text{SALES\_VALUE}$$
$$\text{Customer Out-of-Pocket Net Spend} = \text{SALES\_VALUE} + \text{COUPON\_DISC}$$
$$\text{Pre-Discount Shelf Price Estimate} = \frac{\text{SALES\_VALUE} - \text{RETAIL\_DISC} - \text{COUPON\_MATCH\_DISC}}{\text{QUANTITY}} \quad (\text{when } \text{QUANTITY} > 0)$$

### 1.3 Deduplication
- `coupon.csv` contained 5,164 exact duplicate rows on the composite key `(COUPON_UPC, PRODUCT_ID, CAMPAIGN)`. These were deduplicated, bringing the clean coupon catalog to 119,384 distinct mapping rows across 1,135 coupons.

---

## 2. Customer Segmentation Methodology: Explainable RFM

To deliver explainable, business-friendly customer segmentation without opaque black-box machine learning (e.g. k-means clustering), we implement a classic **Recency, Frequency, Monetary (RFM)** quartile ranking framework.

### 2.1 Metric Definitions
- **Recency ($R$)**: Days elapsed from the household's last observed purchase day to the end of the observation window (Day 711):
  $$\text{Recency} = 711 - \max(\text{DAY}_i)$$
  Scored into quartiles 1–4, where **4 is most recent** (lowest elapsed days) and 1 is least recent.
- **Frequency ($F$)**: Total distinct shopping occasions (baskets) over the 2-year period:
  $$\text{Frequency} = \text{Count}(\text{BASKET\_ID}_i)$$
  Scored into quartiles 1–4, where **4 is highest frequency** and 1 is lowest frequency.
- **Monetary ($M$)**: Total dollar sales value collected from the household over 2 years:
  $$\text{Monetary} = \sum \text{SALES\_VALUE}_i$$
  Scored into quartiles 1–4, where **4 is highest spend** and 1 is lowest spend.

### 2.2 Segment Assignment Logic

| Customer Segment | Criteria | Business Description |
|---|---|---|
| **Champions / Core Loyal** | $R \ge 3 \land F \ge 3 \land M \ge 3$ | Top-tier shoppers; frequent, recent, and highest spenders. Core revenue drivers. |
| **Active / Potential Loyalists** | $R \ge 3 \land (F \ge 2 \lor M \ge 2)$ | Recent shoppers with moderate frequency or basket size; candidates for loyalty trade-up. |
| **At Risk High-Value** | $R \le 2 \land F \ge 3 \land M \ge 3$ | High lifetime spenders who have become inactive recently. High churn risk. |
| **Needs Attention / Lapsing** | $R \le 2 \land (F \ge 2 \lor M \ge 2)$ | Moderate spenders slipping in visit recency. Candidates for reactivation. |
| **Recent Occasional** | $R \ge 3 \land F = 1$ | Shopped recently, but very low frequency. Potential trialists. |
| **Lapsed / Hibernating** | $R \le 2 \land F = 1 \land M = 1$ | Lowest engagement, haven't shopped in months, low historical spend. |

---

## 3. Product & Sales Analytics Methodology

### 3.1 Department Contribution Metrics
- **Sales Share (%)**: $\frac{\text{Department Sales}}{\text{Total Retail Sales}} \times 100$
- **Basket Penetration (%)**: $\frac{\text{Baskets Containing Department SKUs}}{\text{Total Baskets (276,484)}} \times 100$
- **Private Label Share (%)**: $\frac{\text{Private Label Sales in Department}}{\text{Department Sales}} \times 100$

### 3.2 Time Series Smoothing (Weekly Moving Average)
Weekly sales were calculated for Weeks 1 through 102. To distinguish fundamental underlying sales momentum from short-term weekly noise, a **4-week rolling simple moving average (SMA)** was computed:
$$\text{SMA}_w = \frac{1}{4} \sum_{i=0}^{3} \text{Sales}_{w - i}$$

---

## 4. Analytical Assumptions & Boundaries

1. **Continuous Time Representation**: `DAY` (1 to 711) and `WEEK_NO` (1 to 102) represent relative sequential time steps over approximately 24 months. They do not map to exact calendar dates (e.g. October 14, 2023), but seasonal peaks around Weeks 50 and 100 reflect year-end holiday grocery behavior.
2. **Observational Demographic Sample**: Demographics are available for 801 out of 2,500 households (32.0%). These 801 households account for 55.8% of total revenue. Analysis on demographics is conducted strictly on this profiled subset; no synthetic data imputation is applied to the 1,699 unprofiled households.
3. **Absence of `causal_data.csv`**: As requested, `causal_data.csv` (circular feature ads and front-of-store display placements) is excluded. Consequently, promotional analysis focuses on observed redemption rates and shopper profiles, without attempting causal econometric modeling.
4. **Gasoline Volume Conventions**: Gasoline products (`GASOLINE-REG UNLEADED`) record quantities in fractional fuel pump units (e.g. thousandths of gallons or cents), resulting in extremely high quantity counts that must not be conflated with standard packaged grocery unit counts.

