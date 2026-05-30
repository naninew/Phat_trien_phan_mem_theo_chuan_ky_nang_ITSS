"""
Shared profile editing page for customers and company staff.
"""
from nicegui import ui
import httpx
import re

from core.auth import get_access_token, get_user_role
from core.config import BACKEND_URL
from components.page_layout import page_layout


def calculate_password_strength(password: str) -> dict:
    if not password:
        return {"score": 0, "level": "Chưa nhập", "color": "gray"}

    score = 0

    if len(password) >= 8:
        score += 25
    if len(password) >= 12:
        score += 10
    if re.search(r"[a-z]", password):
        score += 15
    if re.search(r"[A-Z]", password):
        score += 15
    if re.search(r"[0-9]", password):
        score += 15
    if re.search(r"[!@#$%^&*()_+\-=\[\]{};:\'\",.<>?/\\|`~]", password):
        score += 20

    score = min(score, 100)

    if score >= 80:
        return {"score": score, "level": "Rất mạnh", "color": "green"}
    if score >= 60:
        return {"score": score, "level": "Mạnh", "color": "blue"}
    if score >= 40:
        return {"score": score, "level": "Trung bình", "color": "orange"}

    return {"score": score, "level": "Yếu", "color": "red"}


def create_profile_page():

    @ui.page("/profile")
    async def profile_page():
        token = get_access_token()
        if not token:
            ui.navigate.to("/login")
            return

        headers = {"Authorization": f"Bearer {token}"}
        role = get_user_role()

        profile_data = {"avatar_url": None}
        password_state = {"show": False}

        ui.add_head_html("""
        <style>
            .profile-page {
                width: 100%;
                max-width: 1120px;
                margin: 0 auto;
                padding: 32px;
            }

            .profile-heading {
                font-size: 32px;
                font-weight: 900;
                color: #0f172a;
                letter-spacing: -0.04em;
            }

            .profile-subtitle {
                color: #64748b;
                font-size: 14px;
            }

            .profile-card {
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 28px;
                box-shadow: 0 10px 32px rgba(15, 23, 42, 0.06);
            }

            .avatar-card {
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 28px;
                box-shadow: 0 10px 32px rgba(15, 23, 42, 0.06);
                position: sticky;
                top: 24px;
            }

            .avatar-frame {
                width: 144px;
                height: 144px;
                border-radius: 999px;
                overflow: hidden;
                border: 5px solid #eff6ff;
                box-shadow: 0 14px 32px rgba(37, 99, 235, 0.18);
                background: #f1f5f9;
            }

            .section-title {
                font-size: 20px;
                font-weight: 850;
                color: #0f172a;
            }

            .section-desc {
                color: #64748b;
                font-size: 13px;
            }

            .section-icon {
                width: 46px;
                height: 46px;
                border-radius: 16px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: #eff6ff;
                color: #2563eb;
            }

            .role-pill {
                padding: 8px 16px;
                border-radius: 999px;
                background: #eff6ff;
                color: #2563eb;
                font-size: 11px;
                font-weight: 900;
                letter-spacing: 0.08em;
            }

            .security-box {
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 22px;
                padding: 18px;
            }

            .password-tip {
                background: #eff6ff;
                border: 1px solid #bfdbfe;
                border-radius: 18px;
                padding: 16px;
            }

            .primary-action {
                height: 52px;
                border-radius: 16px;
                font-weight: 900;
                background: #2563eb;
                color: white;
                box-shadow: 0 12px 24px rgba(37, 99, 235, 0.22);
            }

            .secondary-action {
                height: 46px;
                border-radius: 14px;
                font-weight: 800;
            }
        </style>
        """)

        async def _load_profile():
            try:
                async with httpx.AsyncClient() as client:
                    r = await client.get(
                        f"{BACKEND_URL}/profile/me",
                        headers=headers,
                    )

                    if r.status_code == 200:
                        data = r.json()["data"]

                        name_input.value = data.get("full_name") or ""
                        phone_input.value = data.get("phone") or ""
                        email_input.value = data.get("email") or ""

                        profile_data["avatar_url"] = data.get("avatar_url")

                        if profile_data["avatar_url"]:
                            avatar_img.set_source(
                                f"{BACKEND_URL.replace('/api/v1', '')}{profile_data['avatar_url']}"
                            )

                        if role == "company_staff" and data.get("company"):
                            comp = data["company"]
                            comp_name_input.value = comp.get("company_name") or ""
                            comp_addr_input.value = comp.get("address") or ""
                            comp_hotline_input.value = comp.get("hotline") or ""
                            comp_radius_input.value = float(
                                comp.get("service_radius_km") or 0
                            )
                    else:
                        ui.notify("Không thể tải thông tin cá nhân", type="negative")

            except Exception as e:
                ui.notify(f"Lỗi tải thông tin: {e}", type="negative")

        async def _handle_upload(e):
            try:
                content = await e.file.read()

                async with httpx.AsyncClient() as client:
                    files = {
                        "file": (
                            e.file.name,
                            content,
                            e.file.content_type,
                        )
                    }

                    r = await client.post(
                        f"{BACKEND_URL}/profile/me/avatar",
                        files=files,
                        headers={"Authorization": f"Bearer {token}"},
                    )

                    if r.status_code == 200:
                        new_url = r.json()["data"]["avatar_url"]
                        profile_data["avatar_url"] = new_url
                        avatar_img.set_source(
                            f"{BACKEND_URL.replace('/api/v1', '')}{new_url}"
                        )
                        ui.notify(
                            "Cập nhật ảnh đại diện thành công",
                            type="positive",
                        )
                    else:
                        ui.notify(f"Lỗi upload ảnh: {r.text}", type="negative")

            except Exception as ex:
                ui.notify(f"Lỗi kết nối: {ex}", type="negative")

        async def _update_profile():
            try:
                async with httpx.AsyncClient() as client:
                    user_data = {
                        "full_name": name_input.value,
                        "phone": phone_input.value,
                        "email": email_input.value,
                    }

                    r = await client.put(
                        f"{BACKEND_URL}/profile/me",
                        json=user_data,
                        headers=headers,
                    )

                    if r.status_code != 200:
                        ui.notify(
                            f"Lỗi: {r.json().get('detail', 'Không xác định')}",
                            type="negative",
                        )
                        return

                    if role == "company_staff":
                        comp_data = {
                            "company_name": comp_name_input.value,
                            "address": comp_addr_input.value,
                            "hotline": comp_hotline_input.value,
                            "service_radius_km": float(comp_radius_input.value),
                        }

                        r2 = await client.put(
                            f"{BACKEND_URL}/profile/company",
                            json=comp_data,
                            headers=headers,
                        )

                        if r2.status_code != 200:
                            ui.notify(
                                f"Lỗi cập nhật công ty: {r2.json().get('detail')}",
                                type="negative",
                            )
                            return

                    ui.notify("Đã lưu tất cả thay đổi", type="positive")

            except Exception as e:
                ui.notify(f"Lỗi lưu thông tin: {e}", type="negative")

        def _on_new_password_change(value: str):
            strength = calculate_password_strength(value)

            password_strength_bar.value = strength["score"] / 100
            password_strength_bar.props(f"color={strength['color']}")
            password_strength_label.set_text(
                f"Độ mạnh: {strength['level']} ({strength['score']}%)"
            )

        async def _update_password():
            if (
                not current_pass_input.value
                or not new_pass_input.value
                or not confirm_pass_input.value
            ):
                ui.notify("Vui lòng điền đầy đủ thông tin", type="warning")
                return

            if new_pass_input.value != confirm_pass_input.value:
                ui.notify("Mật khẩu xác nhận không khớp", type="negative")
                return

            if len(new_pass_input.value) < 6:
                ui.notify(
                    "Mật khẩu mới phải có ít nhất 6 ký tự",
                    type="warning",
                )
                return

            try:
                async with httpx.AsyncClient() as client:
                    password_data = {
                        "current_password": current_pass_input.value,
                        "new_password": new_pass_input.value,
                        "confirm_password": confirm_pass_input.value,
                    }

                    r = await client.put(
                        f"{BACKEND_URL}/profile/me/password",
                        json=password_data,
                        headers=headers,
                    )

                    if r.status_code == 200:
                        ui.notify("Cập nhật mật khẩu thành công", type="positive")

                        current_pass_input.value = ""
                        new_pass_input.value = ""
                        confirm_pass_input.value = ""

                        password_strength_bar.value = 0
                        password_strength_label.set_text("Độ mạnh: Chưa nhập")

                        password_state["show"] = False
                        password_section.set_visibility(False)
                    else:
                        detail = r.json().get("detail", "Không xác định")
                        ui.notify(f"Lỗi: {detail}", type="negative")

            except Exception as e:
                ui.notify(f"Lỗi cập nhật mật khẩu: {e}", type="negative")

        def _toggle_password_section():
            password_state["show"] = not password_state["show"]
            password_section.set_visibility(password_state["show"])

        with page_layout("/profile", title="Tài Khoản"):
            with ui.column().classes("profile-page gap-8"):

                with ui.row().classes("w-full items-center justify-between"):
                    with ui.column().classes("gap-1"):
                        ui.label("Cài đặt tài khoản").classes("profile-heading")
                        ui.label(
                            "Quản lý thông tin cá nhân, ảnh đại diện và bảo mật tài khoản"
                        ).classes("profile-subtitle")

                with ui.row().classes("w-full gap-8 items-start"):

                    with ui.column().classes("w-80 gap-6"):
                        with ui.card().classes(
                            "avatar-card w-full p-7 items-center text-center"
                        ):
                            with ui.element("div").classes("avatar-frame mb-5"):
                                avatar_img = ui.image("").classes(
                                    "w-full h-full object-cover"
                                )

                            ui.label("Ảnh đại diện").classes(
                                "text-lg font-black text-gray-900"
                            )
                            ui.label(
                                "Cập nhật ảnh nhận diện tài khoản của bạn"
                            ).classes("text-sm text-gray-500 mb-4")

                            ui.upload(
                                on_upload=_handle_upload,
                                label="Đổi ảnh đại diện",
                                auto_upload=True,
                            ).props("flat color=primary").classes("w-full")

                            ui.separator().classes("my-5")

                            ui.label(role.replace("_", " ").upper()).classes(
                                "role-pill"
                            )

                    with ui.column().classes("flex-1 gap-6"):

                        with ui.card().classes("profile-card w-full p-8"):
                            with ui.row().classes("items-start gap-4 mb-6"):
                                with ui.element("div").classes("section-icon"):
                                    ui.icon("account_circle", size="1.8rem")

                                with ui.column().classes("gap-0"):
                                    ui.label("Thông tin cá nhân").classes(
                                        "section-title"
                                    )
                                    ui.label(
                                        "Cập nhật họ tên, số điện thoại và email liên hệ"
                                    ).classes("section-desc")

                            name_input = ui.input("Họ và tên").classes(
                                "w-full mb-4"
                            ).props("outlined rounded")

                            with ui.row().classes("w-full gap-4"):
                                phone_input = ui.input("Số điện thoại").classes(
                                    "flex-1"
                                ).props("outlined rounded")

                                email_input = ui.input("Email").classes(
                                    "flex-1"
                                ).props("outlined rounded")

                        if role == "company_staff":
                            with ui.card().classes("profile-card w-full p-8"):
                                with ui.row().classes("items-start gap-4 mb-6"):
                                    with ui.element("div").classes("section-icon"):
                                        ui.icon("business", size="1.8rem")

                                    with ui.column().classes("gap-0"):
                                        ui.label("Thông tin công ty").classes(
                                            "section-title"
                                        )
                                        ui.label(
                                            "Quản lý thông tin vận hành và phạm vi phục vụ"
                                        ).classes("section-desc")

                                comp_name_input = ui.input("Tên công ty").classes(
                                    "w-full mb-4"
                                ).props("outlined rounded")

                                comp_addr_input = ui.input("Địa chỉ trụ sở").classes(
                                    "w-full mb-4"
                                ).props("outlined rounded")

                                with ui.row().classes("w-full gap-4"):
                                    comp_hotline_input = ui.input("Hotline").classes(
                                        "flex-1"
                                    ).props("outlined rounded")

                                    comp_radius_input = ui.number(
                                        "Bán kính phục vụ (km)",
                                        step=1,
                                    ).classes("flex-1").props("outlined rounded")

                        with ui.card().classes("profile-card w-full p-8"):
                            with ui.row().classes(
                                "w-full items-center justify-between"
                            ):
                                with ui.row().classes("items-start gap-4"):
                                    with ui.element("div").classes("section-icon"):
                                        ui.icon("shield", size="1.8rem")

                                    with ui.column().classes("gap-0"):
                                        ui.label("Bảo mật tài khoản").classes(
                                            "section-title"
                                        )
                                        ui.label(
                                            "Thay đổi mật khẩu định kỳ để bảo vệ tài khoản"
                                        ).classes("section-desc")

                                ui.button(
                                    "Đổi mật khẩu",
                                    icon="edit",
                                    on_click=_toggle_password_section,
                                ).props("flat color=primary").classes(
                                    "secondary-action"
                                )

                            password_section = ui.column().classes(
                                "w-full gap-4 mt-6 security-box"
                            )

                            with password_section:
                                current_pass_input = ui.input(
                                    "Mật khẩu hiện tại"
                                ).props("outlined rounded type=password").classes(
                                    "w-full"
                                )

                                new_pass_input = ui.input(
                                    "Mật khẩu mới"
                                ).props("outlined rounded type=password").classes(
                                    "w-full"
                                )
                                new_pass_input.on_value_change(
                                    lambda e: _on_new_password_change(e.value)
                                )

                                ui.label("Độ mạnh mật khẩu").classes(
                                    "text-sm font-bold text-gray-700"
                                )

                                password_strength_bar = ui.linear_progress(
                                    value=0
                                ).classes("w-full")
                                password_strength_bar.props("color=gray")

                                password_strength_label = ui.label(
                                    "Độ mạnh: Chưa nhập"
                                ).classes("text-sm text-gray-500")

                                confirm_pass_input = ui.input(
                                    "Xác nhận mật khẩu mới"
                                ).props("outlined rounded type=password").classes(
                                    "w-full"
                                )

                                with ui.element("div").classes("password-tip"):
                                    with ui.row().classes("items-start gap-3"):
                                        ui.icon("info").classes("text-primary mt-1")
                                        ui.html(
                                            """
                                            <div class="text-sm text-blue-900">
                                                <b>Gợi ý mật khẩu mạnh</b>
                                                <ul class="text-xs text-blue-800 ml-4 mt-1">
                                                    <li>Ít nhất 6 ký tự</li>
                                                    <li>Bao gồm chữ hoa, chữ thường và số</li>
                                                    <li>Nên có ký tự đặc biệt như !@#$%</li>
                                                </ul>
                                            </div>
                                            """
                                        )

                                with ui.row().classes("w-full gap-4"):
                                    ui.button(
                                        "Lưu mật khẩu mới",
                                        icon="check",
                                        on_click=_update_password,
                                    ).classes("flex-1 primary-action")

                                    ui.button(
                                        "Hủy",
                                        icon="close",
                                        on_click=_toggle_password_section,
                                    ).props("flat").classes("flex-1 secondary-action")

                            password_section.set_visibility(False)

                        ui.button(
                            "LƯU TẤT CẢ THAY ĐỔI",
                            icon="save",
                            on_click=_update_profile,
                        ).classes("w-full primary-action text-base")

        await _load_profile()