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

Dưới đây là phần phác thảo chi tiết về **Sơ đồ thực thể mối quan hệ (ERD)** và **Danh sách các API/Chức năng chi tiết** để bạn đưa vào tài liệu kỹ thuật hoặc `README.md`.

---

# Phác thảo Kỹ thuật Hệ thống Hỗ trợ Sự cố Xe (Technical Blueprint)

## 1. Sơ đồ thực thể mối quan hệ (ERD Concepts)
Dưới đây là các bảng dữ liệu chính cần có để vận hành hệ thống:

### 1.1. Thực thể chính
* **User (Người dùng/Admin):** `ID`, `Username`, `Password`, `FullName`, `Phone`, `Email`, `Role` (Cá nhân/Admin/Nhân viên công ty).
* **RescueCompany (Công ty cứu hộ):** `ID`, `CompanyName`, `Address`, `Hotline`, `LicenseNumber`, `RatingAvg`, `Status` (Hoạt động/Tạm dừng).
* **Service (Dịch vụ):** `ID`, `ServiceName` (Vá lốp, Kéo xe...), `BasePrice`, `Description`, `CompanyID`.
* **RescueVehicle (Phương tiện cứu hộ):** `ID`, `LicensePlate`, `Type` (Xe cẩu, Xe chở...), `Status` (Sẵn sàng/Đang làm nhiệm vụ), `CompanyID`.
* **RescueRequest (Yêu cầu cứu hộ):** * `ID`, `UserID`, `CompanyID`, `ServiceID`.
    * `Status` (Chờ xác nhận/Đang di chuyển/Đang xử lý/Hoàn thành/Đã hủy).
    * `Location` (Latitude, Longitude), `AddressDescription`, `CarIssueDetail`, `Images`.
    * `TotalCost`, `Feedback`, `Rating`.

---

## 2. Kiến trúc chức năng chi tiết (Feature Breakdown)

### 2.1. Module dành cho Người dùng (Mobile App/Web)
| Chức năng | Mô tả chi tiết |
| :--- | :--- |
| **Định vị GPS** | Tự động lấy tọa độ hiện tại và hiển thị các đơn vị cứu hộ trong bán kính $X$ km. |
| **Ước tính giá** | Hiển thị giá dự kiến dựa trên loại dịch vụ và khoảng cách di chuyển. |
| **Chat & Call** | Kết nối trực tiếp với tài xế cứu hộ qua VoIP hoặc Chat Real-time (Firebase/Socket.io). |
| **Lịch sử sự cố** | Lưu lại các lần cứu hộ trước đó, hóa đơn điện tử và phản hồi. |

### 2.2. Module dành cho Công ty cứu hộ (Dashboard/App Driver)
| Chức năng | Mô tả chi tiết |
| :--- | :--- |
| **Điều phối (Dispatch)** | Hệ thống tự động đẩy thông báo cho tài xế gần nhất với vị trí khách hàng. |
| **Quản lý trạng thái** | Tài xế cập nhật trạng thái: "Đang đến" -> "Đã tiếp cận" -> "Đang xử lý" -> "Xong". |
| **Quản lý doanh thu** | Thống kê thu nhập theo ngày/tháng/năm và chiết khấu hệ thống. |

### 2.3. Module Quản trị (Admin Panel)
| Chức năng | Mô tả chi tiết |
| :--- | :--- |
| **Xác minh đối tác** | Duyệt hồ sơ pháp lý, giấy phép kinh doanh của các công ty mới đăng ký. |
| **Giải quyết khiếu nại** | Xử lý các trường hợp người dùng phản ánh về giá cả hoặc thái độ phục vụ. |
| **Bản đồ nhiệt (Heatmap)** | Theo dõi các khu vực thường xuyên xảy ra sự cố để điều phối đối tác chờ sẵn. |

---

## 3. Gợi ý Công nghệ (Tech Stack)
Để hệ thống vận hành trơn tru theo thời gian thực, bạn có thể tham khảo:
* **Frontend:** React Native hoặc Flutter (để hỗ trợ định vị GPS tốt trên mobile).
* **Backend:** Node.js (Express) hoặc Java (Spring Boot) để xử lý lượng lớn kết nối đồng thời.
* **Real-time:** Socket.io hoặc Firebase Realtime Database để theo dõi vị trí tài xế trên bản đồ.
* **Map API:** Google Maps API hoặc Mapbox (để tính toán lộ trình và khoảng cách).
* **Database:** PostgreSQL (Lưu trữ dữ liệu quan hệ) + Redis (Cache vị trí tài xế).

---

## 4. Sơ đồ luồng dữ liệu (Data Flow - Simplified)
1.  **Khách hàng** gửi Request ($Location + Issue$) -> **Server**.
2.  **Server** quét trong DB tìm **RescueCompany** có bán kính hoạt động phù hợp.
3.  **Server** gửi Notification tới **App Công ty**.
4.  **Công ty** chấp nhận -> **Server** tạo kết nối Real-time giữa 2 bên.
5.  **Tài xế** cập nhật tọa độ liên tục -> **Khách hàng** xem trên bản đồ.
6.  Kết thúc dịch vụ -> **Server** lưu hóa đơn và cập nhật **Rating**.

---

## 5. Danh sách User Stories tiêu biểu

### User Story 1: Người dùng cá nhân gặp sự cố khẩn cấp
> **"Là một** người lái xe đang bị hỏng lốp giữa đường cao tốc vào ban đêm,
> **Tôi muốn** có thể gửi yêu cầu cứu hộ nhanh chóng kèm theo vị trí chính xác của mình qua GPS,
> **Để** tôi có thể nhận được sự trợ giúp từ đơn vị gần nhất mà không cần phải tự tìm kiếm số điện thoại hay mô tả vị trí khó khăn."

* **Tiêu chí chấp nhận (Acceptance Criteria):**
    * Hệ thống tự động xác định tọa độ GPS của người dùng với độ sai số thấp.
    * Hiển thị danh sách ít nhất 3 đơn vị cứu hộ gần nhất trong vòng 5 giây.
    * Người dùng nhận được thông báo xác nhận và thời gian chờ dự kiến ngay sau khi gửi yêu cầu.

---

### User Story 2: Công ty cứu hộ tối ưu hóa điều phối
> **"Là một** quản lý công ty cứu hộ,
> **Tôi muốn** nhận được thông báo chi tiết về tình trạng hư hỏng và hình ảnh sự cố của khách hàng ngay lập tức,
> **Để** tôi có thể điều động đúng loại xe cứu hộ (ví dụ: xe kích bình hoặc xe cẩu) và nhân viên có tay nghề phù hợp đến hiện trường."

* **Tiêu chí chấp nhận (Acceptance Criteria):**
    * Thông báo yêu cầu cứu hộ hiển thị đầy đủ: Loại xe của khách, mô tả sự cố, hình ảnh đính kèm.
    * Hệ thống cho phép công ty chọn và gán một phương tiện cụ thể từ danh sách xe sẵn có cho yêu cầu đó.
    * Trạng thái của xe cứu hộ tự động chuyển sang "Đang làm nhiệm vụ" sau khi tiếp nhận.

---

### User Story 3: Quản trị viên đảm bảo chất lượng dịch vụ
> **"Là một** quản trị viên hệ thống,
> **Tôi muốn** theo dõi bảng thống kê đánh giá (rating) và phản hồi của người dùng về các đơn vị cứu hộ,
> **Để** tôi có thể kịp thời nhắc nhở hoặc loại bỏ các đơn vị có chất lượng phục vụ kém, đảm bảo uy tín của nền tảng."

* **Tiêu chí chấp nhận (Acceptance Criteria):**
    * Hệ thống có bảng điều khiển (Dashboard) hiển thị danh sách các đơn vị có số sao trung bình dưới 3.0.
    * Cho phép Admin xem chi tiết nội dung phản hồi tiêu cực của khách hàng.
    * Có chức năng khóa tạm thời tài khoản của đơn vị cứu hộ nếu vi phạm quy tắc hệ thống.

---

