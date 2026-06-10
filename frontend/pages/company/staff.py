"""
Staff Management - NiceGUI
Redesigned UI/UX for Company Staff Management
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

        with page_layout("/company/staff", title=""):
            
            # --- HEADER SECTION ---
            with ui.row().classes("w-full items-center justify-between mb-8"):
                with ui.column().classes("gap-1"):
                    ui.label("Quản Lý Nhân Sự").classes("text-3xl font-extrabold font-outfit text-slate-800 tracking-tight")
                    ui.label("Quản lý danh sách, trạng thái và thông tin nhân viên cứu hộ").classes("text-slate-500 text-sm")
                
                ui.button("THÊM NHÂN VIÊN", icon="person_add", on_click=lambda: _show_add_dialog()) \
                    .classes("bg-blue-600 text-white px-6 py-3 rounded-xl shadow-md font-bold hover:bg-blue-700 transition-colors").props('unelevated')

            # --- STATISTICS SECTION ---
            stats_row = ui.row().classes("w-full gap-4 mb-8")
            
            # --- MAIN CONTAINER ---
            staff_container = ui.row().classes("w-full gap-6")

            # --- LOGIC ---
            async def refresh_staff():
                staff_container.clear()
                stats_row.clear()
                
                try:
                    staff = await get_company_staff()
                    
                    # Update stats
                    total_staff = len(staff)
                    available_staff = sum(1 for s in staff if s['status'] == 'AVAILABLE')
                    busy_staff = sum(1 for s in staff if s['status'] == 'BUSY')
                    
                    with stats_row:
                        _render_stat_card("Tổng nhân viên", total_staff, "group", "bg-blue-50 text-blue-600")
                        _render_stat_card("Sẵn sàng", available_staff, "check_circle", "bg-emerald-50 text-emerald-600")
                        _render_stat_card("Đang làm nhiệm vụ", busy_staff, "engineering", "bg-amber-50 text-amber-600")
                    
                    with staff_container:
                        if not staff:
                            _render_empty_state()
                        else:
                            for s in staff:
                                _render_staff_card(s)
                                
                except Exception as e:
                    ui.notify(f"Lỗi tải danh sách: {e}", type="negative")

            def _render_stat_card(title, value, icon, color_classes):
                with ui.card().classes(f"flex-1 rounded-2xl p-5 border border-gray-100 shadow-sm {color_classes} bg-opacity-50"):
                    with ui.row().classes("items-center justify-between w-full"):
                        with ui.column().classes("gap-1"):
                            ui.label(title).classes("text-sm font-semibold opacity-80")
                            ui.label(str(value)).classes("text-3xl font-extrabold")
                        ui.icon(icon, size="2.5rem").classes("opacity-80")

            def _render_empty_state():
                with ui.column().classes("w-full items-center justify-center py-20 bg-gray-50/50 rounded-[32px] border border-dashed border-gray-200"):
                    ui.icon("group_off", size="4rem").classes("text-gray-300 mb-4")
                    ui.label("Chưa có nhân viên nào").classes("text-xl font-bold text-gray-700")
                    ui.label("Hãy thêm nhân viên đầu tiên để bắt đầu quản lý đội ngũ cứu hộ").classes("text-gray-500 mb-6")
                    ui.button("Thêm nhân viên ngay", icon="add", on_click=lambda: _show_add_dialog()) \
                        .classes("bg-white border border-gray-300 text-slate-700 px-6 py-2 rounded-xl font-semibold shadow-sm hover:bg-gray-50")

            def _render_staff_card(s):
                status_config = {
                    "AVAILABLE": ("Sẵn sàng", "bg-emerald-100 text-emerald-700 border-emerald-200"),
                    "BUSY": ("Đang nhiệm vụ", "bg-amber-100 text-amber-700 border-amber-200"),
                }
                label, style = status_config.get(s['status'], (s['status'], "bg-gray-100 text-gray-700 border-gray-200"))

                with ui.card().classes("w-72 rounded-2xl p-0 border border-gray-200 shadow-sm hover:shadow-md transition-all overflow-hidden"):
                    # Top section with avatar
                    with ui.column().classes("w-full p-6 items-center gap-3 bg-slate-50/50 relative"):
                        ui.avatar(icon="person", size="4rem", color="blue-1", text_color="blue-8").classes("shadow-sm")
                        
                        with ui.column().classes("items-center gap-1 w-full"):
                            ui.label(f"Nhân viên #{s['id']}").classes("text-lg font-bold text-slate-800")
                            ui.label(f"Trình độ: {s['skill_level']}").classes("text-xs font-medium text-slate-500 bg-white border border-gray-200 px-3 py-1 rounded-full")
                            
                        # Status Badge positioned at top right using ui.label instead of ui.badge to avoid Quasar default colors
                        ui.label(label).classes(f"absolute top-4 right-4 rounded-full px-3 py-1 font-bold text-[10px] uppercase tracking-wider border {style}")
                    
                    ui.separator().classes("bg-gray-100")
                    
                    # Bottom section with actions
                    with ui.row().classes("w-full p-3 justify-center gap-4 bg-white"):
                        if s['status'] != 'AVAILABLE':
                            ui.button(icon="check_circle", on_click=lambda: _update_s(s['id'], status='AVAILABLE')).props("flat round color=positive").tooltip("Đặt: Sẵn sàng")
                        if s['status'] != 'BUSY':
                            ui.button(icon="engineering", on_click=lambda: _update_s(s['id'], status='BUSY')).props("flat round color=warning").tooltip("Đặt: Đang bận")
                        
                        ui.separator().props('vertical').classes("mx-1 h-8 self-center")
                        ui.button(icon="delete_outline", on_click=lambda: _confirm_delete(s['id'])).props("flat round color=negative").tooltip("Xóa nhân viên")

            def _show_add_dialog():
                with ui.dialog() as d, ui.card().classes("p-8 rounded-[24px] w-[420px] shadow-2xl"):
                    with ui.row().classes("w-full justify-between items-center mb-6"):
                        ui.label("Thêm nhân viên mới").classes("text-2xl font-bold font-outfit text-slate-800")
                        ui.button(icon="close", on_click=d.close).props("flat round").classes("text-gray-400 hover:bg-gray-100")
                        
                    level = ui.select(["Junior", "Senior", "Expert"], label="Trình độ", value="Junior").classes("w-full mb-8").props("outlined rounded")
                    
                    with ui.row().classes("w-full justify-end gap-3"):
                        ui.button("Hủy", on_click=d.close).props("flat").classes("text-slate-600 font-semibold px-4 py-2 hover:bg-gray-50 rounded-xl")
                        async def submit():
                            try:
                                if await add_company_staff(level.value):
                                    ui.notify("Đã thêm nhân viên thành công", type="positive")
                                    d.close()
                                    await refresh_staff()
                            except Exception as e:
                                ui.notify(f"Lỗi: {e}", type="negative")
                        ui.button("Lưu Nhập", on_click=submit).classes("bg-blue-600 text-white font-bold px-6 py-2 rounded-xl shadow-sm hover:bg-blue-700")
                d.open()

            def _confirm_delete(sid):
                with ui.dialog() as dlg, ui.card().classes('rounded-[24px] p-8 shadow-2xl w-[400px]'):
                    with ui.column().classes('w-full items-center gap-3'):
                        ui.icon('warning', size='3.5rem').classes('text-red-500 mb-2')
                        ui.label('Xác nhận xóa?').classes('text-2xl font-bold text-slate-800 font-outfit')
                        ui.label(
                            f'Bạn có chắc chắn muốn xóa nhân viên #{sid}? Hành động này không thể hoàn tác.'
                        ).classes('text-sm text-gray-500 text-center mb-4 leading-relaxed')
                        with ui.row().classes('w-full gap-3'):
                            ui.button('Hủy', on_click=dlg.close).props('no-caps flat').classes(
                                'flex-1 border border-gray-200 hover:bg-gray-50 text-slate-600 rounded-xl font-bold py-3 transition-colors'
                            )
                            async def do_delete():
                                try:
                                    if await delete_company_staff(sid):
                                        ui.notify("Đã xóa nhân viên", type="info")
                                        dlg.close()
                                        await refresh_staff()
                                except Exception as e:
                                    ui.notify(f"Lỗi: {e}", type="negative")
                            ui.button('Xóa', icon='delete', on_click=do_delete).props('no-caps').classes(
                                'flex-1 bg-red-600 hover:bg-red-700 text-white rounded-xl font-bold py-3 shadow-md transition-colors'
                            )
                dlg.open()

            async def _update_s(sid, **kwargs):
                try:
                    if await update_company_staff(sid, **kwargs):
                        ui.notify("Cập nhật trạng thái thành công", type="positive")
                        await refresh_staff()
                except Exception as e:
                    ui.notify(f"Lỗi: {e}", type="negative")

            await refresh_staff()
