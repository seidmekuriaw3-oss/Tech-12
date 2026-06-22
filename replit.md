# Ethiosadat Furniture Store

## Overview

A multi-language e-commerce platform for an Ethiopian furniture store (Wollo Dessie Kutaber). Features a customer storefront, admin dashboard, and WhatsApp integration. Supports Amharic, English, and Arabic.

## Stack

- **Backend**: Python 3.11 + Flask 2.3.3
- **Database**: PostgreSQL (via psycopg2-binary, Replit managed)
- **Frontend**: HTML/Jinja2 templates + vanilla JavaScript + CSS
- **Server**: Gunicorn (production), Flask dev server (development)
- **Auth**: Custom session-based (admin password + customer email/password)
- **Image processing**: Pillow
- **Rate limiting**: Flask-Limiter
- **Session**: Flask-Session + Flask-Caching

## Key Commands

- `python app.py` — run dev server on port 5000
- `python run.py --init-db` — initialize/reset database
- `python run.py --seed` — seed sample products and ads

## Environment Variables

Set via Replit Secrets/Env Vars panel:

- `SECRET_KEY` — Flask session signing key (already set)
- `DATABASE_URL` — PostgreSQL connection string (Replit managed)
- `ADMIN_PASSWORD` — Admin login password (default: `1234`, change for production)
- `WHATSAPP_NUMBER` — Store WhatsApp contact number
- `FREE_SHIPPING_THRESHOLD` — Minimum order for free shipping (default: 5000 ETB)
- `SHIPPING_COST` — Standard shipping cost (default: 200 ETB)

## User Preferences

- App runs on port 5000 in development
- Deployment uses Gunicorn on port 8080
