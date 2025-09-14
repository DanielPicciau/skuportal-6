import csv
import os
import threading
from pathlib import Path
from django.conf import settings
from .models import Variant

_lock = threading.Lock()
_timer = None
_DELAY_SEC = 1.0


def _csv_path() -> Path:
    # Store under MEDIA_ROOT/private so it is never collected as static
    base = Path(settings.MEDIA_ROOT) / 'private'
    base.mkdir(parents=True, exist_ok=True)
    return base / 'inventory.csv'


def write_csv_snapshot():
    """Write a full CSV snapshot of all variants atomically."""
    path = _csv_path()
    tmp_path = path.with_suffix('.csv.tmp')
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(tmp_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Main SKU','Variant SKU','Product Name','Brand','Category','Size','Condition','Colour',
            'Date','Cost','Price','Fees','Net','Profit','Margin','Qty','Location','Status'
        ])
        for v in Variant.objects.select_related('product').all():
            writer.writerow([
                v.product.main_sku,
                v.variant_sku,
                v.product.name,
                v.product.brand,
                v.product.category,
                v.size,
                v.condition,
                v.colour,
                v.date.strftime('%d/%m/%Y') if v.date else '',
                f"{v.cost:.2f}",
                f"{v.price:.2f}",
                f"{v.fees:.2f}",
                f"{v.net:.2f}",
                f"{v.profit:.2f}",
                f"{v.margin:.2f}%",
                v.qty,
                v.location,
                v.status,
            ])
    # Atomic replace
    os.replace(tmp_path, path)


def schedule_csv_sync():
    """Debounce CSV writes to avoid frequent disk I/O during bulk edits."""
    global _timer
    # Allow disabling in production via settings
    if not getattr(settings, 'CSV_SYNC_ENABLED', True):
        return
    with _lock:
        if _timer is not None:
            try:
                _timer.cancel()
            except Exception:
                pass
        _timer = threading.Timer(_DELAY_SEC, write_csv_snapshot)
        _timer.daemon = True
        _timer.start()
