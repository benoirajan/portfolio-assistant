# Implementation Plan — Phase 6: Multi-Tenant Architecture & Universal Ingestion

---

## 1. Overview & Objectives

Phase 6 evolves Portfolio Assistant from a single-user `enctoken` script into a multi-tenant platform accessible to **every trader**, regardless of their broker or API subscription level.

Key capabilities introduced:
1. **Universal Data Ingestion**: CAS (Consolidated Account Statement) PDF parser and Broker CSV uploaders so 100% of traders can import holdings for free.
2. **Multi-Broker API Adapters**: Abstract Strategy pattern supporting free broker APIs (**Dhan HQ**, **Angel One SmartAPI**, **Upstox API v2**) alongside Zerodha.
3. **Multi-Tenant Database & Identity**: PostgreSQL + SQLAlchemy database supporting user signups, JWT authentication, and encrypted token storage (`Fernet`).

---

## 2. Multi-Broker Butterfly Architecture

The system uses a **Butterfly Architecture** where diverse broker APIs and file imports feed into the multi-tenant core engine on the left wing, and process into analytical, AI, and monetization services on the right wing:

```mermaid
flowchart LR
    subgraph LEFT["Left Wing: Ingestion Sources"]
        direction TB
        L1["CAS PDF Import (CDSL/NSDL)"]
        L2["Broker CSV File Upload"]
        L3["Dhan HQ API (Free OAuth)"]
        L4["Angel One SmartAPI (Free TOTP)"]
        L5["Upstox API v2 (Free OAuth)"]
        L6["Zerodha Kite API / Session"]
    end

    subgraph CORE["Center Hub: Multi-Tenant Core"]
        direction TB
        C1["BaseBrokerClient Strategy Interface"]
        C2["JWT Auth & Security (Fernet AES-256)"]
        C3[("PostgreSQL DB (Users, Credentials, Holdings)")]
        C1 --> C2 --> C3
    end

    subgraph RIGHT["Right Wing: Platform Capabilities"]
        direction TB
        R1["Fundamental Analytics & Tax Engine"]
        R2["Google Gemini AI Advisory Engine"]
        R3["Portfolio Risk & Exposure Matrix"]
        R4["Next.js React Dashboard"]
    end

    LEFT --> CORE --> RIGHT
```

### Supported Ingestion Sources

| Source | Access Type | Cost to User | Key Features |
|---|---|---|---|
| **CAS PDF Parser** | File Upload (CDSL/NSDL) | ₹0 / Free | Universal support across all Indian brokers & depositories |
| **CSV Uploader** | File Upload (Zerodha/Groww) | ₹0 / Free | Instant offline portfolio ingestion |
| **Dhan HQ API** | Free REST API (OAuth) | ₹0 / Free | Real-time holdings, positions, and 1-click execution |
| **Angel One SmartAPI** | Free REST API (TOTP/OAuth) | ₹0 / Free | Real-time holdings and market data |
| **Upstox API v2** | Free REST API (OAuth) | ₹0 / Free | Real-time holdings sync |
| **Zerodha Kite Connect** | Paid API / Enctoken | ₹2,000/mo or Enctoken | Official REST API & legacy session fallback |

---

## 3. Database Schema Design (PostgreSQL)

```sql
-- Users Table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    tier VARCHAR(20) DEFAULT 'FREE', -- FREE, PRO, ELITE
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User Broker Accounts / Credentials
CREATE TABLE user_broker_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    broker_name VARCHAR(50) NOT NULL, -- ZERODHA, DHAN, ANGEL_ONE, UPSTOX, CAS_IMPORT
    encrypted_access_token TEXT,      -- Fernet AES-256 encrypted
    broker_user_id VARCHAR(100),
    is_primary BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User Holdings Cache
CREATE TABLE user_holdings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    tradingsymbol VARCHAR(100) NOT NULL,
    isin VARCHAR(50),
    quantity INT NOT NULL,
    average_price NUMERIC(12, 2) NOT NULL,
    last_price NUMERIC(12, 2),
    close_price NUMERIC(12, 2),
    source_broker VARCHAR(50),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

---

## 4. Universal Statement Parsers

### A. CAS (Consolidated Account Statement) PDF Parser
- Parses password-protected CDSL / NSDL PDF statements (`pypdf`, `pdfplumber`).
- Extracts equity holdings, ISINs, quantities, average cost prices, and folio numbers.

### B. Broker CSV Ingestion Engine
- Supports standardized CSV uploads from Zerodha Console, Groww, ICICIdirect, and Paytm Money.
- Auto-detects column headers (`Symbol`, `Qty`, `Buy Avg`, `ISIN`).

---

## 5. User Management, Database & Authentication Subsystem

### A. User Authentication Butterfly Flow

```mermaid
flowchart LR
    subgraph AUTH_INPUTS["Left Wing: Auth Ingestion & Identity"]
        direction TB
        I1["User Registration (Email & Password)"]
        I2["User Login (JWT Authentication)"]
        I3["Google OAuth / Social Login"]
        I4["JWT Refresh Token Endpoint"]
    end

    subgraph AUTH_CORE["Center Hub: Security & PostgreSQL DB"]
        direction TB
        C1["Password Hasher (passlib / bcrypt)"]
        C2["JWT Signer & Validator (PyJWT / JOSE)"]
        C3[("PostgreSQL DB: users & user_sessions")]
        C4[("Fernet Token Encrypter (AES-256)")]
        C1 --> C3
        C2 --> C3
    end

    subgraph AUTH_OUTPUTS["Right Wing: Multi-Tenant Protected Services"]
        direction TB
        O1["FastAPI get_current_user Dependency"]
        O2["User-Scoped Holdings Isolation"]
        O3["Entitlements Middleware (Tier Checks)"]
        O4["Next.js AuthContext & Axios Interceptors"]
    end

    AUTH_INPUTS --> AUTH_CORE --> AUTH_OUTPUTS
```

---

### B. Comprehensive User Database Schema (PostgreSQL)

```sql
-- Core User Table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    tier VARCHAR(20) DEFAULT 'FREE', -- FREE, PRO, ELITE
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Active User Refresh Sessions (For Secure Token Rotation)
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    refresh_token_hash VARCHAR(255) NOT NULL,
    user_agent TEXT,
    ip_address VARCHAR(50),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Encrypted Broker API Credentials per User
CREATE TABLE user_broker_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    broker_name VARCHAR(50) NOT NULL, -- ZERODHA, DHAN, ANGEL_ONE, UPSTOX, CAS_IMPORT
    encrypted_access_token TEXT,      -- Fernet AES-256 encrypted
    broker_user_id VARCHAR(100),
    is_primary BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User-Scoped Holdings Table
CREATE TABLE user_holdings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    tradingsymbol VARCHAR(100) NOT NULL,
    isin VARCHAR(50),
    quantity INT NOT NULL,
    average_price NUMERIC(12, 2) NOT NULL,
    last_price NUMERIC(12, 2),
    close_price NUMERIC(12, 2),
    source_broker VARCHAR(50),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

---

### C. Authentication Endpoints & Identity Provider Architecture (Supabase + Google Auth)

The system leverages **Supabase** as the hosted PostgreSQL Database & Auth Engine combined with **Google Cloud** as the external Identity Provider:

```mermaid
flowchart LR
    subgraph IDP["Left Wing: Google Identity Provider"]
        direction TB
        G1["User Clicks 'Sign in with Google'"]
        G2["Google OAuth 2.0 Consent Screen"]
        G3["Issues Google ID Token & Profile"]
        G1 --> G2 --> G3
    end

    subgraph SUPABASE_CORE["Center Hub: Supabase DB & Auth Engine"]
        direction TB
        S1["Supabase Auth Service"]
        S2[("Supabase PostgreSQL DB (auth.users)")]
        S3["Row Level Security (RLS) & JWT Signer"]
        S1 --> S2 --> S3
    end

    subgraph APP_SERVICES["Right Wing: FastAPI & Next.js Context"]
        direction TB
        A1["FastAPI PyJWT / Supabase Token Validator"]
        A2["User-Isolated Broker Credentials & Holdings"]
        A3["Entitlements Middleware Tier Checks"]
        A4["Next.js @supabase/supabase-js Auth Hook"]
    end

    IDP --> SUPABASE_CORE --> APP_SERVICES
```

1. **Configuration Steps**:
   - Register OAuth 2.0 Client ID & Secret in **Google Cloud Console**.
   - Enter Google Client ID & Secret in **Supabase Dashboard -> Authentication -> Providers -> Google**.
2. **Frontend Ingestion**:
   - Next.js uses `@supabase/supabase-js` `supabase.auth.signInWithOAuth({ provider: 'google' })`.
3. **Backend Validation**:
   - FastAPI inspects Supabase Bearer JWTs using Supabase's JWKS public keys.

---

### D. Frontend Auth State Management (Next.js & Supabase)

- **`@supabase/auth-helpers-nextjs`**: Handles session persistence, server-side rendering (SSR) user checks, and automatic token refresh.
- **Axios Interceptor**: Injects `Authorization: Bearer <supabase_access_token>` into every request to FastAPI.
- **`ProtectedRoute.tsx`**: Redirects non-authenticated sessions to `/login`.

