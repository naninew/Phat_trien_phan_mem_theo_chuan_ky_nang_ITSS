"""
Login Page - NiceGUI
"""
from nicegui import ui
from core.auth import login_user, get_redirect_url_for_role, is_authenticated
from core.config import LOGIN_PAGE, CUSTOMER_DASHBOARD
from services.auth_service import AuthService

def create_login_page():
    """Register /login route with premium styling."""

    @ui.page(LOGIN_PAGE)
    async def login_page():
        if is_authenticated():
            ui.navigate.to(CUSTOMER_DASHBOARD)
            return

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
                    with ui.element('div').classes('p-4 bg-primary/10 rounded-3xl'):
                        ui.icon('local_taxi', size='3rem').classes('text-primary')
                    ui.label('Chào mừng trở lại').classes('text-3xl font-bold text-on-surface font-outfit mt-4')
                    ui.label('Hệ thống cứu hộ xe thông minh').classes('text-on-surface-variant')

                # Form
                with ui.column().classes('w-full gap-6'):
                    username = ui.input('Tên đăng nhập').classes('w-full').props('outlined rounded')
                    password = ui.input('Mật khẩu').classes('w-full').props('outlined rounded password-toggle-button').props('type=password')
                    
                    error_label = ui.label('').classes('text-error text-sm text-center min-h-[1.5rem]')
                    
                    login_btn = ui.button('ĐĂNG NHẬP', on_click=lambda: do_login()) \
                        .classes('w-full py-6 rounded-2xl bg-primary text-white font-bold text-lg shadow-lg hover:shadow-primary/30 transform transition hover:-translate-y-1')
                
                # Footer
                with ui.row().classes('w-full justify-center items-center mt-8 gap-1'):
                    ui.label('Chưa có tài khoản?').classes('text-on-surface-variant')
                    ui.link('Đăng ký ngay', '/register').classes('text-primary font-bold hover:underline')

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
                    ui.notify('Đăng nhập thành công!', type='positive')
                    # Redirect is handled inside AuthService.login via login_user? 
                    # No, AuthService.login calls login_user but we still need to navigate.
                    # Wait, login_user doesn't navigate.
                    ui.navigate.to(get_redirect_url_for_role(result['data']['user']['role']))
                else:
                    error_label.set_text(result['message'])
            except Exception as e:
                error_label.set_text(f'Lỗi kết nối: {str(e)}')
            finally:
                login_btn.props(remove='loading')
