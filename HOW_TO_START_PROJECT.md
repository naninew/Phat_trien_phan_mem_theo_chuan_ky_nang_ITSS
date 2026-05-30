# 🚀 Hướng dẫn Khởi động Hệ thống Cứu hộ Xe (ITSS Roadside Assistance)

Tài liệu này hướng dẫn chi tiết cách thiết lập và chạy hệ thống từ lúc mới tải code về. Hệ thống bao gồm Backend (FastAPI) và Frontend (NiceGUI), sử dụng SQLite làm cơ sở dữ liệu mặc định.

---

## 📋 Điều kiện tiên quyết
- **Python**: Phiên bản 3.9 trở lên (Khuyến nghị 3.10+).
- **Trình duyệt**: Chrome, Edge hoặc Firefox bản mới nhất.

---

## 🛠️ Bước 1: Tải mã nguồn và Cài đặt môi trường

1. **Tạo virtualenv và cài thư viện:**
   ```bash
   python3 -m venv .venv
   .venv/bin/python -m pip install -r backend/requirements.txt
   ```

   File `backend/requirements.txt` hiện bao gồm cả dependency Backend và Frontend.

---

## 🗄️ Bước 2: Khởi tạo Cơ sở dữ liệu

Dự án sử dụng SQLite để người mới không cần cài đặt SQL Server phức tạp. Để tạo database mẫu (Seed data):

```bash
cd backend
../.venv/bin/python generate_seed_data.py
```
*Lưu ý: Lệnh này sẽ tạo file `rescue_system.db`. Nếu bạn muốn làm sạch dữ liệu cũ, hãy xóa file .db này trước khi chạy.*

---

## 🖥️ Bước 3: Khởi chạy Hệ thống

### Cách nhanh: chạy Backend và Frontend bằng 1 lệnh

Đứng tại thư mục gốc project và chạy:

```bash
scripts/run_project.sh
```

Nếu muốn reset database và nạp lại dữ liệu mẫu trước khi chạy:

```bash
scripts/run_project.sh --reset-db
```

Nhấn `Ctrl+C` để dừng cả Backend và Frontend.

Nếu port `8000` hoặc `8080` đang bận, script sẽ tự dùng port trống kế tiếp và in URL thật ra terminal.

### Cách thủ công: chạy 2 cửa sổ Terminal riêng biệt

### Cửa sổ 1: Chạy Backend (API)
```bash
.venv/bin/python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```
- API sẽ chạy tại: `http://localhost:8000`
- Tài liệu API (Swagger UI): `http://localhost:8000/docs`

### Cửa sổ 2: Chạy Frontend (WebApp)
```bash
cd frontend
../.venv/bin/python main.py
```
- WebApp sẽ chạy tại: `http://localhost:8080` (Mặc định tự động mở trình duyệt).

---

## 👤 Thông tin Tài khoản Thử nghiệm

Hệ thống đã nạp sẵn các tài khoản sau (Mật khẩu mặc định: `Pass123!`, riêng Admin là `Admin123!`):

| Vai trò | Username | Chức năng chính |
| :--- | :--- | :--- |
| **Quản trị viên** | `admin` | Quản lý toàn sàn, duyệt công ty, xem báo cáo doanh thu. |
| **Khách hàng** | `customer1` -> `customer5` | Đặt cứu hộ, quản lý xe cá nhân, chat với công ty. |
| **Công ty** | `company1` -> `company5` | Quản lý đội xe, nhân viên, tiếp nhận và xử lý sự cố. |

---

## 🧪 Bước 4: Chạy Kiểm thử (Automation Testing)

Để đảm bảo hệ thống hoạt động ổn định sau khi cài đặt, bạn có thể chạy bộ test tự động:

1. **Kiểm tra tính năng Admin:**
   ```bash
   python -m pytest tests/test_sprint8_admin.py -v
   ```

2. **Kiểm tra luồng nghiệp vụ toàn trình (End-to-End):**
   ```bash
   python -m pytest tests/test_e2e_flow.py -v
   ```

---

## ❓ Xử lý sự cố thường gặp

- **Lỗi `ModuleNotFoundError: No module named 'app'`**: Đảm bảo bạn đang chạy lệnh từ thư mục gốc hoặc đã thực hiện `sys.path` đúng như hướng dẫn trong các file test.
- **Cổng 8000 hoặc 8080 đã bị chiếm dụng**: Kiểm tra xem có ứng dụng nào khác đang chạy trên các cổng này không và tắt chúng đi.
- **Lỗi Cơ sở dữ liệu**: Nếu gặp lỗi `IntegrityError`, hãy xóa file `rescue_system.db` và chạy lại `generate_seed_data.py`.

---
*Chúc bạn có trải nghiệm tốt với hệ thống ITSS Roadside Assistance!*
