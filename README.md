# 📈 Portfolio Assistant (Zerodha Integrated)

An intelligent, AI-powered personal financial portfolio assistant designed for Zerodha Demat accounts. The application automates holdings synchronization, sector exposure analysis, risk evaluation, and generates stock buy/sell/hold advice with human-in-the-loop trade execution.

---

## 📄 Documentation

👉 **[Documentation Index](./docs/README.md)** — full directory of all docs

| Document | Description |
|---|---|
| [HLD](./docs/architecture/HLD.md) | System architecture, data flow diagrams, DB schema, security policies |
| [Architecture Review](./docs/architecture/ARCHITECTURE_REVIEW.md) | Design issues, gaps, and recommendations |
| [LLD Index](./docs/lld/00_INDEX.md) | Low-level design for all source files, phase by phase |
| [Zerodha Setup Guide](./docs/guides/zerodha_api_setup_guide.md) | Free vs paid API access, enctoken setup |
| [Gemini SDK Reference](./docs/api-references/Gemini_api_doc.md) | Google Gemini Python SDK integration guide |

---

## ✨ Features (Phase 1 MVP)

- **Zerodha Kite Connect Integration**: Official OAuth 2.0 authentication flow and holdings API wrapper (`kiteconnect` SDK v3).
- **Automated Holdings Sync**: Retrieves long-term equity holdings, quantities, purchase average price, LTP, P&L (₹ and %), and margins.
- **Interactive Streamlit Dashboard**: 
  - **KPI Cards**: Real-time summary of Total Invested, Current Portfolio Value, Overall P&L, and Available Cash Margin.
  - **Color-Coded Holdings Table**: Sortable, filterable holdings view with sector tags.
  - **Sector & Market Cap Analytics**: Plotly pie charts and concentration risk warning thresholds.
- **Demo / Standalone Mode**: Toggleable demo mode allowing full evaluation without immediate Zerodha API key requirements.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.10+, FastAPI, Uvicorn, Pydantic
- **Zerodha Integration**: `kiteconnect` Official Python SDK (v3)
- **Frontend**: Streamlit, Pandas, Plotly Express
- **Config & Auth**: `python-dotenv`, OAuth 2.0 / SHA-256 checksum token exchange

---

## 📂 Project Directory Structure

```text
portfolio-assistant/
├── README.md                        # Setup & user guide (this file)
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment variables template
├── docs/
│   ├── README.md                    # Documentation index
│   ├── architecture/
│   │   ├── HLD.md                   # High-level system architecture
│   │   └── ARCHITECTURE_REVIEW.md   # Design review & recommendations
│   ├── lld/
│   │   ├── 00_INDEX.md              # LLD index + file coverage map
│   │   ├── 01_phase1_auth_and_holdings.md
│   │   ├── 02_phase2_analytics_engine.md
│   │   ├── 03_phase3_ai_advisory.md
│   │   ├── 04_logging.md
│   │   ├── 05_retry_and_fallback.md
│   │   └── 06_file_change_summary.md
│   ├── plans/                       # Per-phase implementation plans
│   ├── guides/
│   │   └── zerodha_api_setup_guide.md
│   └── api-references/
│       └── Gemini_api_doc.md
└── src/
    ├── api/                         # FastAPI routers
    │   ├── auth.py                  # Zerodha OAuth login & callback
    │   ├── holdings.py              # Holdings, positions & margins
    │   ├── analytics.py             # Performance, fundamentals & tax
    │   └── advisory.py              # AI recommendations endpoint
    ├── core/
    │   ├── config.py                # Settings manager
    │   ├── logging_config.py        # Centralised logging setup
    │   └── retry.py                 # Exponential backoff utility
    ├── services/
    │   ├── zerodha_client.py        # Kite Connect wrapper & demo engine
    │   ├── market_data.py           # NSE/yfinance fundamentals fetcher
    │   ├── analytics_engine.py      # XIRR, Sharpe, Beta calculations
    │   ├── tax_harvesting.py        # STCG/LTCG tax analyser
    │   ├── rebalancer.py            # Deterministic rule engine
    │   └── llm_advisor.py           # Gemini/Ollama advisory service
    ├── main.py                      # FastAPI entrypoint
    └── ui/
        └── app.py                   # Streamlit dashboard
```

---

## 🚀 Running the Application

### 1. Prerequisites
- Python 3.10 or higher
- Zerodha Developer Account & Kite Connect API Credentials (optional for Demo Mode). See the detailed step-by-step guide: [Zerodha API Key & Secret Setup Guide](./docs/guides/zerodha_api_setup_guide.md).

### 2. Environment Setup

Clone or navigate to the project directory and create a virtual environment:

**Windows:**
```cmd
cd portfolio_assistant
python -m venv .venv
.venv\Scripts\activate
```

**macOS / Linux:**
```bash
cd portfolio_assistant
python3 -m venv .venv
source .venv/bin/activate
```

Install the required Python packages:

```bash
pip install -r requirements.txt
```

### 3. Configuration (.env)

Copy the sample environment file:

```bash
cp .env.example .env
```

Edit `.env` if you want to connect to live Zerodha Kite Connect API:

```ini
KITE_API_KEY=your_zerodha_api_key
KITE_API_SECRET=your_zerodha_api_secret
KITE_REDIRECT_URL=http://127.0.0.1:8000/api/v1/auth/callback
DEMO_MODE=true  # Set to false when ready to connect live Zerodha account
```

---

### 4. Running the Application

#### Step 4a: Start the FastAPI Backend Server
In terminal 1:
```bash
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Documentation (Swagger UI): [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

#### Step 4b: Start the Streamlit Dashboard UI
In terminal 2:
```bash
streamlit run src/ui/app.py
```
- Open your browser at: [http://localhost:8501](http://localhost:8501)

---

## 🗺️ Roadmap

- [x] **Phase 1**: Zerodha OAuth 2.0 Authentication & Holdings Ingestion MVP
- [x] **Phase 2**: Fundamental Analytics (P/E, ROE), Benchmark Comparison (Nifty 50), XIRR & Tax Harvesting (STCG/LTCG)
- [ ] **Phase 3**: AI Advisory Engine (Google Gemini API LLM Context Prompting & Buy/Sell/Hold Rationale)
- [ ] **Phase 4**: Order Staging Safety Queue & Telegram / Webhook Alerts
