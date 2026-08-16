# Project Rules for Toarps Herrklubb

## Development Server
- Always run the Django development server on **port 1981**
- Start command: `./venv/bin/python manage.py runserver` (or `./venv/bin/python manage.py runserver 1981`)
- Access at: http://127.0.0.1:1981 (or https:// in HTTPS-enabled environments)

## HTTPS Security Standards
- Project enforces HTTPS standards (`SECURE_PROXY_SSL_HEADER`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_HSTS_SECONDS`, `SECURE_REFERRER_POLICY`) for encrypted transport.


## Git & Deployment Rules
- Always ask or wait for instruction before committing or updating the server!
- Production server: `johansiedberg@192.168.86.35`

