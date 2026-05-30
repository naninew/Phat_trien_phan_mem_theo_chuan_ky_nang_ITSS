"""
Login Page - NiceGUI
Route /login  : dành cho customer & company
Route /admin-panel/login : dành riêng cho Admin (UC-47)
"""
from nicegui import ui
from core.auth import login_user, get_redirect_url_for_role, is_authenticated, get_user_role
from core.config import LOGIN_PAGE, ADMIN_LOGIN_PAGE, CUSTOMER_DASHBOARD, ADMIN_DASHBOARD
from services.auth_service import AuthService


def _build_login_form(is_admin_page: bool = False):
    """
    Hàm nội bộ xây dựng form đăng nhập.
    is_admin_page=True → hiển thị label admin, redirect về /admin/dashboard sau login.
    """
    ui.add_head_html("""
    <style>
        .login-card {
            width: 100%;
            max-width: 450px;
            padding: 2.5rem;
            border-radius: 2rem;
            background: white;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
        }
        .login-bg {
            background: linear-gradient(135deg, #f0f4f8 0%, #d6e3ff 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
    </style>
    """)

    with ui.element('div').classes('login-bg w-full'):
        with ui.element('div').classes('login-card'):
            # Header
            with ui.column().classes('items-center w-full gap-2 mb-8'):
                icon_name = 'admin_panel_settings' if is_admin_page else 'local_taxi'
                with ui.element('div').classes('p-4 bg-primary/10 rounded-3xl'):
                    ui.icon(icon_name, size='3rem').classes('text-primary')
                title = 'Quản Trị Viên' if is_admin_page else 'Chào mừng trở lại'
                ui.label(title).classes('text-3xl font-bold text-on-surface font-outfit mt-4')
                subtitle = 'Đăng nhập vào hệ thống quản trị' if is_admin_page else 'Hệ thống cứu hộ xe thông minh'
                ui.label(subtitle).classes('text-on-surface-variant')

            # Form
            with ui.column().classes('w-full gap-5'):
                username = ui.input('Tên đăng nhập').classes('w-full').props('outlined rounded')
                password = ui.input('Mật khẩu').classes('w-full').props(
                    'outlined rounded password-toggle-button type=password'
                )

                with ui.row().classes('w-full justify-end -mt-2'):
                    ui.link('Quên mật khẩu?', '/forgot-password').classes(
                        'text-sm text-primary hover:underline font-medium'
                    )

                error_label = ui.label('').classes(
                    'text-error text-sm text-center min-h-[1.5rem] w-full'
                )

                with ui.row().classes('w-full justify-center mt-2'):
                    login_btn = ui.button('ĐĂNG NHẬP', on_click=lambda: do_login()).classes(
                        'px-12 py-4 rounded-xl bg-primary text-white font-bold text-base '
                        'shadow-md hover:shadow-primary/30 transform transition hover:-translate-y-0.5'
                    )

            # Footer – chỉ hiển thị link đăng ký nếu không phải trang admin
            if not is_admin_page:
                with ui.row().classes('w-full justify-center items-center mt-8 gap-1'):
                    ui.label('Chưa có tài khoản?').classes('text-on-surface-variant')
                    ui.link('Đăng ký ngay', '/register').classes('text-primary font-bold hover:underline')
            else:
                with ui.row().classes('w-full justify-center items-center mt-6'):
                    ui.label('Chỉ dành cho tài khoản Quản trị viên').classes(
                        'text-xs text-gray-400 italic'
                    )

    async def do_login():
        error_label.set_text('')
        u = username.value.strip()
        p = password.value.strip()

        if not u or not p:
            error_label.set_text('Vui lòng điền đầy đủ thông tin')
            return

        login_btn.props('loading')
        try:
            result = await AuthService.login(u, p)
            if result['success']:
                role = result['data']['user']['role']
                # Nếu đang ở trang admin-panel/login, chỉ cho admin login thành công
                if is_admin_page and role != 'admin':
                    error_label.set_text('Trang này chỉ dành cho tài khoản Quản trị viên')
                    # Xóa session vừa lưu vì không phải admin
                    from nicegui import app as _app
                    _app.storage.user.clear()
                    return
                ui.notify('Đăng nhập thành công!', type='positive')
                ui.navigate.to(get_redirect_url_for_role(role))
            else:
                error_label.set_text(result['message'])
        except Exception as e:
            error_label.set_text(f'Lỗi kết nối: {str(e)}')
        finally:
            login_btn.props(remove='loading')


def create_login_page():
    """Đăng ký route /login (dành cho customer & company)."""

    @ui.page(LOGIN_PAGE)
    async def login_page():
        # Nếu đã đăng nhập → redirect về dashboard tương ứng
        if is_authenticated():
            ui.navigate.to(get_redirect_url_for_role(get_user_role()))
            return
        _build_login_form(is_admin_page=False)


def create_admin_login_page():
    """Đăng ký route /admin-panel/login (UC-47 – chỉ dành cho Admin)."""

    @ui.page(ADMIN_LOGIN_PAGE)
    async def admin_login_page():
        # Nếu đã đăng nhập với role admin → redirect thẳng về dashboard
        if is_authenticated() and get_user_role() == 'admin':
            ui.navigate.to(ADMIN_DASHBOARD)
            return
        # Nếu đã đăng nhập với role khác → redirect về dashboard của role đó
        if is_authenticated():
            ui.navigate.to(get_redirect_url_for_role(get_user_role()))
            return
        _build_login_form(is_admin_page=True)