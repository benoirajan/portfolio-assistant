# Action Items & TODO Tasks

> Historical completed tasks have been archived and documented in [Completed Tasks Archive](./completed_tasks.md).

## 📋 Active & Upcoming TODO Tasks

### 1. 💳 Integrate Live Razorpay Keys & Recurring Subscriptions (Priority: P1 - Monetization Follow-up)
* **Architectural Rationale:** Billing was implemented with `RAZORPAY_MOCK_MODE=true` (see [LLD 11](../lld/11_saas_monetization.md)). To take real payments, live Razorpay credentials must be provisioned and the `PricingModal.tsx` Razorpay checkout widget must be verified end-to-end.
* **Objective:** Switch from mock mode to live Razorpay payment processing.
* **Details:**
  * Create a Razorpay account at [dashboard.razorpay.com](https://dashboard.razorpay.com) and obtain `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET`.
  * Set `RAZORPAY_MOCK_MODE=false` in the production `.env` / deployment secrets.
  * Configure the Razorpay webhook URL (pointing to `POST /api/v1/billing/webhook`) in the Razorpay dashboard and set `RAZORPAY_WEBHOOK_SECRET`.
  * Test the full end-to-end payment flow with a Razorpay test card before going live.
  * Optionally migrate from one-time orders to Razorpay Subscriptions for UPI Autopay recurring billing.

---

### 2. 🔗 Multi-Broker Entitlement Support (Priority: P2 - Monetization)
* **Architectural Rationale:** `PRO` tier allows "multi-broker" connections. Currently only Zerodha is integrated. This task adds the entitlement check as a gating placeholder and implements support for a second broker.
* **Objective:** Allow PRO/ELITE users to connect more than one broker account.
* **Details:**
  * Add a `MAX_BROKER_CONNECTIONS` entitlement check in the broker session management logic (`backend/src/api/auth.py` `/broker/enctoken`).
  * FREE users: 1 broker connection. PRO/ELITE: unlimited.
  * Implement a second broker adapter (e.g., Angel One or Groww) as a concrete integration alongside the existing `zerodha_client.py`.
  * The `TIER_DEFINITIONS` list in `backend/src/api/billing.py` already shows "1 broker" for FREE — update once the second broker is implemented.

---

### 3. 📱 Mobile UI Responsiveness & Tab Fixes (Performance & Tax Tabs) (Priority: P2 - UI/UX)
* **Architectural Rationale:** The application layout currently renders for desktop screens and needs dedicated viewport adaptations for mobile phone viewports (< 640px). In addition, the **Performance** and **Tax** tabs contain functional, gating, and rendering issues:
  * **Performance Tab:** Brittle layout with hardcoded negative margins (`mt-[-2rem]`) causing text overlap in the Beta radial gauge; unguarded `.toFixed()` calls that can throw runtime errors on missing/null metrics; and lack of responsive chart scaling.
  * **Tax Tab:** `/api/v1/analytics/tax-harvesting` is gated behind the `PRO` tier (`require_tier("PRO")`). Free users receiving a 403 Forbidden currently see an unhandled empty/broken view instead of an informative upgrade banner; unguarded `.toLocaleString()` calls risk throwing errors on undefined values; and the harvestable loss table overflows on mobile viewports.
* **Objective:** Make all dashboard views mobile-responsive, fix rendering and calculation bugs in the Performance tab, and handle PRO gating and formatting safely in the Tax tab.
* **Details:**
  * **Mobile Navigation & Layout:**
    * Add a collapsible mobile drawer / slide-out hamburger navigation for [`Sidebar.tsx`](../frontend/components/layout/Sidebar.tsx) with a backdrop overlay.
    * Refactor [`KpiBar.tsx`](../frontend/components/kpi/KpiBar.tsx) cards into a responsive 2-column mobile grid or swipeable row.
    * Audit dialogs ([`AuthModal.tsx`](../frontend/components/auth/AuthModal.tsx), [`PricingModal.tsx`](../frontend/components/billing/PricingModal.tsx), [`ThemeToggle.tsx`](../frontend/components/layout/ThemeToggle.tsx)) to ensure zero clipping on screens under 380px.
  * **Performance Tab Fixes ([`PerformanceTab.tsx`](../frontend/components/tabs/PerformanceTab.tsx)):**
    * Replace brittle negative margin overlap in the RadialBar gauge with a responsive, centered SVG gauge or clean arc indicator that scales smoothly on mobile and desktop.
    * Add defensive null/undefined guards (`(metrics?.xirr_percentage ?? 0).toFixed(2)`, etc.) to prevent component crashes on initial or incomplete portfolio states.
    * Optimize valuation matrix and metric cards for single-column mobile viewports.
  * **Tax Tab Fixes ([`TaxTab.tsx`](../frontend/components/tabs/TaxTab.tsx)):**
    * Handle `PRO` tier gating gracefully: if user is on `FREE` tier or `/api/v1/analytics/tax-harvesting` returns 403, render an elegant locked feature card with sample preview and direct "Upgrade to Pro" trigger to [`PricingModal.tsx`](../frontend/components/billing/PricingModal.tsx).
    * Guard all currency and number fields against null/undefined (`(tax?.net_stcg ?? 0).toLocaleString(...)`).
    * Add responsive card / horizontal touch scroll for the harvestable loss candidate table on small screens.


---

### 4. 🌐 Public Marketing Landing Page & Product Showcase (Priority: P2 - Acquisition & UX)
* **Architectural Rationale:** The root route `/` (`frontend/app/page.tsx`) currently executes an immediate redirect to `/dashboard`, directly facing unauthenticated visitors with an "Authentication Required" lock screen. A dedicated, high-conversion landing page is needed to introduce the platform, showcase core value propositions (Multi-Stage Gemini AI Advisory, Zerodha sync, Tax Harvesting, Quantitative Analytics), present SaaS pricing tiers, and convert first-time visitors into registered users.
* **Objective:** Design and build a stunning, responsive landing page at `/` with compelling product visuals, feature sections, interactive pricing preview, and clear CTAs.
* **Details:**
  * Replace the unconditional redirect in [`frontend/app/page.tsx`](../frontend/app/page.tsx) with a full public marketing experience.
  * **Hero Section:** Value proposition ("Institutional-grade Indian equity portfolio analytics powered by multi-tenant AI"), dynamic animated badges, and dual primary CTAs ("Get Started Free", "Explore Dashboard").
  * **Feature Grid:** Highlight the 4 pillars:
    * 🤖 **3-Stage Gemini AI Advisory:** Diagnostic health checks, risk ranking, and staged execution baskets.
    * ⚖️ **Indian Tax-Loss Harvesting:** Real-time STCG/LTCG capital gains computation and tax-saving trade discovery before March 31st.
    * 🔒 **Encrypted Broker Integration:** Zero-friction Zerodha Kite & Enctoken synchronization with Fernet AES-256 encryption at rest.
    * 📊 **Institutional Quantitative Metrics:** Portfolio Beta, Sharpe/Sortino ratios, Herfindahl concentration index, and sector rebalancing.
  * **Interactive Product Preview:** Sleek mock dashboard UI / screenshot component showcasing the dashboard interface.
  * **Pricing & SaaS Tiers:** Display the Free, Pro (₹299/mo), and Elite (₹799/mo) plan tiers with a direct trigger to [`PricingModal.tsx`](../frontend/components/billing/PricingModal.tsx).
  * **Public Header & Footer:** Streamlined navbar with brand logo, [`ThemeToggle.tsx`](../frontend/components/layout/ThemeToggle.tsx), "Sign In" button, and footer with legal/security guarantees.
  * If the user is already authenticated, provide a seamless "Go to Dashboard" button or banner.



