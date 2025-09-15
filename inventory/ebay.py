import time
from typing import Any, Dict, List, Optional, Tuple
try:
    import requests  # optional dependency; only needed if eBay is enabled
except Exception:  # pragma: no cover
    requests = None
from django.conf import settings


class EbayClient:
    """Minimal eBay Browse API client using application access token (client credentials)."""

    def __init__(self,
                 client_id: str,
                 client_secret: str,
                 marketplace_id: str = 'EBAY_GB',
                 env: str = 'production',
                 scope: str = 'https://api.ebay.com/oauth/api_scope/buy.browse.readonly',
                 timeout: int = 10):
        self.client_id = client_id
        self.client_secret = client_secret
        self.marketplace_id = marketplace_id
        self.env = env
        self.scope = scope
        self.timeout = timeout
        self._token: Optional[str] = None
        self._token_expiry: float = 0.0

    @property
    def base_oauth_url(self) -> str:
        return 'https://api.ebay.com/identity/v1/oauth2/token' if self.env == 'production' else 'https://api.sandbox.ebay.com/identity/v1/oauth2/token'

    @property
    def base_browse_url(self) -> str:
        return 'https://api.ebay.com/buy/browse/v1' if self.env == 'production' else 'https://api.sandbox.ebay.com/buy/browse/v1'

    def _ensure_token(self) -> str:
        if requests is None:
            raise RuntimeError('requests is not installed. Install it or disable eBay integration (EBAY_ENABLED=0).')
        now = time.time()
        if self._token and now < (self._token_expiry - 30):  # refresh a bit early
            return self._token

        data = {
            'grant_type': 'client_credentials',
            'scope': self.scope,
        }
        resp = requests.post(
            self.base_oauth_url,
            auth=(self.client_id, self.client_secret),
            data=data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=self.timeout,
        )
        resp.raise_for_status()
        tok = resp.json()
        self._token = tok['access_token']
        self._token_expiry = now + int(tok.get('expires_in', 7200))
        return self._token

    def search(self, q: str, limit: int = 10, filters: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        if requests is None:
            raise RuntimeError('requests is not installed. Install it or disable eBay integration (EBAY_ENABLED=0).')
        token = self._ensure_token()
        params: Dict[str, Any] = {'q': q, 'limit': max(1, min(limit, 50))}
        if filters:
            params.update(filters)
        url = f"{self.base_browse_url}/item_summary/search"
        resp = requests.get(
            url,
            params=params,
            headers={
                'Authorization': f'Bearer {token}',
                'X-EBAY-C-MARKETPLACE-ID': self.marketplace_id,
                'Accept-Language': 'en-GB',
            },
            timeout=self.timeout,
        )
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def summarize_prices(items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Return simple stats (count, avg, median) on item prices from Browse results."""
        import statistics
        prices: List[float] = []
        for it in items:
            p = (it.get('price') or {}).get('value')
            try:
                prices.append(float(p))
            except (TypeError, ValueError):
                continue
        if not prices:
            return {'count': 0, 'avg': None, 'median': None}
        return {
            'count': len(prices),
            'avg': round(sum(prices) / len(prices), 2),
            'median': round(statistics.median(prices), 2),
        }


def get_client() -> Optional[EbayClient]:
    if not getattr(settings, 'EBAY_ENABLED', False):
        return None
    if not settings.EBAY_CLIENT_ID or not settings.EBAY_CLIENT_SECRET:
        return None
    return EbayClient(
        client_id=settings.EBAY_CLIENT_ID,
        client_secret=settings.EBAY_CLIENT_SECRET,
        marketplace_id=settings.EBAY_MARKETPLACE_ID,
        env=settings.EBAY_ENV,
        scope=settings.EBAY_SCOPE,
        timeout=getattr(settings, 'EBAY_TIMEOUT', 10),
    )
