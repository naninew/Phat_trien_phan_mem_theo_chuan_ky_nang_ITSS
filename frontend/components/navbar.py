from nicegui import ui
from core.auth import is_authenticated, get_user_name, logout_user, get_user_role
from core.config import APP_TITLE, LOGIN_PAGE

def create_navbar():
    """Create a modern Material Design 3 navbar."""
    with ui.header().classes('bg-white border-b border-gray-100 shadow-sm px-6 py-0 flex items-center justify-between fixed h-16 top-0 w-full z-50'):
        # Left side: Logo
        with ui.row().classes('items-center gap-3 cursor-pointer h-full').on('click', lambda: ui.navigate.to('/')):
            ui.icon('local_taxi', size='1.8rem').classes('text-blue-600')
            ui.label(APP_TITLE).classes('text-xl text-slate-800 font-extrabold font-outfit tracking-tight hide-on-mobile')

        # Right side: Auth/User Actions
        with ui.row().classes('items-center gap-3 h-full'):
            if is_authenticated():
                # Notifications
                ui.button(icon='notifications_none').props('flat round').classes('text-gray-500 hover:text-blue-600 hover:bg-blue-50 transition-colors')
                
                # User Profile Dropdown
                with ui.button(get_user_name(), icon='account_circle').props('flat').classes('text-slate-700 font-semibold hover:bg-blue-50 rounded-xl px-4 py-2 transition-colors lowercase capitalize-first'):
                    with ui.menu().classes('rounded-xl shadow-lg border border-gray-100') as menu:
                        ui.menu_item('Hồ sơ cá nhân', on_click=lambda: ui.navigate.to('/profile')).classes('hover:text-blue-600')
                        ui.menu_item('Cài đặt', on_click=lambda: ui.notify('Chưa hỗ trợ')).classes('hover:text-blue-600')
                        ui.separator()
                        ui.menu_item('Đăng xuất', on_click=logout_user).classes('text-red-500 hover:bg-red-50')
            else:
                ui.button('Đăng Nhập', on_click=lambda: ui.navigate.to(LOGIN_PAGE)).props('flat').classes('text-blue-600 font-semibold rounded-xl px-5')
                ui.button('Đăng Ký', on_click=lambda: ui.navigate.to('/register')).classes('bg-blue-600 text-white font-bold rounded-xl px-6 shadow-md hover:bg-blue-700 transition-colors')
