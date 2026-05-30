# Hướng dẫn Khởi chạy và Kiểm thử Hệ thống Cứu hộ Xe

Tài liệu này hướng dẫn bạn cách thiết lập môi trường, khởi chạy Backend (FastAPI), Frontend (NiceGUI) và sử dụng dữ liệu mẫu để kiểm thử.

## 1. Yêu cầu Hệ thống
- Python 3.10 trở lên.
- Cài đặt đầy đủ dependencies.

## 2. Thiết lập Backend

1. **Cài đặt thư viện**:
   ```bash
   python3 -m venv .venv
   .venv/bin/python -m pip install -r backend/requirements.txt
   ```

2. **Khởi tạo dữ liệu mẫu (Seed Data)**:
   Bước này sẽ tạo file database `rescue_system.db` (SQLite) và nạp các tài khoản test, công ty cứu hộ mẫu tại Hà Nội.
   ```bash
   .venv/bin/python backend/generate_seed_data.py
   ```

3. **Chạy cả Backend và Frontend bằng 1 lệnh**:
   Đứng tại thư mục gốc project và chạy:
   ```bash
   scripts/run_project.sh
   ```
   Nếu muốn reset database và nạp lại seed data:
   ```bash
   scripts/run_project.sh --reset-db
   ```
   Nếu port `8000` hoặc `8080` đang bận, script sẽ tự dùng port trống kế tiếp và in URL thật ra terminal.

4. **Chạy Backend Server thủ công**:
   Đứng tại thư mục gốc project và chạy:
   ```bash
   .venv/bin/python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
   ```
   *Lưu ý: Không chạy trực tiếp `python app/main.py` vì sẽ lỗi import.*
   *Backend sẽ chạy tại: `http://localhost:8000`*
   *Tài liệu API (Swagger): `http://localhost:8000/docs`*

## 3. Thiết lập Frontend

1. **Cài đặt thư viện**:
   ```bash
   .venv/bin/python -m pip install -r backend/requirements.txt
   ```

2. **Chạy Frontend App**:
   ```bash
   cd frontend
   ../.venv/bin/python main.py
   ```
   *Frontend sẽ chạy tại: `http://localhost:8080`*

## 4. Tài khoản Kiểm thử (Test Accounts)

Sau khi chạy `generate_seed_data.py`, bạn có thể sử dụng các tài khoản sau:

| Vai trò | Username | Password | Mô tả |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `Admin123!` | Quản lý toàn bộ hệ thống |
| **Khách hàng** | `customer1` | `Pass123!` | Người dùng cần cứu hộ |
| **Nhân viên Cty** | `company1` | `Pass123!` | Đơn vị "Cứu Hộ Thăng Long" |
| **Nhân viên Cty** | `company2` | `Pass123!` | Đơn vị "Cứu Hộ Tây Hồ Express" |

## 5. Kịch bản Kiểm thử Gợi ý

1. **Kịch bản Khách hàng**:
   - Đăng nhập `customer1`.
   - Vào "Tìm Cứu Hộ", chọn dịch vụ "Vá lốp xe".
   - Hệ thống sẽ tự động lấy vị trí (hoặc giả lập tại Hà Nội) và hiển thị các công ty gần nhất.
   - Nhấn "Gửi yêu cầu" cho một công ty.

2. **Kịch bản Công ty**:
   - Mở trình duyệt ẩn danh khác, đăng nhập `company1`.
   - Vào "Hàng Đợi", bạn sẽ thấy yêu cầu từ `customer1`.
   - Nhấn "Tiếp nhận", chọn xe cứu hộ và nhập thời gian dự kiến (ETA).
   - Cập nhật trạng thái: "Đang di chuyển" -> "Đã đến nơi" -> "Hoàn thành".

3. **Kịch bản Admin**:
   - Đăng nhập `admin`.
   - Xem thống kê tại Dashboard.
   - Quản lý người dùng hoặc duyệt các công ty mới đăng ký.

---
**Lưu ý**: Đảm bảo Backend đang chạy trước khi thao tác trên Frontend. Nếu gặp lỗi kết nối, hãy kiểm tra file `.env` hoặc cấu hình `BACKEND_URL` trong `frontend/core/config.py`.
