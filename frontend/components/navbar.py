"""
Navigation bar component with role-based menu.
"""
from nicegui import ui
from typing import Optional

from ..core.auth import (
    is_authenticated,
    get_current_user,
    get_user_role,
    logout_user,
    LOGIN_PAGE,
    CUSTOMER_DASHBOARD,
    COMPANY_DASHBOARD,
    ADMIN_DASHBOARD,
)


def create_navbar(title: str = "Roadside Assistance"):
    """
    Create a navigation bar with role-based menu items.
    
    Args:
        title: Application title to display
    """
    with ui.header().classes('replaced-by-classes').props('elevated'):
        with ui.row().classes('w-full items-center justify-between px-4'):
            # Logo and title
            with ui.row().classes('items-center gap-2'):
                ui.icon('construction', size='md')
                ui.label(title).classes('text-lg font-bold')
            
            # Navigation menu
            if is_authenticated():
                user = get_current_user()
                role = get_user_role()
                
                with ui.row().classes('items-center gap-4'):
                    # User info
                    if user:
                        ui.label(f"👤 {user.get('full_name', 'User')}").classes('text-sm')
                    
                    # Role-based menu items
                    with ui.menu() as menu:
                        if role == 'customer':
                            ui.menu_item('Dashboard', lambda: ui.navigate.to(CUSTOMER_DASHBOARD))
                            ui.menu_item('Find Rescue', lambda: ui.navigate.to('/customer/find-rescue'))
                            ui.menu_item('My Requests', lambda: ui.navigate.to('/customer/requests'))
                            ui.menu_item('Community', lambda: ui.navigate.to('/customer/community'))
                        elif role == 'company_staff':
                            ui.menu_item('Dashboard', lambda: ui.navigate.to(COMPANY_DASHBOARD))
                            ui.menu_item('Queue', lambda: ui.navigate.to('/company/queue'))
                            ui.menu_item('Fleet', lambda: ui.navigate.to('/company/fleet'))
                            ui.menu_item('Profile', lambda: ui.navigate.to('/company/profile'))
                        elif role == 'admin':
                            ui.menu_item('Dashboard', lambda: ui.navigate.to(ADMIN_DASHBOARD))
                            ui.menu_item('Users', lambda: ui.navigate.to('/admin/users'))
                            ui.menu_item('Companies', lambda: ui.navigate.to('/admin/companies'))
                            ui.menu_item('Moderation', lambda: ui.navigate.to('/admin/moderation'))
                            ui.menu_item('Reports', lambda: ui.navigate.to('/admin/reports'))
                        
                        ui.separator()
                        ui.menu_item('Logout', logout_user)
                    
                    ui.button(icon='menu', on_click=menu.open).props('flat round dense')
            else:
                # Not authenticated - show login/register
                with ui.row().classes('gap-2'):
                    ui.button('Login', on_click=lambda: ui.navigate.to(LOGIN_PAGE)).props('outline')
                    ui.button('Register', on_click=lambda: ui.navigate.to('/register'))


def create_sidebar(items: list):
    """
    Create a sidebar navigation for dashboard pages.
    
    Args:
        items: List of tuples (label, icon, callback)
    """
    with ui.left_drawer().classes('bg-grey-1') as drawer:
        ui.label('Menu').classes('text-lg font-bold m-4')
        
        for label, icon, callback in items:
            ui.item(label, on_click=callback).props(f'clickable v-ripple')
            with ui.item_section().before():
                ui.icon(icon)
    
    return drawer
