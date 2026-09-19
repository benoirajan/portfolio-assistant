---
name: zerodha-kite-integration
description: Guidelines, authentication workflows, enctoken session handling, and API specs for Zerodha Kite Connect integration.
---

# Zerodha Kite Integration Skill

This skill provides architectural guidelines and implementation patterns for integrating with Zerodha's Kite Connect API and managing web session fallbacks in the Portfolio Assistant.

---

## 1. Dual-Mode Authentication Architecture

The application supports two distinct authentication modes:

1. **Official Kite Connect API Mode (Paid - ₹2,000/mo)**
   - Requires `KITE_API_KEY` and `KITE_API_SECRET`.
   - Standard OAuth 2.0 flow: Redirect user to Zerodha login → Receive `request_token` at callback URL (`http://127.0.0.1:8000/api/v1/auth/callback`) → Exchange for `access_token`.

2. **Web Session Ingestion / Enctoken Mode (Personal / Free - ₹0/mo)**
   - Reads `ZERODHA_ENCTOKEN` from `.env` or request headers (`X-Enctoken`).
   - Token variable lookup order: `ZERODHA_ENCTOKEN` → `ENCTOKEN` → `KITE_ENCTOKEN`.
   - **Token Sanitization:** Must pass all raw inputs through `sanitize_token(raw_token)` to strip extraneous characters, quotes, or cookie headers (`enctoken=...`) copied from browser dev tools.

3. **Demo Mode (`DEMO_MODE=true`)**
   - Serves deterministic sample data (`DEMO_HOLDINGS`, `DEMO_MARGINS`) when no valid session token or API key is available.

---

## 2. Session Lifetime & Invalidation Rules

> [!IMPORTANT]
> Zerodha access tokens and web session `enctoken` strings expire **every morning at 06:00 AM IST** as mandated by Indian SEBI regulations. 

* **Error Handling:** When Zerodha returns `TokenException` or HTTP `403 Forbidden`, flag session as `EXPIRED`, log a warning, and fallback to `DEMO_MODE` or prompt the user for re-authentication.

---

## 3. Core API Endpoint Contracts

| Purpose | Zerodha API Route | Service Function | Key Data Extracted |
| :--- | :--- | :--- | :--- |
| **Holdings** | `GET /portfolio/holdings` | `zerodha_service.get_holdings()` | `tradingsymbol`, `isin`, `quantity`, `average_price`, `last_price`, `pnl` |
| **Positions** | `GET /portfolio/positions` | `zerodha_service.get_positions()` | `day_change`, `unrealised`, `realised`, `quantity` |
| **Margins** | `GET /user/margins` | `zerodha_service.get_margins()` | `equity.net`, `equity.available.cash`, `equity.utilized.debits` |

---

## 4. Retry & Circuit Breaker Policies

Refer to [LLD 05 — Retry & Fallback](file:///home/benoi/Projects/portfolio_assistant/docs/lld/05_retry_and_fallback.md#4-zerodha_clientpy--enctoken-request-retry):

* **Retryable Exceptions:** `NetworkException`, `requests.exceptions.ConnectionError`, HTTP `502`, `503`, `504`.
* **Non-Retryable Exceptions:** `TokenException` (403), `PermissionDeniedException` (401).
* **Exponential Backoff:** Base delay = `1.0s`, multiplier = `2.0`, max attempts = `3`.

---

## 5. References & Documentation Links

* [Zerodha Setup Guide](file:///home/benoi/Projects/portfolio_assistant/docs/guides/zerodha_api_setup_guide.md)
* [Phase 1 Low-Level Design](file:///home/benoi/Projects/portfolio_assistant/docs/lld/01_phase1_auth_and_holdings.md)
