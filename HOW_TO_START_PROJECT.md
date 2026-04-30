# Hướng Dẫn Khởi Động Dự Án - Roadside Rescue System

## Tổng quan

Dự án sử dụng:
- **Frontend**: NiceGUI (Python web framework)
- **Backend**: FastAPI (REST API)
- **Database**: PostgreSQL
- **File Storage**: Local filesystem cho images

---

## Bước 1: Cài Đặt PostgreSQL

### Trên Ubuntu/Debian:
```bash
# Cài đặt PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib -y

# Khởi động PostgreSQL service
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Kiểm tra status
sudo systemctl status postgresql
```

### Trên Windows:
1. Tải PostgreSQL từ: https://www.postgresql.org/download/windows/
2. Chạy installer và làm theo hướng dẫn
3. Ghi nhớ password cho user `postgres`

### Trên macOS:
```bash
# Sử dụng Homebrew
brew install postgresql
brew services start postgresql
```

---

## Bước 2: Tạo Database và Cấu Hình

### Cách 1: Sử dụng script tự động (khuyến nghị)
```bash
cd /workspace/scripts

# Chạy script SQL để tạo database và tables
sudo -u postgres psql -f init_postgres.sql
```

### Cách 2: Thủ công
```bash
# Đăng nhập vào PostgreSQL
sudo -u postgres psql

# Trong PostgreSQL prompt:
CREATE DATABASE rescue_system;
\c rescue_system

# Chạy các lệnh CREATE TABLE từ scripts/init_postgres.sql
# (copy và paste nội dung file SQL)

# Thoát
\q
```

### Xác nhận database đã tạo:
```bash
sudo -u postgres psql -lqt | grep rescue_system
```

---

## Bước 3: Cài Đặt Dependencies

```bash
cd /workspace

# Cài đặt backend dependencies
pip install -r backend/requirements.txt

# Nếu frontend có requirements.txt riêng
# pip install -r frontend/requirements.txt
```

**Các packages chính:**
- FastAPI, Uvicorn (backend)
- SQLAlchemy, psycopg2-binary (database)
- Passlib, PyJWT (authentication)
- NiceGUI (frontend)
- Python-multipart (file uploads)

---

## Bước 4: Cấu Hình Kết Nối Database

Chỉnh sửa file `/workspace/backend/app/database.py`:

```python
DATABASE_URL = "postgresql://postgres:YOUR_PASSWORD@localhost:5432/rescue_system"
```

Thay `YOUR_PASSWORD` bằng password của user postgres.

---

## Bước 5: Khởi Động Backend Server

```bash
cd /workspace/backend

# Chạy backend với auto-reload
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Kiểm tra backend:**
- Mở browser truy cập: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

---

## Bước 6: Khởi Động Frontend Server

Mở terminal mới:

```bash
cd /workspace/frontend

# Chạy frontend NiceGUI
python -m nicegui.run --host 0.0.0.0 --port 8080
```

Hoặc:
```bash
python frontend/run.py
```

**Kiểm tra frontend:**
- Truy cập: http://localhost:8080

---

## Bước 7: Tạo Tài Khoản Admin Đầu Tiên

Tài khoản admin đã được tạo tự động khi chạy script init_postgres.sql:

**Thông tin đăng nhập:**
- Username: `admin`
- Password: `admin123`
- Role: admin

**Tài khoản customer mẫu:**
- Username: `customer`
- Password: `customer123`
- Role: customer

Để tạo thêm user, sử dụng API endpoint hoặc NiceGUI registration page.

---

## Bước 8: Upload Images

Thư mục lưu trữ images: `/workspace/backend/app/uploads/images/`

Các API endpoints cho upload:
- `POST /api/v1/profile/me/avatar` - Upload avatar user
- `POST /api/v1/profile/chat/{request_id}/image` - Upload image trong chat

Images sẽ được truy cập qua: `http://localhost:8000/uploads/images/{filename}`

---

## Chạy Tất Cả Cùng Lúc (Script Tự Động)

```bash
cd /workspace/scripts

# Chạy script setup với menu tương tác
./setup_project.sh
```

Hoặc chạy nền:
```bash
# Backend
cd /workspace/backend
nohup python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &

# Frontend
cd /workspace/frontend
nohup python -m nicegui.run --host 0.0.0.0 --port 8080 > frontend.log 2>&1 &
```

---

## Xử Lý Sự Cố

### Lỗi kết nối database:
```bash
# Kiểm tra PostgreSQL đang chạy
sudo systemctl status postgresql

# Restart PostgreSQL
sudo systemctl restart postgresql

# Kiểm tra credentials trong database.py
```

### Lỗi port đã sử dụng:
```bash
# Kiểm tra port đang dùng
lsof -i :8000
lsof -i :8080

# Kill process
kill -9 <PID>
```

### Lỗi dependencies:
```bash
# Upgrade pip
pip install --upgrade pip

# Reinstall dependencies
pip install -r backend/requirements.txt --force-reinstall
```

### Lỗi permissions thư mục uploads:
```bash
mkdir -p /workspace/backend/app/uploads/images
chmod 755 /workspace/backend/app/uploads
chmod 755 /workspace/backend/app/uploads/images
```

---

## Deploy Production

### Sử dụng Supervisor (Ubuntu/Debian):

1. Cài supervisor:
```bash
sudo apt install supervisor -y
```

2. Tạo config file backend `/etc/supervisor/conf.d/rescue_backend.conf`:
```ini
[program:rescue_backend]
command=/usr/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
directory=/workspace/backend
user=root
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/rescue/backend.log
```

3. Tạo config file frontend `/etc/supervisor/conf.d/rescue_frontend.conf`:
```ini
[program:rescue_frontend]
command=/usr/bin/python3 -m nicegui.run --host 0.0.0.0 --port 8080
directory=/workspace/frontend
user=root
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/rescue/frontend.log
```

4. Khởi động:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start rescue_backend
sudo supervisorctl start rescue_frontend
sudo supervisorctl status
```

### Sử dụng Nginx làm Reverse Proxy:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /uploads/ {
        proxy_pass http://localhost:8000/uploads/;
    }
}
```

---

## API Endpoints Chính

### Authentication:
- `POST /api/v1/auth/register` - Đăng ký user mới
- `POST /api/v1/auth/login` - Đăng nhập
- `GET /api/v1/auth/me` - Lấy thông tin user hiện tại

### Profile:
- `GET /api/v1/profile/me` - Lấy profile user
- `PUT /api/v1/profile/me` - Cập nhật profile
- `POST /api/v1/profile/me/avatar` - Upload avatar
- `PUT /api/v1/profile/company` - Cập nhật company profile (company staff only)
- `POST /api/v1/profile/chat/{request_id}/image` - Upload chat image

### Rescue Services:
- `GET /api/v1/rescue/companies/nearby` - Tìm công ty gần đó
- `POST /api/v1/rescue/requests` - Tạo rescue request
- `GET /api/v1/rescue/requests` - Xem danh sách requests
- `GET /api/v1/rescue/requests/{id}` - Xem chi tiết request
- `PUT /api/v1/rescue/requests/{id}/status` - Cập nhật status
- `POST /api/v1/rescue/requests/{id}/cancel` - Hủy request

---

## Thông Tin Quan Trọng

| Service | URL | Port |
|---------|-----|------|
| Frontend (NiceGUI) | http://localhost:8080 | 8080 |
| Backend API | http://localhost:8000 | 8000 |
| API Documentation | http://localhost:8000/docs | 8000 |
| PostgreSQL | localhost:5432 | 5432 |

**Default Credentials:**
- Admin: `admin` / `admin123`
- Customer: `customer` / `customer123`

**Upload Directory:** `/workspace/backend/app/uploads/images/`

---

## Kiểm Tra Nhanh

```bash
# 1. Kiểm tra PostgreSQL
sudo -u postgres psql -c "\l" | grep rescue_system

# 2. Kiểm tra backend
curl http://localhost:8000/health

# 3. Kiểm tra frontend
curl http://localhost:8080

# 4. Test login API
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

Nếu tất cả đều OK, bạn đã setup thành công! 🎉
