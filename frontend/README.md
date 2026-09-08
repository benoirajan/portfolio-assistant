# Frontend — Portfolio Assistant

Next.js 14 (App Router) React frontend for the Portfolio Assistant. Consumes the FastAPI backend REST API.

---

## Stack

- **Next.js 14** — App Router, TypeScript
- **Tailwind CSS** — styling
- **Recharts** — charts (sector pie, cap bar, beta gauge, concentration bar)
- **React Query** — data fetching & caching
- **Axios** — HTTP client with `X-Enctoken` interceptor

---

## Setup

```bash
cp .env.local.example .env.local
npm install
npm run dev
```

Frontend: http://localhost:3000  
Backend must be running at http://127.0.0.1:8000 — see [backend/README.md](../backend/README.md)

---

## Structure

```text
frontend/
├── app/
│   ├── layout.tsx              # Root layout — QueryClientProvider
│   ├── page.tsx                # Redirects → /dashboard
│   └── dashboard/page.tsx      # Main dashboard
├── components/
│   ├── layout/                 # Header, Sidebar
│   ├── kpi/                    # KpiBar (6 metric cards)
│   └── tabs/                   # HoldingsTab, SectorTab, PerformanceTab, TaxTab, AdvisoryTab
├── hooks/
│   └── usePortfolio.ts         # React Query hooks
├── lib/
│   ├── api.ts                  # Axios instance + API functions
│   └── types.ts                # TypeScript types for all backend responses
└── .env.local.example
```

---

## Environment

| Variable | Default | Description |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://127.0.0.1:8000` | FastAPI backend base URL |
