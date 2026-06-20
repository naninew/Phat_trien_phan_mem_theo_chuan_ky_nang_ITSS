"""
Trang quản lý người dùng – dành cho Quản trị viên (Admin).
"""
from nicegui import ui
import math
from typing import Optional, Dict, Any, List

from core.auth import require_admin_auth
from components.page_layout import page_layout
from services.admin_api import get_users, update_user, delete_user
from services.api_client import api_client

def create_users_page():

    @ui.page('/admin/users')
    async def users_page():
        if not require_admin_auth():
            return

        # State cho phân trang
        state = {'page': 1}

        with page_layout("/admin/users", title="Quản Lý Khách Hàng"):
            
            with ui.row().classes("w-full items-center justify-between mb-4"):
                with ui.column().classes("gap-0"):
                    ui.label("👥 Quản Lý Khách Hàng").classes("text-3xl font-bold text-gray-800")
                    ui.label("Kiểm soát tất cả tài khoản khách hàng trong hệ thống").classes("text-gray-500")
                
                refresh_btn = ui.button(icon="refresh", on_click=lambda: _load_data()).props("flat round color=indigo")

            # Bộ lọc & Tìm kiếm
            with ui.row().classes("w-full items-center gap-4 bg-white p-4 rounded-2xl shadow-sm border border-gray-100 mb-6"):
                search_input = ui.input(placeholder="Tìm tên, username, email, sđt...", on_change=lambda: _load_data()).classes("flex-1").props("outlined dense clearable icon=search")
                
                ui.label("Trạng thái:").classes("text-gray-600 font-medium")
                status_filter = ui.select(
                    options={'all': 'Tất cả', 'ACTIVE': 'Hoạt động', 'INACTIVE': 'Chưa kích hoạt', 'SUSPENDED': 'Bị khóa'},
                    value='all',
                    on_change=lambda: _load_data()
                ).classes("w-40").props("outlined dense")
                
                ui.label("Vai trò:").classes("text-gray-600 font-medium")
                role_filter = ui.select(
                    options={'all': 'Tất cả', 'customer': 'Khách hàng', 'company_staff': 'Công ty', 'admin': 'Quản trị'},
                    value='customer',
                    on_change=lambda: _load_data()
                ).classes("w-40").props("outlined dense")

            # Container danh sách
            users_container = ui.column().classes("w-full gap-4")
            pagination_container = ui.row().classes("w-full justify-center mt-4")

        # ── Logic ────────────────────────────────────────────────────────
        
        async def _load_data(page=None):
            if page is not None:
                state['page'] = page
                
            refresh_btn.props("loading")
            users_container.clear()
            pagination_container.clear()
            
            try:
                response = await get_users(
                    role_filter=role_filter.value,
                    status_filter=status_filter.value,
                    search=search_input.value,
                    page=state['page'],
                    page_size=20
                )
                
                users = response.get("items", [])
                total = response.get("total", 0)
                current_page = response.get("page", 1)

                with users_container:
                    if not users:
                        ui.label("Không tìm thấy người dùng nào").classes("w-full text-center py-10 text-gray-400 italic")
                    else:
                        for u in users:
                            _render_user_card(u)
                            
                with pagination_container:
                    if total > 20:
                        max_page = math.ceil(total / 20)
                        ui.pagination(1, max_page, value=current_page, on_change=lambda e: _load_data(e.value))
                        
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
            req_count = u.get('request_count', 0)

            with ui.card().classes("w-full rounded-2xl p-6 shadow-sm border border-gray-100 hover:border-indigo-200 transition-all cursor-pointer").on('click', lambda: ui.navigate.to(f"/admin/users/{u['id']}")):
                with ui.row().classes("w-full items-center justify-between"):
                    with ui.row().classes("items-center gap-4"):
                        ui.avatar(icon="person").classes(f"bg-{color}-100 text-{color}-600")
                        with ui.column().classes("gap-0"):
                            ui.label(u['full_name']).classes("font-bold text-xl text-gray-800")
                            ui.label(f"@{u['username']} • {u['email']}").classes("text-sm text-gray-500")
                    
                    with ui.row().classes("items-center gap-3"):
                        ui.label(role_label).classes(f"text-xs font-bold uppercase px-3 py-1 rounded-full bg-{color}-50 text-{color}-600 border border-{color}-100")
                        ui.label(status).classes(f"text-xs font-bold uppercase px-3 py-1 rounded-full bg-{s_color}-50 text-{s_color}-600 border border-{s_color}-100")
                        
                        # Badge số yêu cầu
                        ui.badge(f"{req_count} yêu cầu", color="indigo").props("outline")

                        # More actions (stopPropagation để không trigger click của card)
                        with ui.button(icon="more_vert").props("flat round dense").on('click.stop', lambda: None):
                            with ui.menu():
                                ui.menu_item("Đổi vai trò", on_click=lambda: _show_role_dialog(u))
                                ui.separator()
                                if status == "ACTIVE":
                                    ui.menu_item("Khóa tài khoản", on_click=lambda: _show_suspend_dialog(u)).classes("text-red-500")
                                elif status == "SUSPENDED":
                                    ui.menu_item("Mở khóa", on_click=lambda: _show_activate_dialog(u)).classes("text-green-500")
                                ui.separator()
                                ui.menu_item("Xóa tài khoản", on_click=lambda: _confirm_delete(u)).classes("text-red-500")

                with ui.row().classes("mt-4 gap-6 text-sm text-gray-500"):
                    with ui.row().classes("items-center gap-1"):
                        ui.icon("phone", size="1rem")
                        ui.label(u.get('phone', 'N/A'))
                    with ui.row().classes("items-center gap-1"):
                        ui.icon("event", size="1rem")
                        ui.label(f"Tham gia: {u.get('created_at', 'N/A')[:10]}")

        async def _show_suspend_dialog(user):
            with ui.dialog() as dialog, ui.card().classes("p-6 rounded-2xl w-96"):
                ui.label(f"Khóa tài khoản @{user['username']}").classes("text-xl font-bold text-red-600 mb-2")
                reason_input = ui.textarea("Lý do khóa (Bắt buộc)").classes("w-full").props("outlined autofocus")
                
                error_label = ui.label().classes("text-red-500 text-sm mt-2")
                
                with ui.row().classes("w-full justify-end gap-3 mt-4"):
                    ui.button("Hủy", on_click=dialog.close).props("flat")
                    
                    async def do_suspend():
                        reason = reason_input.value.strip() if reason_input.value else ""
                        if len(reason) < 10:
                            error_label.text = "Vui lòng nhập lý do (ít nhất 10 ký tự)"
                            return
                        try:
                            await api_client.put(f"/admin/users/{user['id']}/suspend", data={"reason": reason})
                            ui.notify(f"Đã khóa tài khoản @{user['username']}", type="positive")
                            dialog.close()
                            await _load_data()
                        except Exception as e:
                            error_label.text = str(e)
                            
                    ui.button("Khóa", on_click=do_suspend).classes("bg-red-600 text-white")
            dialog.open()

        async def _show_activate_dialog(user):
            with ui.dialog() as dialog, ui.card().classes("p-6 rounded-2xl"):
                ui.label(f"Mở khóa tài khoản @{user['username']}?").classes("text-xl font-bold mb-4")
                with ui.row().classes("w-full justify-end gap-3 mt-4"):
                    ui.button("Hủy", on_click=dialog.close).props("flat")
                    async def do_activate():
                        try:
                            await api_client.put(f"/admin/users/{user['id']}/activate")
                            ui.notify(f"Đã mở khóa tài khoản @{user['username']}", type="positive")
                            dialog.close()
                            await _load_data()
                        except Exception as e:
                            ui.notify(f"Lỗi: {e}", type="negative")
                    ui.button("Mở khóa", on_click=do_activate).classes("bg-green-600 text-white")
            dialog.open()

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
