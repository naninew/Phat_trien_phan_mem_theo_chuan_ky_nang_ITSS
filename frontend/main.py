"""
Main NiceGUI application entry point.
Roadside Assistance System - Modernized Frontend (Rescue24)
"""
from fastapi.staticfiles import StaticFiles
from nicegui import ui, app
import os
import sys
from pathlib import Path

# ── CẤU HÌNH HỆ THỐNG ĐƯỜNG DẪN ─────────────────────────────────────────────
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))
BASE_DIR = Path(__file__).parent.parent
uploads_dir = BASE_DIR / "backend" / "app" / "uploads" / "images"
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount(
    "/uploads/images",
    StaticFiles(directory=str(uploads_dir)),
    name="uploads_images"
)

# ── IMPORT MODULES ──────────────────────────────────────────────────────────
from core.auth import (
    is_authenticated,
    get_user_role,
    get_redirect_url_for_role,
    LOGIN_PAGE,
)
from core.config import APP_TITLE, APP_VERSION, STORAGE_SECRET

# Import đầy đủ toàn bộ các trang chức năng từ cả 2 phiên bản
from pages.auth.login_page import create_login_page, create_admin_login_page
from pages.auth.register_page import create_register_page
from pages.customer.dashboard import create_customer_dashboard
from pages.customer.vehicles import create_vehicles_page
from pages.customer.find_rescue import create_find_rescue_page
from pages.customer.requests import create_requests_page
from pages.customer.track import create_track_page
from pages.customer.community import create_community_page
from pages.customer.review import create_review_page
from pages.company.dashboard import create_company_dashboard
from pages.company.queue import create_queue_page
from pages.company.staff import create_staff_page
from pages.company.fleet import create_fleet_page
from pages.company.services_mgmt import create_services_management_page
from pages.company.reviews import create_reviews_page
from pages.company.profile import create_profile_page
from pages.admin.dashboard import create_admin_dashboard
from pages.admin.users import create_users_page
from pages.admin.user_detail import create_user_detail_page
from pages.admin.companies import create_companies_page
from pages.admin.reports import create_reports_page
from pages.admin.moderation import create_moderation_page
from pages.admin.profile import create_admin_profile_page
from pages.shared.profile_page import create_profile_page


def apply_global_theme():
    """Apply premium Material Design 3 look and feel globally with fonts, icons and custom utilities."""
    # ĐÃ SỬA: Thêm đường link Material Icons của Google Fonts để kích hoạt ui.icon hoạt động
    ui.add_head_html("""
    <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            /* Material 3 inspired Blue Palette */
            --primary: #005fb0;
            --on-primary: #f0f4f8; 
            --primary-container: #d6e3ff;
            --on-primary-container: #001b3e;
            
            --secondary: #565e71;
            --on-secondary: #f0f4f8;
            --secondary-container: #dae2f9;
            --on-secondary-container: #131c2b;
            
            --surface: #fdfbff;
            --on-surface: #1a1b1f;
            --surface-variant: #e0e2ec;
            --on-surface-variant: #44474e;
            
            --outline: #74777f;
            --error: #ba1a1a;
            
            --glass: rgba(253, 251, 255, 0.8);
            --glass-border: rgba(0, 95, 176, 0.2);
        }
        
        body {
            background-color: var(--surface);
            color: var(--on-surface);
            font-family: 'Inter', sans-serif;
            margin: 0;
            padding: 0;
        }
        
        h1, h2, h3, .font-outfit {
            font-family: 'Outfit', sans-serif;
            font-weight: 700;
        }
        
        .nicegui-content {
            padding: 0 !important;
        }
        
        .m3-card {
            background-color: #fdfbff;
            border-radius: 24px;
            border: 1px solid var(--surface-variant);
            box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
            transition: all 0.3s ease;
        }
        
        .glass-panel {
            background: var(--glass);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid var(--glass-border);
        }
        
        .btn-primary {
            background-color: var(--primary) !important;
            color: var(--on-primary) !important;
            border-radius: 12px !important;
            text-transform: none !important;
            font-weight: 600 !important;
        }
        
        .text-contrast-high {
            color: var(--on-surface) !important;
        }
        
        .text-contrast-medium {
            color: var(--on-surface-variant) !important;
        }
        
        .m3-card:hover {
            background-color: #eff6ff;
            box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
            transform: translateY(-2px);
        }
    </style>
    """)


@ui.page('/')
async def home_page():
    """Premium Material Design 3 Landing Page with responsive layouts."""
    if is_authenticated():
        ui.navigate.to(get_redirect_url_for_role(get_user_role()))
        return

    apply_global_theme()
    
    # ── Header / Navbar (Glassmorphism) ──────────────────────────────────────
    with ui.header().classes('glass-panel px-6 py-4 flex items-center justify-between fixed top-0 w-full z-50'):
        with ui.row().classes('items-center gap-2'):
            ui.icon('local_taxi', size='2.5rem').classes('text-primary')
            ui.label(APP_TITLE).classes('text-2xl font-bold text-primary font-outfit')
        
        with ui.row().classes('gap-4'):
            ui.button('Đăng Nhập', on_click=lambda: ui.navigate.to(LOGIN_PAGE)).props('flat').classes('text-primary font-semibold')
            ui.button('Tham Gia Ngay', on_click=lambda: ui.navigate.to('/register')).classes('btn-primary px-6')

    # ── Hero Section ─────────────────────────────────────────────────────────
# ── Hero Section (Đã fix lỗi ẩn layout trên màn hình nhỏ) ─────────────────
    with ui.row().classes('w-full min-h-screen items-center px-8 md:px-24 pt-20 bg-gradient-to-br from-[#fdfbff] to-[#e6f0ff]'):
        
        # Cột bên trái: Chiếm 58% màn hình (w-7/12)
        with ui.column().classes('w-full lg:w-7/12 gap-8 max-w-2xl'):
            with ui.element('div').classes('inline-flex items-center gap-2 px-4 py-2 bg-primary/10 rounded-full'):
                ui.icon('check_circle', size='1.2rem').classes('text-primary')
                ui.label('Dịch vụ cứu hộ hàng đầu Việt Nam').classes('text-primary font-bold text-xs uppercase tracking-widest')
            
            ui.label('An Tâm Trên Mọi\nNẻo Đường Cùng\nRescue24').classes('text-5xl md:text-7xl font-bold text-on-surface leading-tight font-outfit whitespace-pre-line')
            ui.label('Hệ thống kết nối cứu hộ xe thông minh, hỗ trợ 24/7 với đội ngũ chuyên nghiệp. Tiếp cận hiện trường chỉ sau 15 phút.').classes('text-lg text-on-surface-variant max-w-lg leading-relaxed')
            
            with ui.row().classes('gap-4 mt-4'):
                ui.button('Yêu Cầu Cứu Hộ', on_click=lambda: ui.navigate.to(LOGIN_PAGE)).classes('btn-primary px-10 py-6 text-lg shadow-xl hover:shadow-primary/30')
                ui.button('Xem Bảng Giá', on_click=lambda: ui.notify('Tính năng đang cập nhật')).props('outline').classes('px-10 py-6 text-lg border-2 border-primary text-primary font-bold rounded-xl')

        # Cột bên phải: Chiếm 41% màn hình (w-5/12) - ÉP BUỘC HIỂN THỊ KHÔNG ẨN (Bỏ hidden)
        with ui.column().classes('w-full lg:w-5/12 items-center justify-center relative flex'):
            with ui.element('div').classes('rounded-full flex items-center justify-center shadow-2xl animate-bounce') \
                    .style('width: 260px; height: 260px; background-color: #fffbeb; border: 2px solid #fde68a; box-shadow: 0 20px 25px -5px rgba(245, 158, 11, 0.3);'):
                
                # Ép font-size và color trực tiếp để hiển thị icon local_taxi
                ui.icon('local_taxi').style('font-size: 130px; color: #f59e0b; display: block;')
    with ui.column().classes('w-full py-24 bg-white px-8 md:px-24 items-center hover:bg-blue-100/40 transition-colors'):
        ui.label('Dịch Vụ Của Chúng Tôi').classes('text-primary font-bold text-sm uppercase tracking-[0.2em] mb-4')
        ui.label('Giải Pháp Cứu Hộ Toàn Diện').classes('text-4xl font-bold text-on-surface mb-16 font-outfit')
        
        with ui.row().classes('w-full gap-8 justify-center flex-wrap'):
            _service_feature_card('Cứu Hộ Kỹ Thuật', 'build', 'Sửa chữa hỏng hóc nhẹ, kích bình ắc-quy, thay lốp dự phòng tại chỗ.')
            _service_feature_card('Cẩu Kéo Xe', 'local_shipping', 'Vận chuyển xe về xưởng sửa chữa bằng xe chuyên dụng hiện đại nhất.')
            _service_feature_card('Tiếp Nhiên Liệu', 'local_gas_station', 'Cung cấp xăng, dầu khẩn cấp khi bạn gặp sự cố hết nhiên liệu giữa đường.')
            _service_feature_card('Tư Vấn Sự Cố', 'support_agent', 'Đội ngũ chuyên gia hỗ trợ qua điện thoại miễn phí 24/7 cho mọi tình huống.')

    # ── Stats Section ────────────────────────────────────────────────────────
    with ui.row().classes('w-full py-20 bg-primary justify-around text-[#f0f4f8]'):
        _stat_item('15+', 'Phút chờ trung bình')
        _stat_item('1000+', 'Đối tác cứu hộ')
        _stat_item('50k+', 'Khách hàng tin dùng')
        _stat_item('24/7', 'Hỗ trợ khẩn cấp')

    # ── Footer ───────────────────────────────────────────────────────────────
    with ui.column().classes('w-full py-12 bg-on-surface-variant/5 px-8 md:px-24 border-t border-surface-variant'):
        with ui.row().classes('w-full justify-between items-start mb-8'):
            with ui.column().classes('gap-4'):
                ui.label(APP_TITLE).classes('text-2xl font-bold text-primary font-outfit')
                ui.label('Hệ thống cứu hộ xe thông minh thế hệ mới.').classes('text-sm text-on-surface-variant')
            
            with ui.row().classes('gap-12'):
                with ui.column().classes('gap-2'):
                    ui.label('Về chúng tôi').classes('font-bold text-on-surface mb-2')
                    ui.label('Giới thiệu').classes('text-sm text-on-surface-variant hover:text-primary cursor-pointer')
                    ui.label('Đối tác').classes('text-sm text-on-surface-variant hover:text-primary cursor-pointer')
                with ui.column().classes('gap-2'):
                    ui.label('Pháp lý').classes('font-bold text-on-surface mb-2')
                    ui.label('Điều khoản').classes('text-sm text-on-surface-variant hover:text-primary cursor-pointer')
                    ui.label('Bảo mật').classes('text-sm text-on-surface-variant hover:text-primary cursor-pointer')

        ui.separator()
        ui.label(f'© 2026 {APP_TITLE} (Version {APP_VERSION}). All rights reserved.').classes('w-full text-center mt-8 text-xs text-on-surface-variant')


def _service_feature_card(title, icon, desc):
    """Component card dịch vụ với style hover nền xanh tinh tế."""
    with ui.column().classes('''
        m3-card
        p-8 w-72 h-80 gap-6
        border-none
        hover:bg-blue-50
        hover:-translate-y-2
        hover:shadow-xl
        group 
        transition-all duration-300
    '''):
        with ui.element('div').classes('''
            w-16 h-16 rounded-2xl
            bg-primary/10
            flex items-center justify-center
            group-hover:bg-primary/20
            transition-colors duration-300
        '''):
            ui.icon(icon, size='2.5rem').classes('text-primary')

        ui.label(title).classes('''
            text-xl font-bold
            text-on-surface
            group-hover:text-primary
            font-outfit
            transition-colors duration-300
        ''')

        ui.label(desc).classes('''
            text-on-surface-variant
            group-hover:text-on-surface
            text-sm leading-relaxed
            transition-colors duration-300
        ''')


def _stat_item(value, label):
    """Component hiển thị số liệu thống kê."""
    with ui.column().classes('items-center'):
        ui.label(value).classes('text-5xl font-bold font-outfit mb-2')
        ui.label(label).classes('text-[#f0f4f8]/70 font-medium uppercase tracking-widest text-xs')


def setup_app():
    """Khởi tạo cấu trúc định tuyến và kích hoạt ứng dụng NiceGUI."""
    # 1. Auth pages
    create_login_page()
    create_admin_login_page()   # UC-47: /admin-panel/login
    create_register_page()
    
    # 2. Customer pages
    create_customer_dashboard()
    create_vehicles_page()
    create_find_rescue_page()
    create_requests_page()
    create_track_page()
    create_community_page()
    create_review_page()
    
    # 3. Company pages
    create_company_dashboard()
    create_queue_page()
    create_staff_page()
    create_fleet_page()
    create_services_management_page()
    create_reviews_page()
    create_profile_page()
    
    # 4. Admin pages
    create_admin_dashboard()
    create_users_page()
    create_user_detail_page()
    create_companies_page()
    create_reports_page()
    create_moderation_page()
    create_admin_profile_page()
    
    # 5. Shared pages
    create_profile_page()
    
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