# 🚀 Hướng dẫn Khởi động Dự án Roadside Assistance

Dự án này là hệ thống hỗ trợ cứu hộ xe trực tuyến, sử dụng **FastAPI** cho Backend và **NiceGUI** cho Frontend. Cơ sở dữ liệu mặc định là **SQLite**.

---

## 1. Cài đặt Môi trường

Bạn cần cài đặt các thư viện cần thiết cho cả 2 phần:

### Backend:
```bash
cd backend
pip install -r requirements.txt
# Lưu ý: Nếu cài lỗi psycopg2-binary, bạn có thể bỏ qua vì dự án đang chạy SQLite.
```

### Frontend:
```bash
cd frontend
pip install nicegui httpx python-dotenv
```

---

## 2. Khởi chạy Hệ thống (Theo thứ tự)

### Bước 1: Khởi tạo dữ liệu (Nếu chưa có)
Nếu bạn chưa có file `rescue_system.db` hoặc muốn reset lại toàn bộ data mới, hãy chạy lệnh sau để tạo hệ thống dữ liệu mẫu chuẩn (bao gồm user, công ty, dịch vụ ô tô/xe máy, yêu cầu cứu hộ, chat...):
```bash
cd backend
python generate_seed_data.py
```
*(Lưu ý: Script này sẽ xóa toàn bộ dữ liệu cũ và tạo lại database từ đầu để đảm bảo tính đồng bộ).*

### Bước 2: Chạy Backend Server
Mở terminal 1:
```bash
cd backend
python run.py
```
*Server chạy tại: `http://localhost:8000`. Đừng đóng terminal này.*

### Bước 3: Chạy Frontend Server
Mở terminal 2:
```bash
cd frontend
python main.py
```
*Giao diện chạy tại: `http://localhost:8080`.*

---

## 3. Thông tin Tài khoản Test

Dưới đây là các tài khoản đã được nạp sẵn vào hệ thống sau khi chạy file gen data:

| Vai trò | Username | Password | Chức năng chính |
| :--- | :--- | :--- | :--- |
| **Quản trị viên** | `admin` | `Admin123!` | Quản lý toàn bộ hệ thống, xem chat & thanh toán |
| **Khách hàng 1-5** | `customer1` -> `customer5` | `Pass123!` | Gửi yêu cầu, Chat, Thanh toán, Sửa Profile |
| **Công ty 1-5** | `company1` -> `company5` | `Pass123!` | Tiếp nhận yêu cầu, Quản lý xe/dịch vụ, Chat |

---

## 4. Quy trình Kiểm thử Nhanh (Demo Flow)

1.  **Đăng nhập Khách hàng** (`customer1`): Vào mục **Tìm Cứu Hộ** -> Chọn loại dịch vụ -> Chọn Công ty Thăng Long -> Gửi yêu cầu.
2.  **Đăng nhập Công ty** (`company1`): Vào mục **Hàng Đợi** -> Sẽ thấy yêu cầu mới -> Nhấn **Tiếp nhận** -> Chọn xe cứu hộ.
3.  **Cập nhật trạng thái**: Tại giao diện Công ty, cập nhật yêu cầu sang "Hoàn thành".
4.  **Kiểm tra Admin**: Đăng nhập `admin` để thấy các con số thống kê thay đổi trên Dashboard.

---
**Lưu ý quan trọng**: 
- Luôn chạy Backend trước khi mở Frontend.
- Các file ảnh tải lên sẽ được lưu trong thư mục `backend/uploads/`.
- File database là `backend/rescue_system.db`.
