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
