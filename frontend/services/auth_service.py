from typing import Dict, Any
from services.api_client import APIClient
from core.auth import login_user

class AuthService:
    """Authentication service to handle login and registration."""
    
    @staticmethod
    async def login(username: str, password: str) -> Dict[str, Any]:
        payload = {"username": username, "password": password}
        result = await APIClient.post("/auth/login", data=payload)
        
        if result["success"]:
            data = result["data"]
            login_user(
                token=data["access_token"],
                user_info=data["user"],
                role=data["user"]["role"]
            )
        return result

    @staticmethod
    async def register_customer(user_data: Dict[str, Any]) -> Dict[str, Any]:
        # Ensure role is set
        user_data["role"] = "customer"
        return await APIClient.post("/auth/register", data=user_data)

    @staticmethod
    async def register_company(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Expects data with 'user' and 'company' fields.
        """
        # Backend register endpoint handles both user and company if provided
        # or we might have a specific endpoint. Based on Sprint 1, it's /auth/register
        # and it accepts company_name etc. if role is company_staff.
        data["role"] = "company_staff"
        return await APIClient.post("/auth/register", data=data)
