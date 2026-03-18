# Phat_trien_phan_mem_theo_chuan_ky_nang_ITSS
Phat_trien_phan_mem_theo_chuan_ky_nang_ITSS

Chủ đề 03. Hệ thống hỗ trợ sự cố xe trên đường
# Hệ Thống Hỗ Trợ Sự Cố Xe Trên Đường (Roadside Assistance System)

## 1. Mô tả dự án
Cứu hộ giao thông là dịch vụ thiết yếu và cấp bách khi phương tiện gặp sự cố trên đường. Hệ thống này là một **nền tảng số** giúp kết nối người tham gia giao thông gặp sự cố với các đơn vị cung cấp dịch vụ cứu hộ chuyên nghiệp.

Hệ thống được thiết kế để tối ưu hóa quy trình tiếp nhận, xử lý và giải quyết các sự cố xe cộ theo thời gian thực, bao gồm các tình huống như:
* Thủng lốp, nổ lốp, cần vá hoặc thay lốp dự phòng.
* Hết điện ắc quy, xe không khởi động được.
* Xe chết máy không rõ nguyên nhân, hết xăng giữa đường.
* Tai nạn giao thông cần xe cẩu, xe kéo chuyên dụng.

## 2. Đối tượng sử dụng
* **Người dùng cá nhân:** Người gặp sự cố xe cần tìm kiếm sự hỗ trợ.
* **Công ty cứu hộ:** Các đơn vị kinh doanh dịch vụ sửa chữa, kéo xe và cứu hộ.
* **Quản trị viên (Admin):** Người quản lý tài khoản, kiểm duyệt thông tin và đảm bảo vận hành hệ thống.

---

## 3. Các chức năng chính

### 3.1. Quản lý thông tin cứu hộ
* **Quản lý công ty:** Lưu trữ tên, địa chỉ, số điện thoại, phạm vi hoạt động và giấy phép.
* **Quản lý dịch vụ:** Danh mục vá lốp, nạp nhiên liệu, kéo xe... kèm bảng giá chi tiết.
* **Quản lý phương tiện:** Ghi nhận danh sách xe cứu hộ và thiết bị đi kèm.
* **Quy trình cứu hộ:** Mô tả các bước xử lý từ tiếp nhận đến triển khai hỗ trợ.

### 3.2. Quản lý yêu cầu cứu hộ
* **Gửi yêu cầu:** Nhập mô tả sự cố, vị trí GPS và hình ảnh hiện trường.
* **Tìm kiếm thông minh:** Gợi ý danh sách đơn vị cứu hộ gần nhất dựa trên vị trí thực tế.
* **Theo dõi thời gian thực:** Người dùng theo dõi trạng thái xử lý và vị trí đội cứu hộ.
* **Hủy yêu cầu:** Cho phép hủy nếu sự cố đã được tự khắc phục.

### 3.3. Tương tác và Cộng đồng
* **Hệ thống Chat:** Trò chuyện trực tiếp giữa khách hàng và đơn vị cứu hộ.
* **Đánh giá & Phản hồi:** Hệ thống rating giúp cải thiện chất lượng dịch vụ.
* **Tư vấn cộng đồng:** Nhận hướng dẫn từ những người tham gia giao thông khác cho các lỗi đơn giản.

### 3.4. Quản trị hệ thống
* **Quản lý tài khoản:** Xác thực danh tính người dùng và đối tác cứu hộ.
* **Kiểm duyệt nội dung:** Đảm bảo các đánh giá và thông tin không vi phạm quy định.
* **Báo cáo thống kê:** Theo dõi tần suất yêu cầu, doanh thu và mức độ hài lòng.

---

## 4. Quy trình nghiệp vụ

### 4.1. Quy trình gửi yêu cầu cứu hộ (Dành cho Người dùng)
1. **Đăng nhập** vào hệ thống.
2. **Chọn loại dịch vụ** phù hợp (ví dụ: thay lốp, kích bình).
3. **Cung cấp thông tin:** Vị trí GPS, mô tả lỗi, hình ảnh.
4. **Chọn đơn vị:** Hệ thống gợi ý đơn vị gần nhất -> Người dùng chọn đơn vị mong muốn.
5. **Tiếp nhận:** Đơn vị cứu hộ xác nhận và báo thời gian chờ dự kiến.
6. **Theo dõi:** Người dùng theo dõi tiến độ trên bản đồ.
7. **Hoàn tất:** Xác nhận hoàn thành và thực hiện đánh giá chất lượng.

### 4.2. Quy trình xử lý yêu cầu (Dành cho Công ty cứu hộ)
1. **Nhận thông báo** yêu cầu mới từ hệ thống.
2. **Kiểm tra & Phân loại:** Xác định loại xe cứu hộ và nhân sự phù hợp.
3. **Phản hồi:** Cập nhật thời gian dự kiến đến hiện trường.
4. **Triển khai:** Điều phối nhân viên đến vị trí khách hàng.
5. **Cập nhật:** Ghi nhận trạng thái xử lý lên ứng dụng theo thời gian thực.
6. **Thanh toán & Đóng:** Hoàn tất dịch vụ và nhận phản hồi từ khách hàng.

---

Bạn có muốn tôi phác thảo thêm sơ đồ thực thể mối quan hệ (**ERD**) hoặc sơ đồ luồng dữ liệu (**DFD**) dựa trên các yêu cầu này không?
