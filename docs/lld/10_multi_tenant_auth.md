# LLD 10: Multi-Tenant Authentication, Identity (Google IAM), and Broker Credential Security

## 1. Overview
The Multi-Tenant Authentication system provides identity management, secure credential storage, and data isolation for the Portfolio Assistant SaaS application. It deprecates single-user development mode and enforces strict tenant boundaries across all portfolio ingestion, advisory, and analytics operations.

---

## 2. Key Architecture Components

```mermaid
graph TD
    Client[Next.js 16 Frontend / AuthContext] -->|Bearer JWT or ?token=| Gateway[FastAPI Gateway]
    Client -->|Google GIS Credential| GoogleAuth[POST /api/v1/auth/google]
    Client -->|Email + Password| EmailAuth[POST /api/v1/auth/login]
    
    Gateway --> SecurityDep[get_current_user Dependency]
    SecurityDep --> DB[(PostgreSQL / Supabase Pooler)]
    
    Gateway --> BrokerEndpoint[POST /api/v1/auth/broker/enctoken]
    BrokerEndpoint -->|AES-256 Fernet Encryption| SessionStore[(user_sessions Table)]
    
    Gateway --> ProtectedRoutes[/api/v1/holdings, /api/v1/advisory/*, /api/v1/analytics/*]
    ProtectedRoutes -->|In-Memory Decrypt| KiteClient[Zerodha Kite API Service]
```

### 2.1 Identity Providers & Authentication Flows
1. **Google Identity Services (GIS) / IAM ID Token (`POST /api/v1/auth/google`)**:
   - Accepts Google ID tokens issued by Google Identity Services on the Next.js client.
   - Cryptographically verifies token signatures and claims (`iss`, `sub`, `email`) using `google.oauth2.id_token.verify_oauth2_token`.
   - Provisions or retrieves the user in `public.users` and issues a signed HS256 JWT access token.
2. **Email & Password Authentication (`POST /api/v1/auth/register`, `POST /api/v1/auth/login`)**:
   - Salting & Hashing: Uses **PBKDF2-HMAC-SHA256** with a 16-byte cryptographically secure random salt and 100,000 iterations.
   - Passwords are never stored in plaintext.
3. **Session State & Profile (`GET /api/v1/auth/me`)**:
   - Returns current user profile (`id`, `email`, `tier`, `is_active`) and connected broker status.

---

## 3. Broker Credential Security & In-Memory Resolution

### 3.1 Encryption at Rest (Fernet AES-256)
- Broker session credentials (`enctoken` or OAuth `access_token`) are encrypted with server-side symmetric **AES-256 Fernet** keyed with `ENCRYPTION_SECRET_KEY`.
- Database storage table: `public.user_sessions`
  - `id`: Primary Key (UUID)
  - `user_id`: Foreign Key (`users.id`, `ON DELETE CASCADE`)
  - `token_hash`: SHA-256 fingerprint (used for safe cache indexing and diagnostics without exposing raw tokens)
  - `enctoken_encrypted`: Ciphertext string encrypted via Fernet
  - `created_at` / `updated_at`: Timestamps

### 3.2 Ephemeral In-Memory Resolution
- When an authenticated user requests `/api/v1/holdings` or `/api/v1/advisory/stream`:
  1. `get_current_user` extracts `current_user.id` from the decoded JWT payload.
  2. `get_user_enctoken(current_user.id)` queries `public.user_sessions` for that tenant.
  3. Decrypts the token in ephemeral process memory strictly for the duration of the external API request.
  4. The raw token is never written to log files (only sanitized hashes are logged).

---

## 4. Dual-Transport Authentication (`get_current_user`)

To support standard REST APIs as well as browser-native Server-Sent Events (`EventSource`) which cannot supply custom HTTP request headers, `get_current_user` supports dual-transport token verification:

1. **HTTP Authorization Header**: `Authorization: Bearer <token>` (Standard REST endpoints).
2. **Query Parameter**: `?token=<token>` (Server-Sent Events / SSE streams e.g. `/api/v1/advisory/stream`).

```python
def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    token: Optional[str] = Query(None, description="Optional JWT bearer token for SSE EventSource streams")
) -> User:
    raw_token = auth.credentials if (auth and auth.credentials) else token
    if not raw_token:
        raise HTTPException(status_code=401, detail="Authentication credentials were not provided")

    payload = decode_access_token(raw_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired authentication token")
    ...
```

---

## 5. API Endpoints Reference

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/v1/auth/google` | Google IAM ID Token verification & user provisioning | No |
| `POST` | `/api/v1/auth/register` | User registration with email/password | No |
| `POST` | `/api/v1/auth/login` | User login with email/password | No |
| `GET` | `/api/v1/auth/me` | Fetch authenticated profile & broker status | Yes (Bearer) |
| `POST` | `/api/v1/auth/broker/enctoken` | Save and AES-256 encrypt Zerodha enctoken | Yes (Bearer) |
| `GET` | `/api/v1/auth/broker/status` | Check if tenant has an active encrypted session | Yes (Bearer) |
| `DELETE` | `/api/v1/auth/broker/disconnect` | Revoke and delete stored broker session | Yes (Bearer) |
| `GET` | `/api/v1/advisory/stream` | Stream 3-Stage AI advisory pipeline in real-time | Yes (Bearer / Query) |
