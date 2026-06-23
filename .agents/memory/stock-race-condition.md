---
name: Stock race condition fix
description: How concurrent orders are prevented from overselling.
---

## Rule
All stock reads before order placement use SELECT ... FOR UPDATE OF p (locks product rows).
All stock decrements use: UPDATE products SET stock_quantity = stock_quantity - %s ... WHERE id = %s AND stock_quantity >= %s
If cursor.rowcount == 0 after the UPDATE, the transaction is rolled back immediately.

## Where
- routes/cart_routes.py — place_order() function
- routes/api_routes.py — api_place_order() function

**Why:** Without FOR UPDATE, two concurrent requests can both read stock=1, both pass the check, and both decrement — resulting in stock=-1.
