"""
HTTP API client – singleton pattern với auto-inject token.
Tương thích với cả SQLite dev và PostgreSQL production.
"""
import httpx
from typing import Optional, Dict, Any, List
from nicegui import app as nicegui_app

from core.config import BACKEND_URL


class APIError(Exception):
    """Lỗi API với status code và message thân thiện."""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(message)


class APIClient:
    """
    Async HTTP client wrapper.
    - Singleton: tạo 1 lần, tái dùng connection pool
    - Auto-inject Bearer token từ NiceGUI session
    - Parse lỗi thành user-friendly message
    """

    def __init__(self, base_url: str = BACKEND_URL):
        self.base_url = base_url.rstrip("/")
        self._client: Optional[httpx.AsyncClient] = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    def _build_headers(self, token: Optional[str] = None) -> Dict[str, str]:
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        # Ưu tiên token truyền vào, sau đó lấy từ session
        _token = token
        if not _token:
            try:
                _token = nicegui_app.storage.user.get("access_token")
            except Exception:
                pass
        if _token:
            headers["Authorization"] = f"Bearer {_token}"
        return headers

    @staticmethod
    def _parse_error(exc: httpx.HTTPStatusError) -> APIError:
        try:
            body = exc.response.json()
            msg = body.get("detail") or body.get("message") or str(exc)
        except Exception:
            msg = f"Lỗi HTTP {exc.response.status_code}"
        return APIError(exc.response.status_code, str(msg))

    async def get(self, endpoint: str, params=None, token=None) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        try:
            r = await self._get_client().get(url, params=params, headers=self._build_headers(token))
            r.raise_for_status()
            return r.json()
        except httpx.HTTPStatusError as e:
            raise self._parse_error(e)

    async def post(self, endpoint: str, data=None, params=None, token=None) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        try:
            r = await self._get_client().post(url, json=data, params=params, headers=self._build_headers(token))
            r.raise_for_status()
            return r.json()
        except httpx.HTTPStatusError as e:
            raise self._parse_error(e)

    async def put(self, endpoint: str, data=None, params=None, token=None) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        try:
            r = await self._get_client().put(url, json=data, params=params, headers=self._build_headers(token))
            r.raise_for_status()
            return r.json()
        except httpx.HTTPStatusError as e:
            raise self._parse_error(e)

    async def delete(self, endpoint: str, token=None) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        try:
            r = await self._get_client().delete(url, headers=self._build_headers(token))
            r.raise_for_status()
            return r.json()
        except httpx.HTTPStatusError as e:
            raise self._parse_error(e)


# ── Singleton instance ────────────────────────────────────────────────────────
api_client = APIClient()
