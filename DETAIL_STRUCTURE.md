# Chi tiết cấu trúc mã nguồn — Rescue24 (Roadside Assistance System)

**Phiên bản tài liệu:** 2.0 · **Cập nhật:** 2026-05-31

---

## 1. Tổng quan kiến trúc

Hệ thống theo mô hình **3 tầng**:

| Tầng | Công nghệ | Vai trò |
|------|-----------|---------|
| **Frontend** | NiceGUI 3.x (Python) | Giao diện web theo vai trò (Customer / Company / Admin) |
| **Backend** | FastAPI 0.136 + SQLAlchemy 2.x | REST API, WebSocket chat, phục vụ file tĩnh |
| **Database** | **SQLite** (mặc định dev) · PostgreSQL (tùy chọn prod) | Lưu trữ quan hệ |

**Luồng gọi điển hình:** `NiceGUI page` → `frontend/services/*_api.py` → `httpx` → `backend/app/routes/*` → `services/*_svc.py` → `models` → DB.

**Entry points:**
- Backend: `uvicorn app.main:app --app-dir backend`
- Frontend: `frontend/main.py` (hoặc `scripts/run_project.sh` chạy cả hai)

---

## 2. Sơ đồ thư mục gốc

```
Phat_trien_phan_mem_theo_chuan_ky_nang_ITSS/
├── backend/                          # FastAPI application
│   ├── app/
│   │   ├── main.py                   # FastAPI app, CORS, mount /uploads, đăng ký routers
│   │   ├── database.py               # Engine, SessionLocal, init_db(), migration SQLite nhẹ
│   │   ├── models/                   # SQLAlchemy ORM
│   │   ├── schemas/                  # Pydantic validation
│   │   ├── services/                 # Business logic
│   │   ├── routes/                   # API routers (prefix /api/v1/...)
│   │   ├── utils/                    # JWT, response chuẩn hóa
│   │   └── uploads/images/           # Ảnh upload (avatar, chat, sự cố)
│   ├── generate_seed_data.py         # Xóa & tạo lại DB + dữ liệu mẫu (~10 dòng/bảng)
│   ├── rescue_system.db              # SQLite mặc định (tạo sau seed)
│   ├── requirements.txt            # Dependencies Backend + Frontend
│   ├── run.py                        # Wrapper chạy uvicorn
│   └── check_db.py                   # Tiện ích kiểm tra DB
│
├── frontend/                         # NiceGUI application (Rescue24 UI)
│   ├── main.py                       # Entry: theme, landing, đăng ký routes, ui.run()
│   ├── run.py                        # Wrapper chạy frontend
│   ├── core/                         # config, auth session, layouts, theme
│   ├── components/                   # navbar, sidebar, page_layout, dialog...
│   ├── pages/                        # Trang theo vai trò (@ui.page)
│   ├── services/                     # HTTP client gọi Backend API
│   └── static/                       # hero.png, assets tĩnh
│
├── tests/                            # Pytest (API, sprint, e2e, UI)
│   ├── conftest.py
│   ├── test_sprint*.py               # Kiểm thử theo sprint
│   ├── test_e2e_flow.py
│   ├── backend_tests/
│   └── ui_tests/
│
├── scripts/
│   ├── run_project.sh                # Cài deps, seed DB, chạy Backend + Frontend
│   ├── setup_project.sh
│   ├── init_postgres.sql             # Schema tham khảo PostgreSQL
│   └── run_full_system_test.py
│
├── pytest.ini                        # pythonpath=., testpaths=tests
├── README.md                         # Mô tả nghiệp vụ & use case
├── HOW_TO_START_PROJECT.md           # Hướng dẫn cài đặt & chạy
├── HOW_TO_RUN_TEST.md                # Hướng dẫn kiểm thử chi tiết
├── DETAIL_STRUCTURE.md               # File này
├── TO_DO.md                          # Backlog sprint
└── NEW_SYSTEM_DESIGN_POT.md          # Thiết kế hệ thống mở rộng
```

---

## 3. Backend (`backend/app/`)

### 3.1. `database.py`

- **`DATABASE_URL`**: mặc định `sqlite:///{backend}/rescue_system.db`; override bằng biến môi trường `DATABASE_URL` (PostgreSQL khi deploy).
- **`get_db()`**: dependency FastAPI, yield `Session`.
- **`init_db()`**: `create_all` + `_migrate_sqlite_columns()` (thêm cột mới trên SQLite không cần Alembic).
- Gọi tự động trong `@app.on_event("startup")` của `main.py`.

### 3.2. Models (`backend/app/models/`)

| File | Thực thể chính | Ghi chú |
|------|----------------|---------|
| `user.py` | `User`, `UserRole`, `AccountStatus` | customer / company_staff / admin |
| `company.py` | `RescueCompany` | Đối tác cứu hộ, tọa độ, xác minh |
| `service.py` | `Service` | Dịch vụ & giá theo công ty |
| `vehicle.py` | `Vehicle` (xe khách), `RescueVehicle` (xe cứu hộ) | |
| `staff.py` | `RescueStaff`, `StaffStatus` | Nhân viên công ty |
| `request.py` | `RescueRequest`, `RequestStatus`, `RequestService`, `ServiceAssignment` | Yêu cầu cứu hộ & gán dịch vụ |
| `payment.py` | `Payment` | Thanh toán gắn request |
| `review.py` | `Review` | Đánh giá sau cứu hộ |
| `community.py` | `CommunityPost`, `CommunityReply` | Diễn đàn tư vấn |
| `communication.py` | `Message`, `Notification` | Chat & thông báo |
| `report.py` | `Report` | Báo cáo admin đã xuất |
| `chat.py` | (legacy/aux) | Bổ trợ chat nếu dùng |

Export tập trung tại `models/__init__.py`.

### 3.3. Schemas (`backend/app/schemas/`)

| File | Nội dung |
|------|----------|
| `auth.py` | Đăng ký, đăng nhập, token, user response |
| `rescue.py` | Request, service, vehicle, company nearby |
| `community.py` | Post, reply |
| `chat.py` | Tin nhắn, notification |

### 3.4. Services (`backend/app/services/`)

| File | Trách nhiệm |
|------|-------------|
| `auth_svc.py` | Hash/verify password (bcrypt), JWT, tạo user |
| `rescue_svc.py` | Haversine, tìm công ty gần, CRUD request, ETA/giá ước tính, fleet |
| `chat_svc.py` | Tin nhắn theo request, đánh dấu đã đọc |
| `community_svc.py` | Bài viết & trả lời cộng đồng |
| `report_svc.py` | Thống kê admin, xuất Excel/PDF (openpyxl, reportlab) |
| `notification_svc.py` | Tạo/đọc thông báo hệ thống |

### 3.5. Routes (`backend/app/routes/`)

Tất cả router được `include_router(..., prefix="/api/v1")` trong `main.py`.

| Router | Prefix | File |
|--------|--------|------|
| Auth | `/api/v1/auth` | `auth_routes.py` |
| Rescue | `/api/v1/rescue` | `rescue_routes.py` |
| Profile | `/api/v1/profile` | `profile_routes.py` |
| Admin | `/api/v1/admin` | `admin_routes.py` |
| Chat | `/api/v1/chat` | `chat_routes.py` |
| Community | `/api/v1/community` | `community_routes.py` |
| WebSocket | `/api/v1/ws` | `ws_routes.py` |

**Auth** — `POST /register`, `POST /login`, `GET /me` (JWT).

**Rescue (tiêu biểu)** — `GET /services`, `GET /companies/nearby`, `POST /requests`, `GET /requests`, `GET /requests/{id}`, `PUT /requests/{id}/status`, `POST /requests/{id}/cancel`, `GET /queue`, `PUT /requests/{id}/accept|reject`, `POST /requests/{id}/assign|complete|payment`, quản lý `vehicles`, `staff`, `customer/vehicles`, `companies/{id}/full-details`.

**Profile** — `GET|PUT /me`, `POST /me/avatar`, `PUT /me/password`, `PUT /company`, CRUD `/vehicles` (xe cá nhân), upload ảnh chat.

**Admin (Sprint 8–9)** — `GET /stats`, `/stats/charts`, `/stats/daily`; báo cáo `requests`, `revenue`, `satisfaction`, `export/excel`, `export/pdf`; CRUD/suspend users & companies; duyệt `pending`; moderation reviews & community posts; `GET /requests`.

**Community** — CRUD posts, replies, đánh dấu helpful.

**Chat** — REST messages + `GET|POST /chat/{request_id}`; notifications.

**WebSocket** — `WS /api/v1/ws/chat/{request_id}` (real-time chat).

**Static files** — `GET /uploads/...` (mount từ `backend/app/uploads`).

Swagger: `http://localhost:8000/docs`

### 3.6. Utils

- `jwt_helper.py` — `create_access_token`, decode, dependency `get_current_user`.
- `response.py` — `success_response`, `error_response`, `create_json_response`.

### 3.7. `main.py`

- FastAPI **v2.0.0**, CORS `*`, startup `init_db()`.
- Health: `GET /`, `GET /health`.

---

## 4. Frontend (`frontend/`)

### 4.1. Core

| File | Mục đích |
|------|----------|
| `core/config.py` | `BACKEND_URL`, routes, `STORAGE_SECRET`, `APP_VERSION` |
| `core/auth.py` | Session NiceGUI (`app.storage.user`), `require_auth`, `require_role`, admin gate |
| `core/layouts.py` | Layout dashboard dùng chung |
| `core/theme.py` | Theme bổ sung (nếu tách từ main) |

Biến môi trường quan trọng: `BACKEND_URL` (mặc định `http://127.0.0.1:8000/api/v1`), `FRONTEND_PORT`, `STORAGE_SECRET`.

### 4.2. Services (API client)

| File | API domain |
|------|------------|
| `api_client.py` | `APIClient` — GET/POST/PUT/DELETE + Bearer token |
| `auth_api.py` | login, register, me |
| `rescue_api.py` | cứu hộ, queue, fleet, requests |
| `admin_api.py` | stats, users, companies, reports, moderation |
| `community_api.py` | posts, replies |

### 4.3. Components

- `navbar.py`, `sidebar.py` — điều hướng theo role
- `page_layout.py` — khung trang có auth
- `company_detail_dialog.py` — dialog chi tiết công ty

### 4.4. Pages & routes NiceGUI

Đăng ký trong `main.py` → `setup_app()`.

| Route | File | Vai trò |
|-------|------|---------|
| `/` | `main.py` | Landing (chưa login) |
| `/login` | `auth/login_page.py` | Đăng nhập Customer / Company |
| `/admin-panel/login` | `auth/login_page.py` | Đăng nhập Admin (UC-47) |
| `/register` | `auth/register_page.py` | Đăng ký |
| `/customer/dashboard` | `customer/dashboard.py` | Tổng quan khách |
| `/customer/find-rescue` | `customer/find_rescue.py` | Tìm công ty gần (UC003) |
| `/customer/requests` | `customer/requests.py` | Danh sách yêu cầu |
| `/customer/track/{request_id}` | `customer/track.py` | Theo dõi tiến độ |
| `/customer/vehicles` | `customer/vehicles.py` | Quản lý xe cá nhân |
| `/customer/community` | `customer/community.py` | Cộng đồng |
| `/customer/review/{request_id}` | `customer/review.py` | Đánh giá |
| `/company/dashboard` | `company/dashboard.py` | Tổng quan công ty |
| `/company/queue` | `company/queue.py` | Hàng đợi yêu cầu |
| `/company/fleet` | `company/fleet.py` | Đội xe cứu hộ |
| `/company/staff` | `company/staff.py` | Nhân viên |
| `/company/services` | `company/services_mgmt.py` | Dịch vụ & giá |
| `/company/reviews` | `company/reviews.py` | Đánh giá nhận được |
| `/company/profile` | `company/profile.py` | Hồ sơ công ty |
| `/admin/dashboard` | `admin/dashboard.py` | Dashboard admin |
| `/admin/users` | `admin/users.py` | Quản lý user |
| `/admin/users/{user_id}` | `admin/user_detail.py` | Chi tiết user |
| `/admin/companies` | `admin/companies.py` | Quản lý công ty |
| `/admin/companies/{company_id}` | `admin/company_detail.py` | Chi tiết công ty |
| `/admin/reports` | `admin/reports.py` | Báo cáo & xuất file |
| `/admin/moderation` | `admin/moderation.py` | Kiểm duyệt |
| `/admin/profile` | `admin/profile.py` | Hồ sơ admin |
| `/profile` | `shared/profile_page.py` | Hồ sơ dùng chung |

Admin routes được gom trong `pages/admin/__init__.py` → `register_admin_pages()`.

---

## 5. Kiểm thử (`tests/`)

| Nhóm | File tiêu biểu |
|------|----------------|
| Sprint API | `test_sprint4.py`, `test_sprint6_vehicles.py`, `test_sprint7_company.py`, `test_sprint8_admin.py`, `test_sprint9_admin.py` |
| E2E | `test_e2e_flow.py` |
| Backend unit | `backend_tests/test_api.py`, `test_services.py` |
| UI (Selenium) | `ui_tests/test_all_features.py`, `run_ui_tests.py` |

Chạy: `python -m pytest` (xem `HOW_TO_RUN_TEST.md`). Test sprint dùng SQLite riêng (`test_sprint9.db`, ...).

---

## 6. Scripts & vận hành

| Script | Mô tả |
|--------|--------|
| `scripts/run_project.sh` | Tạo `.venv`, pip install, seed nếu chưa có DB, chạy uvicorn + NiceGUI; `--reset-db`, `--no-install` |
| `scripts/setup_project.sh` | Thiết lập ban đầu |
| `backend/generate_seed_data.py` | Reset DB + seed (admin, customer1–10, company1–10) |

**Tài khoản seed** (in khi chạy xong script):
- Admin: `admin` / `Admin123!`
- Khách & công ty: `customer1`…`customer10`, `company1`…`company10` / `Pass123!`

---

## 7. Luồng dữ liệu điển hình

### 7.1. Đăng nhập

```
/login → auth_api.login → POST /api/v1/auth/login
  → auth_svc.authenticate_user + generate_tokens
  → frontend login_user() lưu token vào app.storage.user
  → redirect /customer/dashboard | /company/dashboard | /admin/dashboard
```

### 7.2. Gửi yêu cầu cứu hộ

```
/customer/find-rescue → GET /rescue/companies/nearby (Haversine)
  → chọn công ty → POST /rescue/requests
  → redirect /customer/track/{id} (polling / WebSocket chat)
```

### 7.3. Công ty xử lý

```
/company/queue → GET /rescue/queue
  → PUT accept → POST assign (vehicle/staff)
  → PUT status (en_route → on_site → completed)
  → POST payment / customer review
```

### 7.4. Admin

```
/admin-panel/login → /admin/dashboard
  → admin_api → /api/v1/admin/stats, /users, /companies/pending, /reports/export/*
```

---

## 8. Bảo mật & phân quyền

- Mật khẩu: **bcrypt** (`passlib`).
- API: **JWT Bearer** (`Authorization: Bearer <token>`).
- Frontend: session NiceGUI; `require_role()` — admin truy cập mọi trang admin.
- Upload ảnh: lưu local `backend/app/uploads/images/`, phục vụ qua `/uploads`.

---

## 9. Cơ sở dữ liệu (tóm tắt bảng)

1. `users`  
2. `rescue_companies`  
3. `services`  
4. `vehicles` (xe khách hàng)  
5. `rescue_vehicles`  
6. `rescue_staff`  
7. `rescue_requests`  
8. `request_services`, `service_assignments`  
9. `payments`  
10. `reviews`  
11. `community_posts`, `community_replies`  
12. `messages`, `notifications`  
13. `reports`  

Quan hệ chính: User 1—N Request; Company 1—N Service/Vehicle/Staff; Request 1—1 Payment/Review.

---

## 10. Biến môi trường

| Biến | Mặc định | Ý nghĩa |
|------|----------|---------|
| `DATABASE_URL` | `sqlite:///.../backend/rescue_system.db` | Chuỗi kết nối DB |
| `BACKEND_URL` | `http://127.0.0.1:8000/api/v1` | URL API cho frontend |
| `FRONTEND_PORT` | `8080` | Cổng NiceGUI |
| `BACKEND_PORT` / `BACKEND_HOST` | `8000` / `127.0.0.1` | Dùng trong `run_project.sh` |
| `STORAGE_SECRET` | (dev placeholder) | Secret session NiceGUI — **đổi khi production** |
| `SQL_ECHO` | `false` | Log SQLAlchemy |

---

## 11. Mapping Use Case ↔ Module (tham chiếu)

| UC | Backend | Frontend |
|----|---------|----------|
| UC001–002 | `auth_routes`, `auth_svc` | `login_page`, `register_page` |
| UC003–008 | `rescue_routes`, `rescue_svc` | `find_rescue`, `requests`, `track`, `review` |
| UC009 | `community_routes` | `community` |
| UC010–011 | `rescue_routes` (fleet, queue) | `fleet`, `queue`, `staff` |
| UC012–016 | `admin_routes`, `report_svc` | `users`, `companies`, `moderation`, `reports` |
| Chat | `chat_routes`, `ws_routes` | track + chat UI |
| UC047 | — | `/admin-panel/login` |

Chi tiết nghiệp vụ: `README.md`, `NEW_SYSTEM_DESIGN_POT.md`, `TO_DO.md`.

---

*Tài liệu phản ánh trạng thái codebase tại Sprint 9 (Admin API, báo cáo Excel/PDF, moderation).*
