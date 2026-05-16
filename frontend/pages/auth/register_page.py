"""
Register Page - NiceGUI
"""
from nicegui import ui
import re
from core.auth import is_authenticated
from core.config import CUSTOMER_DASHBOARD, LOGIN_PAGE
from services.auth_service import AuthService

def create_register_page():
    """Register /register route with tabbed interface."""

    @ui.page('/register')
    async def register_page():
        if is_authenticated():
            ui.navigate.to(CUSTOMER_DASHBOARD)
            return

        ui.add_head_html("""
        <style>
            .register-card {
                width: 100%;
                max-width: 550px;
                padding: 2.5rem;
                border-radius: 2rem;
                background: white;
                box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
            }
            .register-bg {
                background: linear-gradient(135deg, #fdfbff 0%, #e6f0ff 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                padding: 2rem;
            }
        </style>
        """)

        with ui.element('div').classes('register-bg w-full'):
            with ui.element('div').classes('register-card'):
                with ui.column().classes('items-center w-full gap-2 mb-6'):
                    ui.label('Tham Gia Rescue24').classes('text-3xl font-bold text-primary font-outfit')
                    ui.label('Chọn loại tài khoản bạn muốn đăng ký').classes('text-on-surface-variant')

                with ui.tabs().classes('w-full') as tabs:
                    customer_tab = ui.tab('KHÁCH HÀNG', icon='person')
                    company_tab = ui.tab('CÔNG TY CỨU HỘ', icon='business')

                with ui.tab_panels(tabs, value=customer_tab).classes('w-full bg-transparent'):
                    # ── Customer Registration Panel ──────────────────────────────────
                    with ui.tab_panel(customer_tab):
                        with ui.column().classes('w-full gap-4'):
                            c_username = ui.input('Tên đăng nhập *').classes('w-full').props('outlined rounded dense')
                            c_fullname = ui.input('Họ và tên *').classes('w-full').props('outlined rounded dense')
                            c_phone = ui.input('Số điện thoại *').classes('w-full').props('outlined rounded dense')
                            c_email = ui.input('Email *').classes('w-full').props('outlined rounded dense')
                            c_password = ui.input('Mật khẩu *', password=True).classes('w-full').props('outlined rounded dense password-toggle-button')
                            
                            c_error = ui.label('').classes('text-error text-sm min-h-[1.5rem]')
                            c_btn = ui.button('ĐĂNG KÝ KHÁCH HÀNG', on_click=lambda: do_register_customer()) \
                                .classes('w-full py-4 rounded-xl bg-primary text-white font-bold')

                    # ── Company Registration Panel ───────────────────────────────────
                    with ui.tab_panel(company_tab):
                        with ui.column().classes('w-full gap-4'):
                            ui.label('Thông tin người đại diện').classes('font-bold text-sm text-primary border-b w-full pb-1')
                            co_username = ui.input('Tên đăng nhập *').classes('w-full').props('outlined rounded dense')
                            co_fullname = ui.input('Họ và tên *').classes('w-full').props('outlined rounded dense')
                            co_email = ui.input('Email *').classes('w-full').props('outlined rounded dense')
                            co_password = ui.input('Mật khẩu *', password=True).classes('w-full').props('outlined rounded dense password-toggle-button')
                            
                            ui.label('Thông tin công ty').classes('font-bold text-sm text-primary border-b w-full pb-1 mt-2')
                            comp_name = ui.input('Tên công ty *').classes('w-full').props('outlined rounded dense')
                            comp_license = ui.input('Mã số thuế/GPKD *').classes('w-full').props('outlined rounded dense')
                            comp_address = ui.input('Địa chỉ trụ sở *').classes('w-full').props('outlined rounded dense')
                            comp_hotline = ui.input('Hotline cứu hộ *').classes('w-full').props('outlined rounded dense')
                            
                            co_error = ui.label('').classes('text-error text-sm min-h-[1.5rem]')
                            co_btn = ui.button('ĐĂNG KÝ CÔNG TY', on_click=lambda: do_register_company()) \
                                .classes('w-full py-4 rounded-xl bg-primary text-white font-bold')

                with ui.row().classes('w-full justify-center items-center mt-6 gap-1'):
                    ui.label('Đã có tài khoản?').classes('text-on-surface-variant')
                    ui.link('Đăng nhập', LOGIN_PAGE).classes('text-primary font-bold hover:underline')

        async def do_register_customer():
            c_error.set_text('')
            data = {
                "username": c_username.value.strip(),
                "full_name": c_fullname.value.strip(),
                "phone": c_phone.value.strip(),
                "email": c_email.value.strip(),
                "password": c_password.value,
                "role": "customer"
            }
            if not all(data.values()):
                c_error.set_text('Vui lòng điền đầy đủ thông tin')
                return
            
            c_btn.props('loading')
            res = await AuthService.register_customer(data)
            if res['success']:
                ui.notify('Đăng ký thành công! Vui lòng đăng nhập.', type='positive')
                ui.navigate.to(LOGIN_PAGE)
            else:
                c_error.set_text(res['message'])
            c_btn.props(remove='loading')

        async def do_register_company():
            co_error.set_text('')
            data = {
                "username": co_username.value.strip(),
                "full_name": co_fullname.value.strip(),
                "email": co_email.value.strip(),
                "password": co_password.value,
                "company_name": comp_name.value.strip(),
                "business_license": comp_license.value.strip(),
                "address": comp_address.value.strip(),
                "hotline": comp_hotline.value.strip(),
                "role": "company_staff"
            }
            if not all(data.values()):
                co_error.set_text('Vui lòng điền đầy đủ thông tin')
                return
            
            co_btn.props('loading')
            res = await AuthService.register_company(data)
            if res['success']:
                ui.notify('Đăng ký công ty thành công! Vui lòng chờ phê duyệt.', type='positive')
                ui.navigate.to(LOGIN_PAGE)
            else:
                co_error.set_text(res['message'])
            co_btn.props(remove='loading')
