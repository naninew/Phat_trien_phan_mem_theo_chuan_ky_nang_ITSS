"""
Frontend core configuration.
Tất cả config đọc từ environment variable – dễ chuyển môi trường.
"""
import os

# ── Backend API ─────────────────────────────────────────────────────────────
BACKEND_URL: str = os.getenv("BACKEND_URL", "http://localhost:8000/api/v1")

# ── App info ─────────────────────────────────────────────────────────────────
APP_TITLE: str = "Hệ Thống Hỗ Trợ Sự Cố Xe Trên Đường"
APP_VERSION: str = "2.0.0"

# ── Storage keys ─────────────────────────────────────────────────────────────
SESSION_TOKEN_KEY = "access_token"
SESSION_USER_KEY  = "user_info"
SESSION_ROLE_KEY  = "user_role"

# ── Routes ───────────────────────────────────────────────────────────────────
LOGIN_PAGE          = "/login"
ADMIN_LOGIN_PAGE    = "/admin-panel/login"   # UC-47: trang đăng nhập riêng cho Admin
REGISTER_PAGE       = "/register"
CUSTOMER_DASHBOARD  = "/customer/dashboard"
COMPANY_DASHBOARD   = "/company/dashboard"
ADMIN_DASHBOARD     = "/admin/dashboard"

# ── NiceGUI storage secret (override in production via env) ──────────────────
STORAGE_SECRET: str = os.getenv("STORAGE_SECRET", "rescue-system-secret-2024-change-me")

