from nicegui import ui
from core.auth import get_user_role, is_authenticated, logout_user
from core.config import CUSTOMER_DASHBOARD, COMPANY_DASHBOARD, ADMIN_DASHBOARD

def create_sidebar():
    """Create a role-based sidebar."""
    if not is_authenticated():
        return None

    role = get_user_role()
    
    with ui.left_drawer(value=True).classes('bg-surface border-r border-surface-variant p-4 flex flex-col') as drawer:
        with ui.column().classes('w-full gap-2 flex-1'):
            ui.label('MENU').classes('text-xs font-bold text-on-surface-variant tracking-widest mb-4 px-2')
            
            if role == 'customer':
                _nav_item('Dashboard', 'dashboard', CUSTOMER_DASHBOARD)
                _nav_item('Tìm Cứu Hộ', 'explore', '/customer/find-rescue')
                _nav_item('Yêu Cầu Của Tôi', 'history', '/customer/requests')
                _nav_item('Quản Lý Xe', 'directions_car', '/customer/vehicles')
                _nav_item('Cộng Đồng', 'forum', '/customer/community')
                
            elif role == 'company_staff':
                _nav_item('Dashboard', 'dashboard', COMPANY_DASHBOARD)
                _nav_item('Hàng Đợi Cứu Hộ', 'pending_actions', '/company/queue')
                _nav_item('Nhân Sự', 'group', '/company/staff')
                _nav_item('Đội Xe', 'local_shipping', '/company/fleet')
                _nav_item('Dịch Vụ', 'handyman', '/company/services')
                _nav_item('Đánh Giá', 'star', '/company/reviews')
                _nav_item('Hồ Sơ Công Ty', 'business', '/company/profile')
                
            elif role == 'admin':
                _nav_item('Dashboard', 'dashboard', ADMIN_DASHBOARD)
                _nav_item('Quản Lý Người Dùng', 'people', '/admin/users')
                _nav_item('Phê Duyệt Công Ty', 'verified_user', '/admin/companies')
                _nav_item('Báo Cáo Hệ Thống', 'analytics', '/admin/reports')
                _nav_item('Kiểm Duyệt', 'gavel', '/admin/moderation')

            ui.separator().classes('my-4')

            # Profile link — route depends on role
            if role == 'admin':
                _nav_item('Thông Tin Tài Khoản', 'manage_accounts', '/admin/profile')
            else:
                _nav_item('Hồ Sơ Cá Nhân', 'person', '/profile')

        # ── Logout button pinned at the bottom ─────────────────────────────
        ui.separator().classes('my-2')
        with ui.row().classes(
            'w-full items-center gap-3 px-4 py-3 rounded-xl cursor-pointer '
            'hover:bg-red-50 transition-colors group'
        ).on('click', _confirm_logout_sidebar):
            ui.icon('logout', size='1.5rem').classes('text-red-400 group-hover:text-red-600')
            ui.label('Đăng Xuất').classes('font-medium text-red-400 group-hover:text-red-600')

    return drawer


def _confirm_logout_sidebar():
    """Confirm dialog before logout (from sidebar)."""
    with ui.dialog() as dlg, ui.card().classes('rounded-2xl p-6 shadow-2xl w-80'):
        with ui.column().classes('w-full items-center gap-4'):
            ui.icon('logout', size='3rem').classes('text-red-500')
            ui.label('Xác nhận đăng xuất?').classes('text-xl font-bold text-gray-800')
            ui.label(
                'Bạn sẽ được chuyển về trang đăng nhập. Phiên làm việc hiện tại sẽ bị xóa.'
            ).classes('text-sm text-gray-500 text-center')
            with ui.row().classes('w-full gap-3 mt-2'):
                ui.button('Hủy', on_click=dlg.close).props('no-caps flat').classes(
                    'flex-1 border border-gray-300 text-gray-600 rounded-xl font-semibold'
                )
                ui.button('Đăng Xuất', icon='logout', on_click=logout_user).props('no-caps').classes(
                    'flex-1 bg-red-600 text-white rounded-xl font-bold shadow'
                )
    dlg.open()


def _nav_item(label, icon, target):
    with ui.row().classes('w-full items-center gap-3 px-4 py-3 rounded-xl cursor-pointer hover:bg-primary/10 transition-colors') \
        .on('click', lambda t=target: ui.navigate.to(t)):
        ui.icon(icon, size='1.5rem').classes('text-on-surface-variant')
        ui.label(label).classes('font-medium text-on-surface')
