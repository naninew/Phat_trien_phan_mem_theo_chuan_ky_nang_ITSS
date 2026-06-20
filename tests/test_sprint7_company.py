"""
Test Sprint 7: Company Portal Business Logic.
Tests the full lifecycle of a rescue request from the company perspective.
"""

import pytest
from sqlalchemy.orm import Session
from app.services import rescue_svc
from app.models.request import RequestStatus
from app.models.staff import StaffStatus
from app.schemas.rescue import RescueRequestCreate, ServiceAssignmentCreate

def test_company_request_lifecycle(db_session: Session, test_customer, test_company, test_service, test_vehicle, test_rescue_staff):
    # 1. Customer creates a request
    req_in = RescueRequestCreate(
        service_ids=[test_service.id],
        vehicle_id=1, # Mock vehicle id for customer
        company_id=test_company.id,
        latitude=21.0,
        longitude=105.0,
        address_description="Test Address",
        incident_type="Tai nạn",
        description="Cần cứu hộ gấp"
    )
    req = rescue_svc.create_rescue_request(db_session, test_customer.id, req_in)
    assert req.status == RequestStatus.PENDING
    assert req.company_id == test_company.id

    # 2. Company accepts request
    eta = 15
    accepted_req = rescue_svc.accept_request(db_session, req.id, test_company.id, eta)
    assert accepted_req is not None
    assert accepted_req.status == RequestStatus.ACCEPTED
    assert accepted_req.eta_minutes == eta

    # 3. Company assigns staff and vehicle
    assign_in = ServiceAssignmentCreate(
        staff_id=test_rescue_staff.id,
        rescue_vehicle_id=test_vehicle.id,
        notes="Gấp"
    )
    assigned_req = rescue_svc.assign_request(db_session, req.id, test_company.id, assign_in)
    assert assigned_req is not None
    assert assigned_req.status == RequestStatus.ASSIGNED
    assert assigned_req.assignment.staff_id == test_rescue_staff.id
    
    # Check resource statuses
    db_session.refresh(test_rescue_staff)
    db_session.refresh(test_vehicle)
    assert test_rescue_staff.status == StaffStatus.BUSY
    assert test_vehicle.status == "on_mission"

    # 4. Progress status
    # ON_THE_WAY
    updated = rescue_svc.update_request_status(db_session, req.id, RequestStatus.ON_THE_WAY)
    assert updated.status == RequestStatus.ON_THE_WAY

    # IN_PROGRESS
    updated = rescue_svc.update_request_status(db_session, req.id, RequestStatus.IN_PROGRESS)
    assert updated.status == RequestStatus.IN_PROGRESS
    assert updated.actual_arrival_time is not None

    # 5. Complete request and release resources
    final_price = 150000.0
    completed = rescue_svc.update_request_status(db_session, req.id, RequestStatus.COMPLETED, agreed_price=final_price)
    assert completed.status == RequestStatus.COMPLETED
    assert completed.agreed_price == final_price
    assert completed.actual_completion_time is not None

    # Check resources are released
    db_session.refresh(test_rescue_staff)
    db_session.refresh(test_vehicle)
    assert test_rescue_staff.status == StaffStatus.AVAILABLE
    assert test_vehicle.status == "available"

def test_company_reject_request(db_session: Session, test_customer, test_company, test_service):
    req_in = RescueRequestCreate(
        service_ids=[test_service.id],
        vehicle_id=1,
        company_id=test_company.id,
        latitude=21.0,
        longitude=105.0,
        address_description="Test Address",
        incident_type="Tai nạn",
        description="Cần cứu hộ gấp"
    )
    req = rescue_svc.create_rescue_request(db_session, test_customer.id, req_in)
    
    rejected = rescue_svc.reject_request(db_session, req.id, test_company.id)
    assert rejected.status == RequestStatus.REJECTED
    assert rejected.company_id is None
