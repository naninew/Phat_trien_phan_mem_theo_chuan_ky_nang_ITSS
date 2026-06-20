"""
Test luồng đăng ký công ty và phê duyệt admin.

Kịch bản:
1. Đăng ký công ty mới → status = pending
2. Thử đăng nhập → kỳ vọng 403 COMPANY_PENDING
3. Admin đăng nhập
4. Admin xem danh sách pending companies
5. Admin phê duyệt công ty
6. Thử đăng nhập lại → kỳ vọng thành công
"""
import requests
import time
import random

BASE_URL = "http://localhost:8000/api/v1"

def run_test():
    # ── 1. Đăng ký công ty mới ─────────────────────────────────────────────────
    suffix = random.randint(10000, 99999)
    company_data = {
        "username": f"testco_{suffix}",
        "password": "TestPass@123",
        "full_name": f"Nguyễn Văn Test {suffix}",
        "phone": "0987654321",
        "email": f"testco_{suffix}@example.com",
        "role": "company_staff",
        "company_name": f"Công ty Cứu hộ Test {suffix}",
        "business_license": f"MST-{suffix}",
        "address": "123 Đường Test, Hà Nội",
        "hotline": "0988123456"
    }

    print("\n[TEST 1] Đăng ký công ty mới...")
    r = requests.post(f"{BASE_URL}/auth/register", json=company_data)
    print(f"  Status: {r.status_code}")
    body = r.json()
    print(f"  Response: {body}")

    assert r.status_code == 200, f"❌ Đăng ký thất bại: {body}"
    assert body.get("data", {}).get("company_status") == "pending", "❌ Company status phải là 'pending' sau đăng ký"
    company_id = body["data"].get("company_id")
    print(f"  ✅ Đăng ký thành công | company_id={company_id} | status=pending")

    # ── 2. Thử đăng nhập khi chưa được phê duyệt → kỳ vọng 403 ───────────────
    print("\n[TEST 2] Thử đăng nhập khi công ty đang pending...")
    r = requests.post(f"{BASE_URL}/auth/login", json={
        "username": company_data["username"],
        "password": company_data["password"]
    })
    print(f"  Status: {r.status_code}")
    print(f"  Response: {r.json()}")

    assert r.status_code == 403, f"❌ Phải bị từ chối 403, nhưng nhận được {r.status_code}"
    detail = r.json().get("detail", "")
    assert "phê duyệt" in detail or "pending" in detail.lower() or "chờ" in detail, \
        f"❌ Message không đúng: {detail}"
    print(f"  ✅ Đăng nhập bị từ chối đúng với thông báo: '{detail}'")

    # ── 3. Admin đăng nhập ─────────────────────────────────────────────────────
    print("\n[TEST 3] Admin đăng nhập...")
    r = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "admin",
        "password": "Admin123!"
    })
    print(f"  Status: {r.status_code}")
    assert r.status_code == 200, f"❌ Admin login thất bại: {r.json()}"
    admin_token = r.json()["data"]["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    print("  ✅ Admin đăng nhập thành công")

    # ── 4. Admin xem danh sách pending companies ────────────────────────────────
    print("\n[TEST 4] Admin xem danh sách pending companies...")
    r = requests.get(f"{BASE_URL}/admin/companies/pending", headers=admin_headers)
    print(f"  Status: {r.status_code}")
    assert r.status_code == 200, f"❌ Không lấy được pending list: {r.json()}"
    pending_list = r.json().get("data", [])
    print(f"  ✅ Tìm thấy {len(pending_list)} công ty đang chờ duyệt")

    # Verify công ty mới đăng ký có trong list
    found = next((c for c in pending_list if c.get("id") == company_id), None)
    if found:
        print(f"  ✅ Công ty ID={company_id} '{found.get('company_name')}' có trong danh sách pending")
    else:
        print(f"  ⚠️  Công ty ID={company_id} chưa thấy trong pending list (có thể cần refresh)")

    # ── 5. Admin phê duyệt công ty ─────────────────────────────────────────────
    print(f"\n[TEST 5] Admin phê duyệt công ty ID={company_id}...")
    r = requests.put(
        f"{BASE_URL}/admin/companies/{company_id}/approve",
        headers=admin_headers
    )
    print(f"  Status: {r.status_code}")
    print(f"  Response: {r.json()}")
    assert r.status_code == 200, f"❌ Admin approve thất bại: {r.json()}"
    print("  ✅ Admin phê duyệt công ty thành công")

    # ── 6. Đăng nhập lại sau khi được phê duyệt → kỳ vọng thành công ──────────
    print("\n[TEST 6] Đăng nhập lại sau khi được phê duyệt...")
    time.sleep(0.3)  # nhỏ delay cho DB commit
    r = requests.post(f"{BASE_URL}/auth/login", json={
        "username": company_data["username"],
        "password": company_data["password"]
    })
    print(f"  Status: {r.status_code}")
    body = r.json()
    print(f"  Response: {body}")

    assert r.status_code == 200, f"❌ Đăng nhập sau phê duyệt thất bại: {body}"
    token = body["data"]["access_token"]
    assert token, "❌ Không có access_token"
    print(f"  ✅ Đăng nhập thành công! Role: {body['data']['user']['role']}")

    print("\n" + "="*60)
    print("  🎉 TẤT CẢ CÁC TEST ĐỀU PASS!")
    print("="*60)

if __name__ == "__main__":
    try:
        run_test()
    except AssertionError as e:
        print(f"\n  ❌ TEST FAILED: {e}")
        raise SystemExit(1)
    except Exception as e:
        print(f"\n  💥 ERROR: {e}")
        raise SystemExit(2)
