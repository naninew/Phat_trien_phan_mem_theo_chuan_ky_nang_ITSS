"""
Admin API service.
"""
from typing import Dict, Any, List, Optional
from services.api_client import api_client


async def get_stats() -> Dict[str, Any]:
    r = await api_client.get("/admin/stats")
    return r.get("data", {})


async def get_users(role_filter: Optional[str] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
    params = {}
    if role_filter and role_filter != "all":
        params["role_filter"] = role_filter
    if search:
        params["search"] = search
    r = await api_client.get("/admin/users", params=params)
    return r.get("data", [])


async def update_user(user_id: int, user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Cập nhật thông tin người dùng (role, is_active, etc.)"""
    r = await api_client.put(f"/admin/users/{user_id}", data=user_data)
    return r.get("data", {})


async def delete_user(user_id: int) -> bool:
    try:
        await api_client.delete(f"/admin/users/{user_id}")
        return True
    except Exception:
        return False


async def get_companies(status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    params = {}
    if status_filter and status_filter != "all":
        params["status_filter"] = status_filter
    r = await api_client.get("/admin/companies", params=params)
    return r.get("data", [])


async def update_company_status(company_id: int, status: str) -> Dict[str, Any]:
    """Cập nhật trạng thái công ty (active, suspended, etc.)"""
    r = await api_client.put(f"/admin/companies/{company_id}/status", params={"status": status})
    return r.get("data", {})

async def get_all_requests() -> List[Dict[str, Any]]:
    r = await api_client.get("/admin/requests")
    return r.get("data", [])


async def get_chart_stats() -> Dict[str, Any]:
    r = await api_client.get("/admin/stats/charts")
    return r.get("data", {})


async def get_export_data() -> List[Dict[str, Any]]:
    r = await api_client.get("/admin/reports/export")
    return r.get("data", [])


async def get_reviews() -> List[Dict[str, Any]]:
    r = await api_client.get("/admin/reviews")
    return r.get("data", [])


async def delete_review(review_id: int) -> bool:
    try:
        await api_client.delete(f"/admin/reviews/{review_id}")
        return True
    except Exception:
        return False


async def get_community_posts() -> List[Dict[str, Any]]:
    r = await api_client.get("/admin/community/posts")
    return r.get("data", [])


async def delete_community_post(post_id: int) -> bool:
    try:
        await api_client.delete(f"/admin/community/posts/{post_id}")
        return True
    except Exception:
        return False
