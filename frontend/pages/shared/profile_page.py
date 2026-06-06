"""
Shared profile editing page for customers and company staff.
"""
import inspect
import mimetypes
import os
import re

import httpx
from nicegui import app, ui

from components.page_layout import page_layout
from core.auth import get_access_token, get_user_role
from core.config import BACKEND_URL, SESSION_USER_KEY


def calculate_password_strength(password: str) -> dict:
    if not password:
        return {"score": 0, "level": "Chưa nhập", "color": "#cbd5e1"}

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
    if re.search(r"[!@#$%^&*()_+\-=\[\]{};:'\",.<>?/\\|`~]", password):
        score += 20

    score = min(score, 100)
    if score >= 80:
        return {"score": score, "level": "Rất mạnh", "color": "#10b981"}
    if score >= 60:
        return {"score": score, "level": "Mạnh", "color": "#2563eb"}
    if score >= 40:
        return {"score": score, "level": "Trung bình", "color": "#f59e0b"}
    return {"score": score, "level": "Yếu", "color": "#e11d48"}


def _avatar_url(path: str | None) -> str:
    if not path:
        return ""
    if path.startswith("http://") or path.startswith("https://"):
        return path
    return f"{BACKEND_URL.replace('/api/v1', '')}{path}"


def _sync_current_user(data: dict) -> None:
    stored = app.storage.user.get(SESSION_USER_KEY) or {}
    for key in ("id", "username", "full_name", "role", "avatar_url"):
        if key in data:
            stored[key] = data.get(key)
    app.storage.user[SESSION_USER_KEY] = stored


async def _read_upload_content(upload_event) -> tuple[str, bytes, str]:
    """Normalize NiceGUI upload events across versions."""
    file_obj = getattr(upload_event, "file", None)
    content_obj = getattr(upload_event, "content", None) or file_obj
    if content_obj is None or not hasattr(content_obj, "read"):
        raise ValueError("Không đọc được file ảnh đã chọn")

    raw_content = content_obj.read()
    if inspect.isawaitable(raw_content):
        raw_content = await raw_content
    if isinstance(raw_content, str):
        raw_content = raw_content.encode()
    if not raw_content:
        raise ValueError("File ảnh rỗng hoặc không hợp lệ")

    raw_name = getattr(upload_event, "name", None) or getattr(file_obj, "name", None) or "avatar.jpg"
    filename = os.path.basename(str(raw_name)) or "avatar.jpg"
    content_type = (
        getattr(upload_event, "type", None)
        or getattr(file_obj, "content_type", None)
        or mimetypes.guess_type(filename)[0]
        or "application/octet-stream"
    )

    if "." not in filename:
        filename = f"{filename}{mimetypes.guess_extension(content_type) or '.jpg'}"

    return filename, raw_content, content_type


def create_profile_page():

    @ui.page("/profile")
    async def profile_page():
        token = get_access_token()
        if not token:
            ui.navigate.to("/login")
            return

        headers = {"Authorization": f"Bearer {token}"}
        role = get_user_role()
        role_labels = {
            "customer": "Khách hàng",
            "company_staff": "Đơn vị cứu hộ",
            "admin": "Quản trị viên",
        }
        status_labels = {
            "active": "Đang hoạt động",
            "ACTIVE": "Đang hoạt động",
            "inactive": "Tạm khóa",
            "INACTIVE": "Tạm khóa",
            "suspended": "Bị tạm ngưng",
            "SUSPENDED": "Bị tạm ngưng",
        }
        profile_data = {"avatar_url": None, "username": "", "status": "active"}

        ui.add_head_html("""
        <style>
            .account-page {
                width: 100%;
                max-width: 1180px;
                margin: 0 auto;
                padding: 28px 28px 44px;
            }

            .account-hero,
            .account-card {
                background: #ffffff;
                border: 1px solid #e5eaf2;
                border-radius: 22px;
                box-shadow: 0 14px 34px rgba(15, 23, 42, 0.06);
            }

            body.body--dark .account-hero,
            body.body--dark .account-card {
                background: #111827;
                border-color: #263449;
                box-shadow: 0 18px 42px rgba(0, 0, 0, 0.24);
            }

            .account-hero {
                padding: 20px;
            }

            .account-title {
                font-size: 30px;
                font-weight: 900;
                color: #0f172a;
                line-height: 1.15;
            }

            body.body--dark .account-title,
            body.body--dark .section-heading {
                color: #f8fafc;
            }

            .account-muted {
                color: #64748b;
                font-size: 14px;
            }

            body.body--dark .account-muted {
                color: #94a3b8;
            }

            .avatar-shell {
                position: relative;
                width: 132px;
                height: 132px;
                border-radius: 999px;
                overflow: visible;
                background: linear-gradient(135deg, #eff6ff, #dbeafe);
                border: 4px solid #ffffff;
                box-shadow: 0 10px 24px rgba(37, 99, 235, 0.18);
            }

            .avatar-shell img {
                border-radius: 999px;
            }

            .avatar-uploader {
                position: absolute !important;
                right: 4px;
                bottom: -2px;
                z-index: 5;
                width: 42px !important;
                height: 42px !important;
                min-height: 42px !important;
                border-radius: 999px !important;
                overflow: hidden !important;
                border: 3px solid #ffffff !important;
                box-shadow: 0 10px 22px rgba(37, 99, 235, 0.26);
                background: #2563eb !important;
            }

            .avatar-uploader .q-uploader {
                width: 42px !important;
                height: 42px !important;
                min-height: 42px !important;
                border-radius: 999px !important;
                background: #2563eb !important;
            }

            .avatar-uploader .q-uploader__header {
                width: 42px !important;
                height: 42px !important;
                min-height: 42px !important;
                padding: 0 !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                background: #2563eb !important;
            }

            .avatar-uploader .q-uploader__header::before {
                content: "photo_camera";
                font-family: "Material Icons";
                color: white;
                font-size: 22px;
                line-height: 1;
                pointer-events: none;
                z-index: 1;
            }

            .avatar-uploader .q-uploader__title,
            .avatar-uploader .q-uploader__subtitle,
            .avatar-uploader .q-uploader__list {
                display: none !important;
            }

            .avatar-uploader .q-uploader__header-content {
                position: absolute !important;
                inset: 0 !important;
                z-index: 2 !important;
                width: 42px !important;
                height: 42px !important;
                padding: 0 !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
            }

            .avatar-uploader .q-uploader__header .q-btn {
                position: absolute !important;
                inset: 0 !important;
                z-index: 3 !important;
                width: 42px !important;
                height: 42px !important;
                min-height: 42px !important;
                opacity: 0 !important;
                cursor: pointer !important;
                display: flex !important;
            }

            .avatar-camera {
                width: 34px;
                height: 34px;
                border-radius: 999px;
                background: #2563eb;
                color: white;
                display: flex;
                align-items: center;
                justify-content: center;
                border: 3px solid #ffffff;
                box-shadow: 0 8px 18px rgba(37, 99, 235, 0.22);
            }

            .status-pill {
                border-radius: 999px;
                background: #dcfce7;
                color: #15803d;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 800;
            }

            .role-pill {
                border-radius: 999px;
                background: #eff6ff;
                color: #2563eb;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 800;
            }

            .section-icon {
                width: 42px;
                height: 42px;
                border-radius: 14px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: #eff6ff;
                color: #2563eb;
            }

            .section-heading {
                font-size: 18px;
                font-weight: 900;
                color: #0f172a;
            }

            .form-card {
                padding: 22px;
            }

            .save-button {
                height: 44px;
                border-radius: 14px;
                background: #2563eb;
                color: white;
                font-weight: 850;
                box-shadow: 0 10px 22px rgba(37, 99, 235, 0.2);
            }

            .success-banner {
                border: 1px solid #bbf7d0;
                background: #f0fdf4;
                color: #166534;
                border-radius: 14px;
                padding: 10px 12px;
                font-weight: 750;
                font-size: 13px;
            }

            .error-banner {
                border: 1px solid #fecaca;
                background: #fef2f2;
                color: #991b1b;
                border-radius: 14px;
                padding: 10px 12px;
                font-weight: 750;
                font-size: 13px;
            }

            .security-panel {
                border: 1px solid #e5eaf2;
                border-radius: 18px;
                background: #f8fafc;
            }

            body.body--dark .security-panel {
                background: #0f172a;
                border-color: #263449;
            }

            .strength-track {
                height: 9px;
                border-radius: 999px;
                background: #e2e8f0;
                overflow: hidden;
            }

            .strength-fill {
                height: 100%;
                border-radius: 999px;
                transition: width 180ms ease, background-color 180ms ease;
            }

            .hint-chip {
                border-radius: 999px;
                background: #f1f5f9;
                color: #475569;
                padding: 6px 10px;
                font-size: 12px;
                font-weight: 750;
            }

            @media (max-width: 900px) {
                .account-page {
                    padding: 18px 16px 32px;
                }

                .account-hero {
                    padding: 16px;
                }

                .account-title {
                    font-size: 24px;
                }
            }
        </style>
        """)

        async def _load_profile():
            try:
                async with httpx.AsyncClient() as client:
                    r = await client.get(f"{BACKEND_URL}/profile/me", headers=headers)

                if r.status_code != 200:
                    ui.notify("Không thể tải thông tin cá nhân", type="negative")
                    return

                data = r.json()["data"]
                _sync_current_user(data)
                profile_data.update(
                    {
                        "avatar_url": data.get("avatar_url"),
                        "username": data.get("username") or "",
                        "status": data.get("status") or "active",
                    }
                )

                display_name = data.get("full_name") or data.get("username") or "Người dùng"
                header_name.set_text(display_name)
                header_email.set_text(data.get("email") or "Chưa cập nhật email")
                header_status.set_text(status_labels.get(profile_data["status"], profile_data["status"]))
                avatar_initial.set_text(display_name[:1].upper())

                name_input.value = data.get("full_name") or ""
                phone_input.value = data.get("phone") or ""
                email_input.value = data.get("email") or ""
                address_input.value = data.get("address") or ""

                if profile_data["avatar_url"]:
                    avatar_img.set_source(_avatar_url(profile_data["avatar_url"]))
                    avatar_img.set_visibility(True)
                    avatar_initial.set_visibility(False)

                if role == "company_staff" and data.get("company"):
                    comp = data["company"]
                    comp_name_input.value = comp.get("company_name") or ""
                    comp_addr_input.value = comp.get("address") or ""
                    comp_hotline_input.value = comp.get("hotline") or ""
                    comp_radius_input.value = float(comp.get("service_radius_km") or 0)

            except Exception as exc:
                ui.notify(f"Lỗi tải thông tin: {exc}", type="negative")

        async def _handle_upload(e):
            avatar_status.clear()
            try:
                filename, content, content_type = await _read_upload_content(e)
                async with httpx.AsyncClient() as client:
                    r = await client.post(
                        f"{BACKEND_URL}/profile/me/avatar",
                        files={"file": (filename, content, content_type)},
                        headers={"Authorization": f"Bearer {token}"},
                    )

                if r.status_code == 200:
                    new_url = r.json()["data"]["avatar_url"]
                    profile_data["avatar_url"] = new_url
                    _sync_current_user({"avatar_url": new_url})
                    avatar_img.set_source(_avatar_url(new_url))
                    avatar_img.set_visibility(True)
                    avatar_initial.set_visibility(False)
                    with avatar_status:
                        ui.label("Ảnh đại diện đã được cập nhật").classes("success-banner")
                    ui.notify("Cập nhật ảnh đại diện thành công", type="positive")
                    return

                try:
                    detail = r.json().get("detail", r.text)
                except Exception:
                    detail = r.text
                with avatar_status:
                    ui.label(f"Lỗi upload ảnh: {detail}").classes("error-banner")
            except Exception as exc:
                with avatar_status:
                    ui.label(f"Lỗi kết nối: {exc}").classes("error-banner")

        async def _update_profile():
            profile_status.clear()
            save_profile_btn.props("loading")
            try:
                user_data = {
                    "full_name": name_input.value,
                    "phone": phone_input.value,
                    "email": email_input.value,
                    "address": address_input.value,
                }
                async with httpx.AsyncClient() as client:
                    r = await client.put(
                        f"{BACKEND_URL}/profile/me",
                        json=user_data,
                        headers=headers,
                    )

                if r.status_code != 200:
                    detail = r.json().get("detail", "Không xác định")
                    with profile_status:
                        ui.label(f"Lỗi lưu hồ sơ: {detail}").classes("error-banner")
                    return

                _sync_current_user(
                    {
                        "full_name": name_input.value,
                        "avatar_url": profile_data.get("avatar_url"),
                    }
                )
                header_name.set_text(name_input.value or profile_data["username"] or "Người dùng")
                header_email.set_text(email_input.value or "Chưa cập nhật email")
                with profile_status:
                    ui.label("Thông tin cá nhân đã được lưu").classes("success-banner")
                ui.notify("Đã lưu thông tin cá nhân", type="positive")
            except Exception as exc:
                with profile_status:
                    ui.label(f"Lỗi lưu thông tin: {exc}").classes("error-banner")
            finally:
                save_profile_btn.props(remove="loading")

        async def _update_company_profile():
            company_status.clear()
            save_company_btn.props("loading")
            try:
                comp_data = {
                    "company_name": comp_name_input.value,
                    "address": comp_addr_input.value,
                    "hotline": comp_hotline_input.value,
                    "service_radius_km": float(comp_radius_input.value or 0),
                }
                async with httpx.AsyncClient() as client:
                    r = await client.put(
                        f"{BACKEND_URL}/profile/company",
                        json=comp_data,
                        headers=headers,
                    )

                if r.status_code != 200:
                    detail = r.json().get("detail", "Không xác định")
                    with company_status:
                        ui.label(f"Lỗi cập nhật công ty: {detail}").classes("error-banner")
                    return

                with company_status:
                    ui.label("Thông tin công ty đã được lưu").classes("success-banner")
                ui.notify("Đã lưu thông tin công ty", type="positive")
            except Exception as exc:
                with company_status:
                    ui.label(f"Lỗi lưu công ty: {exc}").classes("error-banner")
            finally:
                save_company_btn.props(remove="loading")

        def _on_new_password_change(value: str):
            strength = calculate_password_strength(value or "")
            password_strength_fill.style(
                f"width: {strength['score']}%; background-color: {strength['color']};"
            )
            password_strength_label.set_text(f"{strength['level']} - {strength['score']}%")

        def _reset_password_form():
            current_pass_input.value = ""
            new_pass_input.value = ""
            confirm_pass_input.value = ""
            password_status.clear()
            _on_new_password_change("")

        async def _update_password():
            password_status.clear()
            if not current_pass_input.value or not new_pass_input.value or not confirm_pass_input.value:
                with password_status:
                    ui.label("Vui lòng điền đầy đủ thông tin mật khẩu").classes("error-banner")
                return

            if new_pass_input.value != confirm_pass_input.value:
                with password_status:
                    ui.label("Mật khẩu xác nhận không khớp").classes("error-banner")
                return

            if len(new_pass_input.value) < 6:
                with password_status:
                    ui.label("Mật khẩu mới phải có ít nhất 6 ký tự").classes("error-banner")
                return

            save_password_btn.props("loading")
            try:
                password_data = {
                    "current_password": current_pass_input.value,
                    "new_password": new_pass_input.value,
                    "confirm_password": confirm_pass_input.value,
                }
                async with httpx.AsyncClient() as client:
                    r = await client.put(
                        f"{BACKEND_URL}/profile/me/password",
                        json=password_data,
                        headers=headers,
                    )

                if r.status_code == 200:
                    current_pass_input.value = ""
                    new_pass_input.value = ""
                    confirm_pass_input.value = ""
                    _on_new_password_change("")
                    with password_status:
                        ui.label("Mật khẩu đã được cập nhật thành công").classes("success-banner")
                    ui.notify("Cập nhật mật khẩu thành công", type="positive")
                    return

                detail = r.json().get("detail", "Không xác định")
                with password_status:
                    ui.label(f"Lỗi đổi mật khẩu: {detail}").classes("error-banner")
            except Exception as exc:
                with password_status:
                    ui.label(f"Lỗi cập nhật mật khẩu: {exc}").classes("error-banner")
            finally:
                save_password_btn.props(remove="loading")

        with page_layout("/profile", title="Tài Khoản"):
            with ui.column().classes("account-page gap-5"):
                with ui.column().classes("gap-1"):
                    ui.label("Cài đặt tài khoản").classes("account-title")
                    ui.label("Quản lý hồ sơ, ảnh đại diện và bảo mật tài khoản của bạn.").classes("account-muted")

                with ui.card().classes("account-hero w-full"):
                    with ui.row().classes("w-full items-center gap-4"):
                        with ui.element("div").classes("avatar-shell shrink-0"):
                            avatar_img = ui.image("").classes("h-full w-full rounded-full object-cover overflow-hidden")
                            avatar_img.set_visibility(False)
                            avatar_initial = ui.label("U").classes(
                                "absolute inset-0 flex items-center justify-center rounded-full text-4xl font-black text-blue-700"
                            )
                            ui.upload(
                                on_upload=_handle_upload,
                                label="",
                                auto_upload=True,
                            ).props("flat dense color=primary accept=image/* max-files=1").classes(
                                "avatar-uploader"
                            )
                        with ui.column().classes("min-w-0 flex-1 gap-1"):
                            header_name = ui.label("Đang tải...").classes("text-xl font-black text-slate-900")
                            header_email = ui.label("Đang tải email").classes("account-muted")
                            with ui.row().classes("items-center gap-2 pt-1"):
                                header_status = ui.label("Đang hoạt động").classes("status-pill")
                                ui.label(role_labels.get(role, "Người dùng")).classes("role-pill")

                    avatar_status = ui.column().classes("w-full gap-0 mt-3")

                with ui.row().classes("w-full gap-5 items-start"):
                    with ui.column().classes("flex-[1.15] min-w-[320px] gap-5"):
                        with ui.card().classes("account-card form-card w-full"):
                            with ui.row().classes("w-full items-start justify-between gap-4"):
                                with ui.row().classes("items-start gap-3"):
                                    with ui.element("div").classes("section-icon"):
                                        ui.icon("badge")
                                    with ui.column().classes("gap-0"):
                                        ui.label("Thông tin cá nhân").classes("section-heading")
                                        ui.label("Cập nhật thông tin liên hệ dùng cho yêu cầu cứu hộ.").classes("account-muted")
                                save_profile_btn = ui.button(
                                    "Lưu hồ sơ",
                                    icon="save",
                                    on_click=_update_profile,
                                ).classes("save-button px-5")

                            profile_status = ui.column().classes("w-full gap-0 mt-4")

                            with ui.grid(columns=2).classes("w-full gap-4 mt-4 max-[760px]:grid-cols-1"):
                                name_input = ui.input("Họ và tên").props("outlined rounded stack-label").classes("w-full")
                                phone_input = ui.input("Số điện thoại").props("outlined rounded stack-label").classes("w-full")
                                email_input = ui.input("Email").props("outlined rounded stack-label").classes("w-full")
                                address_input = ui.input("Địa chỉ").props("outlined rounded stack-label").classes("w-full")

                        if role == "company_staff":
                            with ui.card().classes("account-card form-card w-full"):
                                with ui.row().classes("w-full items-start justify-between gap-4"):
                                    with ui.row().classes("items-start gap-3"):
                                        with ui.element("div").classes("section-icon"):
                                            ui.icon("business")
                                        with ui.column().classes("gap-0"):
                                            ui.label("Thông tin công ty").classes("section-heading")
                                            ui.label("Quản lý thông tin vận hành và phạm vi phục vụ.").classes("account-muted")
                                    save_company_btn = ui.button(
                                        "Lưu công ty",
                                        icon="save",
                                        on_click=_update_company_profile,
                                    ).classes("save-button px-5")

                                company_status = ui.column().classes("w-full gap-0 mt-4")

                                comp_name_input = ui.input("Tên công ty").props("outlined rounded stack-label").classes("w-full mt-4")
                                comp_addr_input = ui.input("Địa chỉ trụ sở").props("outlined rounded stack-label").classes("w-full mt-4")
                                with ui.grid(columns=2).classes("w-full gap-4 mt-4 max-[760px]:grid-cols-1"):
                                    comp_hotline_input = ui.input("Hotline").props("outlined rounded stack-label").classes("w-full")
                                    comp_radius_input = ui.number("Bán kính phục vụ (km)", step=1).props("outlined rounded stack-label").classes("w-full")
                        else:
                            save_company_btn = None

                    with ui.column().classes("flex-1 min-w-[320px] gap-5"):
                        with ui.card().classes("account-card form-card w-full"):
                            with ui.row().classes("items-start gap-3"):
                                with ui.element("div").classes("section-icon"):
                                    ui.icon("shield")
                                with ui.column().classes("gap-0"):
                                    ui.label("Bảo mật tài khoản").classes("section-heading")
                                    ui.label("Đổi mật khẩu định kỳ để bảo vệ tài khoản.").classes("account-muted")

                            password_status = ui.column().classes("w-full gap-0 mt-4")

                            with ui.expansion("Đổi mật khẩu", icon="lock_reset").classes("security-panel w-full mt-4"):
                                with ui.column().classes("w-full gap-4 p-4"):
                                    current_pass_input = ui.input("Mật khẩu hiện tại", password=True, password_toggle_button=True).props("outlined rounded stack-label").classes("w-full")
                                    new_pass_input = ui.input("Mật khẩu mới", password=True, password_toggle_button=True).props("outlined rounded stack-label").classes("w-full")
                                    new_pass_input.on_value_change(lambda e: _on_new_password_change(e.value))

                                    with ui.column().classes("w-full gap-2"):
                                        with ui.row().classes("w-full items-center justify-between"):
                                            ui.label("Độ mạnh mật khẩu").classes("text-sm font-bold text-slate-700")
                                            password_strength_label = ui.label("Chưa nhập - 0%").classes("text-sm font-bold text-slate-500")
                                        with ui.element("div").classes("strength-track w-full"):
                                            password_strength_fill = ui.element("div").classes("strength-fill bg-slate-200").style("width: 0%;")
                                        with ui.row().classes("flex-wrap gap-2"):
                                            ui.label("8+ ký tự").classes("hint-chip")
                                            ui.label("Chữ hoa/thường").classes("hint-chip")
                                            ui.label("Có số").classes("hint-chip")
                                            ui.label("Ký tự đặc biệt").classes("hint-chip")

                                    confirm_pass_input = ui.input("Xác nhận mật khẩu mới", password=True, password_toggle_button=True).props("outlined rounded stack-label").classes("w-full")

                                    with ui.row().classes("w-full justify-end gap-3"):
                                        ui.button(
                                            "Hủy",
                                            icon="close",
                                            on_click=_reset_password_form,
                                        ).props("flat").classes("rounded-xl font-bold")
                                        save_password_btn = ui.button(
                                            "Lưu mật khẩu",
                                            icon="check",
                                            on_click=_update_password,
                                        ).classes("save-button px-5")

        await _load_profile()
