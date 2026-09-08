# Low-Level Design — Phase 5: React Frontend

---

## 1. `frontend/lib/types.ts` — TypeScript Type Definitions

Single source of truth for all API response shapes. All types are derived directly from FastAPI response models.

### Key types

| Type | Maps to |
|---|---|
| `Holding` | `/api/v1/holdings` → `holdings[]` item |
| `PortfolioSummary` | `/api/v1/holdings` → `summary` |
| `HoldingsResponse` | Full `/api/v1/holdings` response |
| `PerformanceMetrics` | `/api/v1/analytics/performance` → `metrics` |
| `TaxAnalysis` | `/api/v1/analytics/tax-harvesting` → `tax_analysis` |
| `MarginsResponse` | `/api/v1/margins` |
| `AdvisoryResponse` | `/api/v1/advisory/recommendations` |
| `ConnectionMode` | `'demo' \| 'enctoken' \| 'kite'` |

---

## 2. `frontend/lib/api.ts` — Axios Client & API Functions

Single Axios instance with base URL from `NEXT_PUBLIC_API_URL` (default `http://127.0.0.1:8000`).

### Interceptor
Request interceptor reads `enctoken` from `localStorage` and injects it as `X-Enctoken` header on every outgoing request.

### Exported functions

| Function | Method | Endpoint |
|---|---|---|
| `fetchHoldings` | GET | `/api/v1/holdings` |
| `fetchPerformance` | GET | `/api/v1/analytics/performance` |
| `fetchTax` | GET | `/api/v1/analytics/tax-harvesting` |
| `fetchMargins` | GET | `/api/v1/margins` |
| `fetchAdvisory(goal, maxStock, maxSector)` | GET | `/api/v1/advisory/recommendations` |
| `fetchLoginUrl` | GET | `/api/v1/auth/login-url` |
| `checkHealth` | GET | `/health` |

---

## 3. `frontend/hooks/usePortfolio.ts` — React Query Hooks

All hooks use `staleTime: 5 * 60 * 1000` (5 minutes) matching the previous `@st.cache_data(ttl="5m")` behaviour.

| Hook | Query key | Fetcher |
|---|---|---|
| `useHoldings` | `['holdings']` | `fetchHoldings` |
| `usePerformance` | `['performance']` | `fetchPerformance` |
| `useTax` | `['tax']` | `fetchTax` |
| `useMargins` | `['margins']` | `fetchMargins` |
| `useAdvisory(goal, maxStock, maxSector)` | `['advisory', goal, maxStock, maxSector]` | `fetchAdvisory` |

---

## 4. `frontend/app/layout.tsx` — Root Layout

- Marked `'use client'` to allow `useState` for `QueryClient` instantiation
- Wraps all children in `QueryClientProvider`
- Imports `globals.css` with CSS custom properties for the dark theme

---

## 5. `frontend/components/layout/Header.tsx`

- Calls `checkHealth()` on mount via `useEffect`
- Shows green "Backend online" or red "Backend offline — run uvicorn" status indicator
- No props — self-contained

---

## 6. `frontend/components/layout/Sidebar.tsx`

Three connection modes toggled via a segmented button:

| Mode | Behaviour |
|---|---|
| Demo | No token — backend uses `DEMO_MODE=true` data |
| Enctoken | Password input → `localStorage.setItem('enctoken', ...)` → page reload |
| Kite API | Fetches login URL from backend, opens Zerodha OAuth in new tab |

Also contains:
- Benchmark selector (NIFTY 50 / NIFTY 500 / SENSEX)
- Max sector cap slider (10–40%, default 25%)
- Investment goal selector
- Max single stock cap slider (5–40%, default 15%)

All values are lifted to `dashboard/page.tsx` via props.

---

## 7. `frontend/components/kpi/KpiBar.tsx`

Six metric cards in a flex-wrap row:

| Card | Source |
|---|---|
| Total invested | `summary.total_investment` |
| Current value | `summary.current_value` |
| Overall P&L | `summary.total_pnl` + `total_pnl_percentage` delta |
| Portfolio XIRR | `metrics.xirr_percentage` |
| Portfolio Beta | `metrics.portfolio_beta` |
| Risk profile | `metrics.risk_profile_tag` |

P&L card uses green/red colouring based on sign.

---

## 8. `frontend/components/tabs/HoldingsTab.tsx`

- Symbol search (case-insensitive `includes`)
- Multi-sector filter via toggle buttons
- Computed columns: `invested_value`, `current_value`, `pnl`, `pnl_percentage`, `weight_pct`
- Table with green/red P&L colouring
- All computation done in `useMemo` — no re-renders on unrelated state changes

---

## 9. `frontend/components/tabs/SectorTab.tsx`

Three Recharts charts:

| Chart | Type | Data |
|---|---|---|
| Sector allocation | `PieChart` (donut) | Grouped `current_value` by `sector` |
| Market cap distribution | `BarChart` | Grouped `current_value` by `cap_category` |
| Single stock concentration | `BarChart` | `weight_pct` per symbol with `ReferenceLine` at `maxSectorCap` |

---

## 10. `frontend/components/tabs/PerformanceTab.tsx`

- Four metric cards: XIRR, Sharpe, Sortino, Weighted P/E
- Beta gauge via `RadialBarChart` — colour-coded: green < 0.85, yellow 0.85–1.15, red > 1.15
- Valuation matrix: Weighted ROE, Herfindahl index, Risk classification

---

## 11. `frontend/components/tabs/TaxTab.tsx`

- Four metric cards: Net STCG, STCG tax, Net LTCG, LTCG tax
- LTCG exemption progress bar (₹1.25 lakh limit) — turns red when limit exceeded
- Harvestable loss candidates table (hidden when empty)

---

## 12. `frontend/components/tabs/AdvisoryTab.tsx`

- Source badge: LLM provider name (green) or "Rule-based" fallback (muted)
- Rule engine alerts list with severity colouring (HIGH=red, MEDIUM=yellow, LOW=muted)
- Recommendation cards (`RecCard`) — collapsible with action badge, confidence bar, rationale

Action badge colours:

| Action | Style |
|---|---|
| BUY | Green |
| HOLD | Blue |
| TRIM | Yellow |
| SELL | Red |

---

## 13. `frontend/app/dashboard/page.tsx` — Dashboard Page

Central orchestrator:
- Owns all sidebar state (mode, benchmark, caps, goal)
- Calls all 5 React Query hooks
- Provides empty fallback objects to prevent null-check cascades in child components
- Renders `Header`, `Sidebar`, `KpiBar`, tab bar, and active tab content
- Tab switching is local state — no URL routing needed for MVP
