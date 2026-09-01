# 📈 Portfolio Assistant (Zerodha Integrated)

An intelligent, AI-powered personal financial portfolio assistant designed for Zerodha Demat accounts. The application automates holdings synchronization, sector exposure analysis, risk evaluation, and generates stock buy/sell/hold advice with human-in-the-loop trade execution.

---

## 📄 Architecture & High-Level Design

For a comprehensive architectural breakdown, sequence diagrams, security policies, and database schema, please refer to the High-Level Design document:

👉 **[High-Level Design Document (HLD.md)](./docs/HLD.md)**

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
portfolio_assistant/
├── HLD.md                  # High-Level System Architecture Document
├── README.md               # Setup & User Guide (this file)
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variables configuration template
└── src/
    ├── api/                # FastAPI Routers
    │   ├── auth.py         # Zerodha OAuth login & callback handler
    │   └── holdings.py     # Holdings, positions & margins REST APIs
    ├── core/
    │   └── config.py       # Pydantic/dotenv settings manager
    ├── services/
    │   └── zerodha_client.py # Zerodha KiteConnect wrapper & demo engine
    ├── main.py             # FastAPI backend entrypoint
    └── ui/
        └── app.py          # Streamlit dashboard application
```

---

## 🚀 Running the Application

### 1. Prerequisites
- Python 3.10 or higher
- Zerodha Developer Account & Kite Connect API Credentials (optional for Demo Mode). See the detailed step-by-step guide: [Zerodha API Key & Secret Setup Guide](./docs/zerodha_api_setup_guide.md).

### 2. Environment Setup

Clone or navigate to the project directory and create a virtual environment:

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
- [ ] **Phase 2**: Fundamental Analytics (P/E, ROE), Benchmark Comparison (Nifty 50), XIRR & Tax Harvesting (STCG/LTCG)
- [ ] **Phase 3**: AI Advisory Engine (Google Gemini API LLM Context Prompting & Buy/Sell/Hold Rationale)
- [ ] **Phase 4**: Order Staging Safety Queue & Telegram / Webhook Alerts
