"""
Rescue service API for requests, companies, and vehicles.
"""
from typing import Dict, Any, List, Optional
from .api_client import api_client


async def find_nearby_companies(
    latitude: float,
    longitude: float,
    service_id: int,
    radius_km: float = 50.0,
) -> List[Dict[str, Any]]:
    """
    Find nearby rescue companies.
    
    Args:
        latitude: User's latitude
        longitude: User's longitude
        service_id: Required service ID
        radius_km: Search radius in kilometers
    
    Returns:
        List of company information
    """
    response = await api_client.get(
        "/rescue/companies/nearby",
        params={
            "latitude": latitude,
            "longitude": longitude,
            "service_id": service_id,
            "radius_km": radius_km,
        },
    )
    return response.get("data", [])


async def create_rescue_request(
    service_id: int,
    latitude: float,
    longitude: float,
    address_description: str,
    car_issue_detail: str,
    images: Optional[List[str]] = None,
    payment_method: str = "cash",
    token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a new rescue request.
    
    Args:
        service_id: ID of required service
        latitude: User's latitude
        longitude: User's longitude
        address_description: Location description
        car_issue_detail: Vehicle issue details
        images: Optional list of image URLs
        payment_method: Payment method
        token: Access token
    
    Returns:
        Created request information
    """
    data = {
        "service_id": service_id,
        "latitude": latitude,
        "longitude": longitude,
        "address_description": address_description,
        "car_issue_detail": car_issue_detail,
        "payment_method": payment_method,
    }
    if images:
        data["images"] = images
    
    response = await api_client.post(
        "/rescue/requests",
        data=data,
        token=token,
    )
    return response.get("data", {})


async def get_my_requests(token: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get current user's rescue requests.
    
    Args:
        token: Access token
    
    Returns:
        List of rescue requests
    """
    response = await api_client.get("/rescue/requests", token=token)
    return response.get("data", [])


async def get_request_details(
    request_id: int,
    token: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Get details of a specific rescue request.
    
    Args:
        request_id: Request ID
        token: Access token
    
    Returns:
        Request details or None
    """
    try:
        response = await api_client.get(
            f"/rescue/requests/{request_id}",
            token=token,
        )
        return response.get("data")
    except Exception:
        return None


async def update_request_status(
    request_id: int,
    status: str,
    vehicle_id: Optional[int] = None,
    eta_minutes: Optional[int] = None,
    token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Update the status of a rescue request.
    
    Args:
        request_id: Request ID
        status: New status
        vehicle_id: Optional vehicle ID
        eta_minutes: Optional ETA in minutes
        token: Access token
    
    Returns:
        Updated request information
    """
    data = {"status": status}
    if vehicle_id is not None:
        data["vehicle_id"] = vehicle_id
    if eta_minutes is not None:
        data["eta_minutes"] = eta_minutes
    
    response = await api_client.put(
        f"/rescue/requests/{request_id}/status",
        data=data,
        token=token,
    )
    return response.get("data", {})


async def cancel_request(
    request_id: int,
    token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Cancel a pending rescue request.
    
    Args:
        request_id: Request ID
        token: Access token
    
    Returns:
        Cancellation result
    """
    response = await api_client.post(
        f"/rescue/requests/{request_id}/cancel",
        token=token,
    )
    return response.get("data", {})


async def create_service(
    company_id: int,
    service_name: str,
    base_price: float,
    description: Optional[str] = None,
    token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a new service for a company.
    
    Args:
        company_id: Company ID
        service_name: Service name
        base_price: Base price
        description: Service description
        token: Access token
    
    Returns:
        Created service information
    """
    response = await api_client.post(
        "/rescue/services",
        data={
            "company_id": company_id,
            "service_name": service_name,
            "base_price": base_price,
            "description": description,
        },
        token=token,
    )
    return response.get("data", {})


async def create_vehicle(
    company_id: int,
    license_plate: str,
    vehicle_type: str,
    capacity: Optional[str] = None,
    token: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a new vehicle for a company.
    
    Args:
        company_id: Company ID
        license_plate: License plate
        vehicle_type: Vehicle type
        capacity: Capacity description
        token: Access token
    
    Returns:
        Created vehicle information
    """
    response = await api_client.post(
        "/rescue/vehicles",
        data={
            "company_id": company_id,
            "license_plate": license_plate,
            "vehicle_type": vehicle_type,
            "capacity": capacity,
        },
        token=token,
    )
    return response.get("data", {})


async def get_company_vehicles(
    company_id: int,
    token: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Get all vehicles for a company.
    
    Args:
        company_id: Company ID
        token: Access token
    
    Returns:
        List of vehicles
    """
    response = await api_client.get(
        f"/rescue/companies/{company_id}/vehicles",
        token=token,
    )
    return response.get("data", [])
