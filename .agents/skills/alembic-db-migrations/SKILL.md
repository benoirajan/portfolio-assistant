---
name: alembic-db-migrations
description: Workflow for PostgreSQL database migrations, SQLAlchemy ORM modeling, and Alembic revision management.
---

# Alembic Database Migrations Skill

This skill defines the database schema architecture, ORM standards, and migration workflows for PostgreSQL using SQLAlchemy 2.0 and Alembic.

---

## 1. Database Architecture & Core Tables

The application utilizes managed PostgreSQL (Supabase) as its primary persistent relational store:

| Table Name | Entity Description | Key Columns |
| :--- | :--- | :--- |
| `users` | User accounts & identity | `id` (UUID pk), `email`, `tier`, `created_at` |
| `portfolios` | User portfolio summary records | `id`, `user_id` (FK), `token_hash`, `total_investment`, `current_value` |
| `user_holdings` | Enriched stock holding snapshots | `id`, `portfolio_id` (FK cascade), `tradingsymbol`, `quantity`, `avg_price` |
| `user_sessions` | Auth session tokens | `id`, `user_id` (FK), `token_hash`, `expires_at` |
| `staged_orders` | Order staging queue (Phase 4) | `id`, `user_id`, `tradingsymbol`, `status`, `staged_at` |
| `subscriptions` | SaaS entitlement & billing (Phase 7) | `user_id`, `plan_type` (`FREE` | `PRO`), `razorpay_sub_id` |

---

## 2. Alembic Migration Workflow

All database DDL modifications must be executed via version-controlled Alembic migrations:

### Step 1: Modify SQLAlchemy Models (`backend/src/models/`)
Add or update table classes in `src/models/` inheriting from `Base` (`DeclarativeBase`). Ensure all models are exported in `src/models/__init__.py`.

### Step 2: Auto-Generate Migration Revision
Run the autogenerate command from the `backend/` directory:
```bash
cd backend
.venv/bin/alembic revision --autogenerate -m "add_staged_orders_table"
```

### Step 3: Inspect Migration Script (`backend/alembic/versions/`)
Inspect the generated script to ensure `upgrade()` and `downgrade()` functions accurately reflect the intended DDL changes.

### Step 4: Apply Migration
Apply changes to the Supabase / PostgreSQL database:
```bash
cd backend
.venv/bin/alembic upgrade head
```

---

## 3. Database Guidelines & Safety Rules

1. **Immutability of Applied Migrations:** NEVER alter or delete an existing migration file that has been merged and applied to staging or production. Create a new migration file instead.
2. **Explicit Foreign Key Constraints:** Always declare explicit `ondelete="CASCADE"` or `ondelete="SET NULL"` rules on foreign key references.
3. **Index High-Frequency Query Fields:** Place composite indexes on fields frequently used in filter clauses: `(token_hash)`, `(user_id, created_at)`, `(portfolio_id, tradingsymbol)`.
4. **Test-First Execution:** Always test migrations and model changes via `./run_dev.sh` or `python -m unittest tests/test_portfolio.py`.

---

## 4. References & Documentation Links

* [LLD 09: Database Persistence](file:///home/benoi/Projects/portfolio_assistant/docs/lld/09_database_persistence.md)
* [Hybrid Cloud Deployment Plan](file:///home/benoi/Projects/portfolio_assistant/docs/architecture/HYBRID_DEPLOYMENT_PLAN.md)
* [High-Level Architecture & DB Schema (HLD.md)](file:///home/benoi/Projects/portfolio_assistant/docs/architecture/HLD.md)
* [Phase 6 Multi-Tenant & Ingestion Plan](file:///home/benoi/Projects/portfolio_assistant/docs/plans/phase_6_multi_tenant_and_universal_ingestion.md)
