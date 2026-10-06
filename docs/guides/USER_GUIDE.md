# Portfolio Assistant — User Guide

A guide for using the Portfolio Assistant dashboard to track, analyse, and get AI-driven advice on your Zerodha equity portfolio.

---

## Opening the Dashboard

Navigate to **http://localhost:3000** in your browser. You will land on the main dashboard.

The top-right corner of the header shows the backend connection status:
- 🟢 **Backend online** — everything is working
- 🔴 **Backend offline** — the backend server is not running; contact your administrator

---

## Step 1 — Connect Your Portfolio (Sidebar)

The left sidebar controls where your portfolio data comes from. Choose one of three modes:

### Demo mode (default)
Click the **Demo** button. A sample portfolio loads instantly — no login required. Use this to explore all features before connecting your real account.

### Enctoken mode (free, live data)
Use this to sync your real Zerodha holdings for free using your browser session.

1. Log in to [kite.zerodha.com](https://kite.zerodha.com) in a separate browser tab
2. Open browser DevTools (`F12`) → **Application** tab → **Cookies** → `kite.zerodha.com`
3. Find the cookie named `enctoken` and copy its value
4. Back in the sidebar, click **Enctoken**
5. Paste the value into the password field that appears
6. Click **Save & Reload**

> Your token expires every day at 6:00 AM IST. Repeat this process each morning to keep data fresh.

### Kite API mode (paid)
Click **Kite API**, then click **Login with Zerodha**. You will be redirected to Zerodha's login page. This requires an active Kite Connect subscription (₹2,000/month).

---

## Step 2 — Adjust Your Settings (Sidebar)

After connecting, configure the analysis parameters to match your preferences.

### Risk & Benchmark section

| Setting | What it does |
|---|---|
| **Benchmark** | The index used to calculate your portfolio's Beta (NIFTY 50, NIFTY 500, or SENSEX) |
| **Max sector cap %** | The maximum allocation you want in any single sector. Drag the slider (10–40%). Sectors above this threshold are flagged in the Sector tab. |

### AI Advisory section

| Setting | What it does |
|---|---|
| **Investment goal** | Tells the AI your objective — choose from Moderate Growth, Aggressive Growth, Capital Preservation, Income / Dividend, or Balanced |
| **Max single stock %** | The maximum weight you want in any one stock. Drag the slider (5–40%). Stocks above this trigger a TRIM recommendation. |

---

## Step 3 — Read the KPI Bar

The row of metric cards at the top of the main area gives you a quick portfolio snapshot:

| Card | What it means |
|---|---|
| **Total invested** | Sum of all your buy prices × quantities |
| **Current value** | Sum of all holdings at today's last traded price |
| **Overall P&L** | Current value minus invested value, with percentage below |
| **Portfolio XIRR** | Your annualised return accounting for the timing of each purchase |
| **Portfolio Beta** | How much your portfolio moves relative to Nifty 50 (1.0 = moves with the market) |
| **Risk profile** | A classification tag (e.g. Moderate, Aggressive) based on your Beta and concentration |

---

## Step 4 — Explore the Tabs

Click any tab in the navigation bar to switch views.

---

### 📊 Holdings tab

A full table of every stock you hold.

**Filtering your holdings:**
- Type a symbol in the **Search** box to filter rows instantly
- Click any **sector tag** to filter by that sector; click again to deselect

**Columns explained:**

| Column | Meaning |
|---|---|
| Symbol | NSE trading symbol |
| Sector | Industry sector assigned to the stock |
| Category | Market cap category (Large Cap, Mid Cap, etc.) |
| Qty | Number of shares held |
| Avg Price | Your average buy price per share |
| LTP | Last traded price |
| P&L (₹) | Unrealised profit or loss in rupees (green = profit, red = loss) |
| P&L (%) | Percentage gain or loss from your average buy price |
| Weight | This stock's share of your total portfolio value |
| P/E | Price-to-Earnings ratio |
| P/B | Price-to-Book ratio |
| ROE | Return on Equity (%) |
| 200 SMA | Price trend relative to the 200-day moving average |

---

### 🍕 Sector tab

Three charts showing how your money is distributed.

- **Sector allocation (pie chart)** — each slice is a sector; hover to see the exact rupee value
- **Market cap distribution (bar chart)** — how much is in Large Cap vs Mid Cap vs Small Cap
- **Single stock concentration (bar chart)** — each bar is one stock's weight; the red dashed line is your Max Sector Cap setting. Bars touching or crossing the line indicate over-concentration.

---

### 📈 Performance tab

Detailed risk and return metrics.

**Top metric cards:**

| Metric | What it means |
|---|---|
| XIRR | Annualised return (accounts for when you bought each lot) |
| Sharpe ratio | Return per unit of total risk (above ~7.1% risk-free rate). Higher is better. |
| Sortino ratio | Like Sharpe but only penalises downside volatility. Higher is better. |
| Weighted P/E | Average P/E across your portfolio, weighted by holding size |

**Beta gauge** — the semicircular chart shows your portfolio's volatility relative to Nifty 50:
- 🟢 Below 0.85 — low volatility (defensive portfolio)
- 🟡 0.85–1.15 — market-aligned
- 🔴 Above 1.15 — high volatility (aggressive portfolio)

**Valuation matrix:**
- **Weighted ROE** — average return on equity across holdings; higher means better-quality businesses
- **Herfindahl concentration index** — below 1,500 means well-diversified; above 2,500 means highly concentrated
- **Risk classification** — overall risk tag for your portfolio

---

### ⚖️ Tax tab

Capital gains tax estimates and tax-saving opportunities.

**Summary cards:**

| Card | Meaning |
|---|---|
| Net STCG | Net short-term capital gains (holdings sold within 1 year) |
| STCG tax (20%) | Estimated tax owed on short-term gains |
| Net LTCG | Net long-term capital gains (holdings held over 1 year) |
| LTCG tax (12.5%) | Estimated tax owed on long-term gains above the exemption |

**LTCG exemption bar** — shows how much of your ₹1.25 lakh annual LTCG exemption you have used. The bar turns red when the limit is fully consumed.

**Harvestable loss candidates** — a table of stocks currently sitting at a loss. Selling these before March 31st offsets your taxable gains. The table shows:
- Unrealised loss amount
- How many days you have held the stock
- Whether it qualifies as STCG or LTCG

If the table is absent and you see a green message, your portfolio has no loss candidates — all holdings are in profit.

---

### 🤖 Advisory tab

AI-generated buy/sell/hold recommendations for each stock in your portfolio.

**Source badge** (top of the tab):
- ✨ **Gemini · [your goal]** — recommendations are powered by Google Gemini AI
- **Rule-based recommendations** — AI key is not configured; recommendations come from the built-in rule engine

**Rule engine alerts** — flagged issues such as sector overweight, single-stock concentration, or valuation concerns. Each alert shows a severity (HIGH / MEDIUM / LOW) and a description.

**Recommendations list** — one card per stock. Each card shows:
- Action badge: **BUY** (green), **HOLD** (blue), **TRIM** (yellow), **SELL** (red)
- Stock symbol and target allocation percentage
- Confidence bar — how confident the AI is in this recommendation (0–100%)
- Click the card to expand the full rationale explaining why this action is suggested

> Recommendations are advisory only. No trades are placed automatically — you remain in full control of all buy/sell decisions.

**Generating a Trade Basket:**
1. Enter your **Max budget for buying** in the input field.
2. Click **Generate Basket** to compute exact share quantities to buy, sell, or trim based on target allocations.

**Exporting to Zerodha Baskets:**
1. Once your trade basket is generated, scroll to the **Export to Zerodha Baskets** section.
2. Choose **Create New Basket** (enter custom name) or **Add to Existing Basket** (select from dropdown).
3. Click **Push to Zerodha Basket**.
4. Once completed, click **Open Zerodha Kite Baskets** to open Zerodha in a new tab (`https://kite.zerodha.com/orders/baskets`).
5. In Zerodha Kite, review the pre-filled basket items and execute manually whenever you wish. No automated trade execution takes place!

---

## Quick Reference

| I want to… | Where to go |
|---|---|
| See all my holdings and P&L | Holdings tab |
| Check if I'm over-concentrated in a sector | Sector tab |
| Find my XIRR and risk metrics | Performance tab |
| Estimate my tax liability | Tax tab |
| Get buy/sell/hold advice | Advisory tab |
| Change my investment goal | Sidebar → AI Advisory → Investment goal |
| Adjust sector concentration limit | Sidebar → Risk & Benchmark → Max sector cap |
| Switch to live Zerodha data | Sidebar → Enctoken or Kite API |
