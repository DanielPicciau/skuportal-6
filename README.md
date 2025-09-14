# SKU Portal (Django)

A gorgeous, fast Django app to log products, auto-generate SKUs, upload images, and import/export CSV/XLSX.

## Features
- **Main SKU** auto (001, 002, 003…) per product; **Variant SKU** like `HOOD-XL-001`.
- Beautiful Tailwind UI (via CDN) with drag-and-drop image uploads.
- Import **CSV/XLSX** and export CSV/XLSX.
- Simple analytics-ready fields (net, profit, margin auto-calculated).

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate  # on Windows use .venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py runserver
```

Open http://127.0.0.1:8000

## Import Format

Columns: `Main SKU (optional), Product Name, Brand, Category, Size, Condition, Colour, Date, Cost, Price, Fees, Qty, Location, Status`.

- Delimiters: auto-detects comma, tab, semicolon, or pipe.
- Header synonyms supported:
  - Product Name → Title, Name
  - Main SKU → Master SKU
  - Variant SKU → SKU Variant
  - Date → Purchase Date
  - Cost → Purchase Price, Buy Price
  - Price → Listed Price, Sale Price
  - Fees → Estimated Fees, Platform Fees
  - Qty → Quantity
  - Location → Location/Bin, Bin, Shelf

Dates accepted: `DD/MM/YYYY`, `YYYY-MM-DD`, `DD-MM-YYYY`.

## Configuration

- Fees: Defaults to Vinted — 5% + £0.70. Edit `inventory/constants.py` (`VINTED_FEE_PERCENT`, `VINTED_FIXED_FEE`). If a variant has `fees` left as 0, fees auto-calculate from these settings when saving.
- Lists: Edit `inventory/constants.py` to customize `CATEGORIES`, `CONDITIONS`, and `STATUSES`. Forms use these lists for dropdowns; stored values are plain text (no hard DB choices), so you can change lists anytime.

Dashboard filtering uses the `STATUSES` list; search supports product fields and both SKUs.

## Security & Deployment

- This is a Django server app. GitHub Pages is static-only and cannot run Django. To host securely:
  - Keep this repository private, or do not commit private data (CSV, DB).
  - Deploy the app to a server that supports Python (e.g., Fly.io, Render, Railway, Heroku, or a VPS) with HTTPS enabled.
  - Set environment variables in production:
    - `DEBUG=0`, `SECRET_KEY=<strong-random>`, `ALLOWED_HOSTS=<your-domain>`, `CSRF_TRUSTED_ORIGINS=https://your-domain`
    - `CSV_SYNC_ENABLED=0` to disable dev CSV snapshotting.
    - Optionally enable strict cookies / HSTS:
      `SECURE_SSL_REDIRECT=1`, `SESSION_COOKIE_SECURE=1`, `CSRF_COOKIE_SECURE=1`, `SECURE_HSTS_SECONDS=31536000`, `SECURE_HSTS_INCLUDE_SUBDOMAINS=1`, `SECURE_HSTS_PRELOAD=1`.

- CSV privacy:
  - In development, a CSV snapshot is written under `media/private/inventory.csv` (not collected as static).
  - The repository `.gitignore` excludes CSVs and `media/` so they are not published.
  - Exports are available only to authenticated users via the UI.

- If you want a static marketing site on GitHub Pages, you can keep a separate Pages repo and link to your deployed app (Render/Fly/etc.) for the authenticated interface.

## Media

Image uploads are stored in `media/`. In development, Django serves them automatically with `DEBUG=True`.
