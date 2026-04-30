"""
Rescue service business logic for requests, companies, and vehicles.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Tuple
from datetime import datetime
import math

from ..models.request import RescueRequest, RequestStatus
from ..models.company import RescueCompany
from ..models.service import Service
from ..models.vehicle import RescueVehicle
from ..schemas.rescue import RescueRequestCreate, ServiceCreate, VehicleCreate


# Earth radius in kilometers
EARTH_RADIUS_KM = 6371.0


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth using Haversine formula.
    
    Args:
        lat1, lon1: Coordinates of point 1 (in degrees)
        lat2, lon2: Coordinates of point 2 (in degrees)
    
    Returns:
        Distance in kilometers
    """
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    # Haversine formula
    a = math.sin(delta_lat / 2) ** 2 + \
        math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return EARTH_RADIUS_KM * c


def find_nearby_companies(
    db: Session,
    latitude: float,
    longitude: float,
    service_id: int,
    radius_km: float = 50.0
) -> List[Tuple[RescueCompany, float, List[Service]]]:
    """
    Find rescue companies near a location that offer a specific service.
    
    Args:
        db: Database session
        latitude: User's latitude
        longitude: User's longitude
        service_id: Required service ID
        radius_km: Search radius in kilometers
    
    Returns:
        List of tuples (Company, distance_km, services)
    """
    # Get all active companies
    companies = db.query(RescueCompany).filter(
        RescueCompany.status == "active",
        RescueCompany.is_verified == True
    ).all()
    
    results = []
    for company in companies:
        # Calculate distance (in production, use PostGIS for better performance)
        # For now, we assume company location is stored in address or need to add lat/lng fields
        # This is a simplified version - you would need company coordinates in real implementation
        distance = 5.0  # Placeholder - would calculate from company's actual coordinates
        
        if distance <= radius_km:
            # Check if company offers the required service
            services = db.query(Service).filter(
                Service.company_id == company.id,
                Service.is_active == True
            ).all()
            
            if any(s.id == service_id for s in services):
                results.append((company, distance, services))
    
    # Sort by distance
    results.sort(key=lambda x: x[1])
    
    return results


def create_rescue_request(
    db: Session,
    user_id: int,
    request_data: RescueRequestCreate
) -> RescueRequest:
    """
    Create a new rescue request.
    
    Args:
        db: Database session
        user_id: ID of the user creating the request
        request_data: Rescue request data
    
    Returns:
        Created RescueRequest object
    """
    db_request = RescueRequest(
        user_id=user_id,
        service_id=request_data.service_id,
        latitude=request_data.latitude,
        longitude=request_data.longitude,
        address_description=request_data.address_description,
        car_issue_detail=request_data.car_issue_detail,
        images=request_data.images if request_data.images else [],
        status=RequestStatus.PENDING,
        payment_method=request_data.payment_method
    )
    
    db.add(db_request)
    db.commit()
    db.refresh(db_request)
    
    return db_request


def get_request_by_id(db: Session, request_id: int) -> Optional[RescueRequest]:
    """
    Get a rescue request by ID.
    
    Args:
        db: Database session
        request_id: Request ID
    
    Returns:
        RescueRequest object if found, None otherwise
    """
    return db.query(RescueRequest).filter(RescueRequest.id == request_id).first()


def get_user_requests(db: Session, user_id: int) -> List[RescueRequest]:
    """
    Get all rescue requests for a user.
    
    Args:
        db: Database session
        user_id: User ID
    
    Returns:
        List of RescueRequest objects
    """
    return db.query(RescueRequest).filter(
        RescueRequest.user_id == user_id
    ).order_by(RescueRequest.created_at.desc()).all()


def update_request_status(
    db: Session,
    request_id: int,
    status: str,
    vehicle_id: Optional[int] = None,
    eta_minutes: Optional[int] = None
) -> Optional[RescueRequest]:
    """
    Update the status of a rescue request.
    
    Args:
        db: Database session
        request_id: Request ID
        status: New status
        vehicle_id: Optional vehicle ID to assign
        eta_minutes: Optional ETA in minutes
    
    Returns:
        Updated RescueRequest object if found, None otherwise
    """
    request = get_request_by_id(db, request_id)
    if not request:
        return None
    
    request.status = status
    
    if vehicle_id is not None:
        request.vehicle_id = vehicle_id
    
    if eta_minutes is not None:
        request.eta_minutes = eta_minutes
    
    if status == RequestStatus.ON_SITE:
        request.actual_arrival_time = datetime.utcnow()
    elif status == RequestStatus.COMPLETED:
        request.actual_completion_time = datetime.utcnow()
    
    db.commit()
    db.refresh(request)
    
    return request


def cancel_request(db: Session, request_id: int) -> Optional[RescueRequest]:
    """
    Cancel a rescue request (only if pending).
    
    Args:
        db: Database session
        request_id: Request ID
    
    Returns:
        Updated RescueRequest object if successful, None otherwise
    """
    request = get_request_by_id(db, request_id)
    if not request or request.status != RequestStatus.PENDING:
        return None
    
    request.status = RequestStatus.CANCELLED
    db.commit()
    db.refresh(request)
    
    return request


def create_service(
    db: Session,
    company_id: int,
    service_data: ServiceCreate
) -> Service:
    """
    Create a new service for a company.
    
    Args:
        db: Database session
        company_id: Company ID
        service_data: Service creation data
    
    Returns:
        Created Service object
    """
    db_service = Service(
        service_name=service_data.service_name,
        base_price=service_data.base_price,
        description=service_data.description,
        company_id=company_id,
        is_active=True
    )
    
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    
    return db_service


def create_vehicle(
    db: Session,
    company_id: int,
    vehicle_data: VehicleCreate
) -> RescueVehicle:
    """
    Create a new vehicle for a company.
    
    Args:
        db: Database session
        company_id: Company ID
        vehicle_data: Vehicle creation data
    
    Returns:
        Created RescueVehicle object
    """
    db_vehicle = RescueVehicle(
        license_plate=vehicle_data.license_plate,
        vehicle_type=vehicle_data.vehicle_type,
        capacity=vehicle_data.capacity,
        company_id=company_id,
        status="available"
    )
    
    db.add(db_vehicle)
    db.commit()
    db.refresh(db_vehicle)
    
    return db_vehicle


def get_company_vehicles(db: Session, company_id: int) -> List[RescueVehicle]:
    """
    Get all vehicles for a company.
    
    Args:
        db: Database session
        company_id: Company ID
    
    Returns:
        List of RescueVehicle objects
    """
    return db.query(RescueVehicle).filter(
        RescueVehicle.company_id == company_id
    ).all()


def update_vehicle_status(
    db: Session,
    vehicle_id: int,
    status: str
) -> Optional[RescueVehicle]:
    """
    Update vehicle status.
    
    Args:
        db: Database session
        vehicle_id: Vehicle ID
        status: New status
    
    Returns:
        Updated RescueVehicle object if found, None otherwise
    """
    vehicle = db.query(RescueVehicle).filter(RescueVehicle.id == vehicle_id).first()
    if not vehicle:
        return None
    
    vehicle.status = status
    db.commit()
    db.refresh(vehicle)
    
    return vehicle


def estimate_price(base_price: float, distance_km: float) -> float:
    """
    Estimate total price based on base price and distance.
    
    Args:
        base_price: Base service price
        distance_km: Distance in kilometers
    
    Returns:
        Estimated total price
    """
    # Price per km (example: 10,000 VND per km)
    price_per_km = 10000.0
    return base_price + (distance_km * price_per_km)


def estimate_eta(distance_km: float, avg_speed_kmh: float = 40.0) -> int:
    """
    Estimate time of arrival in minutes.
    
    Args:
        distance_km: Distance in kilometers
        avg_speed_kmh: Average speed in km/h
    
    Returns:
        Estimated minutes until arrival
    """
    return int((distance_km / avg_speed_kmh) * 60)
