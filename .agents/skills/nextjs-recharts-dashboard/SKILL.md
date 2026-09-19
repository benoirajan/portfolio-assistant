---
name: nextjs-recharts-dashboard
description: Component patterns, TypeScript types, Axios client setups, and Recharts visualization standards for the Next.js 14 frontend.
---

# Next.js & Recharts Dashboard Skill

This skill governs frontend component architecture, state management, API integration, and data visualization for the React dashboard (`frontend/` directory).

---

## 1. Core Tech Stack & Structure

* **Framework:** Next.js 14 App Router (`frontend/app/`).
* **Styling:** Tailwind CSS + Radix UI / Lucide React icons.
* **Data Fetching & Caching:** `@tanstack/react-query` (React Query) + Axios.
* **Data Visualization:** `recharts`.

---

## 2. Single Source of Truth TypeScript Types (`frontend/lib/types.ts`)

All TypeScript interfaces map 1:1 with FastAPI Pydantic schemas:

| TypeScript Interface | Backend Schema | Description |
| :--- | :--- | :--- |
| `Holding` | `HoldingResponse` | Individual stock holding details |
| `PortfolioSummary` | `SummaryResponse` | Total value, total investment, P&L, day change |
| `PerformanceMetrics` | `PerformanceResponse` | XIRR, CAGR, Sharpe ratio, Beta |
| `TaxAnalysis` | `TaxHarvestingResponse` | STCG/LTCG breakdown & tax loss harvesting tips |
| `AdvisoryResponse` | `RecommendationResponse` | AI advice recommendations array & rationale |

---

## 3. Axios Client & Token Interceptor (`frontend/lib/api.ts`)

* **Base URL:** Resolved from `NEXT_PUBLIC_API_URL` (defaults to `http://127.0.0.1:8000`).
* **Session Interceptor:** Attach `X-Enctoken` from `localStorage` to outgoing requests automatically:
  ```typescript
  api.interceptors.request.use((config) => {
    const token = localStorage.getItem('enctoken');
    if (token) config.headers['X-Enctoken'] = token;
    return config;
  });
  ```

---

## 4. React Query Custom Hooks (`frontend/hooks/`)

All hooks enforce a `staleTime` of **5 minutes** (`5 * 60 * 1000`):

* `useHoldings()`: Fetches `/api/v1/holdings`.
* `usePerformance()`: Fetches `/api/v1/analytics/performance`.
* `useTax()`: Fetches `/api/v1/analytics/tax-harvesting`.
* `useAdvisory(goal, maxStock, maxSector)`: Fetches `/api/v1/advisory/recommendations`.

---

## 5. Recharts Visualization Standards

1. **Sector Allocation Donut Chart:**
   - Component: `<PieChart>` + `<Pie innerRadius={60} outerRadius={80}>`.
   - Colors: Use standard Tailwind palette (Indigo, Emerald, Amber, Rose, Cyan).
2. **Portfolio XIRR / Performance Chart:**
   - Component: `<AreaChart>` with gradient fill.
3. **Recommendation Cards:**
   - Format Buy/Sell/Hold badges with distinct Tailwind badges: `bg-emerald-100 text-emerald-800` (BUY), `bg-rose-100 text-rose-800` (SELL), `bg-amber-100 text-amber-800` (HOLD/TRIM).

---

## 6. References & Documentation Links

* [Phase 5 React Frontend LLD](file:///home/benoi/Projects/portfolio_assistant/docs/lld/07_phase5_react_frontend.md)
* [Phase 5 React Frontend Plan](file:///home/benoi/Projects/portfolio_assistant/docs/plans/phase_5_react_frontend.md)
