"""
Main NiceGUI application entry point.
Roadside Assistance System - Modernized Frontend
"""
from nicegui import ui, app
import sys
from pathlib import Path

# Ensure frontend directory is in sys.path
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from core.auth import (
    is_authenticated,
    get_user_role,
    get_redirect_url_for_role,
    LOGIN_PAGE,
)
from core.config import APP_TITLE, APP_VERSION, STORAGE_SECRET
from core.theme import apply_global_theme

# Import pages
from pages.auth.login_page import create_login_page
from pages.auth.register_page import create_register_page
from pages.customer.dashboard import create_customer_dashboard
from pages.customer.vehicles import create_vehicles_page
from pages.customer.find_rescue import create_find_rescue_page
from pages.customer.requests import create_requests_page
from pages.customer.track import create_track_page
from pages.customer.community import create_community_page
from pages.company.dashboard import create_company_dashboard
from pages.company.staff import create_staff_page
from pages.company.services_mgmt import create_services_management_page
from pages.company.reviews import create_reviews_page
from pages.admin.dashboard import create_admin_dashboard
from pages.admin.users import create_users_page
from pages.admin.companies import create_companies_page
from pages.admin.reports import create_reports_page
from pages.admin.moderation import create_moderation_page
from pages.admin.profile import create_admin_profile_page

# --- Helper for Home Page ---
@ui.page('/')
async def home_page():
    """Landing page."""
    if is_authenticated():
        ui.navigate.to(get_redirect_url_for_role(get_user_role()))
        return

    apply_global_theme()
    
    # Simple Hero Landing
    with ui.column().classes('w-full min-h-screen items-center justify-center bg-gradient-to-br from-[#fdfbff] to-[#e6f0ff] gap-8 p-8'):
        ui.icon('local_taxi', size='6rem').classes('text-primary animate-bounce')
        ui.label('Rescue24').classes('text-6xl font-bold text-primary font-outfit')
        ui.label('Hệ thống cứu hộ xe thông minh 24/7').classes('text-xl text-on-surface-variant text-center max-w-lg')
        
        with ui.row().classes('gap-4 mt-4'):
            ui.button('ĐĂNG NHẬP', on_click=lambda: ui.navigate.to(LOGIN_PAGE)).classes('px-10 py-4 rounded-xl bg-primary text-white font-bold shadow-lg')
            ui.button('ĐĂNG KÝ', on_click=lambda: ui.navigate.to('/register')).props('outline').classes('px-10 py-4 rounded-xl border-2 border-primary text-primary font-bold')

def setup_app():
    """Configure and start the app."""
    # Apply theme globally for non-page-decorated content if needed
    # but @ui.page handles its own head typically.
    
    # Register all pages
    create_login_page()
    create_register_page()
    create_customer_dashboard()
    create_vehicles_page()
    create_find_rescue_page()
    create_requests_page()
    create_track_page()
    create_community_page()
    create_company_dashboard()
    create_staff_page()
    create_services_management_page()
    create_reviews_page()
    
    # Admin Pages
    create_admin_dashboard()
    create_users_page()
    create_companies_page()
    create_reports_page()
    create_moderation_page()
    create_admin_profile_page()
    
    # Note: Other sub-pages (vehicles, fleet, etc.) should be registered here as well
    # for a complete app.
    
    # Mount static files
    static_dir = Path(__file__).parent / "static"
    if not static_dir.exists():
        static_dir.mkdir(parents=True, exist_ok=True)
    app.add_static_files('/static', str(static_dir))
    
    # Run UI
    ui.run(
        title=APP_TITLE,
        storage_secret=STORAGE_SECRET,
        reload=True,
        port=8080,
    )

if __name__ in {"__main__", "__mp_main__"}:
    setup_app()
