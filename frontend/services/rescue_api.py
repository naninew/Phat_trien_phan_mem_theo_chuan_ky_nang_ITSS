"""
Rescue API service – gọi tất cả endpoints liên quan đến cứu hộ.
"""
from typing import Dict, Any, List, Optional
from services.api_client import api_client


# ── Services (loại dịch vụ) ──────────────────────────────────────────────────
async def get_services() -> List[Dict[str, Any]]:
    r = await api_client.get("/rescue/services")
    data = r.get("data")

    # DEBUG
    print("RAW RESPONSE:", r)
    print("DATA:", data)
    return r.get("data", [])


# ── Nearby companies ─────────────────────────────────────────────────────────
async def find_nearby_companies(
    latitude: float,
    longitude: float,
    service_ids: List[int],
    radius_km: float = 50.0,
) -> List[Dict[str, Any]]:

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "service_ids": service_ids,
        "radius_km": radius_km,
    }

    print("SEARCH PARAMS =", params)

    r = await api_client.get(
        "/rescue/companies/nearby",
        params=params,
    )

    print("RAW COMPANY RESPONSE =", r)

    return r.get("data", [])


# ── Requests – Customer ───────────────────────────────────────────────────────
async def create_rescue_request(
    service_id: int,
    vehicle_id: int,
    latitude: float,
    longitude: float,
    address_description: str,
    incident_type: str,
    description: str,
    company_id: Optional[int] = None,
    payment_method: str = "cash",
    images: Optional[List[str]] = None,
    #agreed_price = float,
) -> Dict[str, Any]:
    payload = {
        "service_ids": [service_id],
        "vehicle_id": vehicle_id,
        "latitude": latitude,
        "longitude": longitude,
        "address_description": address_description,
        "incident_type": incident_type,
        "description": description,
        "payment_method": payment_method,
        #"agreed_price" :agreed_price,
    }
    print("===== PAYLOAD =====")
    print(payload)
    if company_id:
        payload["company_id"] = company_id
    if images:
        payload["images"] = images
    r = await api_client.post("/rescue/requests", data=payload)
    print(r)
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
    staff_id: Optional[int] = None,
    total_cost: Optional[float] = None,
) -> Dict[str, Any]:
    params: Dict[str, Any] = {"eta_minutes": eta_minutes}
    if vehicle_id:
        params["vehicle_id"] = vehicle_id
    if staff_id:
        params["staff_id"] = staff_id
    if total_cost:
        params["total_cost"] = total_cost
        
    r = await api_client.put(f"/rescue/requests/{request_id}/accept", params=params)
    return r.get("data", {})


async def assign_request(request_id: int, staff_id: int, vehicle_id: int) -> Dict[str, Any]:
    payload = {
        "staff_id": staff_id,
        "rescue_vehicle_id": vehicle_id
    }
    r = await api_client.post(f"/rescue/requests/{request_id}/assign", data=payload)
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
        data={"plate_number": license_plate, "vehicle_type": vehicle_type, "capacity": capacity or None},
    )
    return r.get("data", {})

async def update_vehicle(vehicle_id: int, license_plate: str, vehicle_type: str, capacity: str = "") -> Dict[str, Any]:
    r = await api_client.put(
        f"/rescue/vehicles/{vehicle_id}",
        data={"plate_number": license_plate, "vehicle_type": vehicle_type, "capacity": capacity or None},
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

# ── Customer Vehicles – Personal cars ─────────────────────────────────────────
async def get_customer_vehicles() -> List[Dict[str, Any]]:
    r = await api_client.get("/rescue/customer/vehicles")
    return r.get("data", [])


async def add_customer_vehicle(data: Dict[str, Any]) -> Dict[str, Any]:
    r = await api_client.post("/rescue/customer/vehicles", data=data)
    return r.get("data", {})


async def update_customer_vehicle(vehicle_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    r = await api_client.put(f"/rescue/customer/vehicles/{vehicle_id}", data=data)
    return r.get("data", {})


async def delete_customer_vehicle(vehicle_id: int) -> bool:
    try:
        r = await api_client.delete(f"/rescue/customer/vehicles/{vehicle_id}")
        return r.get("success", False)
    except Exception:
        return False


# ── Company Staff & Resources ────────────────────────────────────────────────
async def get_company_staff() -> List[Dict[str, Any]]:
    r = await api_client.get("/rescue/staff")
    return r.get("data", [])

async def add_company_staff(skill_level: str) -> Dict[str, Any]:
    payload = {"skill_level": skill_level}
    r = await api_client.post("/rescue/staff", data=payload)
    return r.get("data", {})

async def update_company_staff(staff_id: int, skill_level: Optional[str] = None, status: Optional[str] = None) -> bool:
    payload = {}
    if skill_level: payload["skill_level"] = skill_level
    if status: payload["status"] = status
    r = await api_client.put(f"/rescue/staff/{staff_id}", data=payload)
    return r.get("success", False)

async def delete_company_staff(staff_id: int) -> bool:
    r = await api_client.delete(f"/rescue/staff/{staff_id}")
    return r.get("success", False)

async def get_company_services() -> List[Dict[str, Any]]:
    # Note: Backend might need a specific endpoint for company's own services with prices
    # For now, we list services then filter or use a more specific endpoint if exists.
    # Let's check backend/app/routes/rescue_routes.py:43 (create_service)
    # Actually, companies usually need to see their OWN services with prices.
    # Let's assume there's a list_company_services endpoint or we use get_company_full_details
    r = await api_client.get("/profile/company")
    return r.get("data", {}).get("services", [])

async def add_company_service(service_name: str, base_price: float) -> Dict[str, Any]:
    payload = {"service_name": service_name, "base_price": base_price}
    r = await api_client.post("/rescue/services", data=payload)
    return r.get("data", {})

async def update_company_service(service_id: int, base_price: float, is_active: bool = True) -> bool:
    payload = {"base_price": base_price, "is_active": is_active}
    r = await api_client.put(f"/rescue/services/{service_id}", data=payload)
    return r.get("success", False)

async def delete_company_service(service_id: int) -> bool:
    r = await api_client.delete(f"/rescue/services/{service_id}")
    return r.get("success", False)

async def get_company_reviews() -> List[Dict[str, Any]]:
    # Using the existing full-details endpoint but extracting reviews
    r = await api_client.get("/profile/company")
    return r.get("data", {}).get("reviews", [])

async def reject_request(request_id: int) -> bool:
    r = await api_client.put(f"/rescue/requests/{request_id}/reject")
    return r.get("success", False)


# ── Chat & Communication ───────────────────────────────────────────────────
async def get_chat_messages(request_id: int) -> List[Dict[str, Any]]:
    r = await api_client.get(f"/chat/{request_id}")
    return r.get("data", [])

async def send_chat_message(request_id: int, message: str) -> Dict[str, Any]:
    r = await api_client.post(f"/chat/{request_id}", params={"message": message})
    return r.get("data", {})
