"""
Frontend core configuration.
"""

# Backend API URL
BACKEND_URL = "http://localhost:8000/api/v1"

# Application settings
APP_TITLE = "Hệ Thống Hỗ Trợ Sự Cố Xe Trên Đường"
APP_VERSION = "1.0.0"

# Session storage keys
SESSION_TOKEN_KEY = "access_token"
SESSION_USER_KEY = "user_info"
SESSION_ROLE_KEY = "role"

# Default pages
LOGIN_PAGE = "/login"
CUSTOMER_DASHBOARD = "/customer/dashboard"
COMPANY_DASHBOARD = "/company/dashboard"
ADMIN_DASHBOARD = "/admin/dashboard"
