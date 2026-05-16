# HỆ THỐNG ITSS (INTELLIGENT TRAFFIC SUPPORT SYSTEM)
## NỀN TẢNG KẾT NỐI CỨU HỘ XE - TÀI LIỆU TỔNG HỢP ĐẦY ĐỦ

---

## MỤC LỤC
1. [Tổng quan dự án](#1-tổng-quan-dự-án)
2. [Actor và phân quyền](#2-actor-và-phân-quyền)
3. [Luồng nghiệp vụ cốt lõi](#3-luồng-nghiệp-vụ-cốt-lõi)
4. [Mô hình dữ liệu](#4-mô-hình-dữ-liệu)
5. [Chi tiết chức năng Customer](#5-chi-tiết-chức-năng-customer)
6. [Chi tiết chức năng RescueCompany](#6-chi-tiết-chức-năng-rescuecompany)
7. [Chi tiết chức năng Admin](#7-chi-tiết-chức-năng-admin)
8. [Quy tắc nghiệp vụ và ràng buộc](#8-quy-tắc-nghiệp-vụ-và-ràng-buộc)
9. [State Machine](#9-state-machine)

---

## 1. TỔNG QUAN DỰ ÁN

### 1.1. Mục đích hệ thống
ITSS là nền tảng kết nối người gặp sự cố xe ↔ dịch vụ cứu hộ thông qua ứng dụng web/mobile, tập trung vào:
- **Matching nhanh nhất theo GPS** (tương tự Grab)
- **Theo dõi trạng thái real-time** (tương tự Shopee)
- **Chat trực tiếp** (tương tự Messenger)
- **Thanh toán minh bạch**
- **Đánh giá dịch vụ**

### 1.2. Ví dụ thực tế
- Bạn bị thủng lốp giữa đường
- Mở app → gửi yêu cầu
- Hệ thống tìm cứu hộ gần nhất
- Theo dõi họ tới + chat + thanh toán

### 1.3. Phạm vi hệ thống
- **Đối tượng phục vụ**: Người dùng cá nhân có xe, công ty cứu hộ
- **Khu vực hoạt động**: Toàn quốc (theo GPS)
- **Loại sự cố**: Thủng lốp, hết xăng, hết điện bình, chết máy, tai nạn, khác

---

## 2. ACTOR VÀ PHÂN QUYỀN

### 2.1. Customer (Khách hàng cá nhân)
**Vai trò**: Người gặp sự cố xe cần cứu hộ

**Quyền hạn**:
- Đăng ký/đăng nhập tài khoản
- Quản lý thông tin cá nhân và xe
- Tạo yêu cầu cứu hộ
- Theo dõi trạng thái yêu cầu real-time
- Chat với công ty cứu hộ
- Thanh toán dịch vụ
- Đánh giá dịch vụ
- Tham gia cộng đồng hỏi đáp
- Xem lịch sử yêu cầu và thanh toán

### 2.2. RescueCompany (Công ty cứu hộ)
**Vai trò**: Đơn vị cung cấp dịch vụ cứu hộ

**Quyền hạn**:
- Đăng ký tài khoản (chờ Admin xác minh)
- Dashboard tổng quan
- Tiếp nhận/từ chối yêu cầu cứu hộ
- Phân công nhân viên và xe
- Cập nhật trạng thái yêu cầu
- Quản lý dịch vụ cung cấp
- Quản lý phương tiện cứu hộ
- Quản lý nhân viên
- Chat với khách hàng
- Xem đánh giá nhận được

### 2.3. Admin (Quản trị viên)
**Vai trò**: Quản trị hệ thống

**Quyền hạn**:
- Đăng nhập admin panel
- Dashboard tổng quan hệ thống
- Quản lý tài khoản khách hàng (xem, khóa, mở khóa)
- Quản lý công ty cứu hộ (xem, xác minh, từ chối, khóa)
- Kiểm duyệt nội dung (đánh giá, bài đăng cộng đồng)
- Xem và xuất báo cáo (yêu cầu, doanh thu, mức độ hài lòng)

---

## 3. LUỒNG NGHIỆP VỤ CỐT LÕI

### 3.1. Flow chính - Gửi yêu cầu cứu hộ

**Bước 1: Khởi tạo**
1. Customer đăng nhập
2. Chọn loại sự cố
3. Nhập mô tả và vị trí GPS
4. Hệ thống validate thông tin

**Bước 2: Matching**
5. Hệ thống tìm công ty cứu hộ trong khu vực (bán kính 50km)
6. Hiển thị danh sách công ty (khoảng cách, rating, giá, dịch vụ)
7. Customer chọn công ty và dịch vụ
8. Gửi yêu cầu → `RescueRequest.status = PENDING`

**Bước 3: Tiếp nhận**
9. Công ty nhận thông báo
10. Kiểm tra thông tin yêu cầu
11. Quyết định:
    - **Chấp nhận** → `status = ACCEPTED` + nhập `estimatedArrivalTime`
    - **Từ chối** → `status = REJECTED` + lý do

**Bước 4: Điều phối**
12. Công ty phân công nhân viên và xe
13. Tạo `ServiceAssignment`
14. Cập nhật status:
    - Nhân viên: `AVAILABLE → BUSY`
    - Xe: `AVAILABLE → ON_MISSION`
    - Yêu cầu: `ACCEPTED → ASSIGNED`
15. Gửi notification cho khách hàng

**Bước 5: Thực hiện**
16. Nhân viên xuất phát → `status = ON_THE_WAY`
17. Đến nơi, bắt đầu xử lý → `status = IN_PROGRESS`
18. Hoàn thành xử lý → `status = COMPLETED`
19. Cập nhật `agreedPrice`, `actualArrivalTime`, `completedTime`
20. Reset status nhân viên và xe về `AVAILABLE`

**Bước 6: Thanh toán & Đánh giá**
21. Customer xác nhận hoàn thành
22. Chọn phương thức thanh toán (tiền mặt/chuyển khoản/ví điện tử)
23. Tạo `Payment.status = PAID`
24. Customer đánh giá sao (1-5) và nhận xét
25. Tạo `Review` → cập nhật `ratingAverage` của công ty
26. Đóng yêu cầu

### 3.2. Flow phụ - Hủy yêu cầu
- **Điều kiện**: Chỉ khi `status = PENDING`
- Customer nhấn hủy → xác nhận → `status = CANCELLED`
- Gửi notification cho công ty (nếu đã có công ty tiếp nhận)

### 3.3. Flow phụ - Cộng đồng
- Customer tạo bài đăng hỏi đáp
- Cộng đồng phản hồi, đánh dấu "Hữu ích"
- Tác giả hoặc Admin đóng bài khi giải quyết xong

---

## 4. MÔ HÌNH DỮ LIỆU

### 4.1. Entity Relationship Overview

```
Account (Abstract)
├── Customer
├── Admin
└── RescueCompany
    ├── RescueService (1..*)
    ├── RescueVehicle (1..*)
    └── RescueStaff (1..*)

RescueRequest
├── customer (1)
├── company (1)
├── vehicle (1)
├── RequestService (1..*)
│   └── RescueService (1)
├── ServiceAssignment (0..1)
│   ├── staff (1)
│   └── rescueVehicle (1)
├── Payment (0..1)
├── Review (0..1)
└── Message (0..*)
└── Notification (0..*)

Customer
├── Vehicle (0..*)
├── CommunityPost (0..*)
│   └── CommunityReply (0..*)
└── RescueRequest (0..*)

Admin
└── Report (0..*)
```

### 4.2. Chi tiết các Entity

#### **Account** (Abstract Class)
**Attributes**:
- `accountId`: int (PK)
- `username`: String
- `password`: String
- `fullName`: String
- `phone`: String
- `email`: String
- `address`: String
- `status`: AccountStatus (ACTIVE, INACTIVE, SUSPENDED)
- `createdAt`: DateTime

**Methods**:
- `login()`: void
- `logout()`: void
- `updateProfile()`: void
- `changePassword()`: void

---

#### **Customer** (extends Account)
**Attributes**:
- `customerId`: int (PK, extends accountId)
- `currentLatitude`: double
- `currentLongitude`: double

**Methods**:
- `createRescueRequest()`: void
- `cancelRescueRequest()`: void
- `trackRequest()`: void
- `makePayment()`: void
- `submitReview()`: void

**Relationships**:
- 1 Customer tạo 0..* RescueRequest
- 1 Customer có 0..* Vehicle
- 1 Customer viết 0..* Review
- 1 Customer tạo 0..* CommunityPost
- 1 Customer gửi 0..* Message

---

#### **RescueCompany** (extends Account)
**Attributes**:
- `companyId`: int (PK, extends accountId)
- `companyName`: String (unique)
- `businessLicense`: String (unique)
- `operatingArea`: String
- `ratingAverage`: double
- `description`: String
- `isVerified`: boolean

**Methods**:
- `acceptRequest()`: void
- `rejectRequest()`: void
- `assignStaff()`: void
- `updateRequestStatus()`: void
- `manageServices()`: void
- `manageVehicles()`: void
- `manageStaff()`: void

**Relationships**:
- 1 RescueCompany nhận 0..* RescueRequest
- 1 RescueCompany có 1..* RescueService
- 1 RescueCompany có 1..* RescueVehicle
- 1 RescueCompany có 1..* RescueStaff
- 1 RescueCompany nhận 0..* Review
- 1 RescueCompany gửi 0..* Message

---

#### **Admin** (extends Account)
**Methods**:
- `manageCustomers()`: void
- `manageRescueCompanies()`: void
- `moderateReviews()`: void
- `viewReports()`: void
- `verifyCompany()`: void

**Relationships**:
- 1 Admin tạo 0..* Report

---

#### **RescueRequest** (Central Entity)
**Attributes**:
- `requestId`: int (PK)
- `customerId`: int (FK)
- `companyId`: int (FK, nullable)
- `vehicleId`: int (FK)
- `requestTime`: DateTime
- `incidentType`: String
- `description`: String
- `latitude`: double
- `longitude`: double
- `imageUrl`: String
- `status`: RequestStatus (PENDING, ACCEPTED, ASSIGNED, ON_THE_WAY, IN_PROGRESS, COMPLETED, REJECTED, CANCELLED)
- `agreedPrice`: double
- `estimatedArrivalTime`: DateTime
- `actualArrivalTime`: DateTime
- `completedTime`: DateTime

**Methods**:
- `submit()`: void
- `cancel()`: void
- `updateStatus()`: void
- `confirmCompletion()`: void

**Relationships**:
- 1 RescueRequest thuộc về 1 Customer
- 1 RescueRequest được xử lý bởi 1 RescueCompany (nullable)
- 1 RescueRequest liên quan 1 Vehicle của customer
- 1 RescueRequest có 1..* RequestService
- 1 RescueRequest có 0..1 ServiceAssignment
- 1 RescueRequest có 0..1 Payment
- 1 RescueRequest có 0..1 Review
- 1 RescueRequest có 0..* Message
- 1 RescueRequest có 0..* Notification

---

#### **RequestService** (Association Entity)
**Attributes**:
- `requestServiceId`: int (PK)
- `requestId`: int (FK)
- `serviceId`: int (FK)
- `quantity`: int
- `agreedPrice`: double
- `unitPrice`: double

**Methods**:
- `add()`: void
- `remove()`: void

**Relationships**:
- 1..* RequestService thuộc 1 RescueRequest
- 1 RequestService tham chiếu 1 RescueService

---

#### **RescueService**
**Attributes**:
- `serviceId`: int (PK)
- `companyId`: int (FK)
- `serviceName`: String
- `description`: String
- `basePrice`: double
- `estimatedDuration`: int (phút)
- `isActive`: boolean

**Methods**:
- `updatePrice()`: void
- `activate()`: void
- `deactivate()`: void

**Relationships**:
- 1 RescueService thuộc 1 RescueCompany
- 1 RescueService xuất hiện trong 0..* RequestService

---

#### **RescueVehicle**
**Attributes**:
- `rescueVehicleId`: int (PK)
- `companyId`: int (FK)
- `plateNumber`: String (unique)
- `vehicleType`: String (Xe tải cứu hộ/Xe máy/Xe van/Xe con)
- `capacity`: String
- `status`: RescueVehicleStatus (AVAILABLE, ON_MISSION, MAINTENANCE)

**Methods**:
- `updateStatus()`: void

**Relationships**:
- 1 RescueVehicle thuộc 1 RescueCompany
- 1 RescueVehicle được phân công trong 0..* ServiceAssignment

---

#### **RescueStaff**
**Attributes**:
- `staffId`: int (PK)
- `companyId`: int (FK)
- `skillLevel`: String (Sơ cấp/Trung cấp/Cao cấp)
- `status`: StaffStatus (AVAILABLE, BUSY)

**Methods**:
- `receiveAssignment()`: void
- `updateStatus()`: void

**Relationships**:
- 1 RescueStaff thuộc 1 RescueCompany
- 1 RescueStaff được phân công trong 0..* ServiceAssignment

---

#### **ServiceAssignment**
**Attributes**:
- `assignmentId`: int (PK)
- `requestId`: int (FK)
- `staffId`: int (FK)
- `rescueVehicleId`: int (FK)
- `assignedTime`: DateTime
- `notes`: String

**Methods**:
- `assign()`: void
- `reassign()`: void

**Relationships**:
- 1 ServiceAssignment thuộc 1 RescueRequest
- 1 ServiceAssignment gán 1 RescueStaff
- 1 ServiceAssignment gán 1 RescueVehicle

---

#### **Vehicle** (Customer's Vehicle)
**Attributes**:
- `vehicleId`: int (PK)
- `customerId`: int (FK)
- `licensePlate`: String (unique)
- `brand`: String
- `model`: String
- `year`: int
- `fuelType`: String (Xăng/Dầu/Điện/Hybrid)

**Methods**:
- `updateInfo()`: void

**Relationships**:
- 1 Vehicle thuộc 1 Customer
- 1 Vehicle xuất hiện trong 0..* RescueRequest

---

#### **Payment**
**Attributes**:
- `paymentId`: int (PK)
- `requestId`: int (FK)
- `customerId`: int (FK)
- `amount`: double
- `paymentMethod`: String (Tiền mặt/Chuyển khoản/Ví điện tử)
- `paymentStatus`: PaymentStatus (PENDING, PAID, REFUNDED)
- `paymentTime`: DateTime
- `transactionCode`: String

**Methods**:
- `processPayment()`: void
- `refund()`: void

**Relationships**:
- 1 Payment thuộc 1 RescueRequest
- 1 Payment thuộc 1 Customer

---

#### **Review**
**Attributes**:
- `reviewId`: int (PK)
- `requestId`: int (FK, unique)
- `customerId`: int (FK)
- `companyId`: int (FK)
- `rating`: int (1-5)
- `comment`: String (max 500 ký tự)
- `createdAt`: DateTime

**Methods**:
- `editReview()`: void
- `deleteReview()`: void

**Relationships**:
- 1 Review thuộc 1 RescueRequest (1-1)
- 1 Review viết bởi 1 Customer
- 1 Review cho 1 RescueCompany

---

#### **Message**
**Attributes**:
- `messageId`: int (PK)
- `requestId`: int (FK)
- `senderId`: int (FK)
- `receiverId`: int (FK)
- `senderType`: String (Customer/Company)
- `content`: String
- `sentTime`: DateTime
- `isRead`: boolean

**Methods**:
- `send()`: void
- `markAsRead()`: void

**Relationships**:
- 1 Message thuộc 1 RescueRequest
- 1 Message gửi từ 1 Account (Customer hoặc Company)
- 1 Message gửi đến 1 Account

---

#### **Notification**
**Attributes**:
- `notificationId`: int (PK)
- `receiverId`: int (FK)
- `requestId`: int (FK, nullable)
- `title`: String
- `content`: String
- `sentTime`: DateTime
- `isRead`: boolean

**Methods**:
- `markAsRead()`: void

**Relationships**:
- 1 Notification gửi đến 1 Account (Customer hoặc Company)
- 1 Notification có thể liên quan 1 RescueRequest

---

#### **CommunityPost**
**Attributes**:
- `postId`: int (PK)
- `authorId`: int (FK - customerId)
- `requestId`: int (FK, nullable)
- `title`: String (10-200 ký tự)
- `content`: String (min 30 ký tự)
- `incidentType`: String
- `createdAt`: DateTime
- `isClosed`: boolean

**Methods**:
- `createPost()`: void
- `closePost()`: void

**Relationships**:
- 1 CommunityPost tạo bởi 1 Customer
- 1 CommunityPost có 0..* CommunityReply

---

#### **CommunityReply**
**Attributes**:
- `replyId`: int (PK)
- `postId`: int (FK)
- `authorId`: int (FK - customerId)
- `content`: String
- `createdAt`: DateTime
- `isHelpful`: boolean

**Methods**:
- `createReply()`: void
- `markHelpful()`: void

**Relationships**:
- 1 CommunityReply thuộc 1 CommunityPost
- 1 CommunityReply viết bởi 1 Customer

---

#### **Report**
**Attributes**:
- `reportId`: int (PK)
- `adminId`: int (FK)
- `reportType`: String
- `fromDate`: DateTime
- `toDate`: DateTime
- `filters`: String
- `generatedAt`: DateTime

**Methods**:
- `generate()`: void
- `exportPDF()`: void
- `exportExcel()`: void

**Relationships**:
- 1 Report tạo bởi 1 Admin

---

### 4.3. ENUM Types

#### **AccountStatus**
- `ACTIVE`: Tài khoản hoạt động bình thường
- `INACTIVE`: Tài khoản chưa kích hoạt
- `SUSPENDED`: Tài khoản bị khóa

#### **RequestStatus**
- `PENDING`: Chờ công ty phản hồi
- `ACCEPTED`: Công ty đã chấp nhận
- `ASSIGNED`: Đã phân công nhân viên và xe
- `ON_THE_WAY`: Nhân viên đang trên đường đến
- `IN_PROGRESS`: Đang xử lý sự cố
- `COMPLETED`: Hoàn thành
- `REJECTED`: Công ty từ chối
- `CANCELLED`: Customer hủy

#### **RescueVehicleStatus**
- `AVAILABLE`: Sẵn sàng nhận việc
- `ON_MISSION`: Đang trên đường/tại hiện trường
- `MAINTENANCE`: Đang bảo dưỡng, sửa chữa

#### **StaffStatus**
- `AVAILABLE`: Sẵn sàng
- `BUSY`: Đang bận

#### **PaymentStatus**
- `PENDING`: Chờ thanh toán
- `PAID`: Đã thanh toán
- `REFUNDED`: Đã hoàn tiền

---

## 5. CHI TIẾT CHỨC NĂNG CUSTOMER

### CHỨC NĂNG 1.1 — Đăng ký & Đăng nhập

#### **UC-01: Đăng ký tài khoản khách hàng**

**Mô tả**: Người dùng chưa có tài khoản tạo tài khoản mới trên hệ thống.

**Điều kiện tiên quyết**: Người dùng chưa đăng nhập.

**Luồng chính**:
1. Người dùng truy cập trang đăng ký
2. Nhập thông tin: họ tên, số điện thoại, email, mật khẩu, xác nhận mật khẩu, địa chỉ
3. Hệ thống kiểm tra email và số điện thoại chưa tồn tại
4. Hệ thống kiểm tra mật khẩu khớp và đủ mạnh (tối thiểu 8 ký tự)
5. Hệ thống tạo tài khoản với `status = ACTIVE`
6. Hệ thống tự động đăng nhập và chuyển về trang chủ

**Luồng ngoại lệ**:
- **E1**: Email đã tồn tại → hiển thị lỗi "Email đã được sử dụng"
- **E2**: Số điện thoại đã tồn tại → hiển thị lỗi "Số điện thoại đã được sử dụng"
- **E3**: Mật khẩu không khớp → hiển thị lỗi ngay dưới ô xác nhận
- **E4**: Thiếu trường bắt buộc → highlight ô còn trống

**Dữ liệu đầu vào**:
- `fullName`: bắt buộc, 2–100 ký tự
- `phone`: bắt buộc, đúng định dạng 10 số, bắt đầu bằng 0
- `email`: bắt buộc, đúng định dạng email
- `password`: bắt buộc, tối thiểu 8 ký tự
- `address`: bắt buộc

**Dữ liệu đầu ra**: Tài khoản Customer được tạo trong DB, người dùng được đăng nhập.

---

#### **UC-02: Đăng nhập**

**Mô tả**: Người dùng đã có tài khoản đăng nhập vào hệ thống.

**Luồng chính**:
1. Nhập email + mật khẩu
2. Hệ thống xác thực thông tin
3. Kiểm tra `status` tài khoản = `ACTIVE`
4. Đăng nhập thành công, chuyển đến trang chủ Customer

**Luồng ngoại lệ**:
- **E1**: Sai email/mật khẩu → "Email hoặc mật khẩu không đúng"
- **E2**: Tài khoản bị `SUSPENDED` → "Tài khoản đã bị khóa, liên hệ hỗ trợ"
- **E3**: Tài khoản `INACTIVE` → "Tài khoản chưa được kích hoạt"

---

#### **UC-03: Đổi mật khẩu**

**Luồng chính**:
1. Nhập mật khẩu hiện tại
2. Nhập mật khẩu mới + xác nhận
3. Hệ thống xác minh mật khẩu hiện tại đúng
4. Cập nhật mật khẩu mới

**Luồng ngoại lệ**:
- **E1**: Mật khẩu hiện tại sai → thông báo lỗi
- **E2**: Mật khẩu mới trùng mật khẩu cũ → "Mật khẩu mới phải khác mật khẩu cũ"

---

#### **UC-04: Cập nhật hồ sơ cá nhân**

**Luồng chính**:
1. Xem thông tin hiện tại
2. Chỉnh sửa: họ tên, số điện thoại, địa chỉ
3. Lưu thông tin

**Ràng buộc**: Không cho phép đổi email (dùng để đăng nhập).

---

### CHỨC NĂNG 1.2 — Quản lý xe cá nhân

#### **UC-05: Thêm xe**

**Mô tả**: Khách hàng thêm thông tin xe của mình để dùng khi tạo yêu cầu cứu hộ.

**Luồng chính**:
1. Vào mục "Xe của tôi" → nhấn "Thêm xe"
2. Nhập thông tin: biển số, hãng xe, model, năm sản xuất, loại nhiên liệu
3. Lưu xe vào danh sách

**Dữ liệu đầu vào**:
- `licensePlate`: bắt buộc, định dạng biển số VN (vd: 51A-123.45)
- `brand`: bắt buộc (Toyota, Honda, Yamaha...)
- `model`: bắt buộc
- `year`: bắt buộc, từ 1990 đến năm hiện tại
- `fuelType`: bắt buộc (Xăng/Dầu/Điện/Hybrid)

**Ràng buộc**: Biển số không được trùng trong toàn hệ thống.

---

#### **UC-06: Xem danh sách xe**

**Mô tả**: Hiển thị tất cả xe mà khách hàng đã đăng ký.

**Hiển thị**: Biển số, hãng xe, model, năm, loại nhiên liệu, nút sửa/xóa.

---

#### **UC-07: Sửa thông tin xe**

**Ràng buộc**: Chỉ cho sửa khi xe không đang có yêu cầu cứu hộ ở trạng thái đang xử lý (`PENDING` → `IN_PROGRESS`).

---

#### **UC-08: Xóa xe**

**Ràng buộc**: Chỉ xóa được khi xe không có yêu cầu cứu hộ nào chưa hoàn thành.

---

### CHỨC NĂNG 1.3 — Yêu cầu cứu hộ

#### **UC-09: Tạo yêu cầu cứu hộ**

**Mô tả**: Đây là chức năng cốt lõi — khách hàng gặp sự cố tạo yêu cầu hỗ trợ.

**Điều kiện tiên quyết**:
- Đã đăng nhập
- Đã có ít nhất 1 xe trong hệ thống
- Không đang có yêu cầu nào ở trạng thái `PENDING`/`ACCEPTED`/`ON_THE_WAY`/`IN_PROGRESS`

**Luồng chính**:
1. Nhấn "Tạo yêu cầu cứu hộ"
2. **Bước 1 — Chọn xe**: chọn xe từ danh sách xe đã đăng ký
3. **Bước 2 — Chọn vị trí**: bản đồ hiển thị, cho phép:
   - Nhấn "Vị trí của tôi" để lấy GPS tự động
   - Hoặc click/kéo marker trên bản đồ để chọn thủ công
   - Latitude/longitude được ghi nhận tự động
4. **Bước 3 — Mô tả sự cố**:
   - Chọn loại sự cố (Thủng lốp/Hết xăng/Hết điện bình/Chết máy/Tai nạn/Khác)
   - Nhập mô tả chi tiết
   - Upload ảnh xe (tuỳ chọn, tối đa 3 ảnh)
5. **Bước 4 — Chọn dịch vụ và công ty**:
   - Hệ thống hiển thị danh sách công ty cứu hộ gần nhất (theo khoảng cách tính từ GPS)
   - Mỗi công ty hiển thị: tên, khoảng cách, rating, danh sách dịch vụ + giá
   - Khách hàng chọn công ty và tích chọn 1 hoặc nhiều dịch vụ cần dùng
6. Nhấn "Gửi yêu cầu"
7. Hệ thống tạo `RescueRequest` (`status = PENDING`)
8. Hệ thống tạo các dòng `RequestService` tương ứng
9. Hệ thống gửi `Notification` cho công ty được chọn
10. Hiển thị trang theo dõi yêu cầu

**Dữ liệu đầu vào**:
- `vehicleId`: bắt buộc
- `latitude`: bắt buộc
- `longitude`: bắt buộc
- `incidentType`: bắt buộc
- `description`: bắt buộc, tối thiểu 20 ký tự
- `imageUrl`: tuỳ chọn
- `companyId`: bắt buộc
- `serviceIds[]`: bắt buộc, ít nhất 1 dịch vụ

**Luồng ngoại lệ**:
- **E1**: Không có công ty nào trong phạm vi 50km → thông báo và gợi ý mở rộng khu vực
- **E2**: Đang có yêu cầu chưa hoàn thành → chặn tạo mới, hiển thị link đến yêu cầu hiện tại

---

#### **UC-10: Theo dõi yêu cầu cứu hộ**

**Mô tả**: Khách hàng xem trạng thái yêu cầu theo thời gian thực.

**Luồng chính**:
1. Vào trang chi tiết yêu cầu
2. Hiển thị timeline trạng thái
3. Hiển thị thông tin công ty đã chấp nhận (tên, SĐT, thời gian đến dự kiến)
4. Hiển thị bản đồ với marker vị trí sự cố
5. Hiển thị khung chat với công ty cứu hộ
6. Tự động làm mới trạng thái mỗi 30 giây

**Thông tin hiển thị theo từng trạng thái**:

| Trạng thái | Hiển thị |
|------------|----------|
| `PENDING` | "Đang chờ công ty phản hồi..." + thời gian đã chờ |
| `ACCEPTED` | Tên công ty, SĐT, thời gian đến dự kiến |
| `ASSIGNED` | Tên nhân viên, SĐT nhân viên, loại xe cứu hộ |
| `ON_THE_WAY` | "Nhân viên đang trên đường đến" + thời gian dự kiến |
| `IN_PROGRESS` | "Đang xử lý sự cố" |
| `COMPLETED` | Nút "Xác nhận hoàn thành" + "Đánh giá dịch vụ" |
| `REJECTED` | Lý do từ chối + gợi ý tìm công ty khác |

---

#### **UC-11: Hủy yêu cầu cứu hộ**

**Điều kiện**: Chỉ hủy được khi `status = PENDING`.

**Luồng chính**:
1. Nhấn "Hủy yêu cầu"
2. Hệ thống hiển thị popup xác nhận
3. Khách hàng xác nhận
4. Status chuyển thành `CANCELLED`
5. Hệ thống gửi `Notification` cho công ty (nếu đã có công ty tiếp nhận)

---

#### **UC-12: Xem lịch sử yêu cầu**

**Luồng chính**:
1. Vào mục "Lịch sử yêu cầu"
2. Hiển thị danh sách tất cả yêu cầu (sắp xếp mới nhất trước)
3. Mỗi dòng hiển thị: ngày tạo, loại sự cố, tên công ty, trạng thái, tổng tiền
4. Nhấn vào dòng → xem chi tiết

**Tính năng lọc**:
- Theo trạng thái
- Theo khoảng thời gian
- Theo loại sự cố

---

#### **UC-13: Xác nhận hoàn thành dịch vụ**

**Điều kiện**: Công ty đã cập nhật `status = COMPLETED`.

**Luồng chính**:
1. Khách hàng nhận thông báo "Dịch vụ đã hoàn thành"
2. Xem trang xác nhận hiển thị chi tiết dịch vụ đã dùng + giá `agreedPrice`
3. Nhấn "Xác nhận" → chuyển sang bước thanh toán

---

### CHỨC NĂNG 1.4 — Thanh toán

#### **UC-14: Thanh toán dịch vụ**

**Điều kiện**: Yêu cầu đã ở trạng thái `COMPLETED`, chưa có `Payment`.

**Luồng chính**:
1. Xem trang tóm tắt thanh toán:
   - Danh sách dịch vụ đã sử dụng + đơn giá + số lượng
   - Tổng tiền (`agreedPrice`)
   - Thông tin công ty cứu hộ
2. Chọn phương thức thanh toán:
   - **Tiền mặt**: xác nhận đã thanh toán trực tiếp
   - **Chuyển khoản**: hiển thị thông tin ngân hàng + nhập mã giao dịch
   - **Ví điện tử**: nhập mã giao dịch
3. Nhấn "Xác nhận thanh toán"
4. Hệ thống tạo `Payment` (`status = PAID`)
5. Hệ thống gửi `Notification` cho công ty

**Luồng ngoại lệ**:
- **E1**: Chưa xác nhận mã giao dịch (với chuyển khoản/ví) → yêu cầu nhập

---

#### **UC-15: Xem lịch sử thanh toán**

**Hiển thị**: Danh sách các lần thanh toán, mỗi dòng gồm ngày, dịch vụ, công ty, số tiền, phương thức, trạng thái.

---

### CHỨC NĂNG 1.5 — Đánh giá

#### **UC-16: Đánh giá dịch vụ**

**Điều kiện**: Yêu cầu đã `COMPLETED` + đã thanh toán + chưa có `Review`.

**Luồng chính**:
1. Nhấn "Đánh giá dịch vụ" từ trang chi tiết yêu cầu
2. Chọn số sao (1–5)
3. Nhập nhận xét (tuỳ chọn, tối đa 500 ký tự)
4. Gửi đánh giá
5. Hệ thống cập nhật lại `ratingAverage` của công ty

**Ràng buộc**: Mỗi yêu cầu chỉ được đánh giá 1 lần.

---

#### **UC-17: Sửa/Xóa đánh giá**

**Điều kiện**: Chỉ trong vòng 7 ngày kể từ khi tạo.

---

### CHỨC NĂNG 1.6 — Tin nhắn & Thông báo

#### **UC-18: Nhắn tin với công ty cứu hộ**

**Mô tả**: Trao đổi trực tiếp trong phạm vi 1 yêu cầu cứu hộ.

**Luồng chính**:
1. Từ trang chi tiết yêu cầu, mở khung chat
2. Nhập nội dung tin nhắn → gửi
3. Hệ thống lưu `Message` (`senderId = customer`, `receiverId = company`)
4. Tin nhắn xuất hiện ở cả 2 phía (tự làm mới mỗi 5 giây)

**Ràng buộc**: Chỉ nhắn được khi yêu cầu đang ở trạng thái `ACCEPTED` → `IN_PROGRESS`.

---

#### **UC-19: Xem thông báo**

**Luồng chính**:
1. Nhấn vào chuông thông báo trên navbar
2. Hiển thị danh sách thông báo (mới nhất trước)
3. Thông báo chưa đọc được highlight
4. Nhấn vào thông báo → chuyển đến trang liên quan + đánh dấu đã đọc

**Các loại thông báo Customer nhận được**:
- Công ty chấp nhận yêu cầu
- Công ty từ chối yêu cầu (kèm lý do)
- Nhân viên được phân công
- Nhân viên đang trên đường
- Dịch vụ hoàn thành

---

### CHỨC NĂNG 1.7 — Cộng đồng hỗ trợ

#### **UC-20: Tạo bài đăng hỏi đáp**

**Mô tả**: Đặt câu hỏi để nhận tư vấn từ cộng đồng về sự cố xe.

**Dữ liệu đầu vào**:
- `title`: bắt buộc, 10–200 ký tự
- `incidentType`: bắt buộc
- `content`: bắt buộc, tối thiểu 30 ký tự

---

#### **UC-21: Xem danh sách bài đăng cộng đồng**

**Tính năng**:
- Phân trang (10 bài/trang)
- Lọc theo loại sự cố
- Tìm kiếm theo tiêu đề
- Badge "Đã giải quyết" cho bài đã đóng

---

#### **UC-22: Phản hồi bài đăng**

**Luồng chính**:
1. Vào trang chi tiết bài đăng
2. Xem các phản hồi hiện có
3. Nhập nội dung phản hồi → gửi
4. Nhấn "Hữu ích" để đánh dấu phản hồi hay

---

#### **UC-23: Đóng/Xóa bài đăng**

**Điều kiện**: Chỉ tác giả hoặc Admin mới có quyền.

---

## 6. CHI TIẾT CHỨC NĂNG RESCUECOMPANY

### CHỨC NĂNG 2.1 — Đăng ký & Xác minh

#### **UC-24: Đăng ký tài khoản công ty**

**Mô tả**: Công ty cứu hộ đăng ký tài khoản để cung cấp dịch vụ trên hệ thống.

**Luồng chính**:
1. Truy cập trang đăng ký công ty
2. Nhập thông tin tài khoản: email, mật khẩu, họ tên người đại diện, SĐT
3. Nhập thông tin công ty: tên công ty, số giấy phép kinh doanh, khu vực hoạt động, mô tả
4. Hệ thống tạo tài khoản với `isVerified = False`
5. Hiển thị thông báo "Tài khoản đang chờ Admin xác minh"

**Dữ liệu đầu vào**:

**Tài khoản**:
- `email`: bắt buộc, duy nhất
- `password`: bắt buộc, tối thiểu 8 ký tự
- `fullName`: bắt buộc (người đại diện)
- `phone`: bắt buộc

**Thông tin công ty**:
- `companyName`: bắt buộc, duy nhất
- `businessLicense`: bắt buộc, duy nhất
- `operatingArea`: bắt buộc (mô tả khu vực hoạt động)
- `description`: tuỳ chọn

**Ràng buộc**: Công ty chưa được xác minh (`isVerified = False`) sẽ không thể tiếp nhận yêu cầu.

---

#### **UC-25: Đăng nhập công ty**

**Luồng chính**: Tương tự UC-02 nhưng sau đăng nhập chuyển về Company Dashboard.

**Luồng ngoại lệ thêm**:
- **E3**: `isVerified = False` → hiển thị trang "Chờ xác minh", không vào được dashboard

---

### CHỨC NĂNG 2.2 — Dashboard tổng quan

#### **UC-26: Xem Dashboard**

**Mô tả**: Trang tổng quan hiển thị các chỉ số quan trọng của công ty.

**Thông tin hiển thị** (dữ liệu tính theo ngày hiện tại):
- **Yêu cầu mới**: `status = PENDING` chưa phản hồi
- **Đang xử lý**: `status ∈ {ACCEPTED, ASSIGNED, ON_THE_WAY, IN_PROGRESS}`
- **Hoàn thành hôm nay**: `completedTime` trong ngày hôm nay
- **Rating trung bình**: `ratingAverage` của công ty

---

### CHỨC NĂNG 2.3 — Tiếp nhận yêu cầu cứu hộ

#### **UC-27: Xem danh sách yêu cầu mới**

**Mô tả**: Công ty xem các yêu cầu cứu hộ chưa được phản hồi.

**Hiển thị mỗi yêu cầu**:
- Thời gian tạo yêu cầu
- Loại sự cố
- Khoảng cách từ trụ sở đến vị trí sự cố
- Tên khách hàng + SĐT
- Dịch vụ yêu cầu
- Bản đồ nhỏ hiển thị vị trí (Leaflet mini-map)
- Nút "Chấp nhận"/"Từ chối"

**Sắp xếp**: Ưu tiên theo thời gian tạo (cũ nhất trước).

---

#### **UC-28: Chấp nhận yêu cầu**

**Điều kiện**: Yêu cầu đang ở `status = PENDING`.

**Luồng chính**:
1. Nhấn "Chấp nhận"
2. Nhập thời gian đến dự kiến (`estimatedArrivalTime`)
3. Xác nhận
4. Status chuyển thành `ACCEPTED`
5. Hệ thống gửi `Notification` cho khách hàng (kèm tên công ty, SĐT, thời gian dự kiến)

---

#### **UC-29: Từ chối yêu cầu**

**Điều kiện**: Yêu cầu đang ở `status = PENDING`.

**Luồng chính**:
1. Nhấn "Từ chối"
2. Nhập lý do từ chối (bắt buộc)
3. Xác nhận
4. Status chuyển thành `REJECTED`
5. Hệ thống gửi `Notification` cho khách hàng (kèm lý do)

**Lý do từ chối mẫu** (dropdown):
- Ngoài khu vực hoạt động
- Không đủ nhân lực hiện tại
- Không có dịch vụ phù hợp
- Khác (nhập tay)

---

#### **UC-30: Phân công nhân viên và xe**

**Điều kiện**: Yêu cầu đang ở `status = ACCEPTED`.

**Luồng chính**:
1. Vào trang chi tiết yêu cầu → nhấn "Phân công"
2. Hệ thống hiển thị:
   - Danh sách nhân viên đang `AVAILABLE`
   - Danh sách xe đang `AVAILABLE`
3. Chọn 1 nhân viên + 1 xe + ghi chú (tuỳ chọn)
4. Xác nhận phân công
5. Hệ thống tạo `ServiceAssignment`
6. Status nhân viên chuyển thành `BUSY`
7. Status xe chuyển thành `ON_MISSION`
8. Status yêu cầu chuyển thành `ASSIGNED`
9. Gửi `Notification` cho nhân viên và khách hàng

**Luồng ngoại lệ**:
- **E1**: Không có nhân viên `AVAILABLE` → thông báo "Không có nhân viên trống, vui lòng từ chối hoặc chờ"
- **E2**: Không có xe `AVAILABLE` → tương tự

---

#### **UC-31: Cập nhật trạng thái yêu cầu**

**Mô tả**: Công ty cập nhật tiến trình xử lý yêu cầu.

**Các bước trạng thái hợp lệ**:
- `ASSIGNED` → `ON_THE_WAY`: Nhân viên đang xuất phát
- `ON_THE_WAY` → `IN_PROGRESS`: Nhân viên đã đến nơi, bắt đầu xử lý
- `IN_PROGRESS` → `COMPLETED`: Xử lý xong

**Khi chuyển sang `COMPLETED`**:
1. Công ty nhập `agreedPrice` (giá thực tế sau thỏa thuận)
2. Ghi nhận `actualArrivalTime` + `completedTime`
3. Cập nhật status nhân viên → `AVAILABLE`
4. Cập nhật status xe → `AVAILABLE`
5. Gửi `Notification` cho khách hàng

---

#### **UC-32: Xem tất cả yêu cầu của công ty**

**Tính năng lọc**:
- Theo trạng thái
- Theo khoảng thời gian
- Theo loại sự cố
- Theo nhân viên xử lý

**Hiển thị**: Bảng danh sách có phân trang, mỗi dòng có link xem chi tiết.

---

### CHỨC NĂNG 2.4 — Quản lý dịch vụ

#### **UC-33: Xem danh sách dịch vụ**

**Hiển thị**: Tên dịch vụ, mô tả, giá cơ bản, thời gian xử lý dự kiến, trạng thái hoạt động.

---

#### **UC-34: Thêm dịch vụ mới**

**Dữ liệu đầu vào**:
- `serviceName`: bắt buộc
- `description`: bắt buộc
- `basePrice`: bắt buộc, > 0, đơn vị VNĐ
- `estimatedDuration`: bắt buộc, tính bằng phút, > 0
- `isActive`: mặc định `True`

**Ràng buộc**: Tên dịch vụ không được trùng trong cùng 1 công ty.

---

#### **UC-35: Sửa dịch vụ**

**Ràng buộc**: Không sửa được dịch vụ đang có trong yêu cầu chưa hoàn thành.

---

#### **UC-36: Ẩn/Hiện dịch vụ**

**Mô tả**: Thay vì xóa, công ty ẩn dịch vụ (`isActive = False`) để không hiện trong danh sách tìm kiếm của khách hàng.

---

### CHỨC NĂNG 2.5 — Quản lý phương tiện

#### **UC-37: Thêm xe cứu hộ**

**Dữ liệu đầu vào**:
- `plateNumber`: bắt buộc, duy nhất toàn hệ thống
- `vehicleType`: bắt buộc (Xe tải cứu hộ/Xe máy/Xe van/Xe con)
- `capacity`: bắt buộc (mô tả tải trọng/năng lực)
- `status`: mặc định `AVAILABLE`

---

#### **UC-38: Cập nhật trạng thái xe**

**Các trạng thái**:
- `AVAILABLE`: Sẵn sàng nhận việc
- `ON_MISSION`: Đang trên đường/tại hiện trường
- `MAINTENANCE`: Đang bảo dưỡng, sửa chữa

**Ràng buộc**: Không thể đặt `MAINTENANCE` khi xe đang `ON_MISSION`.

---

#### **UC-39: Xóa xe cứu hộ**

**Ràng buộc**: Chỉ xóa được khi `status = AVAILABLE` và không có phân công chưa hoàn thành.

---

### CHỨC NĂNG 2.6 — Quản lý nhân viên

#### **UC-40: Thêm nhân viên**

**Dữ liệu đầu vào**:

**Tài khoản**:
- `email`: bắt buộc, duy nhất
- `password`: bắt buộc (tạm thời, nhân viên đổi sau)
- `fullName`: bắt buộc
- `phone`: bắt buộc

**Thông tin nhân viên**:
- `skillLevel`: bắt buộc (Sơ cấp/Trung cấp/Cao cấp)
- `status`: mặc định `AVAILABLE`

---

#### **UC-41: Xem danh sách nhân viên**

**Hiển thị**: Họ tên, SĐT, trình độ, trạng thái hiện tại, số yêu cầu đã xử lý.

---

#### **UC-42: Cập nhật thông tin nhân viên**

---

#### **UC-43: Vô hiệu hoá nhân viên**

**Ràng buộc**: Chỉ vô hiệu khi nhân viên đang `AVAILABLE` (không có phân công đang chạy).

---

### CHỨC NĂNG 2.7 — Tin nhắn & Thông báo

#### **UC-44: Nhắn tin với khách hàng**

**Mô tả**: Trao đổi về sự cố trong phạm vi 1 yêu cầu.

**Ràng buộc**: Chỉ nhắn được khi yêu cầu đang `ACCEPTED` → `IN_PROGRESS`.

---

#### **UC-45: Xem thông báo công ty**

**Các loại thông báo công ty nhận được**:
- Có yêu cầu cứu hộ mới
- Khách hàng hủy yêu cầu
- Khách hàng đã thanh toán
- Khách hàng gửi đánh giá mới

---

### CHỨC NĂNG 2.8 — Đánh giá nhận được

#### **UC-46: Xem danh sách đánh giá**

**Hiển thị**: Rating sao, nhận xét, tên khách hàng, ngày đánh giá, yêu cầu liên quan.

**Thống kê**: Tỉ lệ từng mức sao (1★ đến 5★), rating trung bình.

---

## 7. CHI TIẾT CHỨC NĂNG ADMIN

### CHỨC NĂNG 3.1 — Đăng nhập Admin

#### **UC-47: Đăng nhập**

**Luồng chính**:
1. Truy cập `/admin-panel/login`
2. Nhập email + mật khẩu (tài khoản Admin)
3. Đăng nhập thành công → Admin Dashboard

**Bảo mật**: Tất cả URL `/admin-panel/*` chỉ truy cập được khi đã đăng nhập với tài khoản Admin.

---

### CHỨC NĂNG 3.2 — Dashboard Admin

#### **UC-48: Xem tổng quan hệ thống**

**Thông tin hiển thị**:
- Tổng số khách hàng
- Tổng số công ty cứu hộ
- Số công ty chờ xác minh
- Tổng số yêu cầu hôm nay
- Doanh thu hôm nay
- Rating trung bình toàn hệ thống

---

### CHỨC NĂNG 3.3 — Quản lý tài khoản khách hàng

#### **UC-49: Xem danh sách khách hàng**

**Tính năng**:
- Tìm kiếm theo tên, email, SĐT
- Lọc theo trạng thái tài khoản (`ACTIVE`/`INACTIVE`/`SUSPENDED`)
- Phân trang (20 dòng/trang)

**Hiển thị mỗi dòng**:
- Họ tên, email, SĐT, ngày đăng ký, trạng thái, số yêu cầu đã tạo

---

#### **UC-50: Xem chi tiết khách hàng**

**Hiển thị**:
- Thông tin cá nhân đầy đủ
- Danh sách xe đã đăng ký
- Lịch sử yêu cầu cứu hộ (5 cái gần nhất)
- Lịch sử thanh toán
- Đánh giá đã viết

---

#### **UC-51: Khóa tài khoản khách hàng**

**Luồng chính**:
1. Vào chi tiết khách hàng → nhấn "Khóa tài khoản"
2. Nhập lý do khóa (bắt buộc)
3. Xác nhận
4. Status chuyển thành `SUSPENDED`
5. Tài khoản không thể đăng nhập

**Ràng buộc**: Không khóa được tài khoản đang có yêu cầu chưa hoàn thành (`status ≠ COMPLETED`/`CANCELLED`/`REJECTED`).

---

#### **UC-52: Mở khóa tài khoản khách hàng**

**Luồng chính**:
1. Nhấn "Mở khóa"
2. Xác nhận
3. Status chuyển thành `ACTIVE`

---

### CHỨC NĂNG 3.4 — Quản lý công ty cứu hộ

#### **UC-53: Xem danh sách công ty**

**Tính năng lọc**:
- Theo trạng thái xác minh (Chờ duyệt/Đã xác minh/Bị từ chối)
- Theo khu vực hoạt động
- Tìm kiếm theo tên công ty

**Hiển thị mỗi dòng**:
- Tên công ty, người đại diện, SĐT, khu vực, ngày đăng ký, trạng thái, rating

---

#### **UC-54: Xem chi tiết công ty**

**Hiển thị**:
- Thông tin đầy đủ của công ty
- Giấy phép kinh doanh
- Danh sách dịch vụ
- Danh sách xe cứu hộ
- Danh sách nhân viên
- Lịch sử yêu cầu (10 cái gần nhất)
- Tất cả đánh giá nhận được

---

#### **UC-55: Xác minh công ty (Duyệt)**

**Điều kiện**: Công ty có `isVerified = False`, chưa bị từ chối.

**Luồng chính**:
1. Xem thông tin công ty + giấy phép kinh doanh
2. Nhấn "Xác minh/Duyệt"
3. Xác nhận
4. `isVerified` chuyển thành `True`
5. Hệ thống gửi `Notification` cho công ty: "Tài khoản đã được xác minh, bạn có thể bắt đầu nhận yêu cầu"

---

#### **UC-56: Từ chối xác minh công ty**

**Luồng chính**:
1. Nhấn "Từ chối"
2. Nhập lý do (bắt buộc)
3. Xác nhận
4. Gửi `Notification` cho công ty kèm lý do

---

#### **UC-57: Khóa/Mở khóa tài khoản công ty**

**Luồng chính**: Tương tự UC-51/UC-52 nhưng áp dụng cho `RescueCompany`.

**Ràng buộc**: Không khóa khi công ty đang có yêu cầu chưa hoàn thành.

---

### CHỨC NĂNG 3.5 — Kiểm duyệt nội dung

#### **UC-58: Xem danh sách đánh giá**

**Tính năng**:
- Lọc theo số sao (1★/2★/.../5★)
- Lọc theo công ty
- Lọc theo khoảng thời gian
- Tìm kiếm theo nội dung nhận xét

**Hiển thị**: Tên khách hàng, tên công ty, số sao, nội dung, ngày viết, nút xóa.

---

#### **UC-59: Xóa đánh giá vi phạm**

**Luồng chính**:
1. Nhấn "Xóa đánh giá"
2. Nhập lý do xóa
3. Xác nhận
4. Xóa `Review` khỏi DB
5. Hệ thống tự tính lại `ratingAverage` của công ty
6. Gửi `Notification` cho khách hàng đã viết: "Đánh giá của bạn đã bị xóa vì [lý do]"

---

#### **UC-60: Kiểm duyệt bài đăng cộng đồng**

**Luồng chính**:
1. Xem danh sách bài đăng cộng đồng
2. Lọc theo trạng thái, loại sự cố
3. Xóa bài vi phạm (kèm lý do)
4. Gửi `Notification` cho tác giả

---

### CHỨC NĂNG 3.6 — Báo cáo & Thống kê

#### **UC-61: Báo cáo yêu cầu cứu hộ**

**Bộ lọc**:
- `fromDate`: ngày bắt đầu
- `toDate`: ngày kết thúc
- `companyId`: lọc theo công ty (tuỳ chọn)
- `incidentType`: lọc theo loại sự cố (tuỳ chọn)
- `status`: lọc theo trạng thái (tuỳ chọn)

**Dữ liệu hiển thị**:
- Tổng số yêu cầu trong kỳ
- Số yêu cầu theo từng trạng thái
- Số yêu cầu theo loại sự cố (bảng + biểu đồ tròn)
- Số yêu cầu theo ngày (biểu đồ đường)
- Tỉ lệ hủy/từ chối

---

#### **UC-62: Báo cáo doanh thu**

**Dữ liệu hiển thị**:
- Tổng doanh thu trong kỳ (tổng `amount` từ `Payment` `status = PAID`)
- Doanh thu theo từng công ty (bảng xếp hạng)
- Doanh thu theo ngày (biểu đồ cột)
- Doanh thu theo phương thức thanh toán (biểu đồ tròn)

---

#### **UC-63: Báo cáo mức độ hài lòng**

**Dữ liệu hiển thị**:
- Rating trung bình toàn hệ thống
- Phân phối số sao (1★ → 5★) dạng thanh ngang
- Top 5 công ty có rating cao nhất
- Top 5 công ty có rating thấp nhất
- Số lượng đánh giá theo khoảng thời gian

---

#### **UC-64: Xuất báo cáo**

**Luồng chính**:
1. Sau khi xem báo cáo, nhấn "Xuất Excel" hoặc "Xuất PDF"
2. Hệ thống tạo file với dữ liệu đã lọc
3. File tự động tải về

**Định dạng Excel**: Mỗi sheet là 1 loại dữ liệu (tổng quan/chi tiết/biểu đồ).

**Định dạng PDF**: Layout đẹp, có logo, tiêu đề báo cáo, khoảng thời gian, bảng dữ liệu.

---

## 8. QUY TẮC NGHIỆP VỤ VÀ RÀNG BUỘC

### 8.1. Quy tắc phân quyền

| Chức năng | Customer | RescueCompany | Admin |
|-----------|----------|---------------|-------|
| Đăng ký/Đăng nhập | ✓ | ✓ | ✓ (chỉ đăng nhập) |
| Quản lý hồ sơ cá nhân | ✓ | ✓ | - |
| Tạo yêu cầu cứu hộ | ✓ | - | - |
| Tiếp nhận yêu cầu | - | ✓ | - |
| Phân công nhân viên | - | ✓ | - |
| Quản lý dịch vụ | Xem | ✓ (CRUD) | - |
| Quản lý xe/nhân viên | - | ✓ (CRUD) | - |
| Chat | ✓ | ✓ | - |
| Thanh toán | ✓ | Xem | Xem |
| Đánh giá | ✓ | Xem | Xóa/Kiểm duyệt |
| Xem báo cáo | - | Xem (riêng công ty) | ✓ (toàn hệ thống) |
| Xác minh công ty | - | - | ✓ |
| Khóa tài khoản | - | - | ✓ |

### 8.2. Quy tắc trạng thái yêu cầu

**State Machine hợp lệ**:

```
PENDING
├──→ ACCEPTED (công ty chấp nhận)
│    ├──→ ASSIGNED (phân công nhân viên + xe)
│    │    ├──→ ON_THE_WAY (nhân viên xuất phát)
│    │    │    ├──→ IN_PROGRESS (đến nơi, xử lý)
│    │    │    │    ├──→ COMPLETED (hoàn thành)
│    │    │    │    │    ├──→ PAID (thanh toán)
│    │    │    │    │    │    └──→ REVIEWED (đánh giá)
│    │    │    │    │    └──→ (kết thúc)
├──→ REJECTED (công ty từ chối)
└──→ CANCELLED (khách hủy - chỉ khi PENDING)
```

**Ràng buộc chuyển trạng thái**:
1. Chỉ được phân công (`ASSIGNED`) khi trạng thái là `ACCEPTED`
2. Chỉ được cập nhật giá (`agreedPrice`) khi ở `IN_PROGRESS` → `COMPLETED`
3. Không cho phép chỉnh sửa/xóa xe & dịch vụ khi đang có yêu cầu ở trạng thái `PENDING` → `IN_PROGRESS`
4. Chỉ được hủy yêu cầu khi `status = PENDING`
5. Chỉ được thanh toán khi `status = COMPLETED` và chưa có `Payment`
6. Chỉ được đánh giá khi đã `COMPLETED` + đã thanh toán + chưa có `Review`

### 8.3. Quy tắc thông báo tự động

**Customer nhận được**:
- Khi công ty chấp nhận yêu cầu (`ACCEPTED`)
- Khi công ty từ chối yêu cầu (`REJECTED`) + lý do
- Khi nhân viên được phân công (`ASSIGNED`)
- Khi nhân viên đang trên đường (`ON_THE_WAY`)
- Khi dịch vụ hoàn thành (`COMPLETED`)
- Khi công ty gửi tin nhắn
- Khi đánh giá bị xóa (bởi Admin)

**RescueCompany nhận được**:
- Khi có yêu cầu mới (`PENDING`)
- Khi khách hàng hủy yêu cầu (`CANCELLED`)
- Khi khách hàng đã thanh toán (`PAID`)
- Khi khách hàng gửi đánh giá mới

**RescueStaff nhận được**:
- Khi được phân công (`ASSIGNED`)

### 8.4. Ràng buộc dữ liệu

**Định dạng và validation**:

| Trường | Ràng buộc |
|--------|-----------|
| `email` | Duy nhất, đúng định dạng email |
| `phone` | 10 số, bắt đầu bằng 0, duy nhất |
| `password` | Tối thiểu 8 ký tự, đủ mạnh |
| `licensePlate` (Vehicle) | Định dạng VN, duy nhất toàn hệ thống |
| `plateNumber` (RescueVehicle) | Duy nhất toàn hệ thống |
| `businessLicense` | Duy nhất |
| `companyName` | Duy nhất |
| `description` (RescueRequest) | Tối thiểu 20 ký tự |
| `content` (CommunityPost) | Tối thiểu 30 ký tự |
| `title` (CommunityPost) | 10-200 ký tự |
| `comment` (Review) | Tối đa 500 ký tự |
| `basePrice` | > 0 |
| `year` (Vehicle) | 1990 → năm hiện tại |
| `rating` | 1-5 |

**Unique constraints**:
- `Vehicle.licensePlate`: duy nhất toàn hệ thống
- `RescueVehicle.plateNumber`: duy nhất toàn hệ thống
- `RescueCompany.businessLicense`: duy nhất
- `RescueCompany.companyName`: duy nhất
- `Review.requestId`: 1 request chỉ có 1 review

### 8.5. Các ENUM trong sơ đồ lớp

**AccountStatus**:
- `ACTIVE`: Hoạt động bình thường
- `INACTIVE`: Chưa kích hoạt
- `SUSPENDED`: Bị khóa

**RequestStatus**:
- `PENDING`: Chờ phản hồi
- `ACCEPTED`: Đã chấp nhận
- `ASSIGNED`: Đã phân công
- `ON_THE_WAY`: Đang trên đường
- `IN_PROGRESS`: Đang xử lý
- `COMPLETED`: Hoàn thành
- `REJECTED`: Từ chối
- `CANCELLED`: Hủy

**RescueVehicleStatus**:
- `AVAILABLE`: Sẵn sàng
- `ON_MISSION`: Đang làm nhiệm vụ
- `MAINTENANCE`: Bảo dưỡng

**StaffStatus**:
- `AVAILABLE`: Sẵn sàng
- `BUSY`: Đang bận

**PaymentStatus**:
- `PENDING`: Chờ thanh toán
- `PAID`: Đã thanh toán
- `REFUNDED`: Đã hoàn tiền

---

## 9. STATE MACHINE

### 9.1. RescueRequest State Machine

```
[Start] → PENDING
              ↓
        ┌─────┴─────
        ↓           ↓
   ACCEPTED    REJECTED
        ↓           ↓
   ASSIGNED    [End]
        ↓
   ON_THE_WAY
        ↓
   IN_PROGRESS
        ↓
   COMPLETED
        ↓
     PAID
        ↓
   REVIEWED
        ↓
      [End]

PENDING → CANCELLED (Customer hủy)
```

**Transitions**:
- `PENDING` → `ACCEPTED`: Company chấp nhận
- `PENDING` → `REJECTED`: Company từ chối
- `PENDING` → `CANCELLED`: Customer hủy
- `ACCEPTED` → `ASSIGNED`: Company phân công staff + vehicle
- `ASSIGNED` → `ON_THE_WAY`: Staff xuất phát
- `ON_THE_WAY` → `IN_PROGRESS`: Staff đến nơi, bắt đầu xử lý
- `IN_PROGRESS` → `COMPLETED`: Hoàn thành, cập nhật agreedPrice
- `COMPLETED` → `PAID`: Customer thanh toán
- `PAID` → `REVIEWED`: Customer đánh giá

### 9.2. RescueVehicle State Machine

```
[Start] → AVAILABLE
              ↓
        ┌─────┴─────┐
        ↓           ↓
   ON_MISSION  MAINTENANCE
        ↓           ↓
   AVAILABLE   AVAILABLE
        ↓           ↓
      [End]
```

**Transitions**:
- `AVAILABLE` → `ON_MISSION`: Được phân công
- `ON_MISSION` → `AVAILABLE`: Hoàn thành nhiệm vụ
- `AVAILABLE` → `MAINTENANCE`: Bảo dưỡng
- `MAINTENANCE` → `AVAILABLE`: Sửa xong

**Ràng buộc**: Không thể `ON_MISSION` → `MAINTENANCE`

### 9.3. RescueStaff State Machine

```
[Start] → AVAILABLE
              ↓
           BUSY
              ↓
        AVAILABLE
              ↓
           [End]
```

**Transitions**:
- `AVAILABLE` → `BUSY`: Được phân công
- `BUSY` → `AVAILABLE`: Hoàn thành nhiệm vụ
