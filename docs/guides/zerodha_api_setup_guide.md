# How to Obtain & Choose Zerodha API Access

A complete guide to Zerodha API options: comparing **Personal / Free Access Methods** vs **Paid Kite Connect API**, outlining limitations, pricing, and exact configuration values for Redirect and Postback URLs.

---

## 🔗 Redirect URL and Postback URL Configuration

When setting up your app in the [Zerodha Developer Console](https://developers.kite.trade/), fill in the following values:

### 1. Redirect URL (REQUIRED)
- **What it is**: The URL in your application where Zerodha redirects you after successful login, passing back the `request_token` as a query parameter (e.g. `?request_token=xyz123`).
- **Exact Value to Enter for Local Development**:
  ```text
  http://127.0.0.1:8000/api/v1/auth/callback
  ```
  *(Or `http://localhost:8501` if connecting directly via Streamlit UI).*

---

### 2. Postback URL (OPTIONAL)
- **What it is**: A webhook URL on your server where Zerodha POSTs real-time notifications whenever an order's status updates (e.g. Executed, Rejected, Cancelled).
- **Exact Value to Enter**:
  - **Leave it BLANK / EMPTY** (Recommended for personal/local use).
  - *(Optional for Phase 4 order tracking)*: `http://127.0.0.1:8000/api/v1/orders/postback`

---

## 💰 Pricing & App Type Comparison

| Feature / Capability | Personal / Free Method | Paid Kite Connect API |
| :--- | :--- | :--- |
| **Monthly Cost** | **₹0 / Free** | **₹2,000 / month** (+ ₹2,000 for Historical Data) |
| **Holdings & Portfolio Ingestion** | ✅ Supported (via Web Session / Demo / Enctoken) | ✅ Official REST API (`GET /portfolio/holdings`) |
| **Positions & Margin Info** | ✅ Supported | ✅ Official REST API (`GET /portfolio/positions`) |
| **Order Placement** | ⚠️ Staged / Manual Click (Kite Publisher button) | ⚡ Automated REST API (`POST /orders/regular`) |
| **Historical Market Candles** | ❌ Not Included (Use `yfinance` / NSE API) | ✅ Official Historical API Endpoint |
| **WebSocket Live Ticks** | ❌ Restricted / Limited | ✅ Official Streaming Ticker (`wss://ws.kite.trade`) |
| **Rate Limit SLA & Support** | ⚠️ No SLA | ✅ Official 3 req/sec SLA & Dev Forum Support |

---

## 🔍 Detailed Limitations of Personal / Free Type vs. Paid Connect

### 1. Subscription Cost
- **Paid Kite Connect**: Costs **₹2,000 per month** (non-refundable credit charge on your Zerodha Developer account). If you need 1-minute/5-minute historical candles from Zerodha, it costs an extra **₹2,000 per month**.
- **Personal / Free**: **₹0**. Ideal for personal portfolio tracking, long-term investors, and decision support tools.

### 2. Order Execution Automation
- **Paid Kite Connect**: Can place, modify, or cancel orders headlessly in the background via automated python scripts (`kite.place_order(...)`).
- **Personal / Free**: Cannot execute automated headless orders. Orders must be staged in a "Basket" or opened via **Kite Publisher buttons** where you manually click "Confirm" in your Kite app/browser. *(Note: This is actually safer for personal risk management!)*

### 3. Historical Data & Ticker Stream
- **Paid Kite Connect**: Provides official WebSocket feed for tick-by-tick real-time prices and Zerodha's historical database.
- **Personal / Free**: Does not include official Zerodha market feeds. However, for a portfolio assistant, historical daily stock prices and fundamental metrics can be fetched for **free** using `yfinance` or Indian market libraries.

### 4. Session Token Lifetime
- Both personal and paid connections require a daily login (Zerodha tokens expire every morning at **6:00 AM IST** for security compliance).

---

## 🎯 Recommendation for Portfolio Assistant

For your personal portfolio assistant, **starting with the Personal / Free tier is highly recommended**:

1. **Zero Recurring Cost**: You don't need to spend ₹2,000/month just to track your delivery holdings and get buy/sell advice.
2. **Safety First**: Your Portfolio Assistant already uses a **Human-in-the-Loop** model (staging orders for your explicit approval rather than auto-trading).
3. **Free Data Providers**: Fundamentals and historical prices for portfolio analysis (XIRR, Sharpe ratio, Sector allocation) can be fetched seamlessly using free python libraries (`yfinance` / NSE wrappers).

---

## 🛠️ How to Set Up Personal / Free Mode in Portfolio Assistant

1. **Option A: Demo Mode (Default)**:
   - Set `DEMO_MODE=true` in `.env`.
   - Test all analytics, charts, sector breakdowns, and AI advice without entering any Zerodha API keys.

2. **Option B: Web Session Ingestion (Enctoken)**:
   - Extract your active Kite web session token (`enctoken`) from your browser cookies (`kite.zerodha.com`) to sync your live holdings for free without paying the ₹2,000 monthly subscription.
