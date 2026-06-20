"""Admin portal pages — đăng ký tất cả route /admin/*."""
from .dashboard import create_admin_dashboard
from .users import create_users_page
from .user_detail import create_user_detail_page
from .companies import create_companies_page
from .company_detail import create_company_detail_page
from .reports import create_reports_page
from .moderation import create_moderation_page
from .profile import create_admin_profile_page


def register_admin_pages() -> None:
    """Đăng ký toàn bộ trang quản trị Admin (NiceGUI routes)."""
    create_admin_dashboard()
    create_users_page()
    create_user_detail_page()       # /admin/users/{user_id}
    create_companies_page()
    create_company_detail_page()    # /admin/companies/{company_id}
    create_reports_page()
    create_moderation_page()
    create_admin_profile_page()


__all__ = [
    "register_admin_pages",
    "create_admin_dashboard",
    "create_users_page",
    "create_user_detail_page",
    "create_companies_page",
    "create_company_detail_page",
    "create_reports_page",
    "create_moderation_page",
    "create_admin_profile_page",
]
