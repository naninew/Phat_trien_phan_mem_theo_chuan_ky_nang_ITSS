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
    async def patch(endpoint: str, data: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.patch(
                    f"{BACKEND_URL}{endpoint}",
                    json=data,
                    params=params,
                    headers=APIClient.get_headers()
                )
                return APIClient._handle_response(response)
            except Exception as e:
                return {"success": False, "message": str(e)}

    @staticmethod
    async def delete(
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    "DELETE",
                    f"{BACKEND_URL}{endpoint}",
                    params=params,
                    json=data,
                    headers=APIClient.get_headers()
                )
                return APIClient._handle_response(response)
            except Exception as e:
                return {"success": False, "message": str(e)}

    @staticmethod
    async def download(endpoint: str, params: Optional[Dict[str, Any]] = None) -> tuple[bytes, str]:
        """Tải file binary (Excel/PDF) từ backend."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{BACKEND_URL}{endpoint}",
                params=params,
                headers=APIClient.get_headers(),
            )
            if response.status_code == 401:
                app.storage.user.clear()
                ui.navigate.to("/login")
                raise RuntimeError("Session expired. Please login again.")
            if response.status_code >= 400:
                detail = "Không thể tải file"
                try:
                    detail = response.json().get("detail", detail)
                except Exception:
                    pass
                raise RuntimeError(detail)
            filename = "bao_cao.bin"
            cd = response.headers.get("content-disposition", "")
            if "filename=" in cd:
                filename = cd.split("filename=")[-1].strip('"')
            return response.content, filename

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
                return {"success": False, "message": APIClient._format_error_message(res_data.get("detail"))}
        except Exception:
            return {"success": False, "message": f"Server error: {response.status_code}"}

    @staticmethod
    def _format_error_message(detail: Any) -> str:
        if not detail:
            return "Đã xảy ra lỗi"
        if isinstance(detail, str):
            translations = {
                "Username already registered": "Tên đăng nhập đã được sử dụng",
                "Email already registered": "Email đã được sử dụng",
                "Invalid phone number format": "Số điện thoại chưa đúng định dạng",
            }
            return translations.get(detail, detail)
        if isinstance(detail, list):
            messages = []
            for item in detail:
                if not isinstance(item, dict):
                    messages.append(str(item))
                    continue
                field = item.get("loc", [""])[-1]
                msg = item.get("msg") or item.get("message") or "Dữ liệu không hợp lệ"
                field_labels = {
                    "username": "Tên đăng nhập",
                    "password": "Mật khẩu",
                    "full_name": "Họ và tên",
                    "phone": "Số điện thoại",
                    "email": "Email",
                    "role": "Vai trò",
                }
                msg_translations = {
                    "String should have at least 10 characters": "phải có ít nhất 10 ký tự",
                    "String should have at least 6 characters": "phải có ít nhất 6 ký tự",
                    "ensure this value has at least 10 characters": "phải có ít nhất 10 ký tự",
                    "ensure this value has at least 6 characters": "phải có ít nhất 6 ký tự",
                    "value is not a valid email address": "chưa đúng định dạng",
                    "Invalid phone number format": "chưa đúng định dạng",
                }
                label = field_labels.get(field, str(field))
                message = msg_translations.get(str(msg), str(msg))
                messages.append(f"{label} {message}")
            return "; ".join(messages)
        if isinstance(detail, dict):
            return str(detail.get("message") or detail.get("msg") or detail)
        return str(detail)

# Create a singleton instance
api_client = APIClient()
