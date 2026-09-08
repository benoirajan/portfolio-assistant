# Implementation Plan — Phase 5: React Frontend

---

## 1. Overview & Objectives

Phase 5 migrates the UI from Streamlit to a production-grade React frontend built with **Next.js 14 (App Router)**, **Tailwind CSS**, and **Recharts**. The FastAPI backend is consumed unchanged via its existing REST API. The Streamlit `src/ui/app.py` is retained but no longer the primary UI.

---

## 2. Tech Stack

| Concern | Choice | Reason |
|---|---|---|
| Framework | Next.js 14 App Router | SSR-ready, file-based routing, React Server Components |
| Styling | Tailwind CSS | No external component lib — full control, minimal bundle |
| Charts | Recharts | Composable, React-native, replaces Plotly |
| Data fetching | `@tanstack/react-query` | Caching, stale-time, loading/error states — replaces `@st.cache_data` |
| HTTP client | Axios | Interceptor-based `X-Enctoken` header injection |
| Icons | `lucide-react` | Lightweight, tree-shakeable |

---

## 3. Folder Structure

```text
frontend/
├── app/
│   ├── layout.tsx              # Root layout — QueryClientProvider
│   ├── page.tsx                # Redirects to /dashboard
│   └── dashboard/
│       └── page.tsx            # Main dashboard page
├── components/
│   ├── layout/
│   │   ├── Header.tsx          # Title + backend health status
│   │   └── Sidebar.tsx         # Connection mode, risk & AI settings
│   ├── kpi/
│   │   └── KpiBar.tsx          # 6 metric cards
│   └── tabs/
│       ├── HoldingsTab.tsx     # Holdings table with search & sector filter
│       ├── SectorTab.tsx       # Sector pie + cap bar + concentration bar
│       ├── PerformanceTab.tsx  # Beta gauge + valuation matrix
│       ├── TaxTab.tsx          # STCG/LTCG + exemption progress + candidates
│       └── AdvisoryTab.tsx     # Rule flags + recommendation cards
├── hooks/
│   └── usePortfolio.ts         # React Query hooks for all 5 endpoints
├── lib/
│   ├── api.ts                  # Axios instance + all API call functions
│   └── types.ts                # TypeScript types for all backend responses
└── .env.local.example
```

---

## 4. API Endpoints Consumed

| Hook | Endpoint | Stale time |
|---|---|---|
| `useHoldings` | `GET /api/v1/holdings` | 5 min |
| `usePerformance` | `GET /api/v1/analytics/performance` | 5 min |
| `useTax` | `GET /api/v1/analytics/tax-harvesting` | 5 min |
| `useMargins` | `GET /api/v1/margins` | 5 min |
| `useAdvisory` | `GET /api/v1/advisory/recommendations` | 5 min |

---

## 5. Auth / Token Flow

- **Demo mode**: no token needed — backend returns demo data when `DEMO_MODE=true`
- **Enctoken mode**: user pastes enctoken into sidebar → saved to `localStorage` → injected as `X-Enctoken` header via Axios interceptor on every request
- **Kite API mode**: "Login with Zerodha" button opens the Kite OAuth URL fetched from `GET /api/v1/auth/login-url`

---

## 6. Streamlit → React Mapping

| Streamlit | React |
|---|---|
| `st.sidebar` | `Sidebar.tsx` |
| `st.tabs` | Tab state in `dashboard/page.tsx` |
| `@st.cache_data(ttl="5m")` | React Query `staleTime: 5 * 60 * 1000` |
| `st.metric` | `KpiBar.tsx` cards |
| `px.pie` / `px.bar` | Recharts `PieChart` / `BarChart` |
| `go.Indicator` (beta gauge) | Recharts `RadialBarChart` |
| `st.dataframe` | HTML table with Tailwind |
| `st.progress` | Tailwind div with dynamic width |
| `st.expander` | Toggle state in `RecCard` |

---

## 7. Running

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Frontend: http://localhost:3000  
Backend must be running at http://127.0.0.1:8000
