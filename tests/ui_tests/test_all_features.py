"""
Comprehensive UI Test Suite
Contains test functions for all frontend features.
"""

import httpx
from typing import Dict, Any

async def test_homepage(base_url: str):
    """Test that homepage loads and has correct content."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{base_url}/")
        assert response.status_code == 200
        assert "Dịch vụ cứu hộ" in response.text
        assert "Bắt Đầu Ngay" in response.text

async def test_login_page(base_url: str):
    """Test that login page loads."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{base_url}/login")
        assert response.status_code == 200
        assert "Đăng Nhập" in response.text or "Login" in response.text

async def test_register_page(base_url: str):
    """Test that registration page loads."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{base_url}/register")
        assert response.status_code == 200
        assert "Đăng Ký" in response.text or "Register" in response.text

async def test_customer_dashboard_protected(base_url: str):
    """Test that customer dashboard is protected."""
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(f"{base_url}/customer/dashboard")
        # Check if it redirects to login or doesn't show dashboard content
        assert "Customer Dashboard" not in response.text or "Login" in response.text

async def test_company_dashboard_protected(base_url: str):
    """Test that company dashboard is protected."""
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(f"{base_url}/company/dashboard")
        assert "Company Dashboard" not in response.text or "Login" in response.text

async def test_admin_dashboard_protected(base_url: str):
    """Test that admin dashboard is protected."""
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(f"{base_url}/admin/dashboard")
        # In NiceGUI, it might return 200 with a redirect script or content
        # We check if it DOES NOT contain dashboard-specific keywords if not logged in
        assert "Admin Dashboard" not in response.text or "Login" in response.text

async def test_api_health(base_url: str):
    """Test backend API health."""
    api_url = base_url.replace('8080', '8000')
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{api_url}/health")
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            assert response.json().get("status") == "healthy"
        except Exception as e:
            raise Exception(f"Backend API health check failed at {api_url}/health: {e}")

async def test_all_routes_accessibility(base_url: str):
    """Check if all major routes are defined and return 200 or redirect (not 404)."""
    routes = [
        "/customer/find-rescue",
        "/customer/requests",
        "/company/queue",
        "/company/fleet",
        "/company/profile",
        "/admin/users",
        "/admin/companies"
    ]
    async with httpx.AsyncClient(follow_redirects=False) as client:
        for route in routes:
            response = await client.get(f"{base_url}{route}")
            assert response.status_code != 404, f"Route {route} returned 404"

# Dictionary of all tests to be run
ALL_UI_TESTS = [
    ("Homepage Connectivity", test_homepage),
    ("Login Page Accessibility", test_login_page),
    ("Register Page Accessibility", test_register_page),
    ("Customer RBAC Check", test_customer_dashboard_protected),
    ("Company RBAC Check", test_company_dashboard_protected),
    ("Admin RBAC Check", test_admin_dashboard_protected),
    ("Backend API Connectivity", test_api_health),
    ("Frontend Routes Integrity", test_all_routes_accessibility),
]
