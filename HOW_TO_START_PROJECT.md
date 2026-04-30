# Hướng Dẫn Khởi Động Dự Án - Roadside Assistance System

## Tổng quan
Hệ thống Hỗ Trợ Sự Cố Xe Trên Đường được phát triển bằng **NiceGUI** (frontend) và **FastAPI** (backend), sử dụng **PostgreSQL** làm cơ sở dữ liệu.

---

## Yêu Cầu Hệ Thống

### Phần mềm cần cài đặt
- **Python**: Phiên bản 3.8 trở lên
- **PostgreSQL**: Phiên bản 12 trở lên
- **pip**: Trình quản lý gói Python

### Thư viện Python
Tất cả thư viện được liệt kê trong file `backend/requirements.txt`

---

## Các Bước Cài Đặt Chi Tiết

### Bước 1: Cài Đặt PostgreSQL

#### Trên Ubuntu/Debian:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

#### Trên Windows:
1. Tải PostgreSQL từ https://www.postgresql.org/download/windows/
2. Chạy file cài đặt và làm theo hướng dẫn
3. Ghi nhớ mật khẩu tài khoản `postgres`

#### Trên macOS:
```bash
brew install postgresql
```

### Bước 2: Tạo Cơ Sở Dữ Liệu

```bash
# Đăng nhập vào PostgreSQL
sudo -u postgres psql

# Hoặc trên Windows:
# psql -U postgres
```

```sql
-- Tạo database mới
CREATE DATABASE rescue_system;

-- Tạo user (nếu cần)
CREATE USER rescue_admin WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE rescue_system TO rescue_admin;

-- Thoát
\q
```

### Bước 3: Cấu Hình Database Connection

Mở file `/workspace/backend/app/database.py` và cập nhật thông tin kết nối:

```python
DATABASE_URL = "postgresql://postgres:your_password@localhost:5432/rescue_system"
```

**Lưu ý**: Thay đổi:
- `postgres`: username của bạn
- `your_password`: mật khẩu của bạn
- `localhost`: host (nếu DB ở máy khác)
- `5432`: port (mặc định là 5432)
- `rescue_system`: tên database

### Bước 4: Cài Đặt Dependencies

```bash
# Di chuyển vào thư mục backend
cd /workspace/backend

# Cài đặt các thư viện cần thiết
pip install -r requirements.txt
```

### Bước 5: Khởi Tạo Database

```bash
# Từ thư mục backend
cd /workspace/backend

# Chạy script khởi tạo database
python -m app.database
```

Hoặc chạy trực tiếp:
```bash
python backend/app/database.py
```

Nếu thành công, bạn sẽ thấy thông báo:
```
Database tables created successfully!
```

### Bước 6: Khởi Động Backend Server

```bash
# Từ thư mục backend
cd /workspace/backend

# Chạy server
python run.py
```

Hoặc sử dụng uvicorn trực tiếp:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Kiểm tra backend hoạt động**:
- Mở trình duyệt truy cập: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Health check: http://localhost:8000/health

Bạn sẽ thấy thông báo chào mừng và có thể test API qua Swagger UI.

### Bước 7: Cấu Hình Frontend

Mở file `/workspace/frontend/core/config.py` để kiểm tra cấu hình:

```python
# Đảm bảo BACKEND_URL trỏ đúng đến backend server
BACKEND_URL = "http://localhost:8000/api/v1"
```

### Bước 8: Cài Đặt NiceGUI cho Frontend

```bash
# Từ thư mục workspace
cd /workspace

# Cài đặt NiceGUI nếu chưa có
pip install nicegui
```

### Bước 9: Tạo File Chạy Frontend (main.py)

Tạo file `/workspace/frontend/main.py`:

```python
"""
Frontend main entry point for NiceGUI application.
"""
from nicegui import ui, app
from typing import Callable

from .core.config import APP_TITLE, APP_VERSION
from .core.auth import is_authenticated, get_user_role, get_redirect_url_for_role, LOGIN_PAGE
from .components.navbar import create_navbar

# Import pages (sẽ được tạo sau)
# from .pages.auth import login_page, register_page
# from .pages.customer import dashboard as customer_dashboard
# from .pages.company import dashboard as company_dashboard
# from .pages.admin import dashboard as admin_dashboard


def render_header():
    """Render navigation header."""
    create_navbar(APP_TITLE)


@ui.page('/')
def index():
    """Root page - redirect based on authentication."""
    if is_authenticated():
        role = get_user_role()
        redirect_url = get_redirect_url_for_role(role)
        ui.navigate.to(redirect_url)
    else:
        ui.navigate.to(LOGIN_PAGE)


@ui.page('/login')
def login_page():
    """Login page."""
    render_header()
    # Implement login form here
    ui.label('Login Page').classes('text-2xl m-4')
    # TODO: Add login form implementation


@ui.page('/register')
def register_page():
    """Registration page."""
    render_header()
    ui.label('Register Page').classes('text-2xl m-4')
    # TODO: Add registration form implementation


# Customer Dashboard
@ui.page('/customer/dashboard')
def customer_dashboard():
    """Customer dashboard page."""
    render_header()
    ui.label('Customer Dashboard').classes('text-2xl m-4')
    # TODO: Implement customer dashboard


# Company Dashboard
@ui.page('/company/dashboard')
def company_dashboard():
    """Company dashboard page."""
    render_header()
    ui.label('Company Dashboard').classes('text-2xl m-4')
    # TODO: Implement company dashboard


# Admin Dashboard
@ui.page('/admin/dashboard')
def admin_dashboard():
    """Admin dashboard page."""
    render_header()
    ui.label('Admin Dashboard').classes('text-2xl m-4')
    # TODO: Implement admin dashboard


# Run application
if __name__ in {"__main__", "__mp_main__"}:
    print(f"Starting {APP_TITLE} v{APP_VERSION}")
    print("Frontend URL: http://localhost:8080")
    print("Backend URL: http://localhost:8000")
    
    # Configure storage
    app.storage.browser['id'] = 'roadside_assistance'
    
    # Run NiceGUI server
    ui.run(
        title=APP_TITLE,
        host='0.0.0.0',
        port=8080,
        reload=True,
        storage_secret='your-secret-key-change-in-production'
    )
```

### Bước 10: Khởi Động Frontend Server

```bash
# Từ thư mục workspace
cd /workspace

# Chạy frontend
python -m frontend.main
```

Hoặc:
```bash
python frontend/main.py
```

**Kiểm tra frontend hoạt động**:
- Mở trình duyệt truy cập: http://localhost:8080

---

## Quy Trình Khởi Động Hàng Ngày

### Khi Phát Triển (Development)

Mở 2 terminal riêng biệt:

**Terminal 1 - Backend:**
```bash
cd /workspace/backend
python run.py
```

**Terminal 2 - Frontend:**
```bash
cd /workspace
python frontend/main.py
```

### Khi Sản Xuất (Production)

Sử dụng process manager như `supervisor` hoặc `systemd`:

**Ví dụ với supervisor:**

Tạo file `/etc/supervisor/conf.d/rescue-backend.conf`:
```ini
[program:rescue-backend]
command=/usr/bin/python3 run.py
directory=/workspace/backend
autostart=true
autorestart=true
stderr_logfile=/var/log/rescue-backend.err.log
stdout_logfile=/var/log/rescue-backend.out.log
user=root
environment=PYTHONUNBUFFERED=1
```

Tạo file `/etc/supervisor/conf.d/rescue-frontend.conf`:
```ini
[program:rescue-frontend]
command=/usr/bin/python3 -m frontend.main
directory=/workspace
autostart=true
autorestart=true
stderr_logfile=/var/log/rescue-frontend.err.log
stdout_logfile=/var/log/rescue-frontend.out.log
user=root
environment=PYTHONUNBUFFERED=1
```

Khởi động services:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start rescue-backend
sudo supervisorctl start rescue-frontend
```

---

## Tạo Tài Khoản Admin Đầu Tiên

Sau khi khởi động hệ thống, tạo tài khoản admin qua API:

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "Admin@123",
    "full_name": "System Administrator",
    "phone": "0901234567",
    "email": "admin@rescue.com"
  }'
```

**Lưu ý**: Sau khi tạo, cần cập nhật role thành `admin` trong database:

```bash
psql -U postgres -d rescue_system
```

```sql
UPDATE users SET role = 'admin' WHERE username = 'admin';
```

---

## Xử Lý Sự Cố Thường Gặp

### Lỗi Kết Nối Database

**Triệu chứng**: `could not connect to server`

**Giải pháp**:
1. Kiểm tra PostgreSQL đang chạy:
   ```bash
   sudo systemctl status postgresql
   ```
2. Khởi động nếu chưa chạy:
   ```bash
   sudo systemctl start postgresql
   ```
3. Kiểm tra thông tin kết nối trong `database.py`

### Lỗi Port Đã Sử Dụng

**Triệu chứng**: `Address already in use`

**Giải pháp**:
1. Tìm process đang dùng port:
   ```bash
   lsof -i :8000  # Backend
   lsof -i :8080  # Frontend
   ```
2. Kill process:
   ```bash
   kill -9 <PID>
   ```
3. Hoặc thay đổi port trong cấu hình

### Lỗi Thiếu Thư Viện

**Triệu chứng**: `ModuleNotFoundError`

**Giải pháp**:
```bash
pip install -r backend/requirements.txt
pip install nicegui
```

### Lỗi CORS

**Triệu chứng**: Frontend không gọi được API

**Giải pháp**:
- Kiểm tra CORS configuration trong `backend/app/main.py`
- Đảm bảo `allow_origins` chứa URL frontend

---

## Kiểm Tra Hệ Thống Hoạt Động

### Backend Health Check
```bash
curl http://localhost:8000/health
```

Kết quả mong đợi:
```json
{"status": "healthy"}
```

### API Documentation
Truy cập: http://localhost:8000/docs

### Frontend
Truy cập: http://localhost:8080

---

## Sao Lưu và Phục Hồi Database

### Sao Lưu
```bash
pg_dump -U postgres rescue_system > backup_$(date +%Y%m%d).sql
```

### Phục Hồi
```bash
psql -U postgres rescue_system < backup_20240101.sql
```

---

## Cập Nhật Hệ Thống

Khi có code mới:

1. Dừng servers
2. Pull code mới (nếu dùng Git)
3. Cập nhật dependencies:
   ```bash
   pip install -r backend/requirements.txt --upgrade
   ```
4. Chạy migrations (nếu có)
5. Khởi động lại servers

---

## Liên Hệ Hỗ Trợ

Nếu gặp vấn đề, kiểm tra:
- Log files trong thư mục `logs/`
- Console output khi khởi động
- PostgreSQL logs: `/var/log/postgresql/`

---

**Chúc bạn thành công!** 🚗🔧
