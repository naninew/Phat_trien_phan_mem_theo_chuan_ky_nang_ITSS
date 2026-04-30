"""
Main NiceGUI application entry point.
Roadside Assistance System - Frontend
"""
from nicegui import ui, app
from typing import Optional

# Import core modules
from .core.auth import (
    is_authenticated,
    get_current_user,
    get_user_role,
    logout_user,
    LOGIN_PAGE,
    CUSTOMER_DASHBOARD,
    COMPANY_DASHBOARD,
    ADMIN_DASHBOARD,
)
from .core.config import APP_TITLE, APP_VERSION

# Import pages
from .pages.auth.login_page import create_login_page
from .pages.auth.register_page import create_register_page
from .pages.customer.dashboard import create_customer_dashboard
from .pages.customer.find_rescue import create_find_rescue_page
from .pages.customer.requests import create_requests_page
from .pages.company.dashboard import create_company_dashboard
from .pages.company.queue import create_queue_page
from .pages.company.fleet import create_fleet_page
from .pages.admin.dashboard import create_admin_dashboard
from .pages.admin.users import create_users_page
from .pages.admin.companies import create_companies_page


def create_home_page():
    """Create home/landing page."""
    
    with ui.column().classes('w-full items-center justify-center min-h-screen p-8'):
        ui.icon('construction', size='xl').classes('text-primary')
        ui.label(APP_TITLE).classes('text-4xl font-bold mt-4')
        ui.label(f'Version {APP_VERSION}').classes('text-gray-500 mt-2')
        
        ui.markdown('''
        ## Welcome to Roadside Assistance System
        
        Our platform connects drivers in need with professional rescue services.
        
        ### Services Include:
        - 🚗 Tire change & repair
        - 🔋 Battery jump-start
        - ⛽ Fuel delivery
        - 🏗️ Towing & recovery
        - 🔧 Emergency repairs
        
        ''').classes('max-w-2xl text-center mt-8')
        
        with ui.row().classes('gap-4 mt-8'):
            if is_authenticated():
                role = get_user_role()
                if role == 'customer':
                    ui.button('Go to Dashboard', on_click=lambda: ui.navigate.to(CUSTOMER_DASHBOARD))
                elif role == 'company_staff':
                    ui.button('Go to Dashboard', on_click=lambda: ui.navigate.to(COMPANY_DASHBOARD))
                elif role == 'admin':
                    ui.button('Go to Dashboard', on_click=lambda: ui.navigate.to(ADMIN_DASHBOARD))
                ui.button('Logout', on_click=logout_user).props('outline')
            else:
                ui.button('Login', on_click=lambda: ui.navigate.to(LOGIN_PAGE))
                ui.button('Register', on_click=lambda: ui.navigate.to('/register')).props('outline')


def setup_routes():
    """Setup all NiceGUI routes."""
    
    # Home page
    @ui.page('/')
    def home():
        create_home_page()
    
    # Auth pages
    create_login_page()
    create_register_page()
    
    # Customer pages
    create_customer_dashboard()
    create_find_rescue_page()
    create_requests_page()
    
    # Company pages
    create_company_dashboard()
    create_queue_page()
    create_fleet_page()
    
    # Admin pages
    create_admin_dashboard()
    create_users_page()
    create_companies_page()
    
    # Add more pages as needed


def run_frontend(host: str = '0.0.0.0', port: int = 8080, reload: bool = False):
    """
    Run the NiceGUI frontend application.
    
    Args:
        host: Host address to bind
        port: Port number
        reload: Enable auto-reload for development
    """
    setup_routes()
    ui.run(
        host=host,
        port=port,
        reload=reload,
        title=APP_TITLE,
        storage_secret='roadside-assistance-secret-key-change-in-production',
    )


if __name__ in {"__main__", "__mp_main__"}:
    run_frontend()
