import sys
from pathlib import Path
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page configuration
st.set_page_config(
    page_title="Retail Intelligence Dashboard | dunnhumby",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: #FFFFFF;
        padding: 1.1rem 1.2rem;
        border-radius: 10px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #0F172A;
        margin: 0.2rem 0;
    }
    .metric-delta {
        font-size: 0.82rem;
        color: #10B981;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# Data loading with cache
@st.cache_data(show_spinner="Loading retail data...")
def load_data():
    base_dir = Path(__file__).resolve().parent / "data" / "processed"
    
    if not (base_dir / "household_summary.csv").exists():
        st.error(f"Processed retail data not found at {base_dir}. Please ensure required files are present.")
        st.stop()
        
    hh = pd.read_csv(base_dir / "household_summary.csv")
    campaigns = pd.read_csv(base_dir / "cleaned_campaigns.csv") if (base_dir / "cleaned_campaigns.csv").exists() else pd.DataFrame()
    camp_hh = pd.read_csv(base_dir / "cleaned_campaign_households.csv") if (base_dir / "cleaned_campaign_households.csv").exists() else pd.DataFrame()
    redempt = pd.read_csv(base_dir / "cleaned_coupon_redemptions.csv") if (base_dir / "cleaned_coupon_redemptions.csv").exists() else pd.DataFrame()
    
    # Precompute RFM segments
    rfm = hh.copy()
    rfm["R_Score"] = pd.qcut(rfm["recency_days"], q=4, labels=[4, 3, 2, 1]).astype(int)
    rfm["F_Score"] = pd.qcut(rfm["basket_count"].rank(method="first"), q=4, labels=[1, 2, 3, 4]).astype(int)
    rfm["M_Score"] = pd.qcut(rfm["total_sales"].rank(method="first"), q=4, labels=[1, 2, 3, 4]).astype(int)
    
    def assign_segment(row):
        r, f, m = row["R_Score"], row["F_Score"], row["M_Score"]
        if r >= 3 and f >= 3 and m >= 3:
            return "Champions / Core Loyal"
        elif r >= 3 and (f >= 2 or m >= 2):
            return "Active / Potential Loyalists"
        elif r <= 2 and f >= 3 and m >= 3:
            return "At Risk High-Value"
        elif r <= 2 and (f >= 2 or m >= 2):
            return "Needs Attention / Lapsing"
        elif r >= 3 and f == 1:
            return "Recent New / Occasional"
        else:
            return "Lapsed / Hibernating"
            
    rfm["Customer_Segment"] = rfm.apply(assign_segment, axis=1)
    
    # Weekly aggregation
    if (base_dir / "weekly_trends.csv").exists():
        weekly = pd.read_csv(base_dir / "weekly_trends.csv")
    elif (base_dir / "baskets.csv").exists():
        baskets = pd.read_csv(base_dir / "baskets.csv")
        weekly = baskets.groupby("WEEK_NO").agg(
            total_sales=("basket_sales", "sum"),
            basket_count=("BASKET_ID", "count"),
            active_households=("household_key", "nunique"),
            retail_discounts=("retail_disc_amount", "sum")
        ).reset_index()
        weekly["sales_4wk_ma"] = weekly["total_sales"].rolling(4, min_periods=1).mean()
    else:
        weekly = pd.DataFrame()
        
    # Department summary
    if (base_dir / "department_summary.csv").exists():
        dept_agg = pd.read_csv(base_dir / "department_summary.csv")
    else:
        dept_agg = pd.DataFrame()
        
    # Brand summary
    if (base_dir / "brand_summary.csv").exists():
        brand_agg = pd.read_csv(base_dir / "brand_summary.csv")
    else:
        brand_agg = pd.DataFrame()
        
    # SKU velocity summary
    if (base_dir / "sku_velocity_summary.csv").exists():
        tier_summary = pd.read_csv(base_dir / "sku_velocity_summary.csv")
    else:
        tier_summary = pd.DataFrame()
        
    return hh, campaigns, camp_hh, redempt, rfm, weekly, dept_agg, brand_agg, tier_summary

hh_df, camp_df, camp_hh_df, redempt_df, rfm_df, weekly_df, dept_df, brand_df, tier_df = load_data()

# Sidebar
st.sidebar.image("https://img.icons8.com/fluency/96/shopping-cart.png", width=64)
st.sidebar.title("Retail Intelligence")
st.sidebar.caption("dunnhumby Complete Journey (102 Weeks)")

nav = st.sidebar.radio(
    "Navigation",
    ["📊 Executive Overview", "👥 Customer & RFM Intelligence", "🛒 Product & Assortment", "🏷️ Promotion & Campaign ROI", "⚡ SQL Query Explorer"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("**Dataset Scope**")
st.sidebar.markdown("""
- **Households**: 2,500
- **Transactions**: 2.59M lines
- **Shopping Trips**: 276.5K
- **Active SKUs**: 92,353
- **Timeline**: 102 Weeks (711 Days)
""")

# Executive overview view
if nav == "📊 Executive Overview":
    st.markdown('<div class="main-header">Retail Performance Executive Overview</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Two-year performance indicators across 2,500 households and 276,484 shopping occasions.</div>', unsafe_allow_html=True)
    
    total_sales = hh_df["total_sales"].sum()
    total_net = hh_df["total_net_spend"].sum()
    total_trips = int(hh_df["basket_count"].sum())
    total_hh = hh_df["household_key"].nunique()
    avg_basket = total_sales / total_trips
    total_retail_disc = weekly_df["retail_discounts"].sum() if not weekly_df.empty else 1450630.08
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Retail Sales</div>
            <div class="metric-value">${total_sales/1e6:.2f}M</div>
            <div class="metric-delta">Recorded Revenue</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Customer Net Spend</div>
            <div class="metric-value">${total_net/1e6:.2f}M</div>
            <div class="metric-delta">Out-of-Pocket Spend</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Shopping Trips</div>
            <div class="metric-value">{total_trips/1e3:.1f}K</div>
            <div class="metric-delta">276,484 Baskets</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Average Basket</div>
            <div class="metric-value">${avg_basket:.2f}</div>
            <div class="metric-delta">Spend per Occasion</div>
        </div>
        """, unsafe_allow_html=True)
    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Loyalty Discounts</div>
            <div class="metric-value">${total_retail_disc/1e6:.2f}M</div>
            <div class="metric-delta">18.0% of Sales Value</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Weekly revenue trend
    col_left, col_right = st.columns([1.5, 1])
    
    with col_left:
        st.subheader("Weekly Sales Trend & 4-Week Moving Average")
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Bar(
            x=weekly_df["WEEK_NO"],
            y=weekly_df["total_sales"] / 1e3,
            name="Weekly Sales ($K)",
            marker_color="#CBD5E1",
            opacity=0.7
        ))
        fig_trend.add_trace(go.Scatter(
            x=weekly_df["WEEK_NO"],
            y=weekly_df["sales_4wk_ma"] / 1e3,
            name="4-Week Moving Avg ($K)",
            line=dict(color="#2563EB", width=2.5)
        ))
        fig_trend.add_annotation(x=50, y=110, text="Year 1 Holiday Peak", showarrow=True, arrowhead=1)
        fig_trend.add_annotation(x=101, y=118, text="Year 2 Holiday Peak", showarrow=True, arrowhead=1)
        fig_trend.update_layout(
            xaxis_title="Timeline (Week 1 to 102)",
            yaxis_title="Revenue ($ in Thousands)",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=0, r=0, t=10, b=0),
            height=360
        )
        st.plotly_chart(fig_trend)
        
    with col_right:
        st.subheader("Pareto 80/20 Customer Concentration")
        pareto_data = hh_df.sort_values("total_sales", ascending=False).reset_index(drop=True)
        pareto_data["cum_sales"] = pareto_data["total_sales"].cumsum()
        pareto_data["cum_sales_pct"] = pareto_data["cum_sales"] / total_sales * 100
        pareto_data["hh_pct"] = (np.arange(1, len(pareto_data) + 1) / len(pareto_data)) * 100
        
        fig_pareto = go.Figure()
        fig_pareto.add_trace(go.Scatter(
            x=pareto_data["hh_pct"],
            y=pareto_data["cum_sales_pct"],
            name="Customer Revenue Share",
            line=dict(color="#059669", width=2.5)
        ))
        fig_pareto.add_trace(go.Scatter(
            x=[0, 100], y=[0, 100],
            name="Equal Distribution",
            line=dict(color="#94A3B8", dash="dash")
        ))
        fig_pareto.add_vline(x=20, line_dash="dot", line_color="#DC2626")
        fig_pareto.add_annotation(x=20, y=53.1, text="Top 20% HH -> 53.1% Revenue", showarrow=True, arrowhead=1)
        fig_pareto.update_layout(
            xaxis_title="% of Households (Ranked by Spend)",
            yaxis_title="% of Total Revenue",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=0, r=0, t=10, b=0),
            height=360
        )
        st.plotly_chart(fig_pareto)
        
    # Department quick breakdown
    st.markdown("---")
    st.subheader("Department Contribution Summary")
    
    col_d1, col_d2 = st.columns([1, 1])
    with col_d1:
        st.markdown("""
        - **Grocery Core**: Accounts for **50.5% of store revenue** ($4.07M) and penetrates **91.8%** of customer shopping trips.
        - **Traffic Builders**: Drug GM (15.2% share) and Produce (64.9% trip penetration) drive steady weekly store footfall.
        - **Promotional Dominance**: Automatic loyalty card discounts account for **97%** of all customer discounts.
        """)
    with col_d2:
        st.markdown("""
        - **Pareto Realities**: The top 20% of households (500 families) contribute **53.1%** of revenue, while the bottom 40% generate less than 13%.
        - **Assortment Inefficiency**: Over 55% of the 92,353 catalog SKUs generated under $50 across two years.
        """)

# Customer and RFM intelligence view
elif nav == "👥 Customer & RFM Intelligence":
    st.markdown('<div class="main-header">Customer Behavior & RFM Segmentation</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Descriptive segmentation based on Recency, Frequency, and Monetary quartiles.</div>', unsafe_allow_html=True)
    
    seg_summary = rfm_df.groupby("Customer_Segment").agg(
        households=("household_key", "count"),
        total_sales=("total_sales", "sum"),
        avg_spend=("total_sales", "mean"),
        avg_trips=("basket_count", "mean"),
        avg_recency=("recency_days", "mean"),
        avg_basket=("avg_basket_value", "mean")
    ).reset_index()
    
    total_sales = rfm_df["total_sales"].sum()
    seg_summary["hh_share_pct"] = (seg_summary["households"] / len(rfm_df) * 100).round(1)
    seg_summary["revenue_share_pct"] = (seg_summary["total_sales"] / total_sales * 100).round(1)
    seg_summary = seg_summary.sort_values("total_sales", ascending=False).reset_index(drop=True)
    
    c1, c2 = st.columns([1.2, 1])
    with c1:
        st.subheader("Customer Share vs. Revenue Share by Segment")
        fig_seg = go.Figure()
        fig_seg.add_trace(go.Bar(
            x=seg_summary["Customer_Segment"],
            y=seg_summary["hh_share_pct"],
            name="% of Households",
            marker_color="#93C5FD"
        ))
        fig_seg.add_trace(go.Bar(
            x=seg_summary["Customer_Segment"],
            y=seg_summary["revenue_share_pct"],
            name="% of Revenue",
            marker_color="#1D4ED8"
        ))
        fig_seg.update_layout(
            barmode="group",
            xaxis_tickangle=-25,
            yaxis_title="Percentage (%)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=0, r=0, t=10, b=0),
            height=380
        )
        st.plotly_chart(fig_seg)
        
    with c2:
        st.subheader("Segment Profile Summary")
        st.dataframe(
            seg_summary[[
                "Customer_Segment", "households", "hh_share_pct", 
                "revenue_share_pct", "avg_spend", "avg_trips", "avg_basket"
            ]].style.format({
                "hh_share_pct": "{:.1f}%",
                "revenue_share_pct": "{:.1f}%",
                "avg_spend": "${:,.0f}",
                "avg_trips": "{:.0f}",
                "avg_basket": "${:.2f}"
            }),
            height=340
        )
        
    st.markdown("---")
    st.subheader("Demographic Spend Analysis (801 Profiled Households)")
    
    demo_profile = rfm_df[rfm_df["has_demographics"]].copy()
    
    d_col1, d_col2 = st.columns(2)
    with d_col1:
        st.markdown("**Spend by Income Level (classification_3)**")
        income_order = sorted(demo_profile["classification_3"].unique(), key=lambda x: int(x.replace("Level", "")) if "Level" in x else 99)
        inc_agg = demo_profile.groupby("classification_3")["total_sales"].mean().reindex(income_order).reset_index()
        fig_inc = px.bar(
            inc_agg,
            x="classification_3",
            y="total_sales",
            labels={"classification_3": "Income Bracket", "total_sales": "Average 2-Year Spend ($)"},
            color_discrete_sequence=["#2563EB"]
        )
        fig_inc.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=300)
        st.plotly_chart(fig_inc)
        
    with d_col2:
        st.markdown("**Spend Distribution by Homeowner Status**")
        fig_home = px.box(
            demo_profile[demo_profile["HOMEOWNER_DESC"].isin(["Homeowner", "Renter", "Unknown"])],
            x="HOMEOWNER_DESC",
            y="total_sales",
            points=False,
            labels={"HOMEOWNER_DESC": "Status", "total_sales": "2-Year Spend ($)"},
            color="HOMEOWNER_DESC",
            color_discrete_sequence=["#10B981", "#F59E0B", "#64748B"]
        )
        fig_home.update_layout(showlegend=False, margin=dict(l=0, r=0, t=10, b=0), height=300)
        st.plotly_chart(fig_home)

# Product and assortment view
elif nav == "🛒 Product & Assortment":
    st.markdown('<div class="main-header">Product & Assortment Performance</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Department contributions, Private Label adoption, and catalog velocity audit.</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1.2, 1])
    with col1:
        st.subheader("Top Departments by Revenue Share")
        top_depts = dept_df.head(10).sort_values("total_sales", ascending=True)
        fig_dept = px.bar(
            top_depts,
            x="revenue_share_pct",
            y="DEPARTMENT",
            orientation="h",
            labels={"revenue_share_pct": "Share of Revenue (%)", "DEPARTMENT": ""},
            color_discrete_sequence=["#1E40AF"]
        )
        fig_dept.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=360)
        st.plotly_chart(fig_dept)
        
    with col2:
        st.subheader("National Brand vs. Private Label Split")
        fig_brand = px.pie(
            brand_df,
            names="BRAND",
            values="total_sales",
            color="BRAND",
            color_discrete_map={"National": "#3B82F6", "Private": "#F97316"},
            hole=0.45
        )
        fig_brand.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=360)
        st.plotly_chart(fig_brand)
        
    st.markdown("---")
    st.subheader("Assortment Velocity & Catalog Long-Tail Problem")
    
    t_c1, t_c2 = st.columns([1.2, 1])
    with t_c1:
        fig_tier = px.bar(
            tier_df,
            x="velocity_tier",
            y="sku_pct",
            labels={"velocity_tier": "Assortment Velocity Tier", "sku_pct": "% of Catalog SKUs"},
            color="sku_pct",
            color_continuous_scale="Blues"
        )
        fig_tier.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=320)
        st.plotly_chart(fig_tier)
        
    with t_c2:
        st.markdown("""
        **Assortment Finding**:
        - **55.4% of SKUs (51,180 items)** generate less than **$50 total** across two years.
        - Pruning the bottom 15–20% of non-performing items reduces working capital and simplifies center-store restocking.
        """)
        st.dataframe(
            tier_df.style.format({
                "sku_count": "{:,}",
                "sku_pct": "{:.1f}%",
                "tier_revenue": "${:,.0f}",
                "rev_pct": "{:.1f}%"
            })
        )

# Promotion and campaign ROI view
elif nav == "🏷️ Promotion & Campaign ROI":
    st.markdown('<div class="main-header">Promotions & Direct Marketing Effectiveness</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Evaluating 30 direct marketing campaigns, coupon participation, and redeemer premiums.</div>', unsafe_allow_html=True)
    
    # Campaign targeting and redemption aggregation
    camp_targets = camp_hh_df.groupby("CAMPAIGN")["household_key"].nunique().reset_index(name="targeted_hh")
    camp_reds = redempt_df.groupby("CAMPAIGN").agg(
        redemptions=("COUPON_UPC", "count"),
        active_redeemers=("household_key", "nunique")
    ).reset_index()
    
    camp_m = camp_df.merge(camp_targets, on="CAMPAIGN", how="left").merge(camp_reds, on="CAMPAIGN", how="left").fillna(0)
    camp_m["participation_rate_pct"] = (camp_m["active_redeemers"] / camp_m["targeted_hh"] * 100).round(2)
    
    p_c1, p_c2 = st.columns(2)
    with p_c1:
        st.subheader("Redemptions by Campaign Type")
        type_agg = camp_m.groupby("DESCRIPTION").agg(
            campaigns=("CAMPAIGN", "count"),
            redemptions=("redemptions", "sum"),
            avg_participation=("participation_rate_pct", "mean")
        ).reset_index()
        fig_type = px.bar(
            type_agg,
            x="DESCRIPTION",
            y="redemptions",
            color="DESCRIPTION",
            labels={"DESCRIPTION": "Campaign Type", "redemptions": "Total Redemptions"},
            color_discrete_sequence=["#2563EB", "#10B981", "#F59E0B"]
        )
        fig_type.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=320, showlegend=False)
        st.plotly_chart(fig_type)
        
    with p_c2:
        st.subheader("Household Participation Rate (%)")
        fig_part = px.bar(
            type_agg,
            x="DESCRIPTION",
            y="avg_participation",
            color="DESCRIPTION",
            labels={"DESCRIPTION": "Campaign Type", "avg_participation": "Average Participation (%)"},
            color_discrete_sequence=["#2563EB", "#10B981", "#F59E0B"]
        )
        fig_part.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=320, showlegend=False)
        st.plotly_chart(fig_part)
        
    st.markdown("---")
    st.subheader("Coupon Redeemer vs. Non-Redeemer Comparison")
    
    redeemers = set(redempt_df["household_key"].unique())
    hh_copy = hh_df.copy()
    hh_copy["Group"] = np.where(hh_copy["household_key"].isin(redeemers), "Coupon Redeemer (N=434)", "Non-Redeemer (N=2,066)")
    
    comp_agg = hh_copy.groupby("Group").agg(
        households=("household_key", "count"),
        mean_spend=("total_sales", "mean"),
        median_spend=("total_sales", "median"),
        mean_trips=("basket_count", "mean"),
        mean_basket=("avg_basket_value", "mean")
    ).reset_index()
    
    rc1, rc2 = st.columns([1, 1])
    with rc1:
        st.dataframe(
            comp_agg.style.format({
                "households": "{:,}",
                "mean_spend": "${:,.2f}",
                "median_spend": "${:,.2f}",
                "mean_trips": "{:.1f}",
                "mean_basket": "${:.2f}"
            })
        )
    with rc2:
        st.markdown("""
        - **Spend Premium**: Coupon redeemers spend **115% more** ($5,785 vs $2,684).
        - **Frequency Driven**: Redeemers visit twice as often (**194 trips vs 93 trips**), while average basket values are comparable ($30.95 vs $28.47).
        - **Promotional Finding**: Redeemers are highly engaged frequent shoppers using coupons on existing weekly pantry routines.
        """)

# SQL query explorer view
elif nav == "⚡ SQL Query Explorer":
    st.markdown('<div class="main-header">SQL Analytical Query Repository</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Production-grade PostgreSQL queries used in the analysis.</div>', unsafe_allow_html=True)
    
    query_category = st.selectbox(
        "Select Analytical Domain",
        ["Customer & Pareto Analysis", "Product & Assortment Analysis", "Promotion & Campaign Analysis"]
    )
    
    if query_category == "Customer & Pareto Analysis":
        sql_path = Path(__file__).resolve().parent / "sql" / "customer_analysis.sql"
    elif query_category == "Product & Assortment Analysis":
        sql_path = Path(__file__).resolve().parent / "sql" / "product_sales_analysis.sql"
    else:
        sql_path = Path(__file__).resolve().parent / "sql" / "promotion_analysis.sql"
        
    if sql_path.exists():
        with open(sql_path, "r") as f:
            sql_content = f.read()
        st.code(sql_content, language="sql")
    else:
        st.error(f"SQL file not found at {sql_path}")
