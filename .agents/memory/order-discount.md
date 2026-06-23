---
name: Order discount rate
description: Where the logged-in user discount rate lives and how to use it.
---

## Rule
USER_DISCOUNT_RATE = 0.10 is defined only in routes/shared.py.
All route files import it from there. Never hardcode 0.9 or 10% in route files.
Discounted price_at_time = round(price * (1 - USER_DISCOUNT_RATE), 2) for logged-in users.

**Why:** Changing the discount rate in one place (shared.py) propagates everywhere automatically.
