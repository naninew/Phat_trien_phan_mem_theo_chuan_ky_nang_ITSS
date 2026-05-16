"""
Trang đăng nhập – NiceGUI.
"""
from nicegui import ui

from core.auth import (
    login_user,
    get_redirect_url_for_role,
    is_authenticated,
)
from core.config import LOGIN_PAGE, CUSTOMER_DASHBOARD
from services.auth_api import login


def create_login_page():
    """Đăng ký route /login với thiết kế chuyên nghiệp."""

    @ui.page(LOGIN_PAGE)
    async def login_page():
        if is_authenticated():
            ui.navigate.to(CUSTOMER_DASHBOARD)
            return

        # Global theme and local styles
        ui.add_head_html("""
        <style>
            .login-container {
                min-height: 100vh;
                background-color: var(--surface);
                display: flex;
                width: 100%;
            }
            .hero-section {
                flex: 1;
                background: linear-gradient(rgba(0, 95, 176, 0.6), rgba(0, 95, 176, 0.8)), 
                            url('/static/hero.png');
                background-size: cover;
                background-position: center;
                display: flex;
                flex-direction: column;
                justify-content: center;
                padding: 60px;
                color: #f0f4f8;
            }
            .form-section {
                width: 480px;
                display: flex;
                flex-direction: column;
                justify-content: center;
                padding: 60px;
                background: #fdfbff;
            }
            @media (max-width: 900px) {
                .hero-section { display: none; }
                .form-section { width: 100%; padding: 40px; }
            }
            .m3-input .q-field__control {
                border-radius: 12px !important;
            }
        </style>
        """)

        # Ensure static folder and hero image mapping exists (in real environment we'd mount it)
        # For now we use a placeholder or assume the user will mount it.
        # Let's use a nice CSS fallback just in case.

        with ui.element("div").classes("login-container"):
            # Left: Hero Section
            with ui.element("div").classes("hero-section"):
                ui.label("Rescue System").classes("text-5xl font-bold font-outfit mb-4")
                ui.label("Dịch vụ cứu hộ xe chuyên nghiệp, hỗ trợ 24/7 trên mọi nẻo đường. An tâm vững tay lái cùng đội ngũ cứu hộ tin cậy.").classes("text-xl opacity-90 leading-relaxed max-w-lg")
                
                with ui.row().classes("mt-10 gap-6"):
                    with ui.column().classes("items-center"):
                        ui.label("15-30'").classes("text-3xl font-bold text-primary-container")
                        ui.label("Thời gian chờ").classes("text-sm opacity-80")
                    ui.separator().props('vertical').classes('bg-[#f0f4f8]/20')
                    with ui.column().classes("items-center"):
                        ui.label("500+").classes("text-3xl font-bold text-primary-container")
                        ui.label("Đối tác").classes("text-sm opacity-80")
            
            # Right: Form Section
            with ui.element("div").classes("form-section"):
                with ui.column().classes("w-full max-w-sm mx-auto gap-8"):
                    # Logo & Header
                    with ui.column().classes("gap-2"):
                        with ui.element('div').classes('p-3 bg-primary-container rounded-2xl w-fit'):
                            ui.icon("local_taxi", size="2.5rem").classes("text-primary")
                        ui.label("Chào mừng trở lại").classes("text-3xl font-bold text-on-surface font-outfit")
                        ui.label("Vui lòng đăng nhập để tiếp tục sử dụng dịch vụ").classes("text-on-surface-variant")

                    # Form
                    with ui.column().classes("w-full gap-4"):
                        username_inp = ui.input(
                            label="Tên đăng nhập",
                            placeholder="username của bạn",
                        ).classes("w-full m3-input").props('outlined stack-label')
                        
                        password_inp = ui.input(
                            label="Mật khẩu",
                            placeholder="••••••••",
                            password=True,
                            password_toggle_button=True,
                        ).classes("w-full m3-input").props('outlined stack-label')

                        error_lbl = ui.label("").classes("text-error text-sm font-medium min-h-[1.5rem]")

                        login_btn = ui.button("Đăng Nhập").classes(
                            "w-full py-4 rounded-2xl bg-primary text-on-primary font-bold text-lg shadow-lg hover:shadow-xl transform transition hover:-translate-y-1"
                        ).props('unelevated')

                    async def do_login():
                        error_lbl.set_text("")
                        u = username_inp.value.strip()
                        p = password_inp.value

                        if not u or not p:
                            error_lbl.set_text("Vui lòng nhập đầy đủ thông tin")
                            return

                        login_btn.props("loading")
                        login_btn.disable()
                        try:
                            result = await login(u, p)
                            if result and "access_token" in result:
                                user_info = result.get("user", {})
                                role = user_info.get("role", "customer")
                                login_user(result["access_token"], user_info, role)
                                ui.notify(f"Chào mừng, {user_info.get('full_name', u)}! 👋", type="positive")
                                ui.navigate.to(get_redirect_url_for_role(role))
                            else:
                                error_lbl.set_text("Sai tên đăng nhập hoặc mật khẩu")
                        except Exception as e:
                            error_lbl.set_text(f"Lỗi hệ thống: {str(e)}")
                        finally:
                            login_btn.props(remove="loading")
                            login_btn.enable()

                    login_btn.on("click", do_login)
                    password_inp.on("keydown.enter", do_login)

                    # Footer Links
                    with ui.column().classes("w-full items-center gap-4 mt-4"):
                        with ui.row().classes("gap-1"):
                            ui.label("Chưa có tài khoản?").classes("text-on-surface-variant")
                            ui.link("Đăng ký ngay", "/register").classes("text-primary font-bold hover:underline")
                        
                        ui.link("Quên mật khẩu?", "#").classes("text-sm text-on-surface-variant opacity-60")
