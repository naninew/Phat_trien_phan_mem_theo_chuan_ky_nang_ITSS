# Chi Tiết Cấu Trúc Mã Nguồn - Roadside Assistance System

## Tổng Quan Kiến Trúc

Hệ thống được phát triển theo kiến trúc **3-tier** với:
- **Frontend**: NiceGUI (Python-based web UI)
- **Backend**: FastAPI (RESTful API)
- **Database**: PostgreSQL (Quan hệ)

---

## Sơ Đồ Thư Mục

```
/workspace/
├── backend/                      # Backend FastAPI
│   ├── app/
│   │   ├── models/               # SQLAlchemy ORM Models
│   │   │   ├── __init__.py
│   │   │   ├── user.py           # User model
│   │   │   ├── company.py        # RescueCompany model
│   │   │   ├── service.py        # Service model
│   │   │   ├── vehicle.py        # RescueVehicle model
│   │   │   ├── request.py        # RescueRequest model
│   │   │   ├── payment.py        # Payment model
│   │   │   ├── review.py         # Review model
│   │   │   └── community.py      # CommunityPost, Comment models
│   │   │
│   │   ├── schemas/              # Pydantic Validation Schemas
│   │   │   ├── __init__.py
│   │   │   ├── auth.py           # Login/Register schemas
│   │   │   └── rescue.py         # Rescue service schemas
│   │   │
│   │   ├── services/             # Business Logic Layer
│   │   │   ├── __init__.py
│   │   │   ├── auth_svc.py       # Authentication logic
│   │   │   └── rescue_svc.py     # Rescue operations logic
│   │   │
│   │   ├── routes/               # API Endpoint Routers
│   │   │   ├── __init__.py
│   │   │   ├── auth_routes.py    # /api/v1/auth/* endpoints
│   │   │   └── rescue_routes.py  # /api/v1/rescue/* endpoints
│   │   │
│   │   ├── utils/                # Utility Functions
│   │   │   ├── __init__.py
│   │   │   ├── jwt_helper.py     # JWT token generation/validation
│   │   │   └── response.py       # Standardized response formatting
│   │   │
│   │   ├── database.py           # Database connection & session
│   │   └── main.py               # FastAPI app initialization
│   │
│   ├── requirements.txt          # Python dependencies
│   ├── run.py                    # Backend entry point
│   └── generate_seed_data.py     # Database initialization & mock data generator
│
├── frontend/                     # Frontend NiceGUI
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py             # App configuration
│   │   └── auth.py               # Session management
│   │
│   ├── components/               # Reusable UI Components
│   │   ├── __init__.py
│   │   └── navbar.py             # Navigation bar component
│   │
│   ├── pages/                    # Page Definitions
│   │   ├── auth/                 # Login/Register pages
│   │   ├── customer/             # Customer dashboard pages
│   │   ├── company/              # Company dashboard pages
│   │   └── admin/                # Admin dashboard pages
│   │
│   ├── services/                 # API Client Services
│   │   ├── __init__.py
│   │   ├── api_client.py         # Base HTTP client
│   │   ├── auth_api.py           # Auth API calls
│   │   └── rescue_api.py         # Rescue API calls
│   │
│   ├── static/                   # Static assets (CSS, images)
│   └── main.py                   # Frontend entry point (cần tạo)
│
├── README.md                     # Project overview
├── HOW_TO_START_PROJECT.md       # Setup instructions
└── DETAIL_STRUCTURE.md           # This file
```

---

## Chi Tiết Từng Module

### BACKEND

#### 1. Database Layer (`backend/app/database.py`)

**Mục đích**: Quản lý kết nối PostgreSQL và session.

**Biến toàn cục**:
- `DATABASE_URL` (str): Connection string PostgreSQL
- `engine`: SQLAlchemy engine
- `SessionLocal`: Session factory
- `Base`: Declarative base class

**Hàm**:

##### `get_db() -> Generator[Session, None, None]`
- **Input**: Không có
- **Output**: Yield một SQLAlchemy Session
- **Mô tả**: Dependency để inject database session vào routes
- **Ví dụ**:
```python
@router.get("/users")
def get_users(db: Session = Depends(get_db)):
    ...
```

##### `init_db()`
- **Input**: Không có
- **Output**: None
- **Mô tả**: Tạo tất cả tables từ models
- **Side effects**: Tạo tables trong database

---

#### 2. Models Layer (`backend/app/models/`)

##### `user.py` - User Model

**Class**: `User(Base)`

**Attributes**:
| Tên | Type | Mô tả |
|-----|------|-------|
| id | int | Primary key |
| username | str(50) | Unique username |
| password_hash | str(255) | Hashed password |
| full_name | str(100) | Full name |
| phone | str(20) | Phone number |
| email | str(100) | Unique email |
| role | UserRole enum | customer/company_staff/admin |
| is_active | bool | Account status |
| created_at | datetime | Creation timestamp |
| updated_at | datetime | Last update timestamp |

**Relationships**:
- `rescue_requests`: One-to-many với RescueRequest
- `company`: One-to-one với RescueCompany

**Enum `UserRole`**:
- `CUSTOMER = "customer"`
- `COMPANY_STAFF = "company_staff"`
- `ADMIN = "admin"`

---

##### `company.py` - RescueCompany Model

**Class**: `RescueCompany(Base)`

**Attributes**:
| Tên | Type | Mô tả |
|-----|------|-------|
| id | int | Primary key |
| company_name | str(200) | Company name |
| address | Text | Address |
| hotline | str(20) | Hotline phone |
| license_number | str(50) | Unique license |
| rating_avg | float | Average rating (0-5) |
| status | str(20) | active/suspended |
| service_radius_km | float | Service radius |
| owner_id | int | FK to users.id |
| is_verified | bool | Verification status |

**Relationships**:
- `owner`: Many-to-one với User
- `services`: One-to-many với Service
- `vehicles`: One-to-many với RescueVehicle
- `rescue_requests`: One-to-many với RescueRequest

---

##### `service.py` - Service Model

**Class**: `Service(Base)`

**Attributes**:
| Tên | Type | Mô tả |
|-----|------|-------|
| id | int | Primary key |
| service_name | str(100) | Service name |
| base_price | float | Base price (VND) |
| description | Text | Description |
| company_id | int | FK to rescue_companies.id |
| is_active | bool | Service status |

**Relationships**:
- `company`: Many-to-one với RescueCompany
- `rescue_requests`: One-to-many với RescueRequest

---

##### `vehicle.py` - RescueVehicle Model

**Class**: `RescueVehicle(Base)`

**Attributes**:
| Tên | Type | Mô tả |
|-----|------|-------|
| id | int | Primary key |
| license_plate | str(20) | License plate |
| vehicle_type | str(50) | Type (xe cẩu, xe kích bình...) |
| capacity | str(50) | Capacity description |
| status | VehicleStatus enum | available/on_mission/maintenance |
| company_id | int | FK to rescue_companies.id |
| is_active | bool | Vehicle status |

**Enum `VehicleStatus`**:
- `AVAILABLE = "available"`
- `ON_MISSION = "on_mission"`
- `MAINTENANCE = "maintenance"`

**Relationships**:
- `company`: Many-to-one với RescueCompany

---

##### `request.py` - RescueRequest Model

**Class**: `RescueRequest(Base)`

**Attributes**:
| Tên | Type | Mô tả |
|-----|------|-------|
| id | int | Primary key |
| user_id | int | FK to users.id |
| company_id | int | FK to rescue_companies.id |
| service_id | int | FK to services.id |
| vehicle_id | int | FK to rescue_vehicles.id |
| latitude | float | GPS latitude |
| longitude | float | GPS longitude |
| address_description | Text | Location description |
| car_issue_detail | Text | Issue description |
| images | JSON | List of image URLs |
| status | RequestStatus enum | Request status |
| eta_minutes | int | Estimated arrival time |
| actual_arrival_time | datetime | Actual arrival |
| actual_completion_time | datetime | Completion time |
| total_cost | float | Total cost |
| payment_status | str | unpaid/paid/refunded |
| payment_method | str | cash/momo/vnpay/card |
| feedback | Text | Customer feedback |
| rating | int | Rating 1-5 |

**Enum `RequestStatus`**:
- `PENDING = "pending"`
- `ACCEPTED = "accepted"`
- `EN_ROUTE = "en_route"`
- `ON_SITE = "on_site"`
- `COMPLETED = "completed"`
- `CANCELLED = "cancelled"`

**Relationships**:
- `user`: Many-to-one với User
- `company`: Many-to-one với RescueCompany
- `service`: Many-to-one với Service
- `vehicle`: Many-to-one với RescueVehicle
- `payment`: One-to-one với Payment
- `review`: One-to-one với Review

---

##### `payment.py` - Payment Model

**Class**: `Payment(Base)`

**Attributes**:
| Tên | Type | Mô tả |
|-----|------|-------|
| id | int | Primary key |
| rescue_request_id | int | FK unique to rescue_requests.id |
| amount | float | Payment amount |
| payment_method | str | cash/momo/vnpay/card |
| transaction_id | str(100) | External transaction ID |
| status | str(20) | pending/success/failed/refunded |
| payment_url | str(500) | Payment gateway URL |
| paid_at | datetime | Payment completion time |

**Relationships**:
- `rescue_request`: One-to-one với RescueRequest

---

##### `review.py` - Review Model

**Class**: `Review(Base)`

**Attributes**:
| Tên | Type | Mô tả |
|-----|------|-------|
| id | int | Primary key |
| rescue_request_id | int | FK unique to rescue_requests.id |
| user_id | int | FK to users.id |
| company_id | int | FK to rescue_companies.id |
| rating | int | Rating 1-5 |
| comment | Text | Review comment |
| is_approved | bool | Admin approval status |

**Relationships**:
- `rescue_request`: One-to-one với RescueRequest
- `user`: Many-to-one với User
- `company`: Many-to-one với RescueCompany

---

##### `community.py` - Community Models

**Class**: `CommunityPost(Base)`

**Attributes**:
| Tên | Type | Mô tả |
|-----|------|-------|
| id | int | Primary key |
| user_id | int | FK to users.id |
| title | str(200) | Post title |
| content | Text | Post content |
| images | Text | Comma-separated image URLs |
| is_resolved | bool | Resolution status |
| is_approved | bool | Admin approval |

**Relationships**:
- `user`: Many-to-one với User
- `comments`: One-to-many với Comment

**Class**: `Comment(Base)`

**Attributes**:
| Tên | Type | Mô tả |
|-----|------|-------|
| id | int | Primary key |
| post_id | int | FK to community_posts.id |
| user_id | int | FK to users.id |
| content | Text | Comment content |
| is_approved | bool | Admin approval |

**Relationships**:
- `post`: Many-to-one với CommunityPost
- `user`: Many-to-one với User

---

#### 3. Schemas Layer (`backend/app/schemas/`)

##### `auth.py` - Authentication Schemas

**Class**: `UserRegister(BaseModel)`
- **Input fields**: username, password, full_name, phone, email
- **Validators**: 
  - `validate_phone`: Kiểm tra format số điện thoại
- **Output**: Validated registration data

**Class**: `UserLogin(BaseModel)`
- **Input fields**: username, password
- **Output**: Validated login credentials

**Class**: `TokenResponse(BaseModel)`
- **Fields**: access_token, refresh_token, token_type, expires_in
- **Output**: Token response structure

**Class**: `UserResponse(BaseModel)`
- **Fields**: id, username, full_name, phone, email, role, is_active
- **Output**: User information response

---

##### `rescue.py` - Rescue Service Schemas

**Class**: `ServiceCreate(BaseModel)`
- **Input fields**: service_name, base_price, description (optional)
- **Validation**: base_price > 0

**Class**: `ServiceResponse(BaseModel)`
- **Fields**: id, service_name, base_price, description, company_id, is_active
- **Output**: Service data response

**Class**: `RescueRequestCreate(BaseModel)`
- **Input fields**: service_id, latitude, longitude, address_description, car_issue_detail, images (optional), payment_method (optional)
- **Validation**: 
  - latitude: -90 to 90
  - longitude: -180 to 180

**Class**: `RescueRequestUpdate(BaseModel)`
- **Input fields**: status (optional), eta_minutes (optional), vehicle_id (optional)
- **Validators**: `validate_status` - kiểm tra status hợp lệ

**Class**: `RescueRequestResponse(BaseModel)`
- **Fields**: Tất cả fields của RescueRequest model
- **Output**: Full request data response

**Class**: `CompanyNearbyResponse(BaseModel)`
- **Fields**: id, company_name, address, hotline, rating_avg, distance_km, estimated_price, eta_minutes, services
- **Output**: Nearby company with calculated data

**Class**: `VehicleCreate(BaseModel)`
- **Input fields**: license_plate, vehicle_type, capacity (optional)

**Class**: `VehicleResponse(BaseModel)`
- **Fields**: id, license_plate, vehicle_type, capacity, status, company_id, is_active

---

#### 4. Services Layer (`backend/app/services/`)

##### `auth_svc.py` - Authentication Service

**Hàm**:

###### `hash_password(password: str) -> str`
- **Input**: Plain text password
- **Output**: Hashed password (bcrypt)
- **Mô tả**: Mã hóa mật khẩu trước khi lưu

###### `verify_password(plain_password: str, hashed_password: str) -> bool`
- **Input**: Plain password, hashed password
- **Output**: True nếu khớp, False ngược lại
- **Mô tả**: Xác minh mật khẩu khi login

###### `get_user_by_username(db: Session, username: str) -> Optional[User]`
- **Input**: Database session, username
- **Output**: User object hoặc None
- **Mô tả**: Tìm user theo username

###### `get_user_by_email(db: Session, email: str) -> Optional[User]`
- **Input**: Database session, email
- **Output**: User object hoặc None
- **Mô tả**: Tìm user theo email

###### `get_user_by_id(db: Session, user_id: int) -> Optional[User]`
- **Input**: Database session, user ID
- **Output**: User object hoặc None
- **Mô tả**: Tìm user theo ID

###### `authenticate_user(db: Session, username: str, password: str) -> Optional[User]`
- **Input**: DB session, username, plain password
- **Output**: User object nếu thành công, None nếu thất bại
- **Mô tả**: Xác thực user với username/password
- **Logic**: 
  1. Tìm user theo username
  2. Verify password
  3. Kiểm tra is_active

###### `create_user(db: Session, user_data: UserRegister, role: UserRole = UserRole.CUSTOMER) -> User`
- **Input**: DB session, registration data, optional role
- **Output**: Created User object
- **Mô tả**: Tạo user mới
- **Side effects**: Lưu vào database

###### `generate_tokens(user: User) -> Tuple[str, str]`
- **Input**: User object
- **Output**: Tuple (access_token, refresh_token)
- **Mô tả**: Tạo JWT tokens cho user

###### `update_user_status(db: Session, user_id: int, is_active: bool) -> Optional[User]`
- **Input**: DB session, user ID, new status
- **Output**: Updated User object hoặc None
- **Mô tả**: Cập nhật trạng thái hoạt động của user

---

##### `rescue_svc.py` - Rescue Service Business Logic

**Hằng số**:
- `EARTH_RADIUS_KM = 6371.0`: Bán kính Trái Đất

**Hàm**:

###### `haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float`
- **Input**: Tọa độ 2 điểm (degrees)
- **Output**: Khoảng cách km
- **Mô tả**: Tính khoảng cách great-circle bằng công thức Haversine

###### `find_nearby_companies(db, latitude, longitude, service_id, radius_km=50.0) -> List[Tuple[RescueCompany, float, List[Service]]]`
- **Input**: DB session, user coords, service ID, search radius
- **Output**: List của tuples (Company, distance, services)
- **Mô tả**: Tìm công ty cứu hộ gần vị trí có dịch vụ yêu cầu
- **Logic**:
  1. Lấy tất cả companies active và verified
  2. Tính khoảng cách từ mỗi company đến user
  3. Lọc companies trong bán kính
  4. Kiểm tra có service yêu cầu
  5. Sort theo khoảng cách

###### `create_rescue_request(db, user_id, request_data) -> RescueRequest`
- **Input**: DB session, user ID, request data
- **Output**: Created RescueRequest object
- **Mô tả**: Tạo yêu cầu cứu hộ mới
- **Side effects**: Lưu request vào DB với status="pending"

###### `get_request_by_id(db, request_id) -> Optional[RescueRequest]`
- **Input**: DB session, request ID
- **Output**: RescueRequest hoặc None
- **Mô tả**: Lấy thông tin request theo ID

###### `get_user_requests(db, user_id) -> List[RescueRequest]`
- **Input**: DB session, user ID
- **Output**: List của RescueRequest objects
- **Mô tả**: Lấy tất cả requests của user, sorted by created_at DESC

###### `update_request_status(db, request_id, status, vehicle_id=None, eta_minutes=None) -> Optional[RescueRequest]`
- **Input**: DB session, request ID, new status, optional vehicle ID, optional ETA
- **Output**: Updated RescueRequest hoặc None
- **Mô tả**: Cập nhật trạng thái request
- **Side effects**:
  - Cập nhật status
  - Gán vehicle nếu có
  - Set actual_arrival_time khi status="on_site"
  - Set actual_completion_time khi status="completed"

###### `cancel_request(db, request_id) -> Optional[RescueRequest]`
- **Input**: DB session, request ID
- **Output**: Updated RescueRequest hoặc None
- **Mô tả**: Hủy request (chỉ khi status="pending")
- **Điều kiện**: Chỉ hủy được nếu đang ở trạng thái pending

###### `create_service(db, company_id, service_data) -> Service`
- **Input**: DB session, company ID, service data
- **Output**: Created Service object
- **Mô tả**: Tạo dịch vụ mới cho company

###### `create_vehicle(db, company_id, vehicle_data) -> RescueVehicle`
- **Input**: DB session, company ID, vehicle data
- **Output**: Created RescueVehicle object
- **Mô tả**: Tạo phương tiện mới cho company

###### `get_company_vehicles(db, company_id) -> List[RescueVehicle]`
- **Input**: DB session, company ID
- **Output**: List của RescueVehicle objects
- **Mô tả**: Lấy tất cả vehicles của company

###### `update_vehicle_status(db, vehicle_id, status) -> Optional[RescueVehicle]`
- **Input**: DB session, vehicle ID, new status
- **Output**: Updated RescueVehicle hoặc None
- **Mô tả**: Cập nhật trạng thái vehicle

###### `estimate_price(base_price, distance_km) -> float`
- **Input**: Base price, distance in km
- **Output**: Estimated total price
- **Mô tả**: Tính giá dự kiến = base_price + (distance * 10000 VND/km)

###### `estimate_eta(distance_km, avg_speed_kmh=40.0) -> int`
- **Input**: Distance in km, average speed
- **Output**: Estimated minutes
- **Mô tả**: Tính thời gian dự kiến đến = (distance / speed) * 60

---

#### 5. Routes Layer (`backend/app/routes/`)

##### `auth_routes.py` - Authentication Endpoints

**Router prefix**: `/api/v1/auth`

**Endpoints**:

###### `POST /register`
- **Input**: `UserRegister` schema
- **Output**: `{"code", "message", "data": {"user_id", "username"}}`
- **Mô tả**: Đăng ký user mới
- **Logic**:
  1. Kiểm tra username đã tồn tại
  2. Kiểm tra email đã tồn tại
  3. Tạo user mới với role=CUSTOMER
- **Errors**: 400 nếu username/email đã tồn tại

###### `POST /login`
- **Input**: `UserLogin` schema
- **Output**: `{"code", "message", "data": {"access_token", "refresh_token", "token_type", "expires_in", "user": {...}}}`
- **Mô tả**: Đăng nhập và nhận tokens
- **Logic**:
  1. Authenticate user
  2. Generate tokens
  3. Trả về user info
- **Errors**: 401 nếu thông tin không đúng

###### `GET /me`
- **Input**: None (requires JWT token)
- **Output**: User information
- **Mô tả**: Lấy thông tin user hiện tại
- **Lưu ý**: Chưa implement JWT dependency

---

##### `rescue_routes.py` - Rescue Service Endpoints

**Router prefix**: `/api/v1/rescue`

**Endpoints**:

###### `GET /companies/nearby?latitude=&longitude=&service_id=&radius_km=`
- **Input**: Query params (lat, lng, service_id, radius_km)
- **Output**: List of companies với distance, estimated_price, eta_minutes
- **Mô tả**: Tìm công ty cứu hộ gần vị trí

###### `POST /requests`
- **Input**: `RescueRequestCreate` schema
- **Output**: `{"request_id", "status", "created_at"}`
- **Mô tả**: Tạo yêu cầu cứu hộ mới
- **Lưu ý**: Chưa lấy user_id từ JWT

###### `GET /requests`
- **Input**: None (requires authentication)
- **Output**: List of user's requests
- **Mô tả**: Lấy tất cả requests của user hiện tại

###### `GET /requests/{request_id}`
- **Input**: Path param request_id
- **Output**: Full request details
- **Mô tả**: Lấy chi tiết request
- **Errors**: 404 nếu không tìm thấy

###### `PUT /requests/{request_id}/status`
- **Input**: Path param request_id, Body `RescueRequestUpdate`
- **Output**: Updated request status
- **Mô tả**: Cập nhật trạng thái request
- **Errors**: 404 nếu không tìm thấy

###### `POST /requests/{request_id}/cancel`
- **Input**: Path param request_id
- **Output**: Cancelled request status
- **Mô tả**: Hủy request
- **Errors**: 400 nếu không thể hủy

###### `POST /services?company_id=`
- **Input**: Query param company_id, Body `ServiceCreate`
- **Output**: Created service info
- **Mô tả**: Tạo dịch vụ mới cho company

###### `POST /vehicles?company_id=`
- **Input**: Query param company_id, Body `VehicleCreate`
- **Output**: Created vehicle info
- **Mô tả**: Tạo vehicle mới cho company

###### `GET /companies/{company_id}/vehicles`
- **Input**: Path param company_id
- **Output**: List of company's vehicles
- **Mô tả**: Lấy tất cả vehicles của company

---

#### 6. Utils Layer (`backend/app/utils/`)

##### `jwt_helper.py` - JWT Token Helper

**Hàm** (giả định dựa trên usage):

###### `create_access_token(data: dict) -> str`
- **Input**: Token payload data
- **Output**: JWT access token string
- **Mô tả**: Tạo access token với expiration

###### `create_refresh_token(data: dict) -> str`
- **Input**: Token payload data
- **Output**: JWT refresh token string
- **Mô tả**: Tạo refresh token với expiration dài hơn

---

##### `response.py` - Response Formatting

**Hàm**:

###### `success_response(data=None, message="Success", code=200) -> Dict`
- **Input**: Data, message, HTTP code
- **Output**: `{"code", "message", "data"}`
- **Mô tả**: Tạo standardized success response

###### `error_response(message="Error", code=400, errors=None) -> Dict`
- **Input**: Error message, HTTP code, optional errors dict
- **Output**: `{"code", "message", "data": None, "errors"?}`
- **Mô tả**: Tạo standardized error response

###### `create_json_response(data, message, code) -> JSONResponse`
- **Input**: Same as success_response
- **Output**: FastAPI JSONResponse object
- **Mô tả**: Tạo FastAPI response với format chuẩn

###### `create_error_json_response(message, code) -> JSONResponse`
- **Input**: Error message, HTTP code
- **Output**: FastAPI JSONResponse object
- **Mô tả**: Tạo FastAPI error response

---

#### 7. Main Application (`backend/app/main.py`)

**FastAPI App Configuration**:
- Title: "Roadside Assistance System API"
- Version: "1.0.0"
- CORS: Allow all origins (development)

**Included Routers**:
- `/api/v1/auth` → auth_routes
- `/api/v1/rescue` → rescue_routes

**Startup Event**:
```python
@app.on_event("startup")
async def startup_event():
    init_db()
```

**Endpoints**:
- `GET /`: Welcome message
- `GET /health`: Health check → `{"status": "healthy"}`

---

### FRONTEND

#### 1. Core Layer (`frontend/core/`)

##### `config.py` - Configuration

**Constants**:
- `BACKEND_URL = "http://localhost:8000/api/v1"`
- `APP_TITLE = "Hệ Thống Hỗ Trợ Sự Cố Xe Trên Đường"`
- `APP_VERSION = "1.0.0"`
- `SESSION_TOKEN_KEY = "access_token"`
- `SESSION_USER_KEY = "user_info"`
- `SESSION_ROLE_KEY = "role"`
- `LOGIN_PAGE = "/login"`
- `CUSTOMER_DASHBOARD = "/customer/dashboard"`
- `COMPANY_DASHBOARD = "/company/dashboard"`
- `ADMIN_DASHBOARD = "/admin/dashboard"`

---

##### `auth.py` - Session Management

**Hàm**:

###### `get_current_user() -> Optional[Dict]`
- **Input**: None
- **Output**: User info dict hoặc None
- **Mô tả**: Lấy thông tin user từ session storage

###### `get_access_token() -> Optional[str]`
- **Input**: None
- **Output**: Access token string hoặc None
- **Mô tả**: Lấy token từ session

###### `get_user_role() -> Optional[str]`
- **Input**: None
- **Output**: Role string hoặc None
- **Mô tả**: Lấy role của user từ session

###### `is_authenticated() -> bool`
- **Input**: None
- **Output**: True/False
- **Mô tả**: Kiểm tra user đã đăng nhập chưa

###### `login_user(token, user_info, role) -> None`
- **Input**: Token, user info dict, role string
- **Output**: None
- **Mô tả**: Lưu thông tin auth vào session
- **Side effects**: Update app.storage.user

###### `logout_user() -> None`
- **Input**: None
- **Output**: None
- **Mô tả**: Xóa session và redirect về login page
- **Side effects**: Clear session, navigate to /login

###### `require_auth() -> bool`
- **Input**: None
- **Output**: True nếu authenticated, False ngược lại
- **Mô tả**: Kiểm tra và redirect nếu chưa login

###### `require_role(required_role) -> bool`
- **Input**: Required role string
- **Output**: True nếu có quyền, False ngược lại
- **Mô tả**: Kiểm tra user có role yêu cầu không
- **Logic**: Admin có quyền truy cập tất cả

###### `get_redirect_url_for_role(role) -> str`
- **Input**: Role string
- **Output**: Dashboard URL string
- **Mô tả**: Lấy URL dashboard mặc định cho role

---

#### 2. Services Layer (`frontend/services/`)

##### `api_client.py` - HTTP Client

**Class**: `APIClient`

**Methods**:

###### `__init__(base_url=BACKEND_URL)`
- **Input**: Optional base URL
- **Output**: None
- **Mô tả**: Khởi tạo client với base URL và timeout

###### `_get_headers(token=None) -> Dict[str, str]`
- **Input**: Optional token
- **Output**: Headers dict với Content-Type và Authorization
- **Mô tả**: Tạo headers cho request

###### `get(endpoint, params=None, token=None) -> Dict`
- **Input**: Endpoint, optional params, optional token
- **Output**: Response JSON dict
- **Mô tả**: Thực hiện GET request

###### `post(endpoint, data=None, token=None) -> Dict`
- **Input**: Endpoint, optional data dict, optional token
- **Output**: Response JSON dict
- **Mô tả**: Thực hiện POST request với JSON body

###### `put(endpoint, data=None, token=None) -> Dict`
- **Input**: Endpoint, optional data dict, optional token
- **Output**: Response JSON dict
- **Mô tả**: Thực hiện PUT request

###### `delete(endpoint, token=None) -> Dict`
- **Input**: Endpoint, optional token
- **Output**: Response JSON dict
- **Mô tả**: Thực hiện DELETE request

**Global instance**: `api_client = APIClient()`

---

##### `auth_api.py` - Authentication API Calls

**Hàm**:

###### `login(username, password) -> Dict`
- **Input**: Username, password
- **Output**: Response data dict với access_token, user info
- **Mô tả**: Gọi API login
- **API call**: POST /auth/login

###### `register(username, password, full_name, phone, email) -> Dict`
- **Input**: Registration fields
- **Output**: Response data dict
- **Mô tả**: Gọi API register
- **API call**: POST /auth/register

###### `get_current_user(token) -> Optional[Dict]`
- **Input**: Access token
- **Output**: User info dict hoặc None
- **Mô tả**: Gọi API lấy thông tin user
- **API call**: GET /auth/me

---

##### `rescue_api.py` - Rescue API Calls

**Hàm** (dựa trên README và routes):

###### `find_nearby_companies(latitude, longitude, service_id, radius_km)`
- **Input**: Location coords, service ID, radius
- **Output**: List of companies
- **API call**: GET /rescue/companies/nearby

###### `create_rescue_request(request_data)`
- **Input**: Request data dict
- **Output**: Created request info
- **API call**: POST /rescue/requests

###### `get_my_requests(token)`
- **Input**: Access token
- **Output**: List of requests
- **API call**: GET /rescue/requests

###### `get_request_details(request_id, token)`
- **Input**: Request ID, token
- **Output**: Request details
- **API call**: GET /rescue/requests/{id}

###### `update_request_status(request_id, status_update, token)`
- **Input**: Request ID, status data, token
- **Output**: Updated status
- **API call**: PUT /rescue/requests/{id}/status

###### `cancel_request(request_id, token)`
- **Input**: Request ID, token
- **Output**: Cancellation result
- **API call**: POST /rescue/requests/{id}/cancel

---

#### 3. Components Layer (`frontend/components/`)

##### `navbar.py` - Navigation Component

**Hàm**:

###### `create_navbar(title="Roadside Assistance")`
- **Input**: Optional title string
- **Output**: None (renders UI)
- **Mô tả**: Tạo navigation bar với menu theo role
- **UI Elements**:
  - Header với logo và title
  - User info display
  - Role-based menu items:
    - Customer: Dashboard, Find Rescue, My Requests, Community
    - Company: Dashboard, Queue, Fleet, Profile
    - Admin: Dashboard, Users, Companies, Moderation, Reports
  - Logout button
  - Login/Register buttons (khi chưa login)

###### `create_sidebar(items)`
- **Input**: List of tuples (label, icon, callback)
- **Output**: Drawer object
- **Mô tả**: Tạo sidebar navigation cho dashboard
- **UI Elements**: Left drawer với menu items có icon

---

#### 4. Pages Layer (`frontend/pages/`)

**Cấu trúc thư mục**:
```
pages/
├── auth/           # Login, Register pages
├── customer/       # Customer pages
├── company/        # Company pages
└── admin/          # Admin pages
```

**Các trang cần implement** (theo README):

**Auth Pages**:
- `login.py` → UC001
- `register.py` → UC002

**Customer Pages**:
- `dashboard.py` → Layout + navigation
- `find_rescue.py` → UC003
- `send_request.py` → UC004
- `track.py` → UC005, UC006
- `payment.py` → UC007
- `review.py` → UC008
- `community.py` → UC009

**Company Pages**:
- `dashboard.py` → Layout
- `queue.py` → UC011
- `fleet.py` → UC010
- `profile.py` → UC014

**Admin Pages**:
- `dashboard.py` → Overview
- `users.py` → UC012
- `companies.py` → UC013
- `moderation.py` → UC015
- `reports.py` → UC016

---

## Luồng Dữ Liệu Điển Hình

### Luồng Đăng Ký & Đăng Nhập

```
User → Frontend (/register)
  ↓
[POST /api/v1/auth/register]
  ↓
Backend: auth_routes.register()
  ↓
auth_svc: Check username/email exists
  ↓
auth_svc: create_user() → hash_password()
  ↓
Database: INSERT INTO users
  ↓
Frontend: Redirect to /login
  ↓
User → Frontend (/login)
  ↓
[POST /api/v1/auth/login]
  ↓
Backend: auth_routes.login()
  ↓
auth_svc: authenticate_user() → verify_password()
  ↓
auth_svc: generate_tokens() → jwt_helper
  ↓
Frontend: login_user(token, user_info, role)
  ↓
app.storage.user ← Session data
  ↓
Redirect to role-based dashboard
```

### Luồng Gửi Yêu Cầu Cứu Hộ

```
Customer → Frontend (/customer/find-rescue)
  ↓
rescue_api.find_nearby_companies(lat, lng, service_id)
  ↓
[GET /api/v1/rescue/companies/nearby]
  ↓
Backend: rescue_routes.find_nearby_companies()
  ↓
rescue_svc.find_nearby_companies()
  ↓
  → haversine_distance() tính khoảng cách
  ↓
Frontend: Hiển thị danh sách companies
  ↓
Customer chọn company → /customer/send-request
  ↓
rescue_api.create_rescue_request(data)
  ↓
[POST /api/v1/rescue/requests]
  ↓
Backend: rescue_routes.create_rescue_request()
  ↓
rescue_svc.create_rescue_request()
  ↓
Database: INSERT INTO rescue_requests (status=pending)
  ↓
Frontend: Redirect to /customer/track
  ↓
Real-time polling → Cập nhật trạng thái
```

### Luồng Xử Lý Yêu Cầu (Company)

```
Company Staff → Frontend (/company/queue)
  ↓
rescue_api.get_pending_requests()
  ↓
[GET /api/v1/rescue/requests?status=pending]
  ↓
Backend: Query requests assigned to company
  ↓
Frontend: Hiển thị danh sách requests
  ↓
Staff chọn request → Xem chi tiết
  ↓
Staff nhấn "Tiếp nhận"
  ↓
rescue_api.update_request_status(request_id, {status: "accepted"})
  ↓
[PUT /api/v1/rescue/requests/{id}/status]
  ↓
Backend: rescue_routes.update_request_status()
  ↓
rescue_svc.update_request_status()
  ↓
Database: UPDATE rescue_requests SET status='accepted'
  ↓
Frontend: Cập nhật UI
  ↓
Staff gán vehicle → Update vehicle status
  ↓
Staff cập nhật "Đang di chuyển" → "Đang xử lý" → "Hoàn thành"
```

---

## Security Considerations

### Authentication Flow
1. Password hashing: bcrypt qua `passlib`
2. JWT tokens: Access token (1 hour), Refresh token (7 days)
3. Token stored in NiceGUI session storage
4. Protected routes check token validity

### Authorization
- Role-based access control (RBAC)
- Admin có quyền truy cập tất cả
- Company chỉ xem/edit requests của mình
- Customer chỉ xem requests của mình

### Input Validation
- Pydantic schemas validate all inputs
- Phone number regex validation
- Coordinate range validation (-90 to 90, -180 to 180)
- Status enum validation

---

## Database Schema Summary

### Tables
1. **users** - All system users
2. **rescue_companies** - Rescue service providers
3. **services** - Services offered by companies
4. **rescue_vehicles** - Company vehicles
5. **rescue_requests** - Customer rescue requests
6. **payments** - Payment transactions
7. **reviews** - Customer reviews
8. **community_posts** - Community discussion posts
9. **comments** - Comments on posts

### Key Relationships
- User → Company (1:1)
- Company → Services (1:N)
- Company → Vehicles (1:N)
- User → Requests (1:N)
- Company → Requests (1:N)
- Request → Payment (1:1)
- Request → Review (1:1)

---

## API Endpoints Summary

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/v1/auth/register | Register new user |
| POST | /api/v1/auth/login | Login |
| GET | /api/v1/auth/me | Get current user |

### Rescue Services
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/v1/rescue/companies/nearby | Find nearby companies |
| POST | /api/v1/rescue/requests | Create rescue request |
| GET | /api/v1/rescue/requests | Get user's requests |
| GET | /api/v1/rescue/requests/{id} | Get request details |
| PUT | /api/v1/rescue/requests/{id}/status | Update request status |
| POST | /api/v1/rescue/requests/{id}/cancel | Cancel request |
| POST | /api/v1/rescue/services | Create service |
| POST | /api/v1/rescue/vehicles | Create vehicle |
| GET | /api/v1/rescue/companies/{id}/vehicles | Get company vehicles |

---

## Extension Points

### Chưa Implement (TODO)
1. **JWT Authentication Middleware**: Routes còn placeholder
2. **Real-time Updates**: WebSocket cho tracking
3. **Map Integration**: Google Maps/Mapbox embed
4. **Payment Gateway**: VNPay/MoMo integration
5. **Email/SMS Notifications**: Confirmation alerts
6. **Image Upload**: S3/local storage for images
7. **Admin CRUD APIs**: User/company management
8. **Reporting APIs**: Statistics and exports

### Future Enhancements
1. **PostGIS**: Better geospatial queries
2. **Redis Cache**: Cache nearby companies results
3. **Message Queue**: Async processing for notifications
4. **Rate Limiting**: API throttling
5. **Logging**: Structured logging with ELK stack
6. **Monitoring**: Prometheus + Grafana dashboards

---

**Tài liệu này được cập nhật lần cuối**: Based on current codebase state
