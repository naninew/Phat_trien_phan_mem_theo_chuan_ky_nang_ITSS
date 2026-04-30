"""
Modern Responsive Navigation Bar Component
Supports desktop horizontal menu and mobile hamburger drawer
"""
from nicegui import ui
from typing import Optional, List, Dict, Callable

# Menu items configuration by role
MENU_ITEMS = {
    'customer': [
        {'label': 'Dashboard', 'icon': '🏠', 'route': '/customer/dashboard'},
        {'label': 'Find Rescue', 'icon': '🆘', 'route': '/customer/find-rescue'},
        {'label': 'My Requests', 'icon': '📋', 'route': '/customer/requests'},
        {'label': 'Profile', 'icon': '👤', 'route': '/customer/profile'},
    ],
    'company_staff': [
        {'label': 'Dashboard', 'icon': '🏠', 'route': '/company/dashboard'},
        {'label': 'Queue Management', 'icon': '📊', 'route': '/company/queue'},
        {'label': 'Fleet Tracking', 'icon': '🚗', 'route': '/company/fleet'},
        {'label': 'Profile', 'icon': '👤', 'route': '/company/profile'},
    ],
    'admin': [
        {'label': 'Dashboard', 'icon': '🏠', 'route': '/admin/dashboard'},
        {'label': 'User Management', 'icon': '👥', 'route': '/admin/users'},
        {'label': 'Company Management', 'icon': '🏢', 'route': '/admin/companies'},
        {'label': 'System Settings', 'icon': '⚙️', 'route': '/admin/settings'},
    ],
}

def create_navbar(
    user_role: Optional[str] = None,
    user_name: Optional[str] = None,
    on_logout: Optional[Callable] = None,
    on_menu_click: Optional[Callable] = None,
    title: str = "RescueConnect"
):
    """
    Create a modern responsive navigation bar
    
    Args:
        user_role: Current user role (customer, company_staff, admin)
        user_name: Display name of logged-in user
        on_logout: Callback function for logout action
        on_menu_click: Callback function when menu item is clicked
        title: Application title
    """
    
    # Get menu items for current role
    items = MENU_ITEMS.get(user_role, []) if user_role else []
    
    # Create header
    with ui.header().classes('bg-white border-b border-gray-200 sticky top-0 z-50 shadow-sm') as header:
        with ui.element('div').classes('container mx-auto px-4'):
            with ui.element('div').classes('flex items-center justify-between h-16'):
                
                # Left side: Logo and Title
                with ui.element('div').classes('flex items-center gap-3'):
                    ui.html('<span class="text-3xl">🚑</span>')
                    ui.label(title).classes('text-xl font-bold text-indigo-600')
                
                # Center: Desktop Navigation (hidden on mobile)
                with ui.element('div').classes('hidden lg:flex items-center space-x-1'):
                    for item in items:
                        with ui.button(
                            on_click=lambda i=item: (
                                ui.navigate.to(i['route']) if not on_menu_click else on_menu_click(i)
                            )
                        ).classes('''
                            px-4 py-2 rounded-lg text-sm font-medium
                            text-gray-600 hover:text-indigo-600 hover:bg-indigo-50
                            transition-all duration-200
                        '''):
                            ui.html(f'<span class="mr-2">{i["icon"]}</span>')
                            ui.label(i['label'])
                
                # Right side: User info and actions
                with ui.element('div').classes('flex items-center gap-3'):
                    # User info (desktop only)
                    if user_name and user_role:
                        with ui.element('div').classes('hidden md:flex items-center gap-2 px-3 py-1.5 bg-gray-50 rounded-lg'):
                            ui.html('<span class="text-lg">👤</span>')
                            with ui.element('div'):
                                ui.label(user_name).classes('text-sm font-medium text-gray-900')
                                ui.label(user_role.replace('_', ' ').title()).classes('text-xs text-gray-500')
                    
                    # Logout button
                    if on_logout:
                        with ui.button(on_click=on_logout).classes('''
                            px-3 py-1.5 rounded-lg text-sm font-medium
                            bg-gray-100 hover:bg-gray-200 text-gray-700
                            transition-all duration-200 flex items-center gap-2
                        '''):
                            ui.html('<span>🚪</span>')
                            ui.label('Logout')
                    
                    # Mobile menu button (hamburger)
                    with ui.button(icon='menu').classes('lg:hidden nicegui-button p-2') as mobile_btn:
                        pass
                    
                    # Mobile drawer
                    with ui.drawer().props('side=right overlay') as drawer:
                        with ui.element('div').classes('p-4 w-64'):
                            # Drawer header
                            with ui.element('div').classes('flex items-center justify-between mb-6'):
                                ui.label('Menu').classes('text-lg font-semibold')
                                with ui.button(icon='close').props('flat round dense'):
                                    drawer.props('model-value=false')
                            
                            # User info in drawer
                            if user_name:
                                with ui.element('div').classes('mb-4 p-3 bg-gray-50 rounded-lg'):
                                    with ui.element('div').classes('flex items-center gap-3'):
                                        ui.html('<span class="text-2xl">👤</span>')
                                        with ui.element('div'):
                                            ui.label(user_name).classes('font-semibold')
                                            ui.label(user_role.replace('_', ' ').title() if user_role else 'Guest').classes('text-sm text-gray-500')
                                
                                ui.separator().classes('my-4')
                            
                            # Mobile menu items
                            for item in items:
                                with ui.button(
                                    on_click=lambda i=item: (
                                        ui.navigate.to(i['route']),
                                        drawer.props('model-value=false')
                                    ) if not on_menu_click else on_menu_click(i)
                                ).classes('''
                                    w-full justify-start px-4 py-3 mb-2 rounded-lg
                                    text-gray-700 hover:bg-indigo-50 hover:text-indigo-600
                                    transition-all duration-200
                                '''):
                                    ui.html(f'<span class="mr-3 text-lg">{i["icon"]}</span>')
                                    ui.label(i['label'])
                            
                            ui.separator().classes('my-4')
                            
                            # Logout in drawer
                            if on_logout:
                                with ui.button(on_click=lambda: (on_logout(), drawer.props('model-value=false'))).classes('''
                                    w-full px-4 py-3 rounded-lg text-sm font-medium
                                    bg-red-50 hover:bg-red-100 text-red-600
                                    transition-all duration-200 flex items-center justify-center gap-2
                                '''):
                                    ui.html('<span>🚪</span>')
                                    ui.label('Logout')
                    
                    # Connect hamburger to drawer
                    mobile_btn.on('click', lambda: drawer.open())
    
    return header


def create_sidebar(menu_items: List[Dict], active_route: str = '', on_click: Optional[Callable] = None):
    """
    Create a sidebar navigation for dashboard pages
    
    Args:
        menu_items: List of menu item dictionaries
        active_route: Currently active route for highlighting
        on_click: Callback when menu item is clicked
    """
    
    with ui.element('aside').classes('''
        hidden lg:block w-64 bg-white border-r border-gray-200 
        min-h-screen fixed left-0 top-16 overflow-y-auto
    ''') as sidebar:
        with ui.element('div').classes('p-4'):
            ui.label('Navigation').classes('text-xs font-semibold text-gray-400 uppercase tracking-wider mb-4')
            
            for item in menu_items:
                is_active = item.get('route', '') == active_route
                
                with ui.button(
                    on_click=lambda i=item: (
                        ui.navigate.to(i['route']) if not on_click else on_click(i)
                    )
                ).classes(f'''
                    w-full justify-start px-4 py-3 mb-2 rounded-lg
                    transition-all duration-200
                    {"bg-indigo-50 text-indigo-600 font-semibold" if is_active else "text-gray-700 hover:bg-gray-50"}
                '''):
                    ui.html(f'<span class="mr-3 text-lg">{item.get("icon", "📍")}</span>')
                    ui.label(item.get('label', ''))
    
    return sidebar
