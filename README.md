# 📈 Portfolio Assistant (Zerodha Integrated)

An intelligent, AI-powered personal financial portfolio assistant for Zerodha Demat accounts. Automates holdings sync, sector exposure analysis, risk evaluation, and generates AI-driven buy/sell/hold recommendations with human-in-the-loop trade execution.

---

## 📄 Documentation

👉 **[Documentation Index](./docs/README.md)**

| Document | Description |
|---|---|
| [HLD](./docs/architecture/HLD.md) | System architecture, data flow diagrams, DB schema, security policies |
| [Architecture Review](./docs/architecture/ARCHITECTURE_REVIEW.md) | Design issues, gaps, and recommendations |
| [LLD Index](./docs/lld/00_INDEX.md) | Low-level design for all source files, phase by phase |
| [Zerodha Setup Guide](./docs/guides/zerodha_api_setup_guide.md) | Free vs paid API access, enctoken setup |
| [Gemini SDK Reference](./docs/api-references/Gemini_api_doc.md) | Google Gemini Python SDK integration guide |

---

## 🏗️ Monorepo Structure

```text
portfolio-assistant/
├── backend/          # FastAPI backend — Python 3.10+
├── frontend/         # React frontend — Next.js + Tailwind + Recharts
├── docs/             # Project-wide documentation
└── README.md         # This file
```

---

## 🚀 Running the Application

### Backend
See [backend/README.md](./backend/README.md) for full setup instructions.

```bash
cd backend
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend
See [frontend/README.md](./frontend/README.md) for full setup instructions.

```bash
cd frontend
npm install
npm run dev
```

- Backend API + Swagger UI: http://127.0.0.1:8000/docs
- Frontend: http://localhost:3000

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.10+, FastAPI, Uvicorn, Pydantic |
| Zerodha Integration | `kiteconnect` Official Python SDK (v3) |
| AI Advisory | Google Gemini API (`google-genai`) |
| Frontend | Next.js, Tailwind CSS, Recharts |
| Database | PostgreSQL + SQLAlchemy + Alembic |
| Cache | Redis |

---

## 🗺️ Roadmap

- [x] **Phase 1**: Zerodha OAuth 2.0 Authentication & Holdings Ingestion MVP
- [x] **Phase 2**: Fundamental Analytics (P/E, ROE), XIRR & Tax Harvesting (STCG/LTCG)
- [ ] **Phase 3**: AI Advisory Engine (Google Gemini — Buy/Sell/Hold recommendations)
- [ ] **Phase 4**: Order Staging Safety Queue & Telegram / Webhook Alerts
- [ ] **Phase 5**: React Frontend (Next.js + Tailwind + Recharts)
