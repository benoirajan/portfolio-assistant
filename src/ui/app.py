import sys
import os

# Ensure project root is in sys.path when running via streamlit
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests

from src.core.config import settings

# Page Configuration
st.set_page_config(
    page_title="Portfolio Assistant | FastAPI Connected",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000/api/v1")

# Helper function to fetch data from FastAPI Backend Server via REST HTTP calls
def fetch_from_backend(endpoint: str, enctoken_input: str = "") -> Tuple[Dict[str, Any], bool]:
    """Fetches data from FastAPI backend REST API (http://127.0.0.1:8000/api/v1/...). Returns (data_dict, server_online_flag)."""
    headers = {}
    effective_token = enctoken_input if enctoken_input else settings.ZERODHA_ENCTOKEN
    if effective_token:
        headers["X-Enctoken"] = effective_token

    url = f"{API_BASE_URL}/{endpoint.lstrip('/')}"
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            return response.json(), True
    except Exception as e:
        pass
    
    # Fallback to local python service if FastAPI server is currently offline
    return fetch_fallback_local(endpoint, effective_token), False

def fetch_fallback_local(endpoint: str, enctoken: str) -> Dict[str, Any]:
    from src.services.zerodha_client import zerodha_service
    from src.services.market_data import market_data_service
    from src.services.analytics_engine import analytics_engine
    from src.services.tax_harvesting import tax_harvesting_analyzer

    if enctoken:
        zerodha_service.set_enctoken(enctoken)

    raw_holdings, is_live, error_msg = zerodha_service.get_holdings_with_status()
    enriched = market_data_service.enrich_holdings_with_fundamentals(raw_holdings)

    if "performance" in endpoint:
        return {"status": "success", "metrics": analytics_engine.calculate_portfolio_metrics(enriched)}
    elif "tax" in endpoint:
        return {"status": "success", "tax_analysis": tax_harvesting_analyzer.analyze_tax_harvesting(enriched)}
    elif "margins" in endpoint:
        return {"status": "success", "margins": zerodha_service.get_margins()}
    else:
        total_inv = sum(h.get("quantity", 0) * h.get("average_price", 0) for h in enriched)
        curr_val = sum(h.get("quantity", 0) * h.get("last_price", 0) for h in enriched)
        total_pnl = curr_val - total_inv
        pnl_pct = (total_pnl / total_inv * 100) if total_inv > 0 else 0.0
        return {
            "status": "success",
            "is_live": is_live,
            "error_message": error_msg,
            "summary": {
                "total_holdings_count": len(enriched),
                "total_investment": round(total_inv, 2),
                "current_value": round(curr_val, 2),
                "total_pnl": round(total_pnl, 2),
                "total_pnl_percentage": round(pnl_pct, 2)
            },
            "holdings": enriched
        }

# Header
st.title("📈 AI Portfolio Assistant")
st.caption("Frontend connected to FastAPI Backend (`http://127.0.0.1:8000`) for Holdings, Fundamentals & Risk Analytics")

# Sidebar Configuration
with st.sidebar:
    st.image("https://kite.zerodha.com/static/images/kite-logo.svg", width=120)
    st.header("Zerodha Account Connection")
    
    default_index = 1 if settings.ZERODHA_ENCTOKEN else 0
    conn_mode = st.radio(
        "Select Connection Mode",
        ["🧪 Demo Portfolio (Sample)", "🔑 Free Live Sync (Web Enctoken)", "⚡ Paid Kite Connect API"],
        index=default_index
    )
    
    enctoken_val = ""
    if conn_mode == "🧪 Demo Portfolio (Sample)":
        st.success("Mode: **Demo Demat Account**")
    elif conn_mode == "🔑 Free Live Sync (Web Enctoken)":
        st.info("Sync actual Zerodha account for **Free** via FastAPI Backend")
        initial_val = settings.ZERODHA_ENCTOKEN if settings.ZERODHA_ENCTOKEN else ""
        enctoken_val = st.text_input("Paste Zerodha `enctoken` Cookie", value=initial_val, type="password")
        if settings.ZERODHA_ENCTOKEN and not enctoken_val:
            st.caption("🔒 Using `ZERODHA_ENCTOKEN` from `.env` file.")
    elif conn_mode == "⚡ Paid Kite Connect API":
        st.info("Kite Connect OAuth API")
        api_key = st.text_input("Kite API Key", value=settings.KITE_API_KEY, type="password")
        api_secret = st.text_input("Kite API Secret", value=settings.KITE_API_SECRET, type="password")
        login_url = f"https://kite.zerodha.com/connect/login?v=3&api_key={api_key}" if api_key else "#"
        st.markdown(f'<a href="{login_url}" target="_blank"><button style="width:100%; background-color:#388e3c; color:white; border:none; padding:10px; border-radius:5px; font-weight:bold; cursor:pointer;">🔑 Login with Zerodha</button></a>', unsafe_allow_html=True)
    
    st.divider()
    st.markdown("### Risk & Benchmark Settings")
    benchmark = st.selectbox("Benchmark Index", ["NIFTY 50", "NIFTY 500", "SENSEX"])
    max_sector_cap = st.slider("Max Sector Exposure Cap (%)", 10, 40, 25)

# Fetch Data from FastAPI Backend
holdings_res, is_server_online = fetch_from_backend("holdings", enctoken_input=enctoken_val)
perf_res, _ = fetch_from_backend("analytics/performance", enctoken_input=enctoken_val)
tax_res, _ = fetch_from_backend("analytics/tax-harvesting", enctoken_input=enctoken_val)
margins_res, _ = fetch_from_backend("margins", enctoken_input=enctoken_val)

# Server & Connection Status Banners
if is_server_online:
    st.caption("🌐 **Backend REST API**: Connected to `http://127.0.0.1:8000` (FastAPI Server Online)")
else:
    st.info("ℹ️ **Backend REST API**: FastAPI server is offline. (Tip: Run `python -m uvicorn src.main:app --port 8000` to start FastAPI server).")

if conn_mode == "🔑 Free Live Sync (Web Enctoken)":
    is_live = holdings_res.get("is_live", False)
    error_msg = holdings_res.get("error_message", None)
    active_token = enctoken_val if enctoken_val else settings.ZERODHA_ENCTOKEN
    if active_token:
        if is_live:
            st.success(f"🟢 **Live Zerodha Data**: Synced {holdings_res.get('summary', {}).get('total_holdings_count', 0)} holdings via FastAPI backend.")
        elif error_msg:
            st.error(f"🔴 **Live Sync Error**: {error_msg}")

summary = holdings_res.get("summary", {})
holdings_list = holdings_res.get("holdings", [])
metrics = perf_res.get("metrics", {})
tax_data = tax_res.get("tax_analysis", {})
margins_data = margins_res.get("margins", {})
df_holdings = pd.DataFrame(holdings_list)

if not df_holdings.empty:
    if "average_price" in df_holdings and "last_price" in df_holdings and "quantity" in df_holdings:
        df_holdings["invested_value"] = df_holdings["quantity"] * df_holdings["average_price"]
        df_holdings["current_value"] = df_holdings["quantity"] * df_holdings["last_price"]
        df_holdings["pnl"] = df_holdings["current_value"] - df_holdings["invested_value"]
        df_holdings["pnl_percentage"] = (df_holdings["pnl"] / df_holdings["invested_value"].replace(0, 1)) * 100

# Top KPI Metric Bar
k1, k2, k3, k4, k5, k6 = st.columns(6)
with k1:
    st.metric("Total Invested", f"₹{summary.get('total_investment', 0):,.2f}")
with k2:
    st.metric("Current Value", f"₹{summary.get('current_value', 0):,.2f}")
with k3:
    pnl = summary.get("total_pnl", 0)
    pnl_pct = summary.get("total_pnl_percentage", 0)
    st.metric("Overall P&L", f"₹{pnl:,.2f}", delta=f"{pnl_pct:.2f}%")
with k4:
    xirr = metrics.get("xirr_percentage", 0.0)
    st.metric("Portfolio XIRR", f"{xirr:.2f}%")
with k5:
    beta = metrics.get("portfolio_beta", 1.0)
    st.metric("Portfolio Beta", f"{beta:.2f}", help="Volatility relative to Nifty 50")
with k6:
    st.metric("Risk Profile", metrics.get("risk_profile_tag", "Balanced"))

st.divider()

# Main Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Holdings & Fundamentals", 
    "🍕 Sector & Concentration", 
    "📈 Performance & Risk Metrics", 
    "⚖️ Tax Loss Harvesting"
])

with tab1:
    st.subheader("Current Demat Holdings & Fundamental Ratios")
    
    if df_holdings.empty:
        st.warning("No holdings found.")
    else:
        col_f1, col_f2 = st.columns([2, 1])
        with col_f1:
            search_query = st.text_input("🔍 Search Stock Symbol", "")
        with col_f2:
            sectors_available = df_holdings["sector"].unique() if "sector" in df_holdings else []
            sector_filter = st.multiselect("Filter by Sector", options=sectors_available)
        
        filtered_df = df_holdings.copy()
        if search_query and "tradingsymbol" in filtered_df:
            filtered_df = filtered_df[filtered_df["tradingsymbol"].str.contains(search_query.upper())]
        if sector_filter and "sector" in filtered_df:
            filtered_df = filtered_df[filtered_df["sector"].isin(sector_filter)]
        
        display_cols = [c for c in [
            "tradingsymbol", "sector", "cap_category", "quantity", "average_price", "last_price",
            "pnl", "pnl_percentage", "pe_ratio", "pb_ratio", "roe", "div_yield", "trend_200_sma"
        ] if c in filtered_df.columns]
        
        display_df = filtered_df[display_cols].rename(columns={
            "tradingsymbol": "Symbol", "sector": "Sector", "cap_category": "Category",
            "quantity": "Qty", "average_price": "Avg Price (₹)", "last_price": "LTP (₹)",
            "pnl": "P&L (₹)", "pnl_percentage": "P&L (%)", "pe_ratio": "P/E",
            "pb_ratio": "P/B", "roe": "ROE (%)", "div_yield": "Div Yield (%)", "trend_200_sma": "200 SMA Trend"
        })

        st.dataframe(
            display_df.style.format({
                "Avg Price (₹)": "₹{:,.2f}", "LTP (₹)": "₹{:,.2f}", "P&L (₹)": "₹{:,.2f}",
                "P&L (%)": "{:+.2f}%", "P/E": "{:.1f}", "P/B": "{:.1f}", "ROE (%)": "{:.1f}%", "Div Yield (%)": "{:.2f}%"
            }).map(
                lambda val: "color: #4caf50; font-weight: bold;" if (isinstance(val, (int, float)) and val > 0) else "color: #f44336; font-weight: bold;", 
                subset=["P&L (₹)", "P&L (%)"]
            ),
            use_container_width=True,
            height=400
        )

with tab2:
    st.subheader("Portfolio Sector & Concentration Analytics")
    if not df_holdings.empty and "current_value" in df_holdings:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Sector Allocation Breakdown")
            sector_df = df_holdings.groupby("sector")["current_value"].sum().reset_index()
            fig_sector = px.pie(sector_df, values="current_value", names="sector", hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            fig_sector.update_traces(textinfo="percent+label")
            st.plotly_chart(fig_sector, use_container_width=True)
            
        with c2:
            st.markdown("#### Market Cap Category Distribution")
            cap_df = df_holdings.groupby("cap_category")["current_value"].sum().reset_index()
            fig_cap = px.bar(cap_df, x="cap_category", y="current_value", color="cap_category", labels={"current_value": "Value (₹)", "cap_category": "Category"}, text_auto='.2s')
            st.plotly_chart(fig_cap, use_container_width=True)

        st.markdown("#### Single Stock Concentration Risk")
        total_val = df_holdings["current_value"].sum()
        if total_val > 0 and "tradingsymbol" in df_holdings:
            df_holdings["weight_pct"] = (df_holdings["current_value"] / total_val) * 100
            fig_weight = px.bar(df_holdings.sort_values("weight_pct", ascending=False), x="tradingsymbol", y="weight_pct", color="weight_pct", color_continuous_scale="Reds")
            fig_weight.add_hline(y=max_sector_cap, line_dash="dash", line_color="red", annotation_text=f"Max Concentration Threshold ({max_sector_cap}%)")
            st.plotly_chart(fig_weight, use_container_width=True)

with tab3:
    st.subheader("📈 Performance & Risk Analytics (Phase 2)")
    
    p1, p2, p3, p4 = st.columns(4)
    with p1:
        st.metric("Extended IRR (XIRR)", f"{metrics.get('xirr_percentage', 0):.2f}%", help="Annualized internal rate of return")
    with p2:
        st.metric("Sharpe Ratio", f"{metrics.get('sharpe_ratio', 0):.2f}", help="Risk-adjusted return above ~7.1% risk-free rate")
    with p3:
        st.metric("Sortino Ratio", f"{metrics.get('sortino_ratio', 0):.2f}", help="Return adjusted for downside risk")
    with p4:
        st.metric("Weighted Portfolio P/E", f"{metrics.get('weighted_pe', 0):.1f}x")

    col_a1, col_a2 = st.columns(2)
    with col_a1:
        st.markdown("#### Portfolio Beta Gauge (vs Nifty 50)")
        fig_beta = go.Figure(go.Indicator(
            mode="gauge+number",
            value=metrics.get("portfolio_beta", 1.0),
            title={'text': "Beta (Nifty 50 = 1.0)"},
            gauge={
                'axis': {'range': [0, 2]},
                'bar': {'color': "#29b6f6"},
                'steps': [
                    {'range': [0, 0.85], 'color': "#81c784"},
                    {'range': [0.85, 1.15], 'color': "#fff176"},
                    {'range': [1.15, 2.0], 'color': "#e57373"}
                ],
            }
        ))
        st.plotly_chart(fig_beta, use_container_width=True)

    with col_a2:
        st.markdown("#### Fundamental Valuation Matrix")
        st.write(f"- **Weighted Portfolio ROE**: `{metrics.get('weighted_roe', 0):.1f}%`")
        st.write(f"- **Herfindahl Concentration Index**: `{metrics.get('herfindahl_index', 0):,.0f}` *(Below 1,500 = Diversified)*")
        st.write(f"- **Risk Classification**: `{metrics.get('risk_profile_tag', 'Balanced')}`")

with tab4:
    st.subheader("⚖️ Tax Loss Harvesting & Capital Gains Analysis")
    st.info("Optimize capital gains tax liabilities by harvesting unrealized losses before March 31st.")
    
    t1, t2, t3, t4 = st.columns(4)
    with t1:
        st.metric("Net STCG Gains (<1 Year)", f"₹{tax_data.get('net_stcg', 0):,.2f}")
    with t2:
        st.metric("STCG Tax Payable (20%)", f"₹{tax_data.get('stcg_tax_payable', 0):,.2f}")
    with t3:
        st.metric("Net LTCG Gains (>1 Year)", f"₹{tax_data.get('net_ltcg', 0):,.2f}")
    with t4:
        st.metric("LTCG Tax Payable (12.5%)", f"₹{tax_data.get('ltcg_tax_payable', 0):,.2f}")

    st.markdown("#### LTCG Annual Exemption Progress (₹1.25 Lakh Limit)")
    ltcg_used = tax_data.get("ltcg_exemption_used", 0)
    st.progress(min(1.0, ltcg_used / 125000.0), text=f"Used ₹{ltcg_used:,.2f} out of ₹1,25,000 Free Exemption Limit")

    candidates = tax_data.get("harvestable_loss_candidates", [])
    if candidates:
        st.markdown("#### 💡 Harvestable Loss Candidates")
        st.dataframe(pd.DataFrame(candidates), use_container_width=True)
    else:
        st.success("No tax loss harvesting candidates required. Portfolio is fully gain-aligned!")
