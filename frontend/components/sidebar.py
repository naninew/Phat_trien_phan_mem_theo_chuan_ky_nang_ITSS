from nicegui import ui
from core.auth import get_user_role, is_authenticated, logout_user
from core.config import CUSTOMER_DASHBOARD, COMPANY_DASHBOARD, ADMIN_DASHBOARD

def create_sidebar():
    """Create a role-based sidebar with instant active item highlighting."""
    if not is_authenticated():
        return None

    role = get_user_role()
    
    # Lấy đường dẫn hiện tại một cách chính xác (Ví dụ: '/', '/profile')
    current_route = ui.context.client.page.path
    
    with ui.left_drawer(value=True).classes('bg-white border-r border-gray-100 p-3 flex flex-col') as drawer:
        with ui.column().classes('w-full gap-1 flex-1'):
            
            if role == 'customer':
                _nav_item('Dashboard', 'dashboard', CUSTOMER_DASHBOARD, current_route)
                _nav_item('Tìm Cứu Hộ', 'explore', '/customer/find-rescue', current_route)
                _nav_item('Yêu Cầu Của Tôi', 'history', '/customer/requests', current_route)
                _nav_item('Quản Lý Xe', 'directions_car', '/customer/vehicles', current_route)
                _nav_item('Cộng Đồng', 'forum', '/customer/community', current_route)
                
            elif role == 'company_staff':
                _nav_item('Dashboard', 'dashboard', COMPANY_DASHBOARD, current_route)
                _nav_item('Hàng Đợi Cứu Hộ', 'pending_actions', '/company/queue', current_route)
                _nav_item('Nhân Sự', 'group', '/company/staff', current_route)
                _nav_item('Đội Xe', 'local_shipping', '/company/fleet', current_route)
                _nav_item('Dịch Vụ', 'handyman', '/company/services', current_route)
                _nav_item('Đánh Giá', 'star', '/company/reviews', current_route)
                _nav_item('Hồ Sơ Công Ty', 'business', '/company/profile', current_route)
                
            elif role == 'admin':
                _nav_item('Dashboard', 'dashboard', ADMIN_DASHBOARD, current_route)
                _nav_item('Quản Lý Người Dùng', 'people', '/admin/users', current_route)
                _nav_item('Phê Duyệt Công Ty', 'verified_user', '/admin/companies', current_route)
                _nav_item('Báo Cáo Hệ Thống', 'analytics', '/admin/reports', current_route)
                _nav_item('Kiểm Duyệt', 'gavel', '/admin/moderation', current_route)

            ui.separator().classes('my-3')

            # Profile link — route depends on role
            if role == 'admin':
                _nav_item('Thông Tin Tài Khoản', 'manage_accounts', '/admin/profile', current_route)
            elif role == 'customer':
                _nav_item('Hồ Sơ Cá Nhân', 'person', '/profile', current_route)

        # ── Logout button pinned at the bottom ─────────────────────────────
        ui.separator().classes('my-1')
        with ui.row().classes(
            'w-full items-center gap-3 px-4 py-3 rounded-xl cursor-pointer '
            'hover:bg-red-50 transition-colors group'
        ).on('click', _confirm_logout_sidebar):
            ui.icon('logout', size='1.5rem').classes('text-red-400 group-hover:text-red-600 transition-colors')
            ui.label('Đăng Xuất').classes('font-semibold text-red-400 group-hover:text-red-600 transition-colors')

    return drawer


def _confirm_logout_sidebar():
    """Confirm dialog before logout (from sidebar)."""
    with ui.dialog() as dlg, ui.card().classes('rounded-3xl p-8 shadow-2xl w-[400px]'):
        with ui.column().classes('w-full items-center gap-3'):
            ui.icon('logout', size='3.5rem').classes('text-red-500 mb-2')
            ui.label('Xác nhận đăng xuất?').classes('text-2xl font-bold text-slate-800 font-outfit')
            ui.label(
                'Bạn sẽ được chuyển về trang đăng nhập. Phiên làm việc hiện tại sẽ bị xóa.'
            ).classes('text-sm text-gray-500 text-center mb-4 leading-relaxed')
            with ui.row().classes('w-full gap-3'):
                ui.button('Hủy', on_click=dlg.close).props('no-caps flat').classes(
                    'flex-1 border border-gray-200 hover:bg-gray-50 text-slate-600 rounded-xl font-bold py-3 transition-colors'
                )
                ui.button('Đăng Xuất', icon='logout', on_click=logout_user).props('no-caps').classes(
                    'flex-1 bg-red-600 hover:bg-red-700 text-white rounded-xl font-bold py-3 shadow-md transition-colors'
                )
    dlg.open()


def _nav_item(label, icon, target, current_route):
    """Render a navigation item with strict and instant background highlight."""
    route_clean = current_route if current_route else '/'
    target_clean = target if target else '/'
    is_active = (route_clean == target_clean)
    base_classes = 'w-full items-center gap-3 px-3 py-2.5 rounded-xl cursor-pointer font-medium transition-colors group'
    
    if is_active:
        row_classes = f'{base_classes} bg-blue-50'
        text_classes = 'text-blue-700 font-bold'
        icon_classes = 'text-blue-600'
    else:
        row_classes = f'{base_classes} bg-transparent hover:bg-slate-50'
        text_classes = 'text-slate-600 group-hover:text-slate-800'
        icon_classes = 'text-slate-400 group-hover:text-slate-600 transition-colors'

    with ui.row().classes(row_classes).on('click', lambda t=target: ui.navigate.to(t)):
        ui.icon(icon, size='1.5rem').classes(icon_classes)
        ui.label(label).classes(text_classes)
