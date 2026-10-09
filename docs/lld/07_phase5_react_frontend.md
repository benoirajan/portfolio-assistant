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
- Wraps application tree in `ThemeProvider` (`next-themes`) supporting `light`, `dark`, and `system` preferences with `attribute="class"`
- Wraps all children in `QueryClientProvider` and `AuthProvider`
- Imports `globals.css` with CSS custom properties for both light and dark themes

---

## 5. `frontend/components/layout/Header.tsx` & `ThemeToggle.tsx`

- Calls `checkHealth()` on mount via `useEffect`
- Shows green "Online" or red "Offline" backend health pill
- Features `ThemeToggle.tsx`:
  - 3-mode theme switcher supporting Light, Dark, and System preference
  - Distinct icons for each mode: `Sun` (Light), `Moon` (Dark), `Monitor` (System)
  - Interactive dropdown menu with checkmark indicating active state
  - Automatically respects user OS preference when set to `system`
  - Zero hydration flash with `suppressHydrationWarning` and mounted state guard
- Displays AI Quota pill and tier badge with responsive styling
- Sign In modal trigger / Sign Out button with user avatar


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

**Visibility & Collapsibility:**
- **Unauthenticated State (`!isAuthenticated`):** The sidebar is completely hidden and omitted from the DOM when logged out. The authentication lock screen spans the full viewport width.
- **Collapsible Desktop Mode:** Supports collapse/expand toggling via `<PanelLeft />` button in `Header.tsx` or `<PanelLeftClose />` inside the sidebar header, smoothly expanding main dashboard content to 100% width when collapsed.
- **Mobile Drawer Mode:** Slide-out drawer with backdrop overlay triggered via mobile menu button.

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
- Pure responsive SVG semi-circle arc gauge (`BetaSvgGauge`):
  - Normalized ratio between 0.0 and 2.0 (1.0 = Nifty benchmark)
  - Color-coded: green < 0.85, yellow 0.85–1.15, red > 1.15
  - Replaced brittle negative margin (`mt-[-2rem]`) with centered SVG coordinate placement
- Valuation matrix: Weighted ROE, Herfindahl index (HHI), Risk classification, 10Y G-Sec benchmark
- Comprehensive defensive null/undefined guards across all `.toFixed()` and `.toLocaleString()` calls

---

## 11. `frontend/components/tabs/TaxTab.tsx`

- **PRO Tier Gating:**
  - Evaluates whether user tier is `FREE` or if the tax endpoint returns 403 Forbidden.
  - When gated, renders an informative locked preview card highlighting real-time STCG/LTCG computation, ₹1.25L exemption tracking, and March 31st loss harvesting trades with a direct trigger to `PricingModal.tsx`.
- **Unlocked View:**
  - Four metric cards: Net STCG (<1 yr at 20%), STCG tax, Net LTCG (>1 yr at 12.5%), LTCG tax
  - LTCG exemption progress bar (Section 112A ₹1,25,000 limit)
  - Harvestable loss candidates table with horizontal touch-scrolling support (`min-w-[500px]`)
  - All currency and numerical metrics defensively guarded against null/undefined values

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

### Basket sub-section (added)

Rendered below the recommendations list, only when `advisory.source` is present (i.e. recommendations loaded).

**Budget input:**
- Number input: "Max budget for buying (₹)" — local state, not sent to any hook until user clicks "Generate Basket"
- "Generate Basket" button triggers `useMutation` → `POST /api/v1/advisory/basket`
- Button is disabled when `recommendations` list is empty or budget ≤ 0

**Basket table** (shown after mutation succeeds):

| Column | Source |
|---|---|
| Action badge | `item.action` — same colour scheme as recommendation cards |
| Symbol | `item.symbol` |
| Quantity | `item.quantity` |
| Est. Value | `item.estimated_value` formatted as ₹ |
| Reason | `item.reason` (truncated, full text on hover via `title` attr) |

**Summary row** below table:
- Total buy: `total_buy_value`
- Total sell/trim proceeds: `total_sell_value`
- Budget used: `budget_utilised_pct`%

---

## 13. `frontend/app/dashboard/page.tsx` — Dashboard Page

Central orchestrator:
- Owns all sidebar state (mode, benchmark, caps, goal)
- Handles responsive drawer navigation: `isMobileNavOpen` controls slide-out `Sidebar` with backdrop overlay on mobile (<768px) and hamburger toggle in `Header`
- Receptors for PRO gating in `TaxTab` with shared `PricingModal`
- Horizontal touch-scrolling tab bar (`overflow-x-auto whitespace-nowrap`) preventing clipping on mobile screens
- Calls all 5 React Query hooks with defensive fallback objects

---

## 14. `frontend/app/page.tsx` — Public Marketing Landing Page

High-conversion public root route:
- **Hero Section:** Value proposition ("Institutional-grade Indian equity analytics powered by multi-stage AI"), live status badge, and dual CTAs ("Get Started Free", "Explore Live Dashboard").
- **Interactive Showcase (`#preview`):** Tabbed live demo switcher showcasing AI Advisory Diagnostic, Indian Tax Harvesting, Quantitative Beta vs Nifty 50, and Sector Allocation with active guardrails.
- **Architectural Pillars (`#features`):** 4 core feature cards highlighting 3-Stage Gemini Advisory, Indian Tax-Loss Harvesting, Encrypted Zerodha sync (Fernet AES-256), and Quantitative Ratios.
- **Pricing & SaaS Tiers (`#pricing`):** Three plan cards (Free ₹0, Pro ₹299/mo, Elite ₹799/mo) with direct triggers to `PricingModal.tsx` and `AuthModal.tsx`.
- **Interactive FAQ (`#faq`):** Accordion answering security, tax calculation, and advisory methodology questions.
- **Header & Footer:** Public navbar with `ThemeToggle.tsx`, auth-aware action buttons ("Go to Dashboard" when authenticated), and educational/regulatory compliance notices.

