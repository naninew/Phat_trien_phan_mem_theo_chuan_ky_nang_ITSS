"""
Trang quản lý người dùng – dành cho Quản trị viên (Admin).
"""
from nicegui import ui
from typing import Optional, Dict, Any, List

from core.auth import require_role
from components.page_layout import page_layout
from services.admin_api import get_users, update_user, delete_user


def create_users_page():

    @ui.page('/admin/users')
    async def users_page():
        if not require_role("admin"):
            return

        with page_layout("/admin/users", title="Quản Lý Người Dùng"):
            
            with ui.row().classes("w-full items-center justify-between mb-4"):
                with ui.column().classes("gap-0"):
                    ui.label("👥 Quản Lý Người Dùng").classes("text-3xl font-bold text-gray-800")
                    ui.label("Kiểm soát tất cả tài khoản trong hệ thống").classes("text-gray-500")
                
                refresh_btn = ui.button(icon="refresh", on_click=lambda: _load_data()).props("flat round color=indigo")

            # Bộ lọc & Tìm kiếm
            with ui.row().classes("w-full items-center gap-4 bg-white p-4 rounded-2xl shadow-sm border border-gray-100 mb-6"):
                search_input = ui.input(placeholder="Tìm tên, username, email...", on_change=lambda: _load_data()).classes("flex-1").props("outlined dense clearable icon=search")
                
                ui.label("Vai trò:").classes("text-gray-600 font-medium")
                role_filter = ui.select(
                    options={'all': 'Tất cả', 'customer': 'Khách hàng', 'company_staff': 'Công ty', 'admin': 'Quản trị'},
                    value='all',
                    on_change=lambda: _load_data()
                ).classes("w-48").props("outlined dense")

            # Container danh sách
            users_container = ui.column().classes("w-full gap-4")

        # ── Logic ────────────────────────────────────────────────────────
        
        async def _load_data():
            refresh_btn.props("loading")
            users_container.clear()
            try:
                all_users = await get_users()
                
                # Filtering
                filtered = all_users
                if role_filter.value != 'all':
                    filtered = [u for u in filtered if u['role'] == role_filter.value]
                if search_input.value:
                    s = search_input.value.lower()
                    filtered = [u for u in filtered if s in u['full_name'].lower() or s in u['username'].lower() or s in u['email'].lower()]

                with users_container:
                    if not filtered:
                        ui.label("Không tìm thấy người dùng nào").classes("w-full text-center py-10 text-gray-400 italic")
                    else:
                        for u in filtered:
                            _render_user_card(u)
            except Exception as e:
                ui.notify(f"Lỗi: {e}", type="negative")
            finally:
                refresh_btn.props(remove="loading")

        def _render_user_card(u):
            role_map = {
                "admin": ("Quản trị", "red"),
                "company_staff": ("Công ty", "green"),
                "customer": ("Khách hàng", "blue"),
            }
            status_colors = {
                "ACTIVE": "green",
                "INACTIVE": "amber",
                "SUSPENDED": "red",
            }
            role_label, color = role_map.get(u['role'], (u['role'], "gray"))
            status = u.get('status', 'ACTIVE')
            s_color = status_colors.get(status, "gray")

            with ui.card().classes("w-full rounded-2xl p-6 shadow-sm border border-gray-100 hover:border-indigo-200 transition-all"):
                with ui.row().classes("w-full items-center justify-between"):
                    with ui.row().classes("items-center gap-4"):
                        ui.avatar(icon="person").classes(f"bg-{color}-100 text-{color}-600")
                        with ui.column().classes("gap-0"):
                            ui.label(u['full_name']).classes("font-bold text-lg text-gray-800")
                            ui.label(f"@{u['username']} • {u['email']}").classes("text-xs text-gray-500")
                    
                    with ui.row().classes("items-center gap-3"):
                        ui.label(role_label).classes(f"text-[10px] font-bold uppercase px-3 py-1 rounded-full bg-{color}-50 text-{color}-600 border border-{color}-100")
                        ui.label(status).classes(f"text-[10px] font-bold uppercase px-3 py-1 rounded-full bg-{s_color}-50 text-{s_color}-600 border border-{s_color}-100")
                        
                        # Active/Suspended toggle
                        is_active = status == "ACTIVE"
                        ui.switch(value=is_active, on_change=lambda e: _toggle_status(u, e.value)).props("dense color=green")

                        # More actions
                        with ui.button(icon="more_vert").props("flat round dense") as more_btn:
                            with ui.menu():
                                ui.menu_item("Đổi vai trò", on_click=lambda: _show_role_dialog(u))
                                ui.separator()
                                ui.menu_item("Xóa tài khoản", on_click=lambda: _confirm_delete(u)).classes("text-red-500")

                with ui.row().classes("mt-4 gap-6 text-sm text-gray-500"):
                    with ui.row().classes("items-center gap-1"):
                        ui.icon("phone", size="1rem")
                        ui.label(u.get('phone', 'N/A'))
                    with ui.row().classes("items-center gap-1"):
                        ui.icon("event", size="1rem")
                        ui.label(f"Tham gia: {u.get('created_at', 'N/A')[:10]}")

        async def _toggle_status(user, val):
            try:
                new_status = "ACTIVE" if val else "SUSPENDED"
                await update_user(user['id'], {"status": new_status})
                ui.notify(f"Đã chuyển trạng thái @{user['username']} sang {new_status}", type="info")
                await _load_data()
            except Exception as e:
                ui.notify(f"Lỗi: {e}", type="negative")

        async def _show_role_dialog(user):
            with ui.dialog() as dialog, ui.card().classes("p-6 rounded-2xl"):
                ui.label(f"Thay đổi vai trò cho @{user['username']}").classes("text-lg font-bold mb-4")
                new_role = ui.select(
                    options={'customer': 'Khách hàng', 'company_staff': 'Công ty', 'admin': 'Quản trị'},
                    value=user['role']
                ).classes("w-full").props("outlined")
                
                with ui.row().classes("w-full justify-end gap-3 mt-6"):
                    ui.button("Đóng", on_click=dialog.close).props("flat")
                    async def do_update():
                        await update_user(user['id'], {"role": new_role.value})
                        ui.notify("Đã cập nhật vai trò", type="positive")
                        dialog.close()
                        await _load_data()
                    ui.button("Cập nhật", on_click=do_update).classes("bg-indigo-600 text-white")
            dialog.open()

        async def _confirm_delete(user):
            with ui.dialog() as dialog, ui.card().classes("p-6 rounded-2xl"):
                ui.label("Xác nhận xóa tài khoản?").classes("text-xl font-bold")
                ui.label(f"Xóa vĩnh viễn tài khoản @{user['username']}. Hành động này không thể hoàn tác!").classes("text-red-500 mb-6")
                with ui.row().classes("w-full justify-end gap-3"):
                    ui.button("Hủy", on_click=dialog.close).props("flat")
                    async def do_del():
                        await delete_user(user['id'])
                        ui.notify("Đã xóa tài khoản", type="info")
                        dialog.close()
                        await _load_data()
                    ui.button("XÓA NGAY", on_click=do_del).classes("bg-red-600 text-white font-bold")
            dialog.open()

        await _load_data()
