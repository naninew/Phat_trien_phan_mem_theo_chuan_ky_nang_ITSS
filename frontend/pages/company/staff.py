"""
Staff Management - NiceGUI
"""
from nicegui import ui
from typing import Dict, Any, List
from core.auth import require_role
from components.page_layout import page_layout
from services.rescue_api import get_company_staff, add_company_staff, update_company_staff, delete_company_staff

def create_staff_page():
    """Register /company/staff route."""

    @ui.page('/company/staff')
    async def staff_page():
        if not require_role("company_staff"):
            return

        with page_layout("/company/staff", title="Quản Lý Nhân Sự"):
            
            with ui.row().classes("w-full items-center justify-between mb-8"):
                with ui.column().classes("gap-0"):
                    ui.label("👥 Đội Ngũ Nhân Viên").classes("text-3xl font-bold font-outfit text-primary")
                    ui.label("Quản lý danh sách và trạng thái trực ca").classes("opacity-60")
                
                ui.button("THÊM NHÂN VIÊN", icon="person_add", on_click=lambda: _show_add_dialog()) \
                    .classes("bg-primary text-white px-6 py-3 rounded-2xl shadow-lg font-bold")

            staff_container = ui.row().classes("w-full gap-6")

            # --- Logic ---
            async def refresh_staff():
                staff_container.clear()
                try:
                    staff = await get_company_staff()
                    with staff_container:
                        if not staff:
                            ui.label("Chưa có nhân viên nào.").classes("italic opacity-50 py-10")
                        for s in staff:
                            _render_staff_card(s)
                except Exception as e:
                    ui.notify(f"Lỗi tải danh sách: {e}", type="negative")

            def _render_staff_card(s):
                status_colors = {
                    "AVAILABLE": ("Sẵn sàng", "bg-green-100 text-green-700"),
                    "BUSY": ("Đang làm nhiệm vụ", "bg-amber-100 text-amber-700"),
                }
                label, style = status_colors.get(s['status'], (s['status'], "bg-gray-100 text-gray-700"))

                with ui.card().classes("w-64 rounded-3xl p-6 border border-surface-variant/30 hover:border-primary/50 transition-all"):
                    with ui.column().classes("items-center w-full gap-4"):
                        ui.avatar(icon="person", size="xl").classes("bg-primary/10 text-primary")
                        with ui.column().classes("items-center gap-0"):
                            ui.label(f"Nhân viên #{s['id']}").classes("text-lg font-bold font-outfit")
                            ui.label(f"Trình độ: {s['skill_level']}").classes("text-xs opacity-50")
                        
                        ui.badge(label).classes(f"rounded-full px-4 py-1 {style}")
                    
                    ui.separator().classes("my-4")
                    
                    with ui.row().classes("w-full justify-center gap-2"):
                        with ui.button(icon="edit").props("flat round color=primary") as btn:
                            with ui.menu():
                                ui.menu_item("Đặt: Sẵn sàng", on_click=lambda: _update_s(s['id'], status='AVAILABLE'))
                                # BUSY thường do hệ thống gán, nhưng cho phép sửa tay nếu cần
                                ui.menu_item("Đặt: Đang bận", on_click=lambda: _update_s(s['id'], status='BUSY'))
                                ui.separator()
                                ui.menu_item("Xóa nhân viên", on_click=lambda: _delete_s(s['id']))

            def _show_add_dialog():
                with ui.dialog() as d, ui.card().classes("p-8 rounded-3xl w-[400px]"):
                    ui.label("Thêm nhân viên mới").classes("text-2xl font-bold mb-6 font-outfit text-primary")
                    level = ui.select(["Junior", "Senior", "Expert"], label="Trình độ", value="Junior").classes("w-full mb-8").props("outlined rounded")
                    
                    with ui.row().classes("w-full justify-end gap-3"):
                        ui.button("HỦY", on_click=d.close).props("flat")
                        async def submit():
                            try:
                                if await add_company_staff(level.value):
                                    ui.notify("Đã thêm nhân viên", type="positive")
                                    d.close()
                                    await refresh_staff()
                            except Exception as e:
                                ui.notify(f"Lỗi: {e}", type="negative")
                        ui.button("LƯU", on_click=submit).classes("bg-primary text-white px-8 rounded-xl")
                d.open()

            async def _update_s(sid, **kwargs):
                try:
                    if await update_company_staff(sid, **kwargs):
                        ui.notify("Cập nhật thành công")
                        await refresh_staff()
                except Exception as e:
                    ui.notify(f"Lỗi: {e}", type="negative")

            async def _delete_s(sid):
                try:
                    if await delete_company_staff(sid):
                        ui.notify("Đã xóa nhân viên")
                        await refresh_staff()
                except Exception as e:
                    ui.notify(f"Lỗi: {e}", type="negative")

            await refresh_staff()
