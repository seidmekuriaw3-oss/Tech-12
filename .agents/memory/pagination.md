---
name: Pagination fix
description: /products route now uses real SQL pagination.
---

Fixed customer_routes.py products() to:
1. COUNT(*) from DB for real total
2. LIMIT %s OFFSET %s in the main query
3. math.ceil(total / per_page) for total_pages
4. page clamped to [1, total_pages]
per_page = 12 items per page.

**Why:** total_pages was hardcoded to 1; all products loaded into memory then sliced.
**How to apply:** Any new list route should follow same COUNT + LIMIT/OFFSET pattern.
