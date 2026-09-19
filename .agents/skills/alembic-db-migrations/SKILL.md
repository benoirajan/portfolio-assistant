---
name: alembic-db-migrations
description: Workflow for PostgreSQL database migrations, SQLAlchemy ORM modeling, and Alembic revision management.
---

# Alembic Database Migrations Skill

This skill defines the database schema architecture, ORM standards, and migration workflows for PostgreSQL using SQLAlchemy 2.0 and Alembic.

---

## 1. Database Architecture & Core Tables

The application utilizes PostgreSQL as its primary persistent relational store:

| Table Name | Entity Description | Key Columns |
| :--- | :--- | :--- |
| `users` | User accounts (Phase 6) | `id` (UUID), `email`, `created_at` |
| `sessions` | Auth session tokens | `user_id`, `enctoken`, `expires_at` |
| `holdings_history` | Historical daily portfolio snaps | `user_id`, `snapshot_date`, `holdings_json` |
| `transactions` | Historical buy/sell trade logs | `user_id`, `tradingsymbol`, `quantity`, `price`, `traded_at` |
| `staged_orders` | Order staging queue (Phase 4) | `id`, `user_id`, `tradingsymbol`, `status`, `staged_at` |
| `subscriptions` | SaaS entitlement & billing (Phase 7) | `user_id`, `plan_type` (`FREE` \| `PRO`), `razorpay_sub_id` |

---

## 2. Alembic Migration Workflow

All database DDL modifications must be executed via version-controlled Alembic migrations:

### Step 1: Modify SQLAlchemy Models (`backend/src/models/`)
Add or update table classes in `src/models/` inheriting from `DeclarativeBase`.

### Step 2: Auto-Generate Migration Revision
Run the autogenerate command from the `backend/` directory:
```bash
cd backend
alembic revision --autogenerate -m "add_staged_orders_table"
```

### Step 3: Inspect Migration Script (`backend/alembic/versions/`)
Inspect the generated script to ensure `upgrade()` and `downgrade()` functions accurately reflect the intended DDL changes.

### Step 4: Apply Migration
Apply changes to the local/staging PostgreSQL database:
```bash
alembic upgrade head
```

---

## 3. Database Guidelines & Safety Rules

1. **Immutability of Applied Migrations:** NEVER alter or delete an existing migration file that has been merged and applied to staging or production. Create a new migration file instead.
2. **Explicit Foreign Key Constraints:** Always declare explicit `ondelete="CASCADE"` or `ondelete="SET NULL"` rules on foreign key references.
3. **Index High-Frequency Query Fields:** Place composite indexes on fields frequently used in filter clauses: `(user_id, snapshot_date)`, `(user_id, tradingsymbol)`.

---

## 4. References & Documentation Links

* [High-Level Architecture & DB Schema (HLD.md)](file:///home/benoi/Projects/portfolio_assistant/docs/architecture/HLD.md)
* [Phase 6 Multi-Tenant & Ingestion Plan](file:///home/benoi/Projects/portfolio_assistant/docs/plans/phase_6_multi_tenant_and_universal_ingestion.md)
* [Phase 7 Monetization & SaaS Plan](file:///home/benoi/Projects/portfolio_assistant/docs/plans/phase_7_monetization_and_saas.md)
