import requests

BASE_URL = "http://localhost:8000/api/v1"

def test_pending_company():
    # 1. Login as admin
    login_data = {"username": "admin", "password": "123"}
    r = requests.post(f"{BASE_URL}/auth/login", data=login_data)
    if r.status_code != 200:
        print("Login failed:", r.text)
        return
    token = r.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Get companies to find a pending one
    r = requests.get(f"{BASE_URL}/admin/companies/pending", headers=headers)
    pending_companies = r.json().get("data", [])
    if not pending_companies:
        print("No pending companies found.")
        return
        
    pending_company_id = pending_companies[0]["id"]
    print(f"Found pending company ID: {pending_company_id}")
    
    # 3. Get company details
    r = requests.get(f"{BASE_URL}/admin/companies/{pending_company_id}/detail", headers=headers)
    detail = r.json().get("data", {})
    
    print("Services:", detail.get("services"))
    print("Staff:", detail.get("staff"))
    print("Vehicles:", detail.get("vehicles"))
    print("Recent Requests:", detail.get("recent_requests"))
    print("Reviews:", detail.get("reviews"))
    
    assert detail.get("services") == [], "Services should be empty"
    assert detail.get("staff") == [], "Staff should be empty"
    assert detail.get("vehicles") == [], "Vehicles should be empty"
    assert detail.get("recent_requests") == [], "Requests should be empty"
    assert detail.get("reviews") == [], "Reviews should be empty"
    print("SUCCESS: Logic is correct!")

if __name__ == "__main__":
    test_pending_company()
