"""
Admin API service.
"""
from typing import Dict, Any, List, Optional
from services.api_client import api_client


async def get_stats() -> Dict[str, Any]:
    r = await api_client.get("/admin/stats")
    return r.get("data", {})


async def get_users(
    role_filter: Optional[str] = None, 
    status_filter: Optional[str] = None, 
    search: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
) -> Dict[str, Any]:
    params = {"page": page, "page_size": page_size}
    if role_filter and role_filter != "all":
        params["role_filter"] = role_filter
    if status_filter and status_filter != "all":
        params["status_filter"] = status_filter
    if search:
        params["search"] = search
    r = await api_client.get("/admin/users", params=params)
    return r.get("data", {"items": [], "total": 0, "page": 1, "page_size": 20})


async def update_user(user_id: int, user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Cập nhật thông tin người dùng (role, is_active, etc.)"""
    r = await api_client.put(f"/admin/users/{user_id}", data=user_data)
    return r.get("data", {})

async def get_user_detail(user_id: int) -> Dict[str, Any]:
    r = await api_client.get(f"/admin/users/{user_id}/detail")
    return r.get("data", {})


async def delete_user(user_id: int) -> bool:
    try:
        await api_client.delete(f"/admin/users/{user_id}")
        return True
    except Exception:
        return False


async def get_companies(
    status_filter: Optional[str] = None,
    verified_filter: Optional[str] = None,
    area: Optional[str] = None,
    search: Optional[str] = None,
) -> List[Dict[str, Any]]:
    params = {}
    if status_filter and status_filter != "all":
        params["status_filter"] = status_filter
    if verified_filter and verified_filter != "all":
        params["verified_filter"] = verified_filter
    if area and area != "all":
        params["area"] = area
    if search:
        params["search"] = search
    r = await api_client.get("/admin/companies", params=params)
    return r.get("data", [])


async def get_company_detail(company_id: int) -> Dict[str, Any]:
    r = await api_client.get(f"/admin/companies/{company_id}/detail")
    return r.get("data", {})


async def approve_company(company_id: int) -> Dict[str, Any]:
    r = await api_client.put(f"/admin/companies/{company_id}/approve")
    return r.get("data", {})


async def reject_company(company_id: int, reason: str) -> Dict[str, Any]:
    r = await api_client.put(f"/admin/companies/{company_id}/reject", data={"reason": reason})
    return r.get("data", {})


async def suspend_company(company_id: int, reason: str) -> Dict[str, Any]:
    r = await api_client.put(f"/admin/companies/{company_id}/suspend", data={"reason": reason})
    return r.get("data", {})


async def activate_company(company_id: int) -> Dict[str, Any]:
    r = await api_client.put(f"/admin/companies/{company_id}/activate")
    return r.get("data", {})


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


def _report_params(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    company_id: Optional[int] = None,
    incident_type: Optional[str] = None,
    status: Optional[str] = None,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {}
    if from_date:
        params["from_date"] = from_date
    if to_date:
        params["to_date"] = to_date
    if company_id:
        params["company_id"] = company_id
    if incident_type and incident_type != "all":
        params["incident_type"] = incident_type
    if status and status != "all":
        params["status"] = status
    return params


async def get_request_report(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    company_id: Optional[int] = None,
    incident_type: Optional[str] = None,
    status: Optional[str] = None,
) -> Dict[str, Any]:
    params = _report_params(from_date, to_date, company_id, incident_type, status)
    r = await api_client.get("/admin/reports/requests", params=params)
    return r.get("data", {})


async def get_revenue_report(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
) -> Dict[str, Any]:
    params = _report_params(from_date, to_date)
    r = await api_client.get("/admin/reports/revenue", params=params)
    return r.get("data", {})


async def get_satisfaction_report(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
) -> Dict[str, Any]:
    params = _report_params(from_date, to_date)
    r = await api_client.get("/admin/reports/satisfaction", params=params)
    return r.get("data", {})


async def export_excel(
    report_type: str,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    company_id: Optional[int] = None,
    incident_type: Optional[str] = None,
    status: Optional[str] = None,
) -> tuple[bytes, str]:
    params = _report_params(from_date, to_date, company_id, incident_type, status)
    params["report_type"] = report_type
    return await api_client.download("/admin/reports/export/excel", params=params)


async def export_pdf(
    report_type: str,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    company_id: Optional[int] = None,
    incident_type: Optional[str] = None,
    status: Optional[str] = None,
) -> tuple[bytes, str]:
    params = _report_params(from_date, to_date, company_id, incident_type, status)
    params["report_type"] = report_type
    return await api_client.download("/admin/reports/export/pdf", params=params)


async def get_daily_stats(days: int = 7) -> Dict[str, Any]:
    r = await api_client.get("/admin/stats/daily", params={"days": days})
    return r.get("data", {})


async def get_pending_companies() -> List[Dict[str, Any]]:
    r = await api_client.get("/admin/companies/pending")
    return r.get("data", [])


async def get_reviews(
    star_filter: Optional[str] = None,
    company_id: Optional[int] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    search: Optional[str] = None,
) -> List[Dict[str, Any]]:
    params = {}
    if star_filter and star_filter != "all":
        params["star_filter"] = int(star_filter)
    if company_id:
        params["company_id"] = company_id
    if from_date:
        params["from_date"] = from_date
    if to_date:
        params["to_date"] = to_date
    if search:
        params["search"] = search
    r = await api_client.get("/admin/reviews", params=params)
    return r.get("data", [])


async def delete_review(review_id: int, reason: str) -> Dict[str, Any]:
    return await api_client.delete(f"/admin/reviews/{review_id}", data={"reason": reason})


async def get_community_posts(
    status_filter: Optional[str] = None,
    incident_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    params = {}
    if status_filter and status_filter != "all":
        params["status_filter"] = status_filter
    if incident_type and incident_type != "all":
        params["incident_type"] = incident_type
    r = await api_client.get("/admin/community/posts", params=params)
    return r.get("data", [])


async def delete_community_post(post_id: int, reason: str) -> Dict[str, Any]:
    return await api_client.delete(f"/admin/community/posts/{post_id}", data={"reason": reason})
