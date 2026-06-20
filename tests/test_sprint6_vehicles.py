import requests
import json
import random

BASE_URL = "http://localhost:8000/api/v1/rescue"

def test_customer_vehicles():
    # Login as customer
    login_url = "http://localhost:8000/api/v1/auth/login"
    login_data = {"username": "customer1", "password": "Pass123!"} 
    
    print(f"Logging in to {login_url}...")
    r = requests.post(login_url, json=login_data)
    print(f"Login status: {r.status_code}")
    if r.status_code != 200:
        print(f"Login failed: {r.text}")
        return

    data = r.json()
    token = data['data']['access_token']
    headers = {"Authorization": f"Bearer {token}"}
    
    print("\n--- Testing Customer Vehicles ---")
    
    # 1. Add vehicle
    v_data = {
        "license_plate": f"30A-{random.randint(10000, 99999)}",
        "brand": "Toyota",
        "model": "Camry",
        "year": 2022,
        "fuel_type": "Gasoline"
    }
    print(f"Adding vehicle: {v_data}")
    r = requests.post(f"{BASE_URL}/customer/vehicles", json=v_data, headers=headers)
    print(f"Add status: {r.status_code}")
    if r.status_code != 200:
        print(f"Error: {r.text}")
        return
    
    vehicle_id = r.json()['data']['id']
    print(f"Added vehicle ID: {vehicle_id}")
    
    # 2. List vehicles
    r = requests.get(f"{BASE_URL}/customer/vehicles", headers=headers)
    print(f"List status: {r.status_code}")
    if r.status_code == 200:
        print(f"Vehicles found: {len(r.json()['data'])}")
    
    # 3. Update vehicle
    u_data = {"brand": "Lexus", "year": 2023}
    r = requests.put(f"{BASE_URL}/customer/vehicles/{vehicle_id}", json=u_data, headers=headers)
    print(f"Update status: {r.status_code}")
    
    # 4. Delete vehicle
    r = requests.delete(f"{BASE_URL}/customer/vehicles/{vehicle_id}", headers=headers)
    print(f"Delete status: {r.status_code}")

if __name__ == "__main__":
    test_customer_vehicles()
