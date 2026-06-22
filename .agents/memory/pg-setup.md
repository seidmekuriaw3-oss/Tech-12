---
name: PostgreSQL-only DB setup
description: How the database layer is configured — always PostgreSQL, placeholder style.
---

All SQL in models.py uses %s placeholders (PostgreSQL native).
The _PsycopgCursor adapter in database/db.py still converts ? → %s as a safety net.
Routes (admin_routes, api_routes, customer_routes) use %s directly.
DATABASE_URL env var is Replit-managed; never SQLite.

**Why:** Project was mid-migration from SQLite; ? was SQLite style. Standardized to %s.
**How to apply:** Any new SQL written anywhere in the project must use %s, not ?.
