import httpx
from typing import Optional, Dict, Any, Union
from core.config import BACKEND_URL, SESSION_TOKEN_KEY
from nicegui import app, ui

class APIClient:
    """Helper class to make requests to the backend API."""
    
    @staticmethod
    def get_headers() -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        token = app.storage.user.get(SESSION_TOKEN_KEY)
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    @staticmethod
    async def get(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{BACKEND_URL}{endpoint}",
                    params=params,
                    headers=APIClient.get_headers()
                )
                return APIClient._handle_response(response)
            except Exception as e:
                return {"success": False, "message": str(e)}

    @staticmethod
    async def post(endpoint: str, data: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{BACKEND_URL}{endpoint}",
                    json=data,
                    params=params,
                    headers=APIClient.get_headers()
                )
                return APIClient._handle_response(response)
            except Exception as e:
                return {"success": False, "message": str(e)}

    @staticmethod
    async def put(endpoint: str, data: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.put(
                    f"{BACKEND_URL}{endpoint}",
                    json=data,
                    params=params,
                    headers=APIClient.get_headers()
                )
                return APIClient._handle_response(response)
            except Exception as e:
                return {"success": False, "message": str(e)}

    @staticmethod
    async def delete(endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.delete(
                    f"{BACKEND_URL}{endpoint}",
                    params=params,
                    headers=APIClient.get_headers()
                )
                return APIClient._handle_response(response)
            except Exception as e:
                return {"success": False, "message": str(e)}

    @staticmethod
    def _handle_response(response: httpx.Response) -> Dict[str, Any]:
        try:
            res_data = response.json()
            if response.status_code == 401:
                # Token expired or invalid
                app.storage.user.clear()
                ui.navigate.to("/login")
                return {"success": False, "message": "Session expired. Please login again."}
            
            if 200 <= response.status_code < 300:
                return {"success": True, "data": res_data.get("data"), "message": res_data.get("message")}
            else:
                return {"success": False, "message": res_data.get("detail") or "An error occurred"}
        except Exception:
            return {"success": False, "message": f"Server error: {response.status_code}"}

# Create a singleton instance
api_client = APIClient()
