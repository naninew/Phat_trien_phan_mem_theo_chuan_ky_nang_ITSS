"""
Trang thông tin tài khoản Admin - Profile & Đăng xuất
"""
from nicegui import ui, app
from typing import Dict, Any, Optional

from core.auth import require_role, get_current_user, get_user_name, logout_user
from components.page_layout import page_layout
from services.api_client import api_client


def create_admin_profile_page():

    @ui.page('/admin/profile')
    async def admin_profile_page():
        if not require_role("admin"):
            return

        with page_layout("/admin/profile", title="Thông Tin Tài Khoản"):
            user = get_current_user() or {}

            # ── Hero Banner ────────────────────────────────────────────────────
            with ui.card().classes(
                "w-full rounded-3xl overflow-hidden shadow-xl border-none mb-2"
            ):
                # Gradient background strip
                with ui.element("div").classes(
                    "w-full h-36 bg-gradient-to-r from-indigo-700 via-purple-700 to-indigo-900 relative"
                ):
                    pass

                # Avatar + name row sitting on the strip
                with ui.row().classes("w-full items-end gap-6 px-8 -mt-14 pb-6"):
                    # Avatar circle
                    with ui.element("div").classes(
                        "w-28 h-28 rounded-full bg-white shadow-lg flex items-center justify-center border-4 border-white"
                    ):
                        ui.icon("admin_panel_settings", size="3.5rem").classes("text-indigo-600")

                    with ui.column().classes("gap-1 flex-1 mt-12"):
                        ui.label(user.get("full_name") or user.get("username") or "Admin").classes(
                            "text-2xl font-bold text-gray-800"
                        )
                        with ui.row().classes("items-center gap-2"):
                            ui.badge("Quản trị viên", color="indigo").classes("text-xs px-3 py-1 rounded-full")
                            if user.get("email"):
                                ui.label(user.get("email")).classes("text-sm text-gray-500")

                    # Logout button (top right of the card)
                    ui.button(
                        "Đăng Xuất",
                        icon="logout",
                        on_click=_confirm_logout,
                    ).classes(
                        "mt-12 bg-red-50 text-red-600 border border-red-200 hover:bg-red-100 "
                        "font-semibold rounded-xl px-6 py-2 shadow-sm transition-all"
                    ).props("no-caps")

            # ── Content Grid ────────────────────────────────────────────────────
            with ui.row().classes("w-full gap-6 items-start"):

                # Left column — account info card
                with ui.column().classes("flex-1 gap-4 min-w-0"):

                    with ui.card().classes("w-full rounded-2xl shadow-sm border border-gray-100 p-6"):
                        with ui.row().classes("items-center gap-3 mb-4"):
                            ui.icon("person", size="1.5rem").classes("text-indigo-500")
                            ui.label("Thông Tin Cá Nhân").classes("text-lg font-bold text-gray-800")

                        # Info rows
                        _info_row("Tên đầy đủ", user.get("full_name") or "—", "badge")
                        _info_row("Tên đăng nhập", user.get("username") or "—", "alternate_email")
                        _info_row("Email", user.get("email") or "—", "email")
                        _info_row("Số điện thoại", user.get("phone") or "—", "phone")
                        _info_row("Địa chỉ", user.get("address") or "—", "location_on")
                        _info_row("Vai trò", "Quản trị viên hệ thống", "shield")
                        _info_row("Trạng thái tài khoản", "Đang hoạt động ✓", "verified")

                    # Edit profile form (collapsible)
                    with ui.expansion("✏️  Chỉnh sửa thông tin", icon="edit").classes(
                        "w-full rounded-2xl shadow-sm border border-gray-100"
                    ):
                        with ui.column().classes("w-full gap-3 p-2"):
                            full_name_in = ui.input(
                                "Tên đầy đủ",
                                value=user.get("full_name") or "",
                                placeholder="Nhập tên đầy đủ...",
                            ).classes("w-full")
                            phone_in = ui.input(
                                "Số điện thoại",
                                value=user.get("phone") or "",
                                placeholder="Nhập số điện thoại...",
                            ).classes("w-full")
                            email_in = ui.input(
                                "Email",
                                value=user.get("email") or "",
                                placeholder="Nhập địa chỉ email...",
                            ).classes("w-full")
                            address_in = ui.input(
                                "Địa chỉ",
                                value=user.get("address") or "",
                                placeholder="Nhập địa chỉ...",
                            ).classes("w-full")

                            async def _save_profile():
                                data = {}
                                if full_name_in.value:
                                    data["full_name"] = full_name_in.value
                                if phone_in.value:
                                    data["phone"] = phone_in.value
                                if email_in.value:
                                    data["email"] = email_in.value
                                if address_in.value:
                                    data["address"] = address_in.value
                                try:
                                    r = await api_client.put("/profile/me", data=data)
                                    if r.get("success"):
                                        # Update local session info
                                        stored = app.storage.user.get("user_info", {})
                                        stored.update(data)
                                        app.storage.user["user_info"] = stored
                                        ui.notify("Cập nhật thông tin thành công!", type="positive")
                                    else:
                                        ui.notify(f"Lỗi: {r.get('message')}", type="negative")
                                except Exception as e:
                                    ui.notify(f"Không thể cập nhật: {e}", type="negative")

                            ui.button("Lưu thay đổi", icon="save", on_click=_save_profile).classes(
                                "bg-indigo-600 text-white font-bold rounded-xl px-6 w-full mt-2"
                            ).props("no-caps")

                # Right column — security & quick actions
                with ui.column().classes("w-80 shrink-0 gap-4"):

                    # Security Card
                    with ui.card().classes("w-full rounded-2xl shadow-sm border border-gray-100 p-6"):
                        with ui.row().classes("items-center gap-3 mb-4"):
                            ui.icon("lock", size="1.5rem").classes("text-purple-500")
                            ui.label("Bảo Mật").classes("text-lg font-bold text-gray-800")

                        with ui.column().classes("w-full gap-3"):
                            ui.label("Đổi mật khẩu").classes("text-sm font-semibold text-gray-700")
                            old_pw = ui.input("Mật khẩu hiện tại", password=True, password_toggle_button=True).classes("w-full")
                            new_pw = ui.input("Mật khẩu mới", password=True, password_toggle_button=True).classes("w-full")
                            confirm_pw = ui.input("Xác nhận mật khẩu", password=True, password_toggle_button=True).classes("w-full")

                            async def _change_password():
                                if not old_pw.value or not new_pw.value:
                                    ui.notify("Vui lòng điền đầy đủ thông tin", type="warning")
                                    return
                                if new_pw.value != confirm_pw.value:
                                    ui.notify("Mật khẩu xác nhận không khớp!", type="negative")
                                    return
                                if len(new_pw.value) < 6:
                                    ui.notify("Mật khẩu mới tối thiểu 6 ký tự", type="warning")
                                    return
                                try:
                                    r = await api_client.put(
                                        "/profile/me/password",
                                        data={"old_password": old_pw.value, "new_password": new_pw.value},
                                    )
                                    if r.get("success"):
                                        ui.notify("Đổi mật khẩu thành công!", type="positive")
                                        old_pw.value = ""
                                        new_pw.value = ""
                                        confirm_pw.value = ""
                                    else:
                                        ui.notify(f"Lỗi: {r.get('message')}", type="negative")
                                except Exception as e:
                                    ui.notify(f"Không thể đổi mật khẩu: {e}", type="negative")

                            ui.button("Đổi Mật Khẩu", icon="key", on_click=_change_password).classes(
                                "bg-purple-600 text-white font-bold rounded-xl px-6 w-full mt-1"
                            ).props("no-caps")

                    # Quick Links Card
                    with ui.card().classes("w-full rounded-2xl shadow-sm border border-gray-100 p-6"):
                        with ui.row().classes("items-center gap-3 mb-4"):
                            ui.icon("dashboard", size="1.5rem").classes("text-indigo-500")
                            ui.label("Điều Hướng Nhanh").classes("text-lg font-bold text-gray-800")

                        _quick_link("Dashboard", "dashboard", "/admin/dashboard", "indigo")
                        _quick_link("Quản lý Người dùng", "people", "/admin/users", "blue")
                        _quick_link("Phê duyệt Công ty", "verified_user", "/admin/companies", "green")
                        _quick_link("Báo cáo Hệ thống", "analytics", "/admin/reports", "purple")
                        _quick_link("Kiểm duyệt", "gavel", "/admin/moderation", "amber")

                    # Danger Zone Card
                    with ui.card().classes(
                        "w-full rounded-2xl shadow-sm border border-red-100 bg-red-50 p-6"
                    ):
                        with ui.row().classes("items-center gap-3 mb-3"):
                            ui.icon("warning", size="1.5rem").classes("text-red-500")
                            ui.label("Vùng Nguy Hiểm").classes("text-lg font-bold text-red-700")

                        ui.label(
                            "Đăng xuất sẽ xóa toàn bộ phiên làm việc hiện tại của bạn."
                        ).classes("text-sm text-red-600 mb-3")

                        ui.button(
                            "Đăng Xuất Ngay",
                            icon="logout",
                            on_click=_confirm_logout,
                        ).classes(
                            "bg-red-600 text-white font-bold rounded-xl px-6 w-full shadow hover:bg-red-700 transition-all"
                        ).props("no-caps")


def _info_row(label: str, value: str, icon: str):
    """Render a labeled info row with icon."""
    with ui.row().classes("w-full items-start gap-3 py-2 border-b border-gray-50"):
        ui.icon(icon, size="1.2rem").classes("text-indigo-400 mt-0.5 shrink-0")
        with ui.column().classes("gap-0 flex-1"):
            ui.label(label).classes("text-xs text-gray-400 font-semibold uppercase tracking-wide")
            ui.label(value).classes("text-sm text-gray-700 font-medium mt-0.5")


def _quick_link(label: str, icon: str, route: str, color: str):
    """Render a clickable quick-link row."""
    with ui.row().classes(
        f"w-full items-center gap-3 px-3 py-2 rounded-xl cursor-pointer "
        f"hover:bg-{color}-50 transition-colors group"
    ).on("click", lambda r=route: ui.navigate.to(r)):
        ui.icon(icon, size="1.2rem").classes(f"text-{color}-500")
        ui.label(label).classes(f"text-sm font-medium text-gray-700 group-hover:text-{color}-700")
        ui.icon("chevron_right", size="1rem").classes("text-gray-300 ml-auto")


def _confirm_logout():
    """Show confirmation dialog before logout."""
    with ui.dialog() as dlg, ui.card().classes("rounded-2xl p-6 shadow-2xl w-80"):
        with ui.column().classes("w-full items-center gap-4"):
            ui.icon("logout", size="3rem").classes("text-red-500")
            ui.label("Xác nhận đăng xuất?").classes("text-xl font-bold text-gray-800")
            ui.label(
                "Bạn sẽ được chuyển về trang đăng nhập. Phiên làm việc hiện tại sẽ bị xóa."
            ).classes("text-sm text-gray-500 text-center")

            with ui.row().classes("w-full gap-3 mt-2"):
                ui.button("Hủy", on_click=dlg.close).classes(
                    "flex-1 border border-gray-300 text-gray-600 rounded-xl font-semibold"
                ).props("no-caps flat")
                ui.button("Đăng Xuất", icon="logout", on_click=logout_user).classes(
                    "flex-1 bg-red-600 text-white rounded-xl font-bold shadow"
                ).props("no-caps")

    dlg.open()
