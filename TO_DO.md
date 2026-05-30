# Kế hoạch triển khai Hệ thống ITSS (Intelligent Traffic Support System)

Dựa trên tài liệu `DETAIL_STRUCTURE.md` (hiện tại) và `NEW_SYSTEM_DESIGN_POT.md` (thiết kế mới), dưới đây là kế hoạch chi tiết từng sprint để chuyển đổi và nâng cấp hệ thống.

**Mục tiêu cốt lõi:**
- Sử dụng **SQLite** thay vì PostgreSQL.
- Xây dựng Frontend sử dụng **NiceGUI** kết hợp **Vue** và **Quasar** cho custom UI.
- Tái cấu trúc theo đúng thiết kế mới nhưng giữ lượng code cần sửa đổi ở mức tối thiểu.
- Ưu tiên: Database & Seed Data -> Backend APIs -> Frontend.

---

## Sprint 1: Cấu trúc Database & Dữ liệu Demo (Seed Data)
**Sprint Goal:** Chuyển đổi toàn bộ schema database sang SQLite, hỗ trợ đầy đủ các Entity mới và có script tạo dữ liệu demo cho tất cả các tính năng.

- `[x]` **Task 1.1**: Đổi cấu hình kết nối database trong `database.py` sang dùng SQLite thuần (`sqlite:///./rescue_system.db`).
- `[x]` **Task 1.2**: Cập nhật mô hình dữ liệu tài khoản (`models/user.py`, `models/company.py`) theo thiết kế mới (thêm `Account` attributes, trạng thái `ACTIVE/INACTIVE/SUSPENDED`).
- `[x]` **Task 1.3**: Thêm các mô hình mới cho Customer: `Vehicle`.
- `[x]` **Task 1.4**: Cập nhật mô hình `RescueCompany`, `RescueService`, `RescueVehicle`.
- `[x]` **Task 1.5**: Thêm các mô hình mới cho phân công và nhân sự: `RescueStaff`, `ServiceAssignment`.
- `[x]` **Task 1.6**: Cập nhật mô hình `RescueRequest` (thêm các field về giá, thời gian, và state machine mới) và thêm `RequestService` (bảng trung gian).
- `[x]` **Task 1.7**: Cập nhật các bảng phụ trợ: `Payment`, `Review`, `Message`, `Notification`, `CommunityPost`, `CommunityReply` (đổi từ Comment), `Report`.
- `[x]` **Task 1.8**: Sửa file `generate_seed_data.py` để tự động insert dữ liệu mẫu cho TẤT CẢ các bảng vừa tạo (User demo các role, công ty demo, xe, yêu cầu cứu hộ các trạng thái, tin nhắn, thông báo, bài viết cộng đồng...).

**Files Context:**
- `backend/app/database.py`
- `backend/app/models/*.py`
- `backend/generate_seed_data.py`

---

## Sprint 2: Backend APIs - Authentication & Quản lý danh mục cơ bản
**Sprint Goal:** Hoàn thiện luồng xác thực (Auth) và các API CRUD cơ bản cho các entity phụ trợ (Xe, Dịch vụ, Nhân viên, Phương tiện).

- `[x]` **Task 2.1**: Cập nhật schema & API Đăng ký/Đăng nhập cho 3 role (Customer, Company, Admin) (`auth_schemas`, `auth_svc.py`, `auth_routes.py`).
- `[x]` **Task 2.2**: Xây dựng CRUD API quản lý Xe (Vehicle) cho Customer.
- `[x]` **Task 2.3**: Xây dựng CRUD API quản lý Dịch vụ (`RescueService`) cho RescueCompany.
- `[x]` **Task 2.4**: Xây dựng CRUD API quản lý Phương tiện (`RescueVehicle`) và Nhân viên (`RescueStaff`) cho RescueCompany.
- `[x]` **Task 2.5**: Xây dựng API Quản lý tài khoản (Admin) (Khóa/Mở khóa User/Company, Xác minh Company).

**Files Context:**
- `backend/app/schemas/auth.py`, `backend/app/schemas/rescue.py`
- `backend/app/services/auth_svc.py`, `backend/app/services/rescue_svc.py`
- `backend/app/routes/auth_routes.py`, `backend/app/routes/rescue_routes.py`

---

## Sprint 3: Quản lý Yêu cầu cứu hộ & Phân công (Hoàn thành)
**Mục tiêu:** Xây dựng State Machine cho luồng cứu hộ, phân công nhân viên và xe.

- [x] **Task 3.1:** Cấu trúc lại bảng `RescueRequest` để hỗ trợ đa dịch vụ (bảng `RequestService`).
- [x] **Task 3.2:** Cập nhật logic tìm kiếm công ty (`find_nearby_companies`) dựa trên danh sách dịch vụ yêu cầu và bán kính.
- [x] **Task 3.3:** Xây dựng logic API Phân công (Assign) tạo `ServiceAssignment` liên kết Staff & Vehicle với Request.
- [x] **Task 3.4:** Viết các API cho công ty cứu hộ: `GET /queue`, `PUT /accept`, `PUT /reject`.
- [x] **Task 3.5:** Cập nhật API cập nhật trạng thái (`PUT /status`): Chuyển trạng thái từ Pending -> Accepted -> Assigned -> On The Way -> In Progress -> Completed.
- [x] **Task 3.6:** Bổ sung API Thanh toán cơ bản (`POST /payment`) và Đánh giá (`POST /review`).
- [x] **Task 3.7:** Xử lý logic giải phóng Staff và Vehicle khi Request hoàn thành hoặc bị Hủy.
- [x] **Task 3.8:** Tích hợp kiểm thử Backend (`pytest`): Viết test case luồng từ Tạo Request -> Tìm Công ty -> Tiếp nhận -> Phân công -> Hoàn thành.

---

## Sprint 4: Backend APIs - Tính năng mở rộng
**Sprint Goal:** Hoàn thiện API cho các tính năng Notification, Chat, Community và Reporting.

- [x] **Task 4.1**: API Gửi và Lấy danh sách Tin nhắn (`Message`) theo `requestId`.
- [x] **Task 4.2**: API Lấy danh sách và đánh dấu đã đọc Thông báo (`Notification`).
- [x] **Task 4.3**: API Quản lý Cộng đồng (Đăng bài `CommunityPost`, Phản hồi `CommunityReply`, Đóng bài).
- [x] **Task 4.4**: API Thống kê và Báo cáo (Dành cho Admin và Dashboard của Company).

**Files Context:**
- `backend/app/schemas/community.py`, `backend/app/schemas/chat.py` (tạo mới)
- `backend/app/services/community_svc.py`, `backend/app/services/chat_svc.py` (tạo mới)
- `backend/app/routes/community_routes.py`, `backend/app/routes/chat_routes.py` (tạo mới)

---

## Sprint 5: Frontend - Khởi tạo Base Layout & Authentication
**Sprint Goal:** Cấu hình base cho NiceGUI kết hợp custom Vue/Quasar, tích hợp hoàn chỉnh trang Auth.

- [x] **Task 5.1**: Cấu hình file `main.py` và `frontend/core/config.py` để import và bind các UI component Vue/Quasar (như QTable, QCard, QTimeline) nếu NiceGUI thuần chưa hỗ trợ tốt.
- [x] **Task 5.2**: Xây dựng `navbar.py` và `sidebar.py` hỗ trợ render động theo 3 Role.
- [x] **Task 5.3**: Xây dựng UI Trang Đăng nhập (`login.py`) và Trang Đăng ký (`register.py` - tab phân tách Customer/Company).
- [x] **Task 5.4**: Tích hợp gọi API Authentication và lưu Session state.

**Files Context:**
- `frontend/main.py`, `frontend/core/auth.py`, `frontend/core/config.py`
- `frontend/components/navbar.py`
- `frontend/pages/auth/*.py`

---

## Sprint 6: Frontend - Customer Portal
**Sprint Goal:** Hoàn thiện các trang dành cho Khách hàng sử dụng dịch vụ.

- [x] **Task 6.1**: Giao diện Dashboard & Quản lý Xe cá nhân (thêm, sửa, xoá).
- [x] **Task 6.2**: Giao diện Yêu cầu Cứu hộ (Form step-by-step: Chọn xe -> Chọn vị trí trên Bản đồ Leaflet -> Mô tả -> Chọn Company từ danh sách matching).
- [x] **Task 6.3**: Giao diện Theo dõi Yêu cầu (Hiển thị UI Timeline thay đổi trạng thái realtime, khung Chat mini).
- [x] **Task 6.4**: Giao diện Xác nhận Hoàn thành, form Thanh toán, và màn hình Đánh giá sao.
- [x] **Task 6.5**: Giao diện Lịch sử yêu cầu và Diễn đàn Cộng đồng (Community).

**Files Context:**
- `frontend/pages/customer/*.py`
- `frontend/services/rescue_api.py`

---

## Sprint 7: Frontend - Company Portal
**Sprint Goal:** Hoàn thiện các trang quản lý nghiệp vụ dành cho Công ty cứu hộ.

- [x] **Task 7.1**: Giao diện Company Dashboard (Thống kê card UI).
- [x] **Task 7.2**: Giao diện Tiếp nhận Yêu cầu (Queue) (Hiển thị list thẻ yêu cầu pending, popup accept/reject).
- [x] **Task 7.3**: Giao diện Phân công nhiệm vụ (Dropdown chọn xe và nhân viên `AVAILABLE`).
- [x] **Task 7.4**: Giao diện Cập nhật trạng thái sự cố (Nút bấm update state từ `ASSIGNED` -> `COMPLETED`).
- [x] **Task 7.5**: Giao diện CRUD quản lý Dịch vụ, Phương tiện, Nhân sự.
- [x] **Task 7.6**: Giao diện Danh sách Đánh giá (Review) nhận được.

**Files Context:**
- `frontend/pages/company/*.py`

---

## Sprint 8: Frontend - Admin Portal & Final Testing
**Sprint Goal:** Hoàn thiện trang Admin quản trị toàn hệ thống và test End-to-End.

- [x] **Task 8.1**: Giao diện Admin Dashboard (Biểu đồ thống kê toàn hệ thống bằng Quasar Charts / Echarts).
- [x] **Task 8.2**: Giao diện Quản lý Khách hàng và Công ty (Data table với tính năng lọc, nút Duyệt/Khoá tài khoản).
- [x] **Task 8.3**: Giao diện Kiểm duyệt nội dung (Đánh giá, Diễn đàn).
- [x] **Task 8.4**: Giao diện Xem và Xuất Báo cáo.
- [x] **Task 8.5**: Kiểm thử toàn trình (End-to-End Testing): Chạy thử từ việc Đăng ký -> Tạo yêu cầu -> Nhận -> Xử lý -> Thanh toán.

**Files Context:**
- `frontend/pages/admin/*.py`
- `tests/test_sprint8_admin.py`
- `tests/test_e2e_flow.py`

---

## Sprint 9: Hoàn thiện Chức năng Admin — Kiểm tra & Cập nhật theo UseCase
> **Mục tiêu:** Đối chiếu từng UseCase (UC-47 → UC-64) với code hiện tại, phát hiện thiếu sót và bổ sung hoàn chỉnh cho toàn bộ chức năng Admin theo đúng đặc tả.

---

### 9.1 — UC-47: Đăng nhập Admin (Chức năng 3.1)
> **Hiện trạng:** Trang login chung tại `/login` đã hoạt động, nhưng chưa có route riêng `/admin-panel/login` và chưa có guard redirect đúng theo đặc tả.

- `[x]` **Task 9.1.1 [Backend]**: Kiểm tra API `POST /auth/login` — đảm bảo khi tài khoản bị SUSPENDED, backend trả về lỗi rõ ràng với message `"Tài khoản đã bị khóa"` (không phải `"Invalid credentials"`). Hiện tại `auth_svc.authenticate_user()` trả về `None` cho cả 2 trường hợp sai mật khẩu và bị khóa — cần phân biệt.
  - **File:** `backend/app/services/auth_svc.py` → hàm `authenticate_user()`
  - **Cần làm:** Tách lý do từ chối: sai mật khẩu vs tài khoản bị khóa. Trả về raise `HTTPException` với code và message riêng biệt.
  - **File:** `backend/app/routes/auth_routes.py` → endpoint `POST /auth/login`

- `[x]` **Task 9.1.2 [Frontend]**: Tạo route `/admin-panel/login` riêng biệt (alias hoặc redirect từ trang login chung).
  - **Cần làm:** Trong `frontend/pages/auth/login_page.py`, thêm decorator `@ui.page('/admin-panel/login')` với cùng nội dung trang login, nhưng sau khi đăng nhập thành công với role=admin thì redirect về `/admin/dashboard`.
  - Đảm bảo guard: nếu đã đăng nhập với role admin mà truy cập `/admin-panel/login` thì redirect thẳng về `/admin/dashboard`.

- `[x]` **Task 9.1.3 [Frontend]**: Bổ sung middleware/guard bảo vệ toàn bộ route `/admin/*`.
  - **Cần làm:** Hàm `require_role("admin")` trong `frontend/core/auth.py` đã tồn tại nhưng cần kiểm tra: nếu chưa đăng nhập thì redirect về `/admin-panel/login` (không phải `/login` chung).
  - **File:** `frontend/core/auth.py` → hàm `require_role()`

---

### 9.2 — UC-48: Dashboard Admin (Chức năng 3.2)
> **Hiện trạng:** Dashboard cơ bản đã có tại `frontend/pages/admin/dashboard.py`. Thiếu: bảng công ty chờ xác minh, thống kê yêu cầu theo trạng thái rõ ràng, biểu đồ bar chart 7 ngày gần nhất, và số liệu "yêu cầu hôm nay".

- `[x]` **Task 9.2.1 [Backend]**: Cập nhật API `GET /admin/stats` để bổ sung thêm các trường:
  - `requests_today`: số yêu cầu được tạo trong ngày hôm nay.
  - `revenue_this_month`: tổng doanh thu tháng hiện tại (từ `Payment.status == "PAID"`).
  - `pending_companies`: số công ty có `is_verified=False` và `status != "suspended"`.
  - `requests_by_status`: dict đếm theo từng trạng thái `{PENDING: N, IN_PROGRESS: N, COMPLETED: N, ...}`.
  - **File:** `backend/app/services/report_svc.py` → hàm `get_admin_stats()`
  - **File:** `backend/app/routes/admin_routes.py` → endpoint `GET /admin/stats`

- `[x]` **Task 9.2.2 [Backend]**: Tạo API mới `GET /admin/stats/daily?days=7` trả về số lượng yêu cầu theo từng ngày trong 7 ngày gần nhất.
  - **Trả về:** `{ labels: ["2025-01-25", ...], values: [12, 8, ...] }`
  - **File:** `backend/app/services/report_svc.py` → thêm hàm `get_daily_request_stats(db, days=7)`
  - **File:** `backend/app/routes/admin_routes.py` → thêm endpoint `GET /admin/stats/daily`

- `[x]` **Task 9.2.3 [Backend]**: Tạo API `GET /admin/companies/pending` trả về danh sách công ty chờ xác minh (`is_verified=False`, `status != "suspended"`), để hiển thị trong bảng dashboard.
  - **Trả về mỗi item:** `{id, company_name, representative_name, phone, registered_at, business_license_url}`
  - **File:** `backend/app/routes/admin_routes.py` → thêm endpoint `GET /admin/companies/pending`

- `[x]` **Task 9.2.4 [Frontend]**: Cập nhật `frontend/pages/admin/dashboard.py`:
  - Thêm stat card **"Yêu cầu hôm nay"** và **"Doanh thu tháng"** (lấy từ API mới).
  - Thêm **bảng "Công ty chờ xác minh"** (lấy từ `GET /admin/companies/pending`) với các cột: Tên công ty, Người đại diện, SĐT, Ngày đăng ký, và 2 nút inline **"Duyệt"** / **"Từ chối"**.
  - Thêm **section "Yêu cầu theo trạng thái"**: hiển thị 3 thẻ mini: Pending / In Progress / Completed với số lượng tương ứng.
  - Thêm **biểu đồ bar chart "Yêu cầu 7 ngày gần đây"** sử dụng `ui.echart` với `type: 'bar'`, data từ API `GET /admin/stats/daily`.
  - **File:** `frontend/pages/admin/dashboard.py`
  - **File:** `frontend/services/admin_api.py` → thêm hàm `get_daily_stats()`, `get_pending_companies()`

---

### 9.3 — UC-49, UC-50, UC-51, UC-52: Quản lý tài khoản khách hàng (Chức năng 3.3)
> **Hiện trạng:** Trang `frontend/pages/admin/users.py` đã có list users với search và filter theo role. Thiếu: filter theo status (ACTIVE/INACTIVE/SUSPENDED), phân trang, hiển thị "số yêu cầu đã tạo", trang chi tiết khách hàng, và luồng khóa/mở khóa với nhập lý do bắt buộc + ràng buộc yêu cầu chưa hoàn thành.

#### UC-49: Danh sách khách hàng
- `[x]` **Task 9.3.1 [Backend]**: Cập nhật `GET /admin/users` để:
  - Filter **chỉ theo role=customer** khi gọi từ trang quản lý khách hàng (thêm query param `role=customer` mặc định).
  - Hỗ trợ filter theo `status` (ACTIVE / INACTIVE / SUSPENDED) qua query param `status_filter`.
  - Hỗ trợ tìm kiếm theo `phone` (bổ sung thêm vào điều kiện `ilike` hiện tại).
  - Bổ sung trường `request_count` (số yêu cầu đã tạo) vào response — dùng subquery đếm `RescueRequest` theo `user_id`.
  - Bổ sung phân trang: query params `page` (default=1) và `page_size` (default=20); trả về thêm `total`, `page`, `page_size`.
  - **File:** `backend/app/routes/admin_routes.py` → endpoint `GET /admin/users`

- `[x]` **Task 9.3.2 [Frontend]**: Cập nhật `frontend/pages/admin/users.py` (filter chỉ xem khách hàng):
  - Thêm dropdown **"Lọc theo trạng thái"** với options: Tất cả / ACTIVE / INACTIVE / SUSPENDED.
  - Thêm trường tìm kiếm theo **SĐT** (bên cạnh tên và email hiện tại).
  - Mỗi dòng user card bổ sung hiển thị: **Số yêu cầu đã tạo** (badge).
  - Thêm **phân trang** (pagination component) hiển thị 20 dòng/trang.
  - **File:** `frontend/pages/admin/users.py`
  - **File:** `frontend/services/admin_api.py` → cập nhật hàm `get_users()` để truyền params filter

#### UC-50: Chi tiết khách hàng
- `[x]` **Task 9.3.3 [Backend]**: Tạo API `GET /admin/users/{user_id}/detail` trả về thông tin đầy đủ của một khách hàng:
  - Thông tin cá nhân: `full_name, email, phone, address, created_at, status`.
  - `vehicles`: danh sách xe đã đăng ký (plate, brand, model, year).
  - `recent_requests`: 5 yêu cầu gần nhất (id, status, incident_type, created_at, company_name, total_cost).
  - `payment_history`: lịch sử thanh toán (request_id, amount, method, status, created_at).
  - `reviews_written`: danh sách đánh giá đã viết (company_name, rating, comment, created_at).
  - **File:** `backend/app/routes/admin_routes.py` → thêm endpoint `GET /admin/users/{user_id}/detail`

- `[x]` **Task 9.3.4 [Frontend]**: Tạo trang mới `frontend/pages/admin/user_detail.py`:
  - Route: `/admin/users/{user_id}`
  - Hiển thị các section: **Thông tin cá nhân** / **Xe đã đăng ký** (table) / **Lịch sử yêu cầu** (5 gần nhất, table) / **Lịch sử thanh toán** (table) / **Đánh giá đã viết** (cards).
  - Nút **"Khóa tài khoản"** / **"Mở khóa"** trên header trang.
  - Nút back về danh sách.
  - **File tạo mới:** `frontend/pages/admin/user_detail.py`
  - **File:** `frontend/services/admin_api.py` → thêm hàm `get_user_detail(user_id)`
  - **File:** `frontend/pages/admin/users.py` → sửa click vào card → navigate tới `/admin/users/{id}`
  - **File:** `frontend/pages/admin/__init__.py` → đăng ký page mới

#### UC-51: Khóa tài khoản khách hàng
- `[x]` **Task 9.3.5 [Backend]**: Cập nhật API khóa tài khoản (`PUT /admin/users/{user_id}/status` hoặc tạo riêng `PUT /admin/users/{user_id}/suspend`):
  - **Nhận thêm body:** `{ "reason": "string" }` — bắt buộc, không để trống.
  - **Kiểm tra ràng buộc:** nếu user đang có RescueRequest với status không phải COMPLETED / CANCELLED / REJECTED thì trả về lỗi 400 `"Không thể khóa tài khoản đang có yêu cầu chưa hoàn thành"`.
  - Cập nhật `user.status = SUSPENDED`, lưu `reason` vào field `suspend_reason` (cần thêm field này vào model nếu chưa có).
  - **File:** `backend/app/models/user.py` → thêm field `suspend_reason: Optional[str]`
  - **File:** `backend/app/routes/admin_routes.py` → sửa/thêm endpoint `PUT /admin/users/{user_id}/suspend`

- `[x]` **Task 9.3.6 [Frontend]**: Cập nhật dialog khóa tài khoản trong `user_detail.py` và `users.py`:
  - Thay thế switch toggle hiện tại bằng dialog xác nhận có **ô nhập lý do** (bắt buộc, min 10 ký tự).
  - Nút **"Xác nhận khóa"** chỉ enable khi đã nhập lý do.
  - Sau khi khóa thành công: cập nhật badge status trên UI, hiển thị notify "Đã khóa tài khoản".
  - Nếu backend trả lỗi ràng buộc → hiển thị message lỗi rõ ràng.
  - **File:** `frontend/pages/admin/user_detail.py`
  - **File:** `frontend/pages/admin/users.py`

#### UC-52: Mở khóa tài khoản khách hàng
- `[x]` **Task 9.3.7 [Backend]**: Tạo/cập nhật API `PUT /admin/users/{user_id}/activate`:
  - Chuyển `user.status = ACTIVE`, xóa `suspend_reason`.
  - **File:** `backend/app/routes/admin_routes.py`

- `[x]` **Task 9.3.8 [Frontend]**: Thêm nút **"Mở khóa"** (hiển thị khi status=SUSPENDED):
  - Dialog xác nhận đơn giản (không cần nhập lý do).
  - Sau khi mở khóa: cập nhật UI.
  - **File:** `frontend/pages/admin/user_detail.py`, `frontend/pages/admin/users.py`

---

### 9.4 — UC-53, UC-54, UC-55, UC-56, UC-57: Quản lý công ty cứu hộ (Chức năng 3.4)
> **Hiện trạng:** Trang `frontend/pages/admin/companies.py` đã có list với filter status và search theo tên. Thiếu: filter theo khu vực, trang chi tiết công ty, luồng Xác minh/Từ chối với nhập lý do, Notification gửi cho công ty, và ràng buộc khóa khi có yêu cầu đang xử lý.

#### UC-53: Danh sách công ty
- `[ ]` **Task 9.4.1 [Backend]**: Cập nhật `GET /admin/companies`:
  - Thêm filter theo `area` (khu vực/tỉnh thành) — thêm query param `area`.
  - Bổ sung trường response: `representative_name` (người đại diện), `registered_at` (ngày đăng ký), `rating` (rating_avg), `status_verified` (is_verified).
  - Filter theo trạng thái xác minh: `verified_filter` = `pending` (is_verified=False, status≠suspended) | `verified` (is_verified=True) | `rejected` (status=suspended).
  - **File:** `backend/app/routes/admin_routes.py` → endpoint `GET /admin/companies`

- `[ ]` **Task 9.4.2 [Frontend]**: Cập nhật `frontend/pages/admin/companies.py`:
  - Thêm dropdown **"Lọc theo xác minh"**: Chờ duyệt / Đã xác minh / Bị từ chối.
  - Thêm dropdown **"Khu vực hoạt động"** (tỉnh/thành phố).
  - Mỗi dòng card bổ sung: Người đại diện, SĐT, Ngày đăng ký, Rating (sao).
  - Click vào card → navigate tới `/admin/companies/{id}`.
  - **File:** `frontend/pages/admin/companies.py`

#### UC-54: Chi tiết công ty
- `[ ]` **Task 9.4.3 [Backend]**: Tạo API `GET /admin/companies/{company_id}/detail`:
  - Thông tin đầy đủ: `company_name, representative_name, phone, hotline, address, area, business_license, is_verified, status, rating_avg, rating_count, created_at`.
  - `services`: danh sách dịch vụ (name, price_range).
  - `vehicles`: danh sách xe cứu hộ (plate, type, status).
  - `staff`: danh sách nhân viên (name, role, status).
  - `recent_requests`: 10 yêu cầu gần nhất (id, customer_name, status, incident_type, created_at, total_cost).
  - `reviews`: tất cả đánh giá nhận được (customer_name, rating, comment, created_at).
  - **File:** `backend/app/routes/admin_routes.py` → thêm `GET /admin/companies/{company_id}/detail`

- `[ ]` **Task 9.4.4 [Frontend]**: Tạo trang mới `frontend/pages/admin/company_detail.py`:
  - Route: `/admin/companies/{company_id}`
  - Tabs: **Thông tin** / **Dịch vụ & Xe** / **Nhân sự** / **Lịch sử yêu cầu** / **Đánh giá**.
  - Header: nút **Xác minh / Duyệt**, nút **Từ chối**, nút **Khóa / Mở khóa**.
  - Hiển thị ảnh/link giấy phép kinh doanh.
  - **File tạo mới:** `frontend/pages/admin/company_detail.py`
  - **File:** `frontend/services/admin_api.py` → thêm `get_company_detail(company_id)`
  - **File:** `frontend/pages/admin/__init__.py` → đăng ký page mới

#### UC-55: Xác minh công ty
- `[ ]` **Task 9.4.5 [Backend]**: Cập nhật `PUT /admin/companies/{company_id}/approve`:
  - Kiểm tra điều kiện: `is_verified=False` và status ≠ "suspended".
  - Cập nhật `is_verified=True`, `status="active"`.
  - **Gửi Notification** cho user tài khoản của công ty đó: `"Tài khoản đã được xác minh, bạn có thể bắt đầu nhận yêu cầu"`.
  - **File:** `backend/app/routes/admin_routes.py` → endpoint `PUT /admin/companies/{company_id}/approve`
  - **File:** `backend/app/services/rescue_svc.py` → thêm hàm `send_notification_to_company(db, company_id, message)`

#### UC-56: Từ chối xác minh công ty
- `[ ]` **Task 9.4.6 [Backend]**: Tạo API `PUT /admin/companies/{company_id}/reject`:
  - **Nhận body:** `{ "reason": "string" }` — bắt buộc.
  - Cập nhật `is_verified=False`, `status="suspended"`, lưu lý do.
  - Gửi Notification cho công ty kèm lý do từ chối.
  - **File:** `backend/app/routes/admin_routes.py` → thêm endpoint `PUT /admin/companies/{company_id}/reject`

- `[ ]` **Task 9.4.7 [Frontend]**: Cập nhật UI trong `company_detail.py` và `companies.py`:
  - Nút **"Xác minh / Duyệt"**: dialog xác nhận đơn giản.
  - Nút **"Từ chối"**: dialog có **ô nhập lý do** (bắt buộc).
  - Sau khi approve/reject: cập nhật badge trạng thái trên UI.
  - **File:** `frontend/pages/admin/company_detail.py`, `frontend/pages/admin/companies.py`

#### UC-57: Khóa / Mở khóa công ty
- `[ ]` **Task 9.4.8 [Backend]**: Cập nhật API `PUT /admin/companies/{company_id}/suspend`:
  - **Nhận body:** `{ "reason": "string" }` — bắt buộc.
  - **Ràng buộc:** kiểm tra công ty có `RescueRequest` nào với status ≠ COMPLETED / CANCELLED / REJECTED không. Nếu có → lỗi 400.
  - Gửi Notification cho công ty về việc bị khóa (kèm lý do).
  - **File:** `backend/app/routes/admin_routes.py` → endpoint `PUT /admin/companies/{company_id}/suspend`

- `[ ]` **Task 9.4.9 [Frontend]**: Thêm dialog khóa/mở khóa công ty (tương tự UC-51/52 cho khách hàng):
  - Dialog khóa có ô nhập lý do bắt buộc.
  - Dialog mở khóa chỉ xác nhận đơn giản.
  - **File:** `frontend/pages/admin/company_detail.py`

---

### 9.5 — UC-58, UC-59, UC-60: Kiểm duyệt nội dung (Chức năng 3.5)
> **Hiện trạng:** Trang `frontend/pages/admin/moderation.py` đã có 2 tab: Reviews và Community. Thiếu: filter theo số sao, theo công ty, theo thời gian, tìm kiếm nội dung trong reviews; filter theo trạng thái và loại sự cố trong community; dialog nhập lý do xóa; gửi Notification sau khi xóa; và tính lại rating sau xóa review.

#### UC-58: Danh sách đánh giá
- `[ ]` **Task 9.5.1 [Backend]**: Cập nhật `GET /admin/reviews`:
  - Thêm query params: `star_filter` (1-5, optional), `company_id` (optional), `from_date`, `to_date`, `search` (tìm trong nội dung comment).
  - **File:** `backend/app/routes/admin_routes.py` → endpoint `GET /admin/reviews`

- `[ ]` **Task 9.5.2 [Frontend]**: Cập nhật tab Reviews trong `frontend/pages/admin/moderation.py`:
  - Thêm filter **"Số sao"** (dropdown: Tất cả / 1★ / 2★ / 3★ / 4★ / 5★).
  - Thêm filter **"Công ty"** (dropdown danh sách các công ty).
  - Thêm **date range picker** (từ ngày / đến ngày).
  - Thêm **ô tìm kiếm** theo nội dung nhận xét.
  - **File:** `frontend/pages/admin/moderation.py`
  - **File:** `frontend/services/admin_api.py` → cập nhật `get_reviews()` truyền params filter

#### UC-59: Xóa đánh giá vi phạm
- `[ ]` **Task 9.5.3 [Backend]**: Cập nhật `DELETE /admin/reviews/{review_id}`:
  - **Nhận body:** `{ "reason": "string" }` — bắt buộc.
  - Sau khi xóa review: tính lại `rating_avg` và `rating_count` của công ty (logic đã có, kiểm tra lại).
  - Gửi Notification cho khách hàng đã viết review: `"Đánh giá của bạn đã bị xóa vì [lý do]"`.
  - **File:** `backend/app/routes/admin_routes.py` → endpoint `DELETE /admin/reviews/{review_id}`

- `[ ]` **Task 9.5.4 [Frontend]**: Cập nhật nút xóa review trong tab Reviews:
  - Thay `ui.confirm` hiện tại bằng dialog có **ô nhập lý do** (bắt buộc).
  - **File:** `frontend/pages/admin/moderation.py`

#### UC-60: Kiểm duyệt bài đăng cộng đồng
- `[ ]` **Task 9.5.5 [Backend]**: Cập nhật `GET /admin/community/posts`:
  - Thêm query params: `status_filter` (OPEN / CLOSED / DELETED), `incident_type` (optional).
  - Bổ sung trường response: `status`, `incident_type`, `replies_count`.
  - **File:** `backend/app/routes/admin_routes.py` → endpoint `GET /admin/community/posts`

- `[ ]` **Task 9.5.6 [Backend]**: Cập nhật `DELETE /admin/community/posts/{post_id}`:
  - **Nhận body:** `{ "reason": "string" }` — bắt buộc.
  - Gửi Notification cho tác giả bài đăng: `"Bài đăng của bạn đã bị xóa vì [lý do]"`.
  - **File:** `backend/app/routes/admin_routes.py` → endpoint `DELETE /admin/community/posts/{post_id}`

- `[ ]` **Task 9.5.7 [Frontend]**: Cập nhật tab Community trong `frontend/pages/admin/moderation.py`:
  - Thêm filter **"Trạng thái"** (OPEN / CLOSED) và **"Loại sự cố"**.
  - Thêm cột **"Số phản hồi"** trong bảng.
  - Thay nút xóa đơn giản bằng dialog có **ô nhập lý do**.
  - **File:** `frontend/pages/admin/moderation.py`

---

### 9.6 — UC-61, UC-62, UC-63, UC-64: Báo cáo & Thống kê (Chức năng 3.6)
> **Hiện trạng:** Trang `frontend/pages/admin/reports.py` chỉ có biểu đồ doanh thu 6 tháng và tỉ lệ trạng thái. Backend `report_svc.py` chỉ có dữ liệu tổng hợp cơ bản. Thiếu: báo cáo yêu cầu theo bộ lọc, báo cáo doanh thu chi tiết theo công ty, báo cáo hài lòng/rating, và xuất PDF (hiện chỉ có CSV).

#### UC-61: Báo cáo yêu cầu cứu hộ
- `[ ]` **Task 9.6.1 [Backend]**: Tạo API `GET /admin/reports/requests`:
  - Query params: `from_date`, `to_date`, `company_id` (optional), `incident_type` (optional), `status` (optional).
  - **Trả về:**
    - `total_requests`: tổng số trong kỳ.
    - `by_status`: `{PENDING: N, IN_PROGRESS: N, COMPLETED: N, CANCELLED: N, REJECTED: N}`.
    - `by_incident_type`: `[{type: "...", count: N}, ...]` (cho biểu đồ tròn).
    - `by_date`: `[{date: "YYYY-MM-DD", count: N}, ...]` (cho biểu đồ đường).
    - `cancel_rate`: tỉ lệ hủy (CANCELLED / total * 100).
    - `reject_rate`: tỉ lệ từ chối (REJECTED / total * 100).
  - **File:** `backend/app/services/report_svc.py` → thêm hàm `get_request_report(db, from_date, to_date, ...)`
  - **File:** `backend/app/routes/admin_routes.py` → thêm endpoint `GET /admin/reports/requests`

- `[ ]` **Task 9.6.2 [Frontend]**: Tạo tab/section **"Báo cáo yêu cầu"** trong `frontend/pages/admin/reports.py`:
  - Bộ lọc: date range picker, dropdown company, dropdown incident_type, dropdown status.
  - Hiển thị:
    - Thẻ tổng hợp: Tổng yêu cầu / Đã hoàn thành / Đã hủy / Tỉ lệ hủy.
    - Bảng yêu cầu theo từng trạng thái.
    - **Biểu đồ tròn** (pie chart) phân bổ loại sự cố.
    - **Biểu đồ đường** (line chart) yêu cầu theo ngày.
  - **File:** `frontend/pages/admin/reports.py`
  - **File:** `frontend/services/admin_api.py` → thêm `get_request_report(params)`

#### UC-62: Báo cáo doanh thu
- `[ ]` **Task 9.6.3 [Backend]**: Tạo API `GET /admin/reports/revenue`:
  - Query params: `from_date`, `to_date`.
  - **Trả về:**
    - `total_revenue`: tổng doanh thu (Payment.status=PAID).
    - `by_company`: `[{company_name, revenue, request_count}, ...]` xếp hạng giảm dần.
    - `by_date`: `[{date, revenue}, ...]` (cho biểu đồ cột).
    - `by_payment_method`: `[{method, count, total_amount}, ...]` (cho biểu đồ tròn).
  - **File:** `backend/app/services/report_svc.py` → thêm hàm `get_revenue_report(db, from_date, to_date)`
  - **File:** `backend/app/routes/admin_routes.py` → thêm `GET /admin/reports/revenue`

- `[ ]` **Task 9.6.4 [Frontend]**: Tạo tab/section **"Báo cáo doanh thu"** trong `frontend/pages/admin/reports.py`:
  - Thẻ tổng doanh thu.
  - **Bảng xếp hạng công ty** theo doanh thu (top N, có cột: Công ty / Doanh thu / Số yêu cầu).
  - **Biểu đồ cột** doanh thu theo ngày/tháng.
  - **Biểu đồ tròn** theo phương thức thanh toán.
  - **File:** `frontend/pages/admin/reports.py`

#### UC-63: Báo cáo mức độ hài lòng
- `[ ]` **Task 9.6.5 [Backend]**: Tạo API `GET /admin/reports/satisfaction`:
  - Query params: `from_date`, `to_date`.
  - **Trả về:**
    - `system_avg_rating`: rating trung bình toàn hệ thống.
    - `by_star`: `{1: N, 2: N, 3: N, 4: N, 5: N}` (phân phối số sao).
    - `top5_highest`: 5 công ty rating cao nhất `[{company_name, rating_avg, rating_count}]`.
    - `top5_lowest`: 5 công ty rating thấp nhất.
    - `reviews_by_date`: `[{date, count}, ...]` số đánh giá theo thời gian.
  - **File:** `backend/app/services/report_svc.py` → thêm hàm `get_satisfaction_report(db, from_date, to_date)`
  - **File:** `backend/app/routes/admin_routes.py` → thêm `GET /admin/reports/satisfaction`

- `[ ]` **Task 9.6.6 [Frontend]**: Tạo tab/section **"Mức độ hài lòng"** trong `frontend/pages/admin/reports.py`:
  - Rating trung bình hệ thống (số lớn, nổi bật).
  - **Thanh ngang** phân phối số sao (1★ → 5★) dạng progress bar.
  - **Bảng Top 5 cao nhất** và **Top 5 thấp nhất**.
  - **Biểu đồ đường** số đánh giá theo thời gian.
  - **File:** `frontend/pages/admin/reports.py`

#### UC-64: Xuất báo cáo (Excel + PDF)
- `[ ]` **Task 9.6.7 [Backend]**: Tạo API `GET /admin/reports/export/excel`:
  - Query params: `report_type` (requests / revenue / satisfaction), `from_date`, `to_date`.
  - Dùng thư viện `openpyxl` để tạo file Excel nhiều sheet:
    - Sheet 1: Tổng quan.
    - Sheet 2: Chi tiết theo công ty.
    - Sheet 3: Chi tiết theo ngày.
  - Trả về file `.xlsx` với `Content-Disposition: attachment`.
  - **File:** `backend/app/routes/admin_routes.py` → thêm `GET /admin/reports/export/excel`
  - **Dependency:** Thêm `openpyxl` vào `requirements.txt`.

- `[ ]` **Task 9.6.8 [Backend]**: Tạo API `GET /admin/reports/export/pdf`:
  - Dùng thư viện `reportlab` hoặc `weasyprint` để tạo PDF.
  - Layout PDF: Logo hệ thống (placeholder), Tiêu đề báo cáo, Khoảng thời gian, Bảng dữ liệu chính, Biểu đồ (ảnh nhúng nếu có thể, hoặc chỉ bảng số liệu).
  - Trả về file `.pdf` với `Content-Disposition: attachment`.
  - **File:** `backend/app/routes/admin_routes.py` → thêm `GET /admin/reports/export/pdf`
  - **Dependency:** Thêm `reportlab` vào `requirements.txt`.

- `[ ]` **Task 9.6.9 [Frontend]**: Cập nhật trang `frontend/pages/admin/reports.py`:
  - Cấu trúc lại thành **tabs**: "Yêu cầu cứu hộ" / "Doanh thu" / "Mức độ hài lòng".
  - Mỗi tab có bộ lọc riêng (date range + filter chuyên biệt).
  - Header chung có 2 nút: **"Xuất Excel"** và **"Xuất PDF"** (tải file trực tiếp từ backend).
  - Nút xuất gọi API backend và trigger `ui.download()` với file nhận được.
  - **File:** `frontend/pages/admin/reports.py`
  - **File:** `frontend/services/admin_api.py` → thêm `export_excel(report_type, params)`, `export_pdf(report_type, params)`

---

### 9.7 — Hỗ trợ chung & Notification System
> **Các task này hỗ trợ nhiều UseCase trong Sprint 9 — cần hoàn thành trước hoặc song song.**

- `[ ]` **Task 9.7.1 [Backend]**: Kiểm tra và hoàn thiện hệ thống Notification:
  - Model `Notification` đã có — kiểm tra các fields: `user_id`, `message`, `is_read`, `created_at`, `notification_type`.
  - Tạo hàm tiện ích `send_notification(db, user_id, message, notification_type)` trong `rescue_svc.py` hoặc tạo `notification_svc.py` riêng.
  - Đảm bảo các API gọi hàm này đúng cách (approve/reject company, suspend user, delete review, delete post).
  - **File:** `backend/app/services/rescue_svc.py` hoặc tạo mới `backend/app/services/notification_svc.py`

- `[ ]` **Task 9.7.2 [Backend]**: Thêm field `suspend_reason` vào model `User` và `RescueCompany` nếu chưa có.
  - **File:** `backend/app/models/user.py`
  - **File:** `backend/app/models/company.py`
  - Tạo migration hoặc chạy lại `init_db()` nếu dùng SQLite.

- `[ ]` **Task 9.7.3 [Backend]**: Thêm `representative_name` vào model `RescueCompany` nếu chưa có (cần cho UC-53, UC-54).
  - **File:** `backend/app/models/company.py`

- `[ ]` **Task 9.7.4 [Frontend]**: Đăng ký tất cả các page mới vào `frontend/pages/admin/__init__.py` và `frontend/main.py`:
  - `user_detail.py` → route `/admin/users/{user_id}`
  - `company_detail.py` → route `/admin/companies/{company_id}`
  - **File:** `frontend/pages/admin/__init__.py`
  - **File:** `frontend/main.py`

- `[ ]` **Task 9.7.5 [Frontend]**: Thêm `requirements.txt` / `pyproject.toml` cho backend:
  - `openpyxl` (xuất Excel)
  - `reportlab` (xuất PDF)

---

### 9.8 — Kiểm thử & Xác minh Sprint 9

- `[ ]` **Task 9.8.1 [Test]**: Viết test case `tests/test_sprint9_admin.py`:
  - Test `POST /auth/login` với tài khoản bị SUSPENDED → phải trả về lỗi "Tài khoản bị khóa" (khác với sai mật khẩu).
  - Test `PUT /admin/users/{id}/suspend` với body không có `reason` → 422 Validation Error.
  - Test `PUT /admin/users/{id}/suspend` khi user có request đang PENDING → 400 ràng buộc.
  - Test `PUT /admin/companies/{id}/approve` → notification được tạo trong DB.
  - Test `PUT /admin/companies/{id}/reject` với reason → notification kèm lý do.
  - Test `DELETE /admin/reviews/{id}` → rating_avg của công ty được tính lại.
  - Test `GET /admin/reports/requests` với date range filter.
  - Test `GET /admin/reports/export/excel` → trả về file .xlsx.

- `[ ]` **Task 9.8.2 [Manual Test]**: Kiểm thử thủ công toàn bộ luồng Admin:
  - Đăng nhập Admin qua `/admin-panel/login` → redirect đúng Dashboard.
  - Dashboard hiển thị đủ: 4 thẻ số liệu, bảng công ty chờ duyệt, biểu đồ 7 ngày, thẻ trạng thái yêu cầu.
  - Duyệt công ty từ Dashboard (nút inline trong bảng chờ duyệt).
  - Vào chi tiết khách hàng → thấy đủ 5 section → Khóa (nhập lý do) → verify tài khoản không login được.
  - Vào Kiểm duyệt → filter review 1 sao → xóa có lý do → verify notification.
  - Xuất Excel và PDF từ trang Báo cáo → file tải về đúng định dạng.

---

## Ghi chú thực hiện

> **Thứ tự ưu tiên trong Sprint 9:**
> 1. Task 9.7.1 – 9.7.3 (hỗ trợ chung, cần làm trước)
> 2. Task 9.1.1 (fix auth SUSPENDED message — critical)
> 3. Task 9.3.5 + 9.3.6 (UC-51: khóa tài khoản với lý do — critical)
> 4. Task 9.4.5 + 9.4.6 + 9.4.8 (UC-55, 56, 57 — approval flow)
> 5. Task 9.2.1 – 9.2.4 (Dashboard bổ sung)
> 6. Task 9.3.3 + 9.3.4 (Chi tiết khách hàng)
> 7. Task 9.4.3 + 9.4.4 (Chi tiết công ty)
> 8. Task 9.5 (Moderation filters + reason dialogs)
> 9. Task 9.6 (Báo cáo chi tiết + xuất file)
> 10. Task 9.8 (Testing)

> **Conventions cần tuân thủ:**
> - Backend: Response format theo `success_response(data=..., message=...)` chuẩn hiện tại.
> - Frontend: Sử dụng `page_layout()` component cho tất cả trang admin.
> - Dialog xóa/khóa/từ chối luôn phải có ô nhập lý do bắt buộc (min 5 ký tự).
> - Sau mỗi action thành công: gọi lại hàm load data để refresh UI.
