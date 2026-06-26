---
name: PostgreSQL only — always use %s
description: All database queries must target PostgreSQL using %s placeholders and ILIKE. Never use SQLite-style ? placeholders.
---

# PostgreSQL is the only database — always %s

The user explicitly confirmed: this project must always use PostgreSQL. Never SQLite.

**Rule:** Every SQL query parameter placeholder must be `%s` — never `?`.  
**Why:** The database driver is `psycopg2` (PostgreSQL). Using `?` causes a runtime error (`TypeError` or `ProgrammingError`). The `database/db.py` adapter has a translator but it is not guaranteed to catch all cases in all call paths.

**Search rule:** Use `ILIKE` instead of `LIKE` for case-insensitive search in PostgreSQL.

**How to apply:**
- Before writing any SQL with parameters, use `%s` everywhere.
- In `get_by_ids`-style queries: `','.join(['%s'] * len(ids))` — NOT `','.join('?' * len(ids))`.
- In UPDATE statements: `SET col=%s` — NOT `SET col=?`.
- Files already fixed: `services/product_service.py`, `seed_products.py`, `seed_ads.py`.
- If adding new services, follow the same pattern as `product_service.py` (already corrected).
