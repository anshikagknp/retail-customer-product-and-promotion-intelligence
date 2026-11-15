# Data Dictionary

**Project**: Retail Customer, Product & Promotion Intelligence  
**Source**: dunnhumby – The Complete Journey  

This document provides a comprehensive technical and business data dictionary covering all raw, cleaned, and derived analytical tables in the project.

---

## 1. Cleaned Transaction Table (`cleaned_transactions.csv` / `.parquet`)
- **Source**: `data/raw/transaction_data.csv`
- **Grain**: Product line item within a purchase basket (1 row per scanned product line).
- **Total Records**: 2,595,732 rows.

| Column Name | Data Type | Nullable | Description & Business Rules |
|---|---|---|---|
| `household_key` | `BIGINT` | No | Unique identifier for each household (2,500 distinct households). |
| `BASKET_ID` | `BIGINT` | No | Unique identifier for a purchase occasion / shopping trip (276,484 distinct baskets). |
| `DAY` | `INT` | No | Relative index day of transaction (Range: 1 to 711). Day 1 is first day of observation. |
| `PRODUCT_ID` | `BIGINT` | No | Unique identifier for each product item (92,339 active products). |
| `QUANTITY` | `INT` | No | Number of product units purchased. (Note: Gasoline volume recorded in pump/fractional units). |
| `SALES_VALUE` | `FLOAT` | No | Dollar amount received by retailer for the item, net of loyalty and coupon match. |
| `STORE_ID` | `BIGINT` | No | Unique identifier for store location where transaction took place. |
| `RETAIL_DISC` | `FLOAT` | No | Discount amount applied due to retailer loyalty card program (Recorded as negative or zero). |
| `TRANS_TIME` | `INT` | No | Time of day when transaction occurred in 24-hour military format (e.g. 1430 = 2:30 PM). |
| `WEEK_NO` | `INT` | No | Relative week index of transaction (Range: 1 to 102). |
| `COUPON_DISC` | `FLOAT` | No | Discount applied due to manufacturer coupon (Recorded as negative or zero). |
| `COUPON_MATCH_DISC` | `FLOAT` | No | Discount applied due to retailer match of manufacturer coupon (Recorded as negative or zero). |
| `TOTAL_DISC` | `FLOAT` | No | Derived sum of all discount components: `RETAIL_DISC + COUPON_DISC + COUPON_MATCH_DISC`. |
| `DISCOUNT_AMOUNT` | `FLOAT` | No | Derived positive magnitude of all discounts: `-TOTAL_DISC`. |
| `RETAIL_DISC_AMOUNT` | `FLOAT` | No | Derived positive loyalty discount dollars: `-RETAIL_DISC`. |
| `COUPON_DISC_AMOUNT` | `FLOAT` | No | Derived positive manufacturer coupon discount dollars: `-COUPON_DISC`. |
| `COUPON_MATCH_AMOUNT` | `FLOAT` | No | Derived positive retailer coupon match dollars: `-COUPON_MATCH_DISC`. |
| `NET_CUSTOMER_SPEND` | `FLOAT` | No | Actual customer out-of-pocket spend: `SALES_VALUE + COUPON_DISC`. |
| `UNIT_SHELF_PRICE` | `FLOAT` | Yes | Estimated pre-discount shelf price per unit: `(SALES_VALUE - RETAIL_DISC - COUPON_MATCH_DISC) / QUANTITY`. |
| `UNIT_REALIZED_PRICE`| `FLOAT` | Yes | Realized price per unit collected by retailer: `SALES_VALUE / QUANTITY`. |
| `IS_ZERO_QUANTITY` | `BOOLEAN` | No | Audit flag indicating if line item has zero quantity (14,466 rows). Preserved per retail audit protocol. |
| `IS_ZERO_SALES` | `BOOLEAN` | No | Audit flag indicating if line item has zero sales value (18,850 rows, free samples/promotions). |
| `HAS_COUPON` | `BOOLEAN` | No | True if manufacturer coupon discount applied (`COUPON_DISC < 0`). |
| `HAS_RETAIL_DISC` | `BOOLEAN` | No | True if loyalty card discount applied (`RETAIL_DISC < 0`). |

---

## 2. Cleaned Product Dimension Table (`cleaned_products.csv`)
- **Source**: `data/raw/product.csv`
- **Grain**: Product SKU (`PRODUCT_ID`).
- **Total Records**: 92,353 rows.

| Column Name | Data Type | Nullable | Description & Business Rules |
|---|---|---|---|
| `PRODUCT_ID` | `BIGINT` | No | Primary Key uniquely identifying the product SKU. |
| `MANUFACTURER` | `BIGINT` | No | Anonymized manufacturer / supplier code. |
| `DEPARTMENT` | `VARCHAR` | No | Top-level merchandising division (e.g. `GROCERY`, `DRUG GM`, `PRODUCE`, `MEAT`). Whitespace trimmed. |
| `BRAND` | `VARCHAR` | No | Brand classification: `National` (vendor brand) or `Private` (retailer store brand). |
| `COMMODITY_DESC` | `VARCHAR` | No | Mid-level category group (e.g. `SOFT DRINKS`, `FLUID MILK PRODUCTS`, `BEEF`). |
| `SUB_COMMODITY_DESC`| `VARCHAR` | No | Lowest-level subcategory classification (e.g. `SFT DRNK SGL SRV BTL PER (EXC`, `GASOLINE-REG UNLEADED`). |
| `CURR_SIZE_OF_PRODUCT`| `VARCHAR` | No | Package size indicator (e.g. `22 LB`, `12 OZ`). Blanks standardized to `UNKNOWN`. |

---

## 3. Cleaned Demographics Dimension Table (`cleaned_demographics.csv`)
- **Source**: `data/raw/hh_demographic.csv`
- **Grain**: Household (`household_key`).
- **Total Records**: 801 rows (subset of 2,500 total households).

| Column Name | Data Type | Nullable | Description & Business Rules |
|---|---|---|---|
| `household_key` | `BIGINT` | No | Primary Key uniquely identifying the household. |
| `classification_1` | `VARCHAR` | No | Age bracket of primary shopper (`Age Group 1` to `Age Group 6`). Values preserve logical ordinality. |
| `classification_2` | `VARCHAR` | No | Marital / household composition category (`X`, `Y`, `Z`). |
| `classification_3` | `VARCHAR` | No | Estimated household income tier (`Level 1` to `Level 12`). Higher levels represent higher income brackets. |
| `HOMEOWNER_DESC` | `VARCHAR` | No | Homeownership status (`Homeowner`, `Renter`, `Probable Owner`, `Probable Renter`, `Unknown`). |
| `classification_5` | `VARCHAR` | No | Demographic cluster grouping (`Group 1` to `Group 6`). |
| `classification_4` | `VARCHAR` | No | Household size (`1`, `2`, `3`, `4`, `5+`). |
| `KID_CATEGORY_DESC` | `VARCHAR` | No | Children in household (`None/Unknown`, `1`, `2`, `3+`). |

---

## 4. Cleaned Campaign Dimension Table (`cleaned_campaigns.csv`)
- **Source**: `data/raw/campaign_desc.csv`
- **Grain**: Campaign ID (`CAMPAIGN`).
- **Total Records**: 30 rows.

| Column Name | Data Type | Nullable | Description & Business Rules |
|---|---|---|---|
| `CAMPAIGN` | `INT` | No | Primary Key uniquely identifying the direct marketing campaign (Ranges 1 to 30). |
| `DESCRIPTION` | `VARCHAR` | No | Strategic campaign classification (`TypeA`, `TypeB`, `TypeC`). |
| `START_DAY` | `INT` | No | Campaign launch index day (Range: 224 to 659). |
| `END_DAY` | `INT` | No | Campaign expiration index day (Range: 264 to 719). |
| `DURATION_DAYS` | `INT` | No | Derived campaign active lifespan: `END_DAY - START_DAY`. |

---

## 5. Cleaned Campaign Household Targeting Table (`cleaned_campaign_households.csv`)
- **Source**: `data/raw/campaign_table.csv`
- **Grain**: `(CAMPAIGN, household_key)`.
- **Total Records**: 7,208 rows.

| Column Name | Data Type | Nullable | Description & Business Rules |
|---|---|---|---|
| `CAMPAIGN` | `INT` | No | Campaign identifier matching `cleaned_campaigns.csv`. |
| `household_key` | `BIGINT` | No | Household identifier receiving the campaign mailer (1,584 distinct households). |
| `DESCRIPTION` | `VARCHAR` | No | Campaign type descriptor (`TypeA`, `TypeB`, `TypeC`). |

---

## 6. Cleaned Coupon Catalog Table (`cleaned_coupons.csv`)
- **Source**: `data/raw/coupon.csv`
- **Grain**: `(COUPON_UPC, PRODUCT_ID, CAMPAIGN)`.
- **Total Records**: 119,384 rows (deduplicated from 124,548 raw rows).

| Column Name | Data Type | Nullable | Description & Business Rules |
|---|---|---|---|
| `COUPON_UPC` | `BIGINT` | No | Universal Product Code uniquely identifying the coupon offer. |
| `PRODUCT_ID` | `BIGINT` | No | Product SKU on which the coupon offer is redeemable. |
| `CAMPAIGN` | `INT` | No | Campaign identifier with which the coupon was issued. |

---

## 7. Cleaned Coupon Redemptions Table (`cleaned_coupon_redemptions.csv`)
- **Source**: `data/raw/coupon_redempt.csv`
- **Grain**: Redemption instance `(household_key, DAY, COUPON_UPC, CAMPAIGN)`.
- **Total Records**: 2,318 rows.

| Column Name | Data Type | Nullable | Description & Business Rules |
|---|---|---|---|
| `household_key` | `BIGINT` | No | Household that redeemed the coupon (434 distinct households). |
| `DAY` | `INT` | No | Day index when redemption took place (Range: 407 to 704). |
| `COUPON_UPC` | `BIGINT` | No | Coupon UPC redeemed (556 distinct coupons). |
| `CAMPAIGN` | `INT` | No | Campaign associated with the redeemed coupon. |

---

## 8. Basket Summary Table (`baskets.csv`)
- **Source**: Aggregated from `cleaned_transactions.csv`.
- **Grain**: Purchase occasion / shopping basket (`BASKET_ID`).
- **Total Records**: 276,484 rows.

| Column Name | Data Type | Nullable | Description |
|---|---|---|---|
| `BASKET_ID` | `BIGINT` | No | Primary Key uniquely identifying the shopping trip. |
| `household_key` | `BIGINT` | No | Household that executed the trip. |
| `DAY` | `INT` | No | Day index of shopping trip. |
| `WEEK_NO` | `INT` | No | Week index of shopping trip. |
| `STORE_ID` | `BIGINT` | No | Store location where trip occurred. |
| `TRANS_TIME` | `INT` | No | Time of day of transaction checkout. |
| `line_item_count`| `INT` | No | Number of scanned product lines in the basket. |
| `distinct_product_count` | `INT` | No | Count of unique product SKUs in the basket. |
| `total_quantity`| `INT` | No | Total unit volume of items purchased. |
| `basket_sales` | `FLOAT` | No | Total dollar amount received by retailer for the basket. |
| `basket_net_spend` | `FLOAT` | No | Total out-of-pocket customer spend for the basket. |
| `retail_disc_amount` | `FLOAT` | No | Dollar savings provided by loyalty card program. |
| `coupon_disc_amount` | `FLOAT` | No | Dollar savings provided by manufacturer coupons. |
| `coupon_match_amount`| `FLOAT` | No | Dollar savings provided by retailer coupon match. |
| `total_discount_amount`| `FLOAT` | No | Sum of all promotional savings on the basket. |
| `has_coupon_used`| `BOOLEAN` | No | Flag indicating if manufacturer coupon was used. |
| `has_retail_disc_used`| `BOOLEAN` | No | Flag indicating if loyalty discount was applied. |
| `avg_line_item_value`| `FLOAT` | No | Average sales value per scanned line: `basket_sales / line_item_count`. |
| `discount_rate_pct` | `FLOAT` | No | Discount depth %: `total_discount_amount / (basket_sales + total_discount_amount) * 100`. |

---

## 9. Household Summary Table (`household_summary.csv`)
- **Source**: Aggregated from `baskets.csv` and joined with `cleaned_demographics.csv`.
- **Grain**: Household (`household_key`).
- **Total Records**: 2,500 rows.

| Column Name | Data Type | Nullable | Description |
|---|---|---|---|
| `household_key` | `BIGINT` | No | Primary Key uniquely identifying the household. |
| `basket_count` | `INT` | No | Total shopping trips executed over 102 weeks (Mean: 110.6, Median: 87). |
| `total_sales` | `FLOAT` | No | Total 2-year spend collected by retailer (Mean: $3,223, Median: $2,510). |
| `total_net_spend` | `FLOAT` | No | Total out-of-pocket spend by customer. |
| `total_quantity` | `INT` | No | Total product units purchased across all trips. |
| `total_discounts` | `FLOAT` | No | Total promotional dollars saved by household. |
| `retail_discounts`| `FLOAT` | No | Total loyalty card dollars saved by household. |
| `coupon_discounts`| `FLOAT` | No | Total coupon dollars redeemed by household. |
| `baskets_with_coupons`| `INT` | No | Number of shopping trips where coupons were redeemed. |
| `first_purchase_day` | `INT` | No | First observed shopping day. |
| `last_purchase_day` | `INT` | No | Most recent observed shopping day. |
| `active_weeks` | `INT` | No | Count of distinct weeks with at least one shopping trip. |
| `visited_stores` | `INT` | No | Count of distinct store locations shopped. |
| `recency_days` | `INT` | No | Days elapsed between Day 711 and household's last purchase day. |
| `active_span_days` | `INT` | No | Days between first and last purchase: `last_day - first_day + 1`. |
| `avg_basket_value` | `FLOAT` | No | Average spend per trip: `total_sales / basket_count`. |
| `avg_basket_units` | `FLOAT` | No | Average units per trip: `total_quantity / basket_count`. |
| `coupon_trip_ratio`| `FLOAT` | No | Share of trips with coupons: `baskets_with_coupons / basket_count`. |
| `has_demographics` | `BOOLEAN` | No | True if household has profile in `cleaned_demographics.csv` (801 True, 1,699 False). |
| Demographic Columns | `VARCHAR` | No | Profiled attributes (`classification_1` to `5`, `HOMEOWNER_DESC`, `KID_CATEGORY_DESC`), filled with `'Unprofiled'` where absent. |

