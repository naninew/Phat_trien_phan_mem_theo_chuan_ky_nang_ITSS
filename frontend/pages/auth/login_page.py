"""
Login Page - NiceGUI
Route /login  : dành cho customer & company
Route /admin-panel/login : dành riêng cho Admin (UC-47)
"""
from nicegui import ui
from core.auth import get_redirect_url_for_role, is_authenticated
from core.config import LOGIN_PAGE, CUSTOMER_DASHBOARD
from services.auth_service import AuthService
def create_login_page():
    """Register /login route with modern professional styling."""

    @ui.page(LOGIN_PAGE)
    async def login_page():
        if is_authenticated():
            ui.navigate.to(CUSTOMER_DASHBOARD)
            return

        ui.add_head_html("""
        <style>
            .login-bg {
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 24px;
                background:
                    radial-gradient(circle at top left, rgba(37, 99, 235, 0.25), transparent 35%),
                    radial-gradient(circle at bottom right, rgba(14, 165, 233, 0.22), transparent 35%),
                    linear-gradient(135deg, #eef2ff 0%, #dbeafe 50%, #f8fafc 100%);
            }

            .login-card {
                width: 100%;
                max-width: 480px;
                padding: 44px;
                border-radius: 32px;
                background: rgba(255, 255, 255, 0.88);
                backdrop-filter: blur(18px);
                border: 1px solid rgba(255, 255, 255, 0.65);
                box-shadow:
                    0 30px 80px rgba(15, 23, 42, 0.16),
                    inset 0 1px 0 rgba(255,255,255,0.7);
            }

            .logo-box {
                width: 84px;
                height: 84px;
                border-radius: 28px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: linear-gradient(135deg, #2563eb, #0ea5e9);
                box-shadow: 0 18px 35px rgba(37, 99, 235, 0.35);
            }

            .login-title {
                font-size: 32px;
                font-weight: 800;
                color: #0f172a;
                letter-spacing: -0.04em;
            }

            .login-subtitle {
                font-size: 15px;
                color: #64748b;
            }

            .login-btn {
                width: 100%;
                height: 54px;
                border-radius: 16px;
                font-weight: 800;
                letter-spacing: 0.03em;
                background: linear-gradient(135deg, #2563eb, #0ea5e9);
                color: white;
                box-shadow: 0 14px 28px rgba(37, 99, 235, 0.28);
                transition: all 0.25s ease;
            }

            .login-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 18px 35px rgba(37, 99, 235, 0.36);
            }

            .password-eye {
                cursor: pointer;
                color: #64748b;
                transition: color 0.2s ease;
            }

            .password-eye:hover {
                color: #2563eb;
            }
        </style>
        """)

        show_password = {'value': False}

        async def do_login():
            error_label.set_text('')

            u = (username.value or '').strip()
            p = (password.value or '').strip()

            if not u or not p:
                error_label.set_text('Vui lòng điền đầy đủ thông tin')
                return

            login_btn.props('loading')

            try:
                result = await AuthService.login(u, p)

                if result['success']:
                    ui.notify('Đăng nhập thành công!', type='positive')
                    ui.navigate.to(
                        get_redirect_url_for_role(
                            result['data']['user']['role']
                        )
                    )
                else:
                    error_label.set_text(result['message'])

            except Exception as e:
                error_label.set_text(f'Lỗi kết nối: {str(e)}')

            finally:
                login_btn.props(remove='loading')

        def toggle_password():
            show_password['value'] = not show_password['value']

            if show_password['value']:
                password.props('type=text')
                eye_icon.name = 'visibility_off'
            else:
                password.props('type=password')
                eye_icon.name = 'visibility'

            eye_icon.update()

        with ui.element('div').classes('login-bg w-full'):
            with ui.element('div').classes('login-card'):

                with ui.column().classes('items-center w-full gap-3 mb-8'):
                    with ui.element('div').classes('logo-box'):
                        ui.icon('local_taxi', size='3.2rem').classes('text-white')

                    ui.label('Chào mừng trở lại').classes('login-title mt-3')
                    ui.label('Hệ thống cứu hộ xe thông minh').classes('login-subtitle')

                with ui.column().classes('w-full gap-5'):
                    username = (
                        ui.input('Tên đăng nhập')
                        .classes('w-full')
                        .props('outlined rounded clearable')
                    )
                    username.add_slot(
                        'prepend',
                        '<q-icon name="person" color="primary" />'
                    )

                    password = (
                        ui.input('Mật khẩu')
                        .classes('w-full')
                        .props('outlined rounded type=password')
                    )
                    password.add_slot(
                        'prepend',
                        '<q-icon name="lock" color="primary" />'
                    )

                    with password.add_slot('append'):
                        eye_icon = (
                            ui.icon('visibility')
                            .classes('password-eye')
                            .on('click', toggle_password)
                        )

                    with ui.row().classes('w-full justify-end -mt-3'):
                        ui.link(
                            'Quên mật khẩu?',
                            '/forgot-password'
                        ).classes(
                            'text-sm text-primary hover:underline font-semibold'
                        )

                    error_label = ui.label('').classes(
                        'text-red-500 text-sm text-center min-h-[1.5rem] w-full'
                    )

                    login_btn = (
                        ui.button('ĐĂNG NHẬP', on_click=do_login)
                        .classes('login-btn mt-1')
                    )

                with ui.row().classes('w-full justify-center items-center mt-8 gap-1'):
                    ui.label('Chưa có tài khoản?').classes('text-gray-500')
                    ui.link(
                        'Đăng ký ngay',
                        '/register'
                    ).classes(
                        'text-primary font-bold hover:underline'
                    )