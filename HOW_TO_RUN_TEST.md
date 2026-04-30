# Hướng Dẫn Chạy Test Suite

Tài liệu này hướng dẫn chi tiết cách chạy toàn bộ hệ thống test của dự án, bao gồm cả backend unit tests, API integration tests, và UI automated tests.

## Mục Lục

1. [Tổng Quan](#tổng-quan)
2. [Yêu Cầu Hệ Thống](#yêu-cầu-hệ-thống)
3. [Cài Đặt Dependencies](#cài-đặt-dependencies)
4. [Các Loại Test](#các-loại-test)
5. [Hướng Dẫn Chạy Test](#hướng-dẫn-chạy-test)
6. [Sử Dụng NiceGUI Test Runner](#sử-dụng-nicegui-test-runner)
7. [Chạy Tự Động Hoàn Toàn](#chạy-tự-động-hoàn-toàn)
8. [Diễn Giải Kết Quả](#diễn-giải-kết-quả)
9. [Xử Lý Lỗi Thường Gặp](#xử-lý-lỗi-thường-gặp)
10. [Best Practices](#best-practices)

---

## Tổng Quan

Dự án sử dụng 3 lớp test chính:

| Loại Test | Mục Đích | Công Cụ | Thời Gian Chạy |
|-----------|----------|---------|----------------|
| **Backend Unit Tests** | Kiểm tra logic business, services, models | pytest | ~5-10 giây |
| **API Integration Tests** | Kiểm tra REST API endpoints | pytest + TestClient | ~10-20 giây |
| **UI Automated Tests** | Kiểm tra giao diện người dùng | NiceGUI + httpx | ~15-30 giây |

---

## Yêu Cầu Hệ Thống

### Phần Cứng Tối Thiểu
- RAM: 4GB
- CPU: 2 cores
- Disk: 1GB free space

### Phần Mềm Bắt Buộc
- Python 3.9+
- PostgreSQL 14+ (cho integration tests)
- Bash shell (Linux/Mac) hoặc Git Bash (Windows)

### Dependencies Python
```bash
pip install pytest pytest-cov pytest-html httpx rich nicegui fastapi sqlalchemy
```

---

## Cài Đặt Dependencies

### Bước 1: Tạo Virtual Environment (Khuyến Nghị)
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc
venv\Scripts\activate  # Windows
```

### Bước 2: Cài Đặt Test Dependencies
```bash
pip install -r requirements.txt
```

Hoặc cài riêng cho testing:
```bash
pip install pytest==7.4.0 \
    pytest-cov==4.1.0 \
    pytest-html==3.2.0 \
    httpx==0.24.1 \
    rich==13.5.0 \
    nicegui==1.4.0 \
    SQLAlchemy==2.0.20
```

### Bước 3: Xác Minh Cài Đặt
```bash
pytest --version
# Output: pytest 7.4.0
```

---

## Các Loại Test

### 1. Backend Unit Tests (`tests/backend_tests/test_services.py`)

Kiểm tra các service functions:
- `UserService`: create_user, authenticate_user, update_user, deactivate_user
- `CompanyService`: create_company, update_company, get_companies_by_owner
- `VehicleService`: create_vehicle, update_vehicle_status, get_vehicles_by_company
- `QueueService`: create_queue, update_queue_status, calculate_queue_position

**Số lượng tests:** 20+ tests

### 2. API Integration Tests (`tests/backend_tests/test_api.py`)

Kiểm tra REST API endpoints:
- `/api/v1/auth/register` - Đăng ký user
- `/api/v1/auth/login` - Đăng nhập
- `/api/v1/users/me` - Lấy thông tin user hiện tại
- `/api/v1/companies` - CRUD companies
- `/api/v1/vehicles` - CRUD vehicles
- `/api/v1/queues` - CRUD queues

**Số lượng tests:** 15+ tests

### 3. UI Automated Tests (`tests/ui_tests/`)

Kiểm tra giao diện NiceGUI:
- Homepage loads correctly
- Login page accessible
- Register page accessible
- Dashboard requires authentication
- API health endpoint responsive
- Navbar component renders
- Static assets load properly

**Số lượng tests:** 7+ tests

---

## Hướng Dẫn Chạy Test

### Cách 1: Chạy Tất Cả Backend Tests (Đơn Giản Nhất)

```bash
# Từ thư mục gốc của dự án
pytest tests/backend_tests/ -v
```

**Output mẫu:**
```
============================= test session starts ==============================
platform linux -- Python 3.9.18, pytest-7.4.0
collected 35 items

tests/backend_tests/test_services.py::TestUserService::test_create_admin_user PASSED [  2%]
tests/backend_tests/test_services.py::TestUserService::test_authenticate_user_success PASSED [  5%]
...
======================== 35 passed in 3.42s ========================
```

### Cách 2: Chạy Với Coverage Report

```bash
pytest tests/ --cov=backend --cov-report=html --cov-report=term
```

Sau đó mở file coverage report:
```bash
# Linux/Mac
open htmlcov/index.html  # Mac
xdg-open htmlcov/index.html  # Linux

# Windows
start htmlcov\index.html
```

### Cách 3: Chạy Từng File Test Cụ Thể

```bash
# Chỉ chạy unit tests
pytest tests/backend_tests/test_services.py -v

# Chỉ chạy API tests
pytest tests/backend_tests/test_api.py -v

# Chỉ chạy một class test
pytest tests/backend_tests/test_services.py::TestUserService -v

# Chỉ chạy một test duy nhất
pytest tests/backend_tests/test_services.py::TestUserService::test_create_admin_user -v
```

### Cách 4: Chạy UI Tests Từ Command Line

```bash
# Đảm bảo ứng dụng đang chạy trên port 8080
python tests/ui_tests/run_ui_tests.py --url http://localhost:8080

# Với verbose mode (hiển thị lỗi chi tiết)
python tests/ui_tests/run_ui_tests.py --url http://localhost:8080 --verbose

# Export kết quả ra file JSON
python tests/ui_tests/run_ui_tests.py --url http://localhost:8080 --export=test_results.json
```

**Output mẫu:**
```
Running UI Tests against http://localhost:8080

Testing: Homepage Loads ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
Testing: Login Page Exists ━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100%
...

Test Results Summary
┏━━━━━━━━━━┬──────────────────────┬─────────┬──────────┓
┃ Status   ┃ Test Name            ┃ Details ┃ Time     ┃
┡━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━━━━━┩
│ ✓ PASSED │ Homepage Loads       │ ✓       │ 12:34:56 │
│ ✓ PASSED │ Login Page Exists    │ ✓       │ 12:34:57 │
│ ✗ FAILED │ Dashboard Requires A │ ✗ Stat… │ 12:34:58 │
└──────────┴──────────────────────┴─────────┴──────────┘

Statistics:
  Total Tests: 7
  Passed: 6
  Failed: 1

  Success Rate: 85.7%
```

### Cách 5: Chạy Script Tự Động Hóa Toàn Bộ

```bash
# Cấp quyền execute lần đầu
chmod +x tests/run_all_tests.sh

# Chạy toàn bộ test suite
./tests/run_all_tests.sh
```

Script này sẽ:
1. ✅ Chạy backend unit tests
2. ✅ Chạy API integration tests  
3. ✅ Chạy UI automated tests
4. ✅ Tạo coverage report
5. ✅ Lưu kết quả vào thư mục timestamped

---

## Sử Dụng NiceGUI Test Runner

NiceGUI Test Runner cung cấp giao diện đồ họa để chạy tests và xem progress trực quan.

### Bước 1: Khởi Động Test Runner UI

```bash
python tests/ui_tests/test_runner.py
```

Truy cập: **http://localhost:8081**

### Bước 2: Sử Dụng Giao Diện

1. **Màn hình chính** hiển thị:
   - Giới thiệu về test suite
   - Các button điều hướng

2. **Click "Open Test Runner"** để vào trang chạy tests

3. **Nhập URL ứng dụng** cần test (mặc định: http://localhost:8080)

4. **Click "Run Tests"** để bắt đầu:
   - Progress bar hiển thị tiến độ real-time
   - Bảng kết quả cập nhật tự động
   - Màu sắc thể hiện status (xanh = passed, đỏ = failed)

5. **Export Results** bằng cách click "Export Results" để tải file JSON

### Bước 3: Xem Demo Progress Visualization

Click "View Demo" để xem mô phỏng progress display mà không cần chạy tests thật.

### Lợi Ích Của NiceGUI Test Runner

- ✅ **Trực quan**: Xem progress real-time với animations
- ✅ **Dễ dùng**: Không cần command line knowledge
- ✅ **Exportable**: Tải kết quả về làm báo cáo
- ✅ **Shareable**: Gửi link cho team members cùng xem

---

## Chạy Tự Động Hoàn Toàn

### Kịch Bản CI/CD (GitHub Actions, GitLab CI, Jenkins)

Tạo file `.github/workflows/tests.yml`:

```yaml
name: Run Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: testpass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-html httpx rich
    
    - name: Run Backend Tests
      run: |
        pytest tests/backend_tests/ -v --tb=short --html=test_report.html
    
    - name: Upload Test Report
      uses: actions/upload-artifact@v3
      with:
        name: test-report
        path: test_report.html
```

### Chạy Local Auto-Test (One-Command)

```bash
# Dành cho admin: chỉ cần 1 lệnh duy nhất
./tests/run_all_tests.sh
```

Sau khi chạy xong, chỉ cần:
1. Mở thư mục `test_results_YYYYMMDD_HHMMSS/`
2. Xem file HTML reports
3. Check success rate

---

## Diễn Giải Kết Quả

### Ký Hiệu Status

| Icon | Status | Ý Nghĩa |
|------|--------|---------|
| ✅ / ✓ | PASSED | Test hoàn thành thành công |
| ❌ / ✗ | FAILED | Test gặp lỗi, cần fix |
| ⚠️ / ⊘ | SKIPPED | Test bị skip (thiếu điều kiện) |
| ⏳ | RUNNING | Test đang chạy |

### Đọc Hiểu Output

#### Pytest Output
```
tests/test_services.py::TestUserService::test_create_user PASSED
                                                  ↑
                                             Test name
```

- **PASSED/FAILED**: Status của test
- **Test name**: Đường dẫn đầy đủ đến test method
- **Coverage %**: Tỷ lệ code được test

#### UI Test Output
```json
{
  "base_url": "http://localhost:8080",
  "executed_at": "2024-01-15T10:30:00",
  "summary": {
    "total": 7,
    "passed": 6,
    "failed": 1,
    "success_rate": 85.7
  },
  "results": [...]
}
```

### Ngưỡng Chấp Nhận Được

| Metric | Tốt | Chấp Nhận | Cần Cải Thiện |
|--------|-----|-----------|---------------|
| Unit Test Pass Rate | 100% | ≥95% | <95% |
| API Test Pass Rate | 100% | ≥90% | <90% |
| UI Test Pass Rate | ≥95% | ≥85% | <85% |
| Code Coverage | ≥80% | ≥70% | <70% |

---

## Xử Lý Lỗi Thường Gặp

### Lỗi 1: `ModuleNotFoundError: No module named 'pytest'`

**Giải pháp:**
```bash
pip install pytest pytest-cov
```

### Lỗi 2: Database Connection Failed

**Triệu chứng:**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**Giải pháp:**
1. Kiểm tra PostgreSQL đang chạy:
   ```bash
   sudo systemctl status postgresql
   ```
2. Start nếu chưa chạy:
   ```bash
   sudo systemctl start postgresql
   ```
3. Kiểm tra credentials trong `.env`

### Lỗi 3: Port Already In Use

**Triệu chứng:**
```
OSError: [Errno 98] Address already in use
```

**Giải pháp:**
```bash
# Tìm process đang giữ port
lsof -i :8080

# Kill process
kill -9 <PID>
```

### Lỗi 4: UI Tests Fail Vì Application Chưa Chạy

**Triệu chứng:**
```
httpx.ConnectError: Connection refused
```

**Giải pháp:**
1. Start backend:
   ```bash
   python backend/main.py
   ```
2. Start frontend:
   ```bash
   python frontend/main.py
   ```
3. Chờ 5 giây cho servers khởi động
4. Re-run UI tests

### Lỗi 5: Test Fixtures Not Found

**Triệu chứng:**
```
ImportError: No module named 'tests.fixtures'
```

**Giải pháp:**
```bash
# Thêm project root vào PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Hoặc chạy pytest từ project root
cd /path/to/project
pytest tests/
```

---

## Best Practices

### 1. Chạy Tests Trước Khi Commit
```bash
# Tạo git pre-commit hook
echo '#!/bin/bash
pytest tests/backend_tests/ -q || exit 1' > .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### 2. Giữ Tests Độc Lập
- Mỗi test phải tự chứa dữ liệu test
- Không phụ thuộc vào thứ tự chạy tests
- Dùng fixtures để setup/teardown

### 3. Đặt Tên Test Rõ Ràng
```python
# ✅ Tốt
def test_create_admin_user_with_valid_data():
    ...

def test_login_fails_with_wrong_password():
    ...

# ❌ Tránh
def test_user():
    ...

def test_stuff():
    ...
```

### 4. Sử Dụng Parametrize Cho Multiple Cases
```python
@pytest.mark.parametrize("role,expected_status", [
    ("ADMIN", 200),
    ("CUSTOMER", 403),
    (None, 401),
])
def test_dashboard_access_by_role(role, expected_status):
    ...
```

### 5. Clean Up Sau Tests
```python
@pytest.fixture
def temp_user(db_session):
    user = create_test_user()
    yield user
    db_session.delete(user)  # Cleanup
    db_session.commit()
```

### 6. Document Test Cases
Thêm docstring cho mỗi test:
```python
def test_queue_position_calculation(self, db_session, test_queue):
    """
    Test calculating queue position.
    
    Given: A queue entry exists with 2 entries ahead
    When: Calculating position
    Then: Should return 3 (1-indexed)
    """
    position = QueueService.calculate_position(...)
    assert position == 3
```

---

## Tài Liệu Liên Quan

- [`HOW_TO_START_PROJECT.md`](../HOW_TO_START_PROJECT.md) - Hướng dẫn khởi động dự án
- [`DETAIL_STRUCTURE.md`](../DETAIL_STRUCTURE.md) - Chi tiết cấu trúc code
- [`README.md`](../README.md) - Tổng quan dự án

---

## Hỗ Trợ

Nếu gặp vấn đề khi chạy tests:

1. **Check logs** trong thư mục `test_results_*/`
2. **Chạy với verbose mode**: `pytest -vvv`
3. **Isolate failing test**: Chạy từng test một
4. **Report issue** với đầy đủ thông tin:
   - OS version
   - Python version
   - Error message full text
   - Steps to reproduce

---

**Cập nhật lần cuối:** 2024
**Version:** 1.0.0
