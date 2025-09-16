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

- Environment variables: add a `.env` file in the project root (auto-loaded on startup) or export vars before running management commands.
- Fees: Defaults to Vinted — 5% + £0.70. Edit `inventory/constants.py` (`VINTED_FEE_PERCENT`, `VINTED_FIXED_FEE`). If a variant has `fees` left as 0, fees auto-calculate from these settings when saving.
- Lists: Edit `inventory/constants.py` to customize `CATEGORIES`, `CONDITIONS`, and `STATUSES`. Forms use these lists for dropdowns; stored values are plain text (no hard DB choices), so you can change lists anytime.

Dashboard filtering uses the `STATUSES` list; search supports product fields and both SKUs.

## eBay Browse API

Enable the optional eBay panel on the product form by setting these environment variables before starting Django. The app now auto-loads a root `.env` file, so you can drop the values there or export them in your shell:

```bash
export EBAY_ENABLED=1
export EBAY_ENV=sandbox  # or production when you go live
export EBAY_CLIENT_ID="<your-app-id>"
export EBAY_CLIENT_SECRET="<your-cert-id>"
export EBAY_MARKETPLACE_ID=EBAY_GB  # choose the marketplace you care about
export EBAY_SCOPE="https://api.ebay.com/oauth/api_scope/buy.browse.readonly"
```

Never commit raw credentials. The sandbox keys you generated in the eBay developer portal go into `EBAY_CLIENT_ID` and `EBAY_CLIENT_SECRET`. If you rotate the Cert ID, update the variable accordingly. When you are ready for production, create a production keyset in the eBay dashboard and switch `EBAY_ENV=production`.

The backend uses the client-credentials OAuth flow, so no user refresh token is required. The included `EbayClient` exchanges the App ID and Cert ID for an application access token and proxies Browse API searches through `/inventory/api/ebay/search`.

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

## Deploying on PythonAnywhere

1. Create a Python 3.12 virtualenv on PythonAnywhere and install the project:
   ```bash
   pip install --upgrade pip
   pip install -r /home/<username>/skuportal/requirements.txt
   ```
2. In the **Web** tab, point the working directory to `/home/<username>/skuportal` and use the existing `manage.py` as the project root.
3. Edit the WSGI configuration (via the **WSGI configuration file** link) so it loads the app:
   ```python
   import os
   import sys

   path = '/home/<username>/skuportal'
   if path not in sys.path:
       sys.path.append(path)

   os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'skuportal.settings')

   from django.core.wsgi import get_wsgi_application
   application = get_wsgi_application()
   ```
4. In the **Environment Variables** section of the web app settings add:
   ```text
   DJANGO_DEBUG=0
   DJANGO_SECRET_KEY=<generate-a-strong-secret>
   DJANGO_ALLOWED_HOSTS=<username>.pythonanywhere.com
   DJANGO_CSRF_TRUSTED_ORIGINS=https://<username>.pythonanywhere.com
   CSV_SYNC_ENABLED=0
   ```
   Include any additional custom domains on both `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS` (comma separated).
5. From a PythonAnywhere Bash console run:
   ```bash
   cd /home/<username>/skuportal
   python manage.py migrate
   python manage.py collectstatic --noinput
   ```
6. Back in the **Web** tab, reload the application. WhiteNoise serves collected static files automatically, so no extra static file mapping is required.

## Media

Image uploads are stored in `media/`. In development, Django serves them automatically with `DEBUG=True`.
- If you use `mise` to install Python and hit a `.tar.zst` extraction error, this repo ships a `.mise.toml` that forces compile mode so no `.zst` is needed. Run:

```bash
mise trust          # trust repo config
rm -rf ~/.local/share/mise/downloads/python/3.12.11 2>/dev/null || true
mise install        # compiles python 3.12 per .mise.toml
mise use -g python@3.12
```
- No mise? Use Docker (no system Python needed):

```bash
docker compose up --build
# open http://127.0.0.1:8000
```

The container runs migrations automatically and serves the app on port 8000.
