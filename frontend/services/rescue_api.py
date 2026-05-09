"""
Rescue API service – gọi tất cả endpoints liên quan đến cứu hộ.
"""
from typing import Dict, Any, List, Optional
from services.api_client import api_client


# ── Services (loại dịch vụ) ──────────────────────────────────────────────────
async def get_services() -> List[Dict[str, Any]]:
    r = await api_client.get("/rescue/services")
    return r.get("data", [])


# ── Nearby companies ─────────────────────────────────────────────────────────
async def find_nearby_companies(
    latitude: float,
    longitude: float,
    service_name: str,
    radius_km: float = 50.0,
) -> List[Dict[str, Any]]:
    r = await api_client.get(
        "/rescue/companies/nearby",
        params={"latitude": latitude, "longitude": longitude, "service_name": service_name, "radius_km": radius_km},
    )
    return r.get("data", [])


# ── Requests – Customer ───────────────────────────────────────────────────────
async def create_rescue_request(
    service_id: int,
    latitude: float,
    longitude: float,
    address_description: str,
    car_issue_detail: str,
    company_id: Optional[int] = None,
    payment_method: str = "cash",
    images: Optional[List[str]] = None,
) -> Dict[str, Any]:
    payload = {
        "service_id": service_id,
        "latitude": latitude,
        "longitude": longitude,
        "address_description": address_description,
        "car_issue_detail": car_issue_detail,
        "payment_method": payment_method,
    }
    if company_id:
        payload["company_id"] = company_id
    if images:
        payload["images"] = images
    r = await api_client.post("/rescue/requests", data=payload)
    return r.get("data", {})


async def get_my_requests() -> List[Dict[str, Any]]:
    r = await api_client.get("/rescue/requests")
    return r.get("data", [])


async def get_request_detail(request_id: int) -> Optional[Dict[str, Any]]:
    try:
        r = await api_client.get(f"/rescue/requests/{request_id}")
        return r.get("data")
    except Exception:
        return None


async def cancel_request(request_id: int) -> Dict[str, Any]:
    r = await api_client.post(f"/rescue/requests/{request_id}/cancel")
    return r.get("data", {})


async def submit_review(request_id: int, rating: int, comment: str = "") -> Dict[str, Any]:
    r = await api_client.post(
        f"/rescue/requests/{request_id}/review",
        params={"rating": rating, "comment": comment},
    )
    return r.get("data", {})


# ── Queue – Company ───────────────────────────────────────────────────────────
async def get_company_queue(status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    params = {}
    if status_filter and status_filter != "all":
        params["status_filter"] = status_filter
    r = await api_client.get("/rescue/queue", params=params)
    return r.get("data", [])


async def accept_request(
    request_id: int,
    eta_minutes: int,
    vehicle_id: Optional[int] = None,
    total_cost: Optional[float] = None,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {"eta_minutes": eta_minutes}
    if vehicle_id:
        params["vehicle_id"] = vehicle_id
    if total_cost:
        params["total_cost"] = total_cost
    r = await api_client.post(f"/rescue/requests/{request_id}/accept", params=params)
    return r.get("data", {})


async def update_request_status(
    request_id: int,
    new_status: str,
    vehicle_id: Optional[int] = None,
    eta_minutes: Optional[int] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"status": new_status}
    if vehicle_id:
        payload["vehicle_id"] = vehicle_id
    if eta_minutes:
        payload["eta_minutes"] = eta_minutes
    r = await api_client.put(f"/rescue/requests/{request_id}/status", data=payload)
    return r.get("data", {})


# ── Vehicles – Company ────────────────────────────────────────────────────────
async def get_my_vehicles() -> List[Dict[str, Any]]:
    r = await api_client.get("/rescue/vehicles")
    return r.get("data", [])


async def add_vehicle(license_plate: str, vehicle_type: str, capacity: str = "") -> Dict[str, Any]:
    r = await api_client.post(
        "/rescue/vehicles",
        data={"license_plate": license_plate, "vehicle_type": vehicle_type, "capacity": capacity or None},
    )
    return r.get("data", {})


async def update_vehicle_status(vehicle_id: int, new_status: str) -> Dict[str, Any]:
    r = await api_client.put(f"/rescue/vehicles/{vehicle_id}/status", params={"new_status": new_status})
    return r.get("data", {})


async def delete_vehicle(vehicle_id: int) -> bool:
    try:
        await api_client.delete(f"/rescue/vehicles/{vehicle_id}")
        return True
    except Exception:
        return False

# ── Chat & Communication ───────────────────────────────────────────────────
async def get_chat_messages(request_id: int) -> List[Dict[str, Any]]:
    r = await api_client.get(f"/chat/{request_id}")
    return r.get("data", [])

async def send_chat_message(request_id: int, message: str) -> Dict[str, Any]:
    r = await api_client.post(f"/chat/{request_id}", params={"message": message})
    return r.get("data", {})
