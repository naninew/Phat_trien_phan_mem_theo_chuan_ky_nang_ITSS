from nicegui import ui
from core.auth import is_authenticated, get_user_name, logout_user, get_user_role
from core.config import APP_TITLE, LOGIN_PAGE

def create_navbar():
    """Create a modern Material Design 3 navbar."""
    with ui.header().classes('glass-panel px-6 py-2 flex items-center justify-between fixed h-16 top-0 w-full z-50'):
        # Left side: Logo
        with ui.row().classes('items-center gap-2 cursor-pointer').on('click', lambda: ui.navigate.to('/')):
            ui.icon('local_taxi', size='2rem').classes('text-white')
            ui.label(APP_TITLE).classes('text-xl text-white font-bold text-primary font-outfit hide-on-mobile')

        # Right side: Auth/User Actions
        with ui.row().classes('items-center gap-4'):
            if is_authenticated():
                # Notifications
                ui.button(icon='notifications').props('flat round').classes('text-on-surface-variant text-white')
                
                # User Profile Dropdown
                with ui.button(get_user_name(), icon='account_circle').props('flat').classes('text-on-surface font-semibold !text-white'):
                    with ui.menu() as menu:
                        ui.menu_item('Hồ sơ cá nhân', on_click=lambda: ui.navigate.to('/profile'))
                        ui.menu_item('Cài đặt', on_click=lambda: ui.notify('Chưa hỗ trợ'))
                        ui.separator()
                        ui.menu_item('Đăng xuất', on_click=logout_user).classes('text-error')
            else:
                ui.button('Đăng Nhập', on_click=lambda: ui.navigate.to(LOGIN_PAGE)).props('flat').classes('text-primary font-semibold')
                ui.button('Đăng Ký', on_click=lambda: ui.navigate.to('/register')).classes('btn-primary px-4')
