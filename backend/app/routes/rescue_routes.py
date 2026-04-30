"""
Rescue service routes for requests, companies, and vehicles.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Any

from ..database import get_db
from ..schemas.rescue import (
    RescueRequestCreate,
    RescueRequestUpdate,
    RescueRequestResponse,
    ServiceCreate,
    ServiceResponse,
    VehicleCreate,
    VehicleResponse,
    CompanyNearbyResponse,
)
from ..services import rescue_svc, auth_svc
from ..utils.response import success_response

router = APIRouter(prefix="/rescue", tags=["Rescue Services"])


@router.get("/companies/nearby", response_model=dict)
def find_nearby_companies(
    latitude: float,
    longitude: float,
    service_id: int,
    radius_km: float = 50.0,
    db: Session = Depends(get_db),
) -> dict:
    """
    Find nearby rescue companies that offer a specific service.
    
    - **latitude**: User's latitude
    - **longitude**: User's longitude
    - **service_id**: Required service ID
    - **radius_km**: Search radius in kilometers (default: 50)
    """
    results = rescue_svc.find_nearby_companies(
        db=db,
        latitude=latitude,
        longitude=longitude,
        service_id=service_id,
        radius_km=radius_km,
    )
    
    companies_data = []
    for company, distance, services in results:
        estimated_price = rescue_svc.estimate_price(
            base_price=services[0].base_price if services else 0,
            distance_km=distance,
        )
        eta_minutes = rescue_svc.estimate_eta(distance_km=distance)
        
        companies_data.append({
            "id": company.id,
            "company_name": company.company_name,
            "address": company.address,
            "hotline": company.hotline,
            "rating_avg": company.rating_avg,
            "distance_km": round(distance, 2),
            "estimated_price": estimated_price,
            "eta_minutes": eta_minutes,
            "services": [
                {
                    "id": s.id,
                    "service_name": s.service_name,
                    "base_price": s.base_price,
                    "description": s.description,
                }
                for s in services
            ],
        })
    
    return success_response(
        data=companies_data,
        message=f"Found {len(companies_data)} nearby companies",
    )


@router.post("/requests", response_model=dict)
def create_rescue_request(
    request_data: RescueRequestCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
) -> dict:
    """
    Create a new rescue request.
    
    - **service_id**: ID of the required service
    - **latitude**: User's current latitude
    - **longitude**: User's current longitude
    - **address_description**: Description of the location
    - **car_issue_detail**: Detailed description of the vehicle issue
    - **images**: Optional list of image URLs
    - **payment_method**: Preferred payment method (default: cash)
    
    Requires valid JWT token in Authorization header.
    """
    # Get user_id from JWT token
    user_id = current_user["user_id"]
    
    request = rescue_svc.create_rescue_request(
        db=db, user_id=user_id, request_data=request_data
    )
    
    return success_response(
        data={
            "request_id": request.id,
            "status": request.status,
            "created_at": request.created_at.isoformat(),
        },
        message="Rescue request created successfully",
    )


@router.get("/requests", response_model=dict)
def get_my_requests(
    db: Session = Depends(get_db),
    current_user: dict = Depends(auth_svc.get_current_user_from_token),
) -> dict:
    """
    Get all rescue requests for the current user.
    
    Requires valid JWT token in Authorization header.
    """
    # Get user_id from JWT token
    user_id = current_user["user_id"]
    
    requests = rescue_svc.get_user_requests(db=db, user_id=user_id)
    
    return success_response(
        data=[
            {
                "id": r.id,
                "status": r.status,
                "service_id": r.service_id,
                "address_description": r.address_description,
                "created_at": r.created_at.isoformat(),
            }
            for r in requests
        ],
        message="Success",
    )


@router.get("/requests/{request_id}", response_model=dict)
def get_request_details(
    request_id: int,
    db: Session = Depends(get_db),
) -> dict:
    """
    Get details of a specific rescue request.
    """
    request = rescue_svc.get_request_by_id(db=db, request_id=request_id)
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rescue request not found",
        )
    
    return success_response(
        data={
            "id": request.id,
            "user_id": request.user_id,
            "company_id": request.company_id,
            "service_id": request.service_id,
            "vehicle_id": request.vehicle_id,
            "latitude": request.latitude,
            "longitude": request.longitude,
            "address_description": request.address_description,
            "car_issue_detail": request.car_issue_detail,
            "status": request.status,
            "eta_minutes": request.eta_minutes,
            "total_cost": request.total_cost,
            "created_at": request.created_at.isoformat(),
        },
        message="Success",
    )


@router.put("/requests/{request_id}/status", response_model=dict)
def update_request_status(
    request_id: int,
    status_update: RescueRequestUpdate,
    db: Session = Depends(get_db),
) -> dict:
    """
    Update the status of a rescue request.
    
    - **status**: New status (pending, accepted, en_route, on_site, completed, cancelled)
    - **eta_minutes**: Estimated time of arrival in minutes
    - **vehicle_id**: ID of assigned vehicle
    """
    request = rescue_svc.update_request_status(
        db=db,
        request_id=request_id,
        status=status_update.status,
        vehicle_id=status_update.vehicle_id,
        eta_minutes=status_update.eta_minutes,
    )
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rescue request not found",
        )
    
    return success_response(
        data={"request_id": request.id, "status": request.status},
        message="Request status updated successfully",
    )


@router.post("/requests/{request_id}/cancel", response_model=dict)
def cancel_request(
    request_id: int,
    db: Session = Depends(get_db),
) -> dict:
    """
    Cancel a pending rescue request.
    """
    request = rescue_svc.cancel_request(db=db, request_id=request_id)
    
    if not request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel request - already being processed or not found",
        )
    
    return success_response(
        data={"request_id": request.id, "status": request.status},
        message="Request cancelled successfully",
    )


@router.post("/services", response_model=dict)
def create_service(
    service_data: ServiceCreate,
    company_id: int,
    db: Session = Depends(get_db),
) -> dict:
    """
    Create a new service for a rescue company.
    """
    service = rescue_svc.create_service(
        db=db, company_id=company_id, service_data=service_data
    )
    
    return success_response(
        data={"service_id": service.id, "service_name": service.service_name},
        message="Service created successfully",
    )


@router.post("/vehicles", response_model=dict)
def create_vehicle(
    vehicle_data: VehicleCreate,
    company_id: int,
    db: Session = Depends(get_db),
) -> dict:
    """
    Create a new vehicle for a rescue company.
    """
    vehicle = rescue_svc.create_vehicle(
        db=db, company_id=company_id, vehicle_data=vehicle_data
    )
    
    return success_response(
        data={"vehicle_id": vehicle.id, "license_plate": vehicle.license_plate},
        message="Vehicle created successfully",
    )


@router.get("/companies/{company_id}/vehicles", response_model=dict)
def get_company_vehicles(
    company_id: int,
    db: Session = Depends(get_db),
) -> dict:
    """
    Get all vehicles for a rescue company.
    """
    vehicles = rescue_svc.get_company_vehicles(db=db, company_id=company_id)
    
    return success_response(
        data=[
            {
                "id": v.id,
                "license_plate": v.license_plate,
                "vehicle_type": v.vehicle_type,
                "capacity": v.capacity,
                "status": v.status,
            }
            for v in vehicles
        ],
        message="Success",
    )
