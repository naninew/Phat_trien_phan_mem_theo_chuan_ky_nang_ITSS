"""
Base API client for HTTP requests to backend.
"""
import httpx
from typing import Optional, Dict, Any, List
from frontend.core.config import BACKEND_URL


class APIClient:
    """Async HTTP client for backend API communication."""
    
    def __init__(self, base_url: str = BACKEND_URL):
        self.base_url = base_url
        self.timeout = 30.0
    
    async def _get_headers(self, token: Optional[str] = None) -> Dict[str, str]:
        """Get request headers with optional auth token."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers
    
    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Make GET request."""
        url = f"{self.base_url}{endpoint}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                url,
                params=params,
                headers=await self._get_headers(token),
            )
            response.raise_for_status()
            return response.json()
    
    async def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Make POST request."""
        url = f"{self.base_url}{endpoint}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url,
                json=data,
                headers=await self._get_headers(token),
            )
            response.raise_for_status()
            return response.json()
    
    async def put(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Make PUT request."""
        url = f"{self.base_url}{endpoint}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.put(
                url,
                json=data,
                headers=await self._get_headers(token),
            )
            response.raise_for_status()
            return response.json()
    
    async def delete(
        self,
        endpoint: str,
        token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Make DELETE request."""
        url = f"{self.base_url}{endpoint}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.delete(
                url,
                headers=await self._get_headers(token),
            )
            response.raise_for_status()
            return response.json()


# Global API client instance
api_client = APIClient()
