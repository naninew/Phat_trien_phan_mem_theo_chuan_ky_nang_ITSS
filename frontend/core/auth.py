"""
Authentication & session management for NiceGUI frontend.
"""
from nicegui import app, ui
from typing import Optional, Dict, Any

from core.config import (
    SESSION_TOKEN_KEY,
    SESSION_USER_KEY,
    SESSION_ROLE_KEY,
    LOGIN_PAGE,
    ADMIN_LOGIN_PAGE,
    CUSTOMER_DASHBOARD,
    COMPANY_DASHBOARD,
    ADMIN_DASHBOARD,
)


# ──────────────────────────────────────────────────────────────────────────────
# Session helpers
# ──────────────────────────────────────────────────────────────────────────────
def get_access_token() -> Optional[str]:
    return app.storage.user.get(SESSION_TOKEN_KEY)


def get_current_user() -> Optional[Dict[str, Any]]:
    return app.storage.user.get(SESSION_USER_KEY)


def get_user_role() -> Optional[str]:
    return app.storage.user.get(SESSION_ROLE_KEY)


def get_user_name() -> str:
    user = get_current_user()
    if user:
        return user.get("full_name") or user.get("username") or "User"
    return "User"


def is_authenticated() -> bool:
    return get_access_token() is not None


def login_user(token: str, user_info: Dict[str, Any], role: str) -> None:
    """Lưu thông tin đăng nhập vào session."""
    app.storage.user[SESSION_TOKEN_KEY] = token
    app.storage.user[SESSION_USER_KEY]  = user_info
    app.storage.user[SESSION_ROLE_KEY]  = role


def logout_user() -> None:
    """Xóa session và chuyển về trang đăng nhập."""
    app.storage.user.clear()
    ui.navigate.to(LOGIN_PAGE)


# ──────────────────────────────────────────────────────────────────────────────
# Route guards
# ──────────────────────────────────────────────────────────────────────────────
def require_auth() -> bool:
    """Gọi ở đầu mỗi page cần đăng nhập (customer/company). Trả về False nếu chưa auth."""
    if not is_authenticated():
        ui.navigate.to(LOGIN_PAGE)
        return False
    return True


def require_admin_auth() -> bool:
    """
    Guard dành riêng cho các trang /admin/*.  
    Nếu chưa đăng nhập → redirect về /admin-panel/login.  
    Nếu đã đăng nhập nhưng không phải admin → redirect về dashboard của role hiện tại.
    """
    if not is_authenticated():
        ui.navigate.to(ADMIN_LOGIN_PAGE)
        return False
    current_role = get_user_role()
    if current_role != "admin":
        ui.notify("Bạn không có quyền truy cập trang quản trị", type="negative")
        ui.navigate.to(get_redirect_url_for_role(current_role))
        return False
    return True


def require_role(role: str) -> bool:
    """
    Kiểm tra role. Nếu không hợp lệ, redirect về dashboard của role hiện tại.
    Admin luôn được phép truy cập tất cả.
    Nếu chưa đăng nhập và role='admin' → redirect về /admin-panel/login.
    """
    if not is_authenticated():
        # Admin pages → trang login riêng của admin
        if role == "admin":
            ui.navigate.to(ADMIN_LOGIN_PAGE)
        else:
            ui.navigate.to(LOGIN_PAGE)
        return False

    current_role = get_user_role()
    if current_role == "admin":
        return True          # Admin có thể vào mọi trang

    if current_role != role:
        ui.notify("Bạn không có quyền truy cập trang này", type="negative")
        # Redirect về đúng dashboard của role hiện tại (không gây loop)
        ui.navigate.to(get_redirect_url_for_role(current_role))
        return False

    return True


def get_redirect_url_for_role(role: Optional[str]) -> str:
    """Trả về URL dashboard mặc định theo role."""
    mapping = {
        "customer":      CUSTOMER_DASHBOARD,
        "company_staff": COMPANY_DASHBOARD,
        "admin":         ADMIN_DASHBOARD,
    }
    return mapping.get(role or "", LOGIN_PAGE)
