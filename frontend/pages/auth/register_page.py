"""
Trang đăng ký – NiceGUI.
"""
import re
from nicegui import ui

from core.auth import is_authenticated
from core.config import CUSTOMER_DASHBOARD, LOGIN_PAGE
from services.auth_api import register


def create_register_page():
    """Đăng ký route /register."""

    @ui.page("/register")
    async def register_page():
        if is_authenticated():
            ui.navigate.to(CUSTOMER_DASHBOARD)
            return

        ui.add_head_html("""
        <style>
        body { margin: 0; }
        .reg-bg {
            min-height: 100vh;
            background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #2563eb 100%);
            display: flex; align-items: center; justify-content: center; padding: 2rem 0;
        }
        </style>
        """)

        with ui.element("div").classes("reg-bg w-full"):
            with ui.card().classes("w-full max-w-md mx-4 rounded-2xl shadow-2xl p-8"):

                with ui.column().classes("items-center mb-6 gap-1"):
                    ui.icon("person_add", size="3rem").classes("text-indigo-600")
                    ui.label("Tạo Tài Khoản").classes("text-2xl font-bold text-indigo-700")
                    ui.label("Đăng ký để sử dụng hệ thống cứu hộ").classes("text-gray-500 text-sm")

                def _inp(label, placeholder="", password=False):
                    i = ui.input(label=label, placeholder=placeholder, password=password, password_toggle_button=password)
                    i.classes("w-full mt-2")
                    i.props("outlined dense")
                    return i

                username_inp    = _inp("Tên đăng nhập *", "Ít nhất 3 ký tự")
                fullname_inp    = _inp("Họ và tên *", "Nguyễn Văn A")
                phone_inp       = _inp("Số điện thoại *", "0912345678")
                email_inp       = _inp("Email *", "you@example.com")
                password_inp    = _inp("Mật khẩu *", "Ít nhất 6 ký tự", password=True)
                confirm_inp     = _inp("Xác nhận mật khẩu *", "", password=True)

                error_lbl = ui.label("").classes("text-red-500 text-sm mt-1 min-h-[1rem]")
                reg_btn = ui.button("Đăng Ký", icon="how_to_reg").classes(
                    "w-full mt-4 bg-indigo-600 hover:bg-indigo-700 text-[#f0f4f8] font-semibold py-2 rounded-xl"
                )

                async def do_register():
                    error_lbl.set_text("")
                    u = username_inp.value.strip()
                    fn = fullname_inp.value.strip()
                    ph = phone_inp.value.strip()
                    em = email_inp.value.strip()
                    pw = password_inp.value
                    cpw = confirm_inp.value

                    # Client-side validation
                    if not all([u, fn, ph, em, pw, cpw]):
                        error_lbl.set_text("Vui lòng điền đầy đủ tất cả các trường")
                        return
                    if len(u) < 3:
                        error_lbl.set_text("Tên đăng nhập phải có ít nhất 3 ký tự")
                        return
                    if not re.match(r"^0[0-9]{9}$", ph):
                        error_lbl.set_text("Số điện thoại không hợp lệ (VD: 0912345678)")
                        return
                    if not re.match(r"[^@]+@[^@]+\.[^@]+", em):
                        error_lbl.set_text("Email không hợp lệ")
                        return
                    if len(pw) < 6:
                        error_lbl.set_text("Mật khẩu phải có ít nhất 6 ký tự")
                        return
                    if pw != cpw:
                        error_lbl.set_text("Mật khẩu xác nhận không khớp")
                        return

                    reg_btn.props("loading")
                    reg_btn.disable()
                    try:
                        result = await register(
                            username=u,
                            password=pw,
                            full_name=fn,
                            phone=ph,
                            email=em,
                        )
                        # Fix bug: kiểm tra user_id thay vì if result
                        if result and result.get("user_id"):
                            ui.notify("Đăng ký thành công! Hãy đăng nhập.", type="positive")
                            ui.navigate.to(LOGIN_PAGE)
                        else:
                            error_lbl.set_text("Đăng ký thất bại, vui lòng thử lại")
                    except Exception as e:
                        msg = str(e)
                        if "already" in msg.lower() or "exist" in msg.lower():
                            error_lbl.set_text("Tên đăng nhập hoặc email đã được dùng")
                        else:
                            error_lbl.set_text(f"Lỗi: {msg}")
                    finally:
                        reg_btn.props(remove="loading")
                        reg_btn.enable()

                reg_btn.on("click", do_register)
                confirm_inp.on("keydown.enter", do_register)

                ui.separator().classes("my-4")
                with ui.row().classes("w-full justify-center items-center gap-1"):
                    ui.label("Đã có tài khoản?").classes("text-sm text-gray-500")
                    ui.link("Đăng nhập", LOGIN_PAGE).classes("text-sm text-indigo-600 font-semibold hover:underline")
