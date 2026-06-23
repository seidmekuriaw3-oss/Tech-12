---
name: WhatsApp low-stock alert
description: How the low-stock alert is triggered and delivered after order placement.
---

## Rule
After every successful order, cart_routes.py and api_routes.py both query the just-ordered products for any whose stock_quantity <= low_stock_threshold (within the same DB transaction, before commit). If any found, send_low_stock_alert(products) is called.

## Where
- services/whatsapp_service.py — `send_low_stock_alert(products: list)` function
- Triggered in routes/cart_routes.py (place_order) and routes/api_routes.py (api_place_order)

## Behavior
- Always prints to server console (visible without CallMeBot)
- Sends WhatsApp only if CALLMEBOT_API_KEY env var is set
- Runs in a background daemon thread — never blocks the order response

**Why:** Store owner needs to restock before the next order; the alert fires at the earliest safe point (post-decrement, pre-commit read) to ensure accuracy.
