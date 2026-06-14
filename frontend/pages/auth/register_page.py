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
        <link href="https://fonts.googleapis.com/icon?family=Material+Icons+Outlined" rel="stylesheet">
        <style>
            .register-shell {
                width: 100%;
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

            .register-card {
                width: 100%;
                max-width: 880px;
                border-radius: 24px;
                background: rgba(255, 255, 255, 0.9);
                backdrop-filter: blur(18px);
                border: 1px solid rgba(255, 255, 255, 0.65);
                box-shadow:
                    0 30px 80px rgba(15, 23, 42, 0.16),
                    inset 0 1px 0 rgba(255,255,255,0.7);
                padding: 22px 26px;
            }

            .form-logo {
                width: 58px;
                height: 58px;
                border-radius: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: linear-gradient(135deg, #2563eb, #0ea5e9);
                box-shadow: 0 18px 35px rgba(37, 99, 235, 0.35);
            }

            .line-icon {
                font-family: 'Material Icons Outlined' !important;
                font-weight: normal !important;
                font-style: normal !important;
            }

            .form-header {
                max-width: 620px;
                margin: 0 auto;
            }

            .form-title {
                font-size: 26px;
                line-height: 1.16;
                font-weight: 800;
                color: #0f172a;
                letter-spacing: 0;
            }

            .form-subtitle {
                color: #64748b;
                font-size: 15px;
                line-height: 1.55;
            }

            .account-segment {
                position: relative;
                display: grid;
                grid-template-columns: 1fr 1fr;
                width: min(100%, 560px);
                gap: 5px;
                padding: 5px;
                margin: 0 auto;
                border-radius: 999px;
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                height: 48px;
                min-height: 48px;
            }

            .account-segment .q-tabs__content {
                position: absolute;
                inset: 5px;
                width: auto !important;
                min-width: 0 !important;
                height: 38px;
                min-height: 38px;
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 5px;
            }

            .account-segment .q-tab {
                width: 100%;
                min-height: 38px;
                height: 38px;
                padding: 0 12px;
                border-radius: 999px;
                color: #475569 !important;
                font-size: 13px;
                font-weight: 800;
                text-transform: none;
                transition: all 0.22s ease;
                background: transparent;
            }

            .account-segment .q-tab:hover {
                background: #eef2f7;
            }

            .account-segment .q-icon {
                font-family: 'Material Icons Outlined' !important;
                color: currentColor !important;
                font-size: 19px !important;
            }

            .account-segment .q-tab--active {
                color: #ffffff !important;
                background: linear-gradient(135deg, #2563eb, #3b82f6);
                box-shadow: 0 10px 20px rgba(37, 99, 235, 0.24);
            }

            .account-segment .q-tab__content {
                min-width: 0;
                gap: 6px;
                flex-direction: row !important;
            }

            .account-segment .q-tab__label {
                overflow: visible;
                text-overflow: clip;
                white-space: nowrap;
            }

            .account-segment .q-tab__indicator {
                display: none;
            }

            .register-panels,
            .register-panels .q-panel,
            .register-panels .q-tab-panel {
                background: transparent !important;
                padding: 0 !important;
            }

            .customer-form {
                width: min(100%, 520px);
                margin: 0 auto;
            }

            .company-grid {
                width: 100%;
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 10px 14px;
            }

            .grid-full {
                grid-column: 1 / -1;
            }

            .r24-field .q-field__control {
                height: 48px;
                border-radius: 13px;
                background: #ffffff;
                border: 1px solid #e2e8f0;
                box-shadow: 0 1px 0 rgba(15, 23, 42, 0.02);
                transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
            }

            .r24-field .q-field__marginal {
                height: 48px;
            }

            .r24-field .q-field__control::before,
            .r24-field .q-field__control::after {
                display: none;
            }

            .r24-field.q-field--focused .q-field__control {
                border-color: #2563eb;
                box-shadow: 0 0 0 4px rgba(37, 99, 235, 0.10);
            }

            .r24-field .q-field__label,
            .r24-field .q-field__native,
            .r24-field input {
                color: #0f172a;
            }

            .r24-field .q-field__label {
                color: #64748b;
                font-weight: 600;
                font-size: 14px;
            }

            .field-icon {
                color: #64748b;
                font-family: 'Material Icons Outlined' !important;
                font-size: 20px !important;
                transition: color 0.2s ease;
            }

            .r24-field.q-field--focused .field-icon {
                color: #2563eb;
            }

            .valid-icon {
                color: #10b981;
                font-family: 'Material Icons Outlined' !important;
                font-size: 19px !important;
            }

            .password-eye {
                color: #64748b;
                cursor: pointer;
                transition: color 0.2s ease;
                font-family: 'Material Icons Outlined' !important;
                font-size: 20px !important;
            }

            .password-eye:hover {
                color: #2563eb;
            }

            .strength-track {
                height: 5px;
                border-radius: 999px;
                overflow: hidden;
                background: #e2e8f0;
            }

            .strength-bar {
                height: 100%;
                width: 0%;
                border-radius: 999px;
                background: #ef4444;
                transition: width 0.25s ease, background 0.25s ease;
            }

            .register-btn {
                width: 100%;
                height: 50px;
                border-radius: 14px;
                color: white;
                font-size: 15px;
                font-weight: 800;
                letter-spacing: 0.02em;
                background: linear-gradient(135deg, #2563eb, #3b82f6);
                box-shadow: 0 18px 34px rgba(37, 99, 235, 0.3);
                transition: transform 0.22s ease, box-shadow 0.22s ease;
                text-transform: none;
            }

            .register-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 24px 42px rgba(37, 99, 235, 0.38);
            }

            .section-label {
                color: #2563eb;
                font-size: 11px;
                font-weight: 800;
                letter-spacing: 0.08em;
                text-transform: uppercase;
                margin-top: 2px;
            }

            .form-error {
                color: #ef4444;
                font-size: 13px;
                min-height: 14px;
            }

            .login-prompt {
                color: #64748b;
                font-size: 14px;
            }

            @media (max-width: 640px) {
                .register-shell {
                    padding: 16px;
                    align-items: flex-start;
                }

                .register-card {
                    padding: 22px 18px;
                    border-radius: 24px;
                }

                .form-title {
                    font-size: 23px;
                }

                .company-grid {
                    grid-template-columns: 1fr;
                }

                .form-header {
                    text-align: left;
                    justify-content: flex-start;
                }

                .account-segment .q-tab {
                    padding: 0 8px;
                    font-size: 12px;
                }
            }
        </style>
        """)

        def password_score(value: str) -> int:
            checks = [
                len(value) >= 8,
                bool(re.search(r'[A-Z]', value)),
                bool(re.search(r'[a-z]', value)),
                bool(re.search(r'[0-9]', value)),
                bool(re.search(r'[^A-Za-z0-9]', value)),
            ]
            return sum(checks)

        def make_field(label: str, icon: str, password: bool = False):
            field = ui.input(label, password=password).classes('w-full r24-field').props('borderless')
            field.add_slot('prepend', f'<q-icon name="{icon}" class="field-icon" size="20px" />')
            with field.add_slot('append'):
                valid = ui.icon('check_circle', size='20px').classes('valid-icon')
                valid.set_visibility(False)
                eye = None
                if password:
                    eye = ui.icon('visibility', size='20px').classes('password-eye')
            return field, valid, eye

        def attach_validation(field, valid_icon, validator):
            def _validate(_=None):
                value = field.value or ''
                valid_icon.set_visibility(bool(validator(value)))
            field.on_value_change(_validate)
            field.on('update:model-value', _validate)
            field.on('blur', _validate)

        def configure_password(field, eye_icon, strength_bar, strength_label, valid_icon):
            visible = {'value': False}

            def toggle_password():
                visible['value'] = not visible['value']
                field.props('type=text' if visible['value'] else 'type=password')
                eye_icon.name = 'visibility_off' if visible['value'] else 'visibility'
                eye_icon.update()

            def update_strength(_=None):
                value = field.value or ''
                score = password_score(value)
                width = [0, 24, 44, 66, 84, 100][score]
                color = '#ef4444'
                label = 'Mật khẩu yếu'
                if score >= 4:
                    color = '#10b981'
                    label = 'Mật khẩu mạnh'
                elif score >= 3:
                    color = '#f59e0b'
                    label = 'Mật khẩu khá'
                strength_bar.style(f'width: {width}%; background: {color};')
                strength_label.set_text(label if value else 'Tối thiểu 8 ký tự, gồm chữ và số')
                valid_icon.set_visibility(score >= 3)

            eye_icon.on('click', toggle_password)
            field.on_value_change(update_strength)
            field.on('update:model-value', update_strength)
            field.on('blur', update_strength)

        with ui.element('div').classes('register-shell'):
            with ui.element('section').classes('register-card'):
                with ui.column().classes('w-full gap-4'):
                    with ui.row().classes('form-header items-center justify-center gap-3 w-full'):
                        with ui.element('div').classes('form-logo'):
                            ui.icon('local_taxi', size='2.4rem').classes('text-white')
                        with ui.column().classes('gap-0'):
                            ui.label('Tạo tài khoản Rescue24').classes('form-title font-outfit')
                            ui.label('Đăng ký để kết nối dịch vụ cứu hộ nhanh, minh bạch và đáng tin cậy.').classes('form-subtitle')

                    with ui.tabs().classes('account-segment w-full') as tabs:
                        customer_tab = ui.tab('Khách hàng', icon='person')
                        company_tab = ui.tab('Công ty cứu hộ', icon='business')

                    with ui.tab_panels(tabs, value=customer_tab).classes('register-panels w-full'):
                        with ui.tab_panel(customer_tab):
                            with ui.column().classes('customer-form gap-2 pt-3'):
                                c_username, c_username_valid, _ = make_field('Tên đăng nhập *', 'person')
                                c_fullname, c_fullname_valid, _ = make_field('Họ và tên *', 'badge')
                                c_phone, c_phone_valid, _ = make_field('Số điện thoại *', 'call')
                                c_email, c_email_valid, _ = make_field('Email *', 'mail')
                                c_password, c_password_valid, c_eye = make_field('Mật khẩu *', 'lock', password=True)
                                with ui.column().classes('w-full gap-1'):
                                    with ui.element('div').classes('strength-track w-full'):
                                        c_strength_bar = ui.element('div').classes('strength-bar')
                                    c_strength_label = ui.label('Tối thiểu 8 ký tự, gồm chữ và số').classes('text-xs text-slate-500')

                                c_error = ui.label('').classes('form-error')
                                c_btn = ui.button('Đăng ký', on_click=lambda: do_register_customer()).classes('register-btn')

                        with ui.tab_panel(company_tab):
                            with ui.column().classes('w-full gap-2 pt-3'):
                                ui.label('Thông tin tài khoản').classes('section-label')
                                with ui.element('div').classes('company-grid'):
                                    co_username, co_username_valid, _ = make_field('Tên đăng nhập *', 'person')
                                    co_fullname, co_fullname_valid, _ = make_field('Người đại diện *', 'badge')
                                    co_email, co_email_valid, _ = make_field('Email *', 'mail')
                                    with ui.column().classes('w-full gap-1'):
                                        co_password, co_password_valid, co_eye = make_field('Mật khẩu *', 'lock', password=True)
                                        with ui.element('div').classes('strength-track w-full'):
                                            co_strength_bar = ui.element('div').classes('strength-bar')
                                        co_strength_label = ui.label('Tối thiểu 8 ký tự, gồm chữ và số').classes('text-xs text-slate-500')

                                ui.label('Thông tin công ty').classes('section-label')
                                with ui.element('div').classes('company-grid'):
                                    comp_name, comp_name_valid, _ = make_field('Tên công ty *', 'business')
                                    comp_license, comp_license_valid, _ = make_field('Mã số thuế/GPKD *', 'verified')
                                    comp_hotline, comp_hotline_valid, _ = make_field('Hotline cứu hộ *', 'headset_mic')
                                    with ui.element('div').classes('grid-full'):
                                        comp_address, comp_address_valid, _ = make_field('Địa chỉ trụ sở *', 'location_on')

                                co_error = ui.label('').classes('form-error')
                                co_btn = ui.button('Đăng ký công ty cứu hộ', on_click=lambda: do_register_company()).classes('register-btn')

                    with ui.row().classes('w-full justify-center items-center gap-1'):
                        ui.label('Đã có tài khoản?').classes('login-prompt')
                        ui.link('Đăng nhập', LOGIN_PAGE).classes('text-[#2563EB] font-bold hover:underline')

        attach_validation(c_username, c_username_valid, lambda value: len(value.strip()) >= 3)
        attach_validation(c_fullname, c_fullname_valid, lambda value: len(value.strip()) >= 2)
        attach_validation(c_phone, c_phone_valid, lambda value: bool(re.fullmatch(r'[0-9+\-\s]{9,15}', value.strip())))
        attach_validation(c_email, c_email_valid, lambda value: bool(re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', value.strip())))
        configure_password(c_password, c_eye, c_strength_bar, c_strength_label, c_password_valid)

        attach_validation(co_username, co_username_valid, lambda value: len(value.strip()) >= 3)
        attach_validation(co_fullname, co_fullname_valid, lambda value: len(value.strip()) >= 2)
        attach_validation(co_email, co_email_valid, lambda value: bool(re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', value.strip())))
        configure_password(co_password, co_eye, co_strength_bar, co_strength_label, co_password_valid)
        attach_validation(comp_name, comp_name_valid, lambda value: len(value.strip()) >= 2)
        attach_validation(comp_license, comp_license_valid, lambda value: len(value.strip()) >= 5)
        attach_validation(comp_address, comp_address_valid, lambda value: len(value.strip()) >= 5)
        attach_validation(comp_hotline, comp_hotline_valid, lambda value: bool(re.fullmatch(r'[0-9+\-\s]{9,15}', value.strip())))

        async def do_register_customer():
            c_error.set_text('')
            data = {
                "username": (c_username.value or '').strip(),
                "full_name": (c_fullname.value or '').strip(),
                "phone": (c_phone.value or '').strip(),
                "email": (c_email.value or '').strip(),
                "password": c_password.value or '',
                "role": "customer"
            }
            if not all(data.values()):
                c_error.set_text('Vui lòng điền đầy đủ thông tin')
                return
            if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', data["email"]):
                c_error.set_text('Email chưa đúng định dạng')
                return
            if password_score(data["password"]) < 3:
                c_error.set_text('Mật khẩu cần mạnh hơn để bảo vệ tài khoản')
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
                "username": (co_username.value or '').strip(),
                "full_name": (co_fullname.value or '').strip(),
                "email": (co_email.value or '').strip(),
                "password": co_password.value or '',
                "company_name": (comp_name.value or '').strip(),
                "business_license": (comp_license.value or '').strip(),
                "address": (comp_address.value or '').strip(),
                "hotline": (comp_hotline.value or '').strip(),
                "role": "company_staff"
            }
            if not all(data.values()):
                co_error.set_text('Vui lòng điền đầy đủ thông tin')
                return
            if not re.fullmatch(r'[^@\s]+@[^@\s]+\.[^@\s]+', data["email"]):
                co_error.set_text('Email chưa đúng định dạng')
                return
            if password_score(data["password"]) < 3:
                co_error.set_text('Mật khẩu cần mạnh hơn để bảo vệ tài khoản')
                return
            
            co_btn.props('loading')
            res = await AuthService.register_company(data)
            if res['success']:
                ui.notify('Đăng ký công ty thành công! Vui lòng chờ phê duyệt.', type='positive')
                ui.navigate.to(LOGIN_PAGE)
            else:
                co_error.set_text(res['message'])
            co_btn.props(remove='loading')
