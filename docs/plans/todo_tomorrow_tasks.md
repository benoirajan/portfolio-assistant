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
