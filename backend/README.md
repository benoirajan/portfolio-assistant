# Backend — Portfolio Assistant

FastAPI backend powering the Portfolio Assistant. Handles Zerodha OAuth, holdings sync, analytics engine, and AI advisory via Google Gemini.

---

## 📂 Structure

```text
backend/
├── src/
│   ├── api/                # FastAPI routers
│   │   ├── auth.py         # Zerodha OAuth login & callback
│   │   ├── holdings.py     # Holdings, positions & margins
│   │   ├── analytics.py    # Performance, fundamentals & tax
│   │   └── advisory.py     # AI recommendations endpoint
│   ├── core/
│   │   ├── config.py       # Settings manager
│   │   ├── logging_config.py
│   │   └── retry.py        # Exponential backoff utility
│   ├── services/
│   │   ├── zerodha_client.py
│   │   ├── market_data.py
│   │   ├── analytics_engine.py
│   │   ├── tax_harvesting.py
│   │   ├── rebalancer.py
│   │   └── llm_advisor.py
│   ├── ui/
│   │   └── app.py          # Streamlit dashboard (pre-React)
│   └── main.py             # FastAPI entrypoint
├── .env.example
├── requirements.txt
└── README.md               # This file
```

---

## ⚙️ Setup

### Prerequisites
- Python 3.10+
- Zerodha Developer Account & Kite Connect API credentials (optional — Demo Mode works without it)

### 1. Virtual environment

**Windows:**
```cmd
python -m venv .venv
.venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```ini
KITE_API_KEY=your_zerodha_api_key
KITE_API_SECRET=your_zerodha_api_secret
KITE_REDIRECT_URL=http://127.0.0.1:8000/api/v1/auth/callback
DEMO_MODE=true
GEMINI_API_KEY=your_gemini_api_key
REDIS_URL=redis://localhost:6379/0
```

### 4. Start Redis Cache (Docker)

Run Redis container using Docker Compose from the root directory:

```bash
docker compose up -d redis
```

Or via Docker CLI:
```bash
docker run -d --name portfolio_redis -p 6379:6379 -v redis_data:/data redis:7-alpine
```

See [Zerodha Setup Guide](../docs/guides/zerodha_api_setup_guide.md) for obtaining API credentials.

---

## 🚀 Running

### FastAPI server
```bash
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```
- Swagger UI: http://127.0.0.1:8000/docs

### Streamlit dashboard (pre-React)
```bash
streamlit run src/ui/app.py
```
- Dashboard: http://localhost:8501
