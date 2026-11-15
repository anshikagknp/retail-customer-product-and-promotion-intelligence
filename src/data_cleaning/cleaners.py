"""
Data cleaning and preparation functions for dunnhumby retail datasets.
Preserves original raw data integrity while creating analysis-ready tables.
"""

import pandas as pd
import numpy as np


def clean_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans raw transaction data, standardizes types, and derives analytical metrics.
    Preserves the original transaction-level grain (2,595,732 rows).
    """
    clean = df.copy()

    # Ensure correct numeric types
    int_cols = ["household_key", "BASKET_ID", "DAY", "PRODUCT_ID", "QUANTITY", "STORE_ID", "TRANS_TIME", "WEEK_NO"]
    float_cols = ["SALES_VALUE", "RETAIL_DISC", "COUPON_DISC", "COUPON_MATCH_DISC"]

    for col in int_cols:
        clean[col] = clean[col].astype(np.int64)
    for col in float_cols:
        clean[col] = clean[col].astype(np.float64)

    # Derived analytical columns
    # In dunnhumby data, discounts are recorded as negative values or 0.
    # Total discounts applied:
    clean["TOTAL_DISC"] = clean["RETAIL_DISC"] + clean["COUPON_DISC"] + clean["COUPON_MATCH_DISC"]
    
    # Positive discount amount for intuitive reporting
    clean["DISCOUNT_AMOUNT"] = -clean["TOTAL_DISC"]
    clean["RETAIL_DISC_AMOUNT"] = -clean["RETAIL_DISC"]
    clean["COUPON_DISC_AMOUNT"] = -clean["COUPON_DISC"]
    clean["COUPON_MATCH_AMOUNT"] = -clean["COUPON_MATCH_DISC"]

    # Net customer out-of-pocket spend:
    # Retailer receives SALES_VALUE, but customer paid SALES_VALUE + COUPON_DISC (since coupon_disc is negative)
    clean["NET_CUSTOMER_SPEND"] = (clean["SALES_VALUE"] + clean["COUPON_DISC"]).round(2)

    # Shelf price per unit (exclusive of loyalty and coupon discounts) when QUANTITY > 0
    # Formula from dunnhumby user guide: (sales_value - retail_disc - coupon_match_disc) / quantity
    mask_pos_qty = clean["QUANTITY"] > 0
    clean["UNIT_SHELF_PRICE"] = np.nan
    clean.loc[mask_pos_qty, "UNIT_SHELF_PRICE"] = (
        (clean.loc[mask_pos_qty, "SALES_VALUE"] - clean.loc[mask_pos_qty, "RETAIL_DISC"] - clean.loc[mask_pos_qty, "COUPON_MATCH_DISC"])
        / clean.loc[mask_pos_qty, "QUANTITY"]
    ).round(4)

    # Unit price realized by retailer: SALES_VALUE / QUANTITY
    clean["UNIT_REALIZED_PRICE"] = np.nan
    clean.loc[mask_pos_qty, "UNIT_REALIZED_PRICE"] = (
        clean.loc[mask_pos_qty, "SALES_VALUE"] / clean.loc[mask_pos_qty, "QUANTITY"]
    ).round(4)

    # Quality flags (without dropping rows)
    clean["IS_ZERO_QUANTITY"] = clean["QUANTITY"] == 0
    clean["IS_ZERO_SALES"] = clean["SALES_VALUE"] == 0
    clean["HAS_COUPON"] = clean["COUPON_DISC"] < 0
    clean["HAS_RETAIL_DISC"] = clean["RETAIL_DISC"] < 0

    return clean


def clean_products(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans raw product master data, trims whitespace, and standardizes blanks.
    """
    clean = df.copy()
    clean["PRODUCT_ID"] = clean["PRODUCT_ID"].astype(np.int64)
    clean["MANUFACTURER"] = clean["MANUFACTURER"].astype(np.int64)

    str_cols = ["DEPARTMENT", "BRAND", "COMMODITY_DESC", "SUB_COMMODITY_DESC", "CURR_SIZE_OF_PRODUCT"]
    for col in str_cols:
        clean[col] = clean[col].astype(str).str.strip()
        clean[col] = clean[col].replace("", "UNKNOWN")

    return clean


def clean_demographics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans household demographics, preserving ordinal categories and handling whitespace.
    """
    clean = df.copy()
    clean["household_key"] = clean["household_key"].astype(np.int64)

    str_cols = [c for c in clean.columns if c != "household_key"]
    for col in str_cols:
        clean[col] = clean[col].astype(str).str.strip()

    # Sort by household_key for deterministic ordering
    clean = clean.sort_values("household_key").reset_index(drop=True)
    return clean


def clean_campaigns(df_desc: pd.DataFrame, df_table: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Cleans campaign metadata and household participation tables.
    """
    desc = df_desc.copy()
    desc["CAMPAIGN"] = desc["CAMPAIGN"].astype(np.int64)
    desc["DESCRIPTION"] = desc["DESCRIPTION"].astype(str).str.strip()
    desc["START_DAY"] = desc["START_DAY"].astype(np.int64)
    desc["END_DAY"] = desc["END_DAY"].astype(np.int64)
    desc["DURATION_DAYS"] = desc["END_DAY"] - desc["START_DAY"]
    desc = desc.sort_values("CAMPAIGN").reset_index(drop=True)

    table = df_table.copy()
    table["household_key"] = table["household_key"].astype(np.int64)
    table["CAMPAIGN"] = table["CAMPAIGN"].astype(np.int64)
    table["DESCRIPTION"] = table["DESCRIPTION"].astype(str).str.strip()
    table = table.drop_duplicates().sort_values(["CAMPAIGN", "household_key"]).reset_index(drop=True)

    return desc, table


def clean_coupons(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans coupon mappings and removes 5,164 exact duplicate rows.
    """
    clean = df.copy()
    clean["COUPON_UPC"] = clean["COUPON_UPC"].astype(np.int64)
    clean["PRODUCT_ID"] = clean["PRODUCT_ID"].astype(np.int64)
    clean["CAMPAIGN"] = clean["CAMPAIGN"].astype(np.int64)

    # Drop duplicate coupon-product-campaign entries
    clean = clean.drop_duplicates().reset_index(drop=True)
    return clean


def clean_coupon_redemptions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans coupon redemption records.
    """
    clean = df.copy()
    clean["household_key"] = clean["household_key"].astype(np.int64)
    clean["DAY"] = clean["DAY"].astype(np.int64)
    clean["COUPON_UPC"] = clean["COUPON_UPC"].astype(np.int64)
    clean["CAMPAIGN"] = clean["CAMPAIGN"].astype(np.int64)
    clean = clean.drop_duplicates().sort_values(["DAY", "household_key"]).reset_index(drop=True)
    return clean


def build_basket_summary(df_tx: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates transaction line items into a basket-level analytical table.
    Grain: BASKET_ID (unique purchase occasion).
    """
    baskets = df_tx.groupby("BASKET_ID").agg(
        household_key=("household_key", "first"),
        DAY=("DAY", "first"),
        WEEK_NO=("WEEK_NO", "first"),
        STORE_ID=("STORE_ID", "first"),
        TRANS_TIME=("TRANS_TIME", "min"),
        line_item_count=("PRODUCT_ID", "count"),
        distinct_product_count=("PRODUCT_ID", "nunique"),
        total_quantity=("QUANTITY", "sum"),
        basket_sales=("SALES_VALUE", "sum"),
        basket_net_spend=("NET_CUSTOMER_SPEND", "sum"),
        retail_disc_amount=("RETAIL_DISC_AMOUNT", "sum"),
        coupon_disc_amount=("COUPON_DISC_AMOUNT", "sum"),
        coupon_match_amount=("COUPON_MATCH_AMOUNT", "sum"),
        total_discount_amount=("DISCOUNT_AMOUNT", "sum"),
        has_coupon_used=("HAS_COUPON", "any"),
        has_retail_disc_used=("HAS_RETAIL_DISC", "any")
    ).reset_index()

    # Derived basket KPIs
    baskets["basket_sales"] = baskets["basket_sales"].round(2)
    baskets["basket_net_spend"] = baskets["basket_net_spend"].round(2)
    baskets["total_discount_amount"] = baskets["total_discount_amount"].round(2)
    baskets["avg_line_item_value"] = (baskets["basket_sales"] / baskets["line_item_count"]).round(2)
    baskets["discount_rate_pct"] = np.where(
        (baskets["basket_sales"] + baskets["total_discount_amount"]) > 0,
        (baskets["total_discount_amount"] / (baskets["basket_sales"] + baskets["total_discount_amount"]) * 100).round(1),
        0.0
    )

    return baskets


def build_household_summary(df_tx: pd.DataFrame, df_baskets: pd.DataFrame, df_demo: pd.DataFrame = None) -> pd.DataFrame:
    """
    Aggregates purchasing behavior to household level.
    Grain: household_key (2,500 households).
    """
    max_day = df_tx["DAY"].max()

    hh = df_baskets.groupby("household_key").agg(
        basket_count=("BASKET_ID", "count"),
        total_sales=("basket_sales", "sum"),
        total_net_spend=("basket_net_spend", "sum"),
        total_quantity=("total_quantity", "sum"),
        total_discounts=("total_discount_amount", "sum"),
        retail_discounts=("retail_disc_amount", "sum"),
        coupon_discounts=("coupon_disc_amount", "sum"),
        baskets_with_coupons=("has_coupon_used", "sum"),
        first_purchase_day=("DAY", "min"),
        last_purchase_day=("DAY", "max"),
        active_weeks=("WEEK_NO", "nunique"),
        visited_stores=("STORE_ID", "nunique")
    ).reset_index()

    hh["total_sales"] = hh["total_sales"].round(2)
    hh["total_net_spend"] = hh["total_net_spend"].round(2)
    hh["total_discounts"] = hh["total_discounts"].round(2)
    hh["recency_days"] = max_day - hh["last_purchase_day"]
    hh["active_span_days"] = (hh["last_purchase_day"] - hh["first_purchase_day"] + 1)
    hh["avg_basket_value"] = (hh["total_sales"] / hh["basket_count"]).round(2)
    hh["avg_basket_units"] = (hh["total_quantity"] / hh["basket_count"]).round(2)
    hh["coupon_trip_ratio"] = (hh["baskets_with_coupons"] / hh["basket_count"]).round(3)

    # Attach demographics if provided
    if df_demo is not None:
        hh = hh.merge(df_demo, on="household_key", how="left")
        demo_cols = [c for c in df_demo.columns if c != "household_key"]
        for col in demo_cols:
            hh[col] = hh[col].fillna("Unprofiled")
        hh["has_demographics"] = hh["household_key"].isin(df_demo["household_key"])
    else:
        hh["has_demographics"] = False

    return hh

