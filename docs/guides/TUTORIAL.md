# Portfolio Assistant — User Tutorial

A step-by-step guide to setting up and using the Portfolio Assistant from scratch.

---

## Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.10+ |
| Node.js | 18+ |
| PostgreSQL | 14+ (optional — not required for Demo Mode) |
| Redis | 7+ (optional — not required for Demo Mode) |

---

## Step 1 — Clone & Configure the Backend

### 1.1 Set up the Python environment

```cmd
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 1.2 Create your `.env` file

```cmd
copy .env.example .env
```

Open `backend/.env` and fill in the values:

```ini
# --- Choose ONE connection mode ---

# Option A: Demo Mode (no Zerodha account needed)
DEMO_MODE=true

# Option B: Live mode via browser session token (free)
DEMO_MODE=false
ZERODHA_ENCTOKEN=<paste your enctoken here>

# Option C: Live mode via paid Kite Connect API
DEMO_MODE=false
KITE_API_KEY=<your_api_key>
KITE_API_SECRET=<your_api_secret>
KITE_REDIRECT_URL=http://127.0.0.1:8000/api/v1/auth/callback

# --- AI Advisory (optional but recommended) ---
GEMINI_API_KEY=<your_gemini_api_key>
GEMINI_MODEL=gemini-3.1-flash-lite
```

> Get a free Gemini API key at https://aistudio.google.com/app/apikey  
> For enctoken setup, see [zerodha_api_setup_guide.md](./zerodha_api_setup_guide.md)

### 1.3 Start the backend

```cmd
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```

Verify it's running: http://127.0.0.1:8000/docs (Swagger UI)

---

## Step 2 — Configure & Start the Frontend

### 2.1 Install dependencies

```cmd
cd frontend
npm install
```

### 2.2 Create your `.env.local` file

```cmd
copy .env.local.example .env.local
```

The default value works for local development:

```ini
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

### 2.3 Start the frontend

```cmd
npm run dev
```

Open the dashboard: http://localhost:3000

---

## Step 3 — Connect Your Portfolio

The sidebar on the left controls how the app fetches your data.

### Connection Modes

| Mode | What it does |
|---|---|
| **Demo** | Loads a pre-built sample portfolio — no Zerodha account needed |
| **Enctoken** | Syncs your real Zerodha holdings using a free browser session token |
| **Kite API** | Syncs via the paid Kite Connect API (₹2,000/month) |

### How to get your Enctoken (free live sync)

1. Log in to [kite.zerodha.com](https://kite.zerodha.com) in your browser
2. Open DevTools → Application → Cookies → `kite.zerodha.com`
3. Copy the value of the `enctoken` cookie
4. Paste it into `backend/.env` as `ZERODHA_ENCTOKEN=<value>`
5. Restart the backend and switch the sidebar to **Enctoken** mode

> Tokens expire daily at 6:00 AM IST — repeat this step each trading day.

---

## Step 4 — Explore the Dashboard

The dashboard has five tabs:

### 📊 Holdings

- Full table of your equity holdings with quantity, average price, LTP, P&L (₹ and %), and portfolio weight
- Fundamental metrics per stock: P/E, P/B, ROE, 200-day SMA trend
- Use the search box to filter by symbol; click sector tags to filter by sector

### 🍕 Sector

- Pie chart showing sector allocation across your portfolio
- Bar chart comparing your sector weights against the configured cap (default 25%)
- Sectors exceeding the cap are highlighted in red

### 📈 Performance

- Key metrics: XIRR, Sharpe ratio, Sortino ratio, Portfolio Beta
- Weighted P/E and ROE across the portfolio
- Herfindahl Index (concentration risk score) and risk profile tag

### ⚖️ Tax

- STCG (Short-Term Capital Gains) and LTCG (Long-Term Capital Gains) breakdown
- Tax payable estimates at current rates
- LTCG exemption used (₹1 lakh limit)
- Tax-loss harvesting candidates — stocks where selling would offset gains

### 🤖 Advisory

- AI-powered Buy / Hold / Trim / Sell recommendations per stock
- Each recommendation shows: action badge, target allocation %, confidence score, and rationale (click to expand)
- Rule engine alerts for concentration risk, sector overweight, and valuation flags
- Powered by Google Gemini when `GEMINI_API_KEY` is set; falls back to rule-based engine otherwise

---

## Step 5 — Sidebar Settings

| Setting | What it controls |
|---|---|
| **Connection Mode** | Demo / Enctoken / Kite API |
| **Benchmark** | Index used for beta calculation (e.g. NIFTY 50) |
| **Max Sector Cap %** | Threshold above which a sector is flagged as overweight |
| **Investment Goal** | Passed to the AI advisor (e.g. Moderate Growth, Aggressive Growth) |
| **Max Stock Cap %** | Maximum single-stock weight before a TRIM recommendation is triggered |

---

## Troubleshooting

### yfinance SSL errors in logs

```
Cookie/crumb fetch failed (CertificateVerifyError)
```

This is a known issue on corporate networks with SSL inspection. Market data falls back to cached/demo values automatically. To fix permanently, set your corporate CA certificate in the environment:

```cmd
set REQUESTS_CA_BUNDLE=C:\path\to\your\corporate-ca.crt
```

### Enctoken HTTP 400 errors

```
Enctoken request to https://api.kite.trade/... failed (HTTP 400)
```

Your enctoken has expired. Extract a fresh one from your browser (see Step 3) and update `backend/.env`, then restart the backend.

### Advisory shows "Rule-based recommendations"

`GEMINI_API_KEY` is not set or is invalid. The app still works — it uses the built-in rule engine. To enable AI recommendations, add a valid key to `backend/.env` and restart.

### Frontend shows no data

Ensure the backend is running at `http://127.0.0.1:8000` before opening the frontend. Check `NEXT_PUBLIC_API_URL` in `frontend/.env.local` matches the backend address.

---

## Quick Reference

```cmd
# Backend
cd backend && .venv\Scripts\activate
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload

# Frontend (separate terminal)
cd frontend
npm run dev
```

| URL | Purpose |
|---|---|
| http://localhost:3000 | React dashboard |
| http://127.0.0.1:8000/docs | Swagger API explorer |
