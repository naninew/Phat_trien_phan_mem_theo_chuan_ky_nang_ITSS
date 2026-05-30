# Hướng dẫn khởi động — Rescue24 (ITSS Roadside Assistance)

Tài liệu hướng dẫn thiết lập và chạy hệ thống từ đầu: **Backend FastAPI** + **Frontend NiceGUI**, cơ sở dữ liệu **SQLite** (không cần cài PostgreSQL để dev).

Cấu trúc chi tiết: [DETAIL_STRUCTURE.md](./DETAIL_STRUCTURE.md) · Kiểm thử: [HOW_TO_RUN_TEST.md](./HOW_TO_RUN_TEST.md)

---

## Điều kiện tiên quyết

| Yêu cầu | Ghi chú |
|---------|---------|
| **Python 3.10+** | Khuyến nghị 3.10 hoặc 3.11 |
| **Trình duyệt** | Chrome, Edge hoặc Firefox |
| **Git Bash** (Windows, tùy chọn) | Để chạy `scripts/run_project.sh` |

---

## Bước 1: Clone và cài dependency

Mở terminal tại **thư mục gốc** repository.

### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r backend\requirements.txt
```

### Linux / macOS / Git Bash

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.txt
```

File `backend/requirements.txt` gồm cả thư viện Backend (FastAPI, SQLAlchemy, JWT…) và Frontend (NiceGUI, plotly).

---

## Bước 2: Khởi tạo cơ sở dữ liệu (seed)

Script tạo file `backend/rescue_system.db`, schema đầy đủ và dữ liệu mẫu (~10 bản ghi mỗi bảng).

**Lưu ý:** Mỗi lần chạy sẽ **xóa toàn bộ dữ liệu cũ** trong DB đó.

### Windows

```powershell
.\.venv\Scripts\python backend\generate_seed_data.py
```

### Linux / macOS

```bash
.venv/bin/python backend/generate_seed_data.py
```

Muốn làm sạch thủ công: xóa `backend/rescue_system.db` rồi chạy lại lệnh trên.

**PostgreSQL (tùy chọn):** đặt `DATABASE_URL=postgresql://user:pass@host:5432/dbname` trước khi chạy seed; tham khảo `scripts/init_postgres.sql`.

---

## Bước 3: Chạy hệ thống

### Cách 1 — Một lệnh (khuyến nghị trên Linux/macOS hoặc Git Bash)

```bash
scripts/run_project.sh
```

Reset DB và nạp lại seed trước khi chạy:

```bash
scripts/run_project.sh --reset-db
```

Bỏ qua bước cài pip (đã cài sẵn):

```bash
scripts/run_project.sh --no-install
```

Script sẽ:
1. Tạo `.venv` nếu chưa có  
2. Cài `backend/requirements.txt` (trừ khi `--no-install`)  
3. Seed DB nếu chưa có file hoặc khi `--reset-db`  
4. Khởi động Backend + Frontend song song  

Nhấn **Ctrl+C** để dừng cả hai.

Nếu cổng **8000** (API) hoặc **8080** (UI) đang bận, script tự chọn cổng trống và in URL thực tế ra terminal. Khi cổng backend đổi, frontend nhận `BACKEND_URL` qua biến môi trường từ script.

### Cách 2 — Hai terminal (Windows / mọi OS)

**Terminal 1 — Backend**

Đứng tại thư mục gốc project:

```powershell
# Windows
.\.venv\Scripts\python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

```bash
# Linux / macOS
.venv/bin/python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

| Dịch vụ | URL |
|---------|-----|
| API | http://127.0.0.1:8000 |
| Swagger | http://127.0.0.1:8000/docs |
| Health | http://127.0.0.1:8000/health |

**Terminal 2 — Frontend**

```powershell
# Windows
cd frontend
$env:BACKEND_URL="http://127.0.0.1:8000/api/v1"
..\.\.venv\Scripts\python main.py
```

```bash
# Linux / macOS
cd frontend
BACKEND_URL="http://127.0.0.1:8000/api/v1" ../.venv/bin/python main.py
```

| Dịch vụ | URL mặc định |
|---------|----------------|
| Web UI | http://localhost:8080 |
| Landing | http://localhost:8080/ |
| Đăng nhập Admin | http://localhost:8080/admin-panel/login |

Đổi cổng frontend: `FRONTEND_PORT=9000` (PowerShell: `$env:FRONTEND_PORT="9000"`).

---

## Tài khoản thử nghiệm

Sau khi chạy `generate_seed_data.py`:

| Vai trò | Username | Mật khẩu | Ghi chú |
|---------|----------|----------|---------|
| **Admin** | `admin` | `Admin123!` | Đăng nhập tại `/admin-panel/login` |
| **Khách hàng** | `customer1` … `customer10` | `Pass123!` | Đăng nhập tại `/login` |
| **Công ty cứu hộ** | `company1` … `company10` | `Pass123!` | Mỗi user gắn một `RescueCompany` ở Hà Nội |

Chức năng chính theo vai trò:

- **Customer:** tìm cứu hộ gần, gửi/theo dõi yêu cầu, quản lý xe, cộng đồng, đánh giá  
- **Company:** hàng đợi, điều phối xe/nhân viên, dịch vụ, fleet  
- **Admin:** thống kê, duyệt công ty, quản lý user, báo cáo Excel/PDF, kiểm duyệt  

---

## Bước 4: Kiểm thử nhanh (tùy chọn)

Đảm bảo đã cài pytest (có trong môi trường dev hoặc `pip install pytest`).

```powershell
# Windows — từ thư mục gốc
.\.venv\Scripts\python -m pytest tests/test_sprint9_admin.py -v
.\.venv\Scripts\python -m pytest tests/test_e2e_flow.py -v
```

```bash
# Linux / macOS
.venv/bin/python -m pytest tests/test_sprint9_admin.py -v
.venv/bin/python -m pytest tests/test_e2e_flow.py -v
```

Chạy toàn bộ test: `python -m pytest -v` (xem thêm [HOW_TO_RUN_TEST.md](./HOW_TO_RUN_TEST.md)).

---

## Xử lý sự cố thường gặp

| Triệu chứng | Cách xử lý |
|-------------|------------|
| `ModuleNotFoundError: No module named 'app'` | Chạy uvicorn với `--app-dir backend` từ **thư mục gốc**, không `cd backend` rồi import sai |
| Frontend không gọi được API | Kiểm tra `BACKEND_URL` trùng cổng backend; xem log terminal backend |
| `IntegrityError` / dữ liệu lỗi | Xóa `backend/rescue_system.db`, chạy lại `generate_seed_data.py` |
| Cổng 8000 / 8080 bận | Đổi cổng (`--port` uvicorn, `FRONTEND_PORT`) hoặc tắt process đang chiếm cổng |
| Ảnh upload không hiển thị | Thư mục `backend/app/uploads/images/` phải tồn tại; backend mount `/uploads` |
| Script `.sh` không chạy trên Windows CMD | Dùng **Git Bash**, **WSL**, hoặc chạy thủ công hai terminal (Cách 2) |

---

## Tài liệu liên quan

- [README.md](./README.md) — mô tả nghiệp vụ & user stories  
- [DETAIL_STRUCTURE.md](./DETAIL_STRUCTURE.md) — cấu trúc mã, API, routes UI  
- [HOW_TO_RUN_TEST.md](./HOW_TO_RUN_TEST.md) — kiểm thử đầy đủ  
- [TO_DO.md](./TO_DO.md) — backlog sprint  

---

*Rescue24 · Hệ thống hỗ trợ sự cố xe trên đường — ITSS*
