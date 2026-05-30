"""
Trang quản lý đơn vị cứu hộ – dành cho Quản trị viên (Admin).
"""
from nicegui import ui
from typing import Optional, Dict, Any, List

from core.auth import require_admin_auth
from components.page_layout import page_layout
from services.admin_api import get_companies, update_company_status


def create_companies_page():

    @ui.page('/admin/companies')
    async def companies_page():
        if not require_admin_auth():
            return

        with page_layout("/admin/companies", title="Quản Lý Đơn Vị"):
            
            with ui.row().classes("w-full items-center justify-between mb-4"):
                with ui.column().classes("gap-0"):
                    ui.label("🏢 Quản Lý Đơn Vị Cứu Hộ").classes("text-3xl font-bold text-gray-800")
                    ui.label("Duyệt và kiểm soát các đối tác cứu hộ trên hệ thống").classes("text-gray-500")
                
                refresh_btn = ui.button(icon="refresh", on_click=lambda: _load_data()).props("flat round color=indigo")

            # Bộ lọc
            with ui.row().classes("w-full items-center gap-4 bg-white p-4 rounded-2xl shadow-sm border border-gray-100 mb-6"):
                search_input = ui.input(placeholder="Tìm tên công ty, hotline, số giấy phép...", on_change=lambda: _load_data()).classes("flex-1").props("outlined dense clearable icon=search")
                
                ui.label("Trạng thái:").classes("text-gray-600 font-medium")
                status_filter = ui.select(
                    options={'all': 'Tất cả', 'active': 'Đang hoạt động', 'pending': 'Chờ duyệt', 'suspended': 'Đang tạm dừng'},
                    value='all',
                    on_change=lambda: _load_data()
                ).classes("w-56").props("outlined dense")

            # Container
            container = ui.column().classes("w-full gap-4")

        # ── Logic ────────────────────────────────────────────────────────
        
        async def _load_data():
            refresh_btn.props("loading")
            container.clear()
            try:
                all_comps = await get_companies()
                
                # Filter
                filtered = all_comps
                if status_filter.value != 'all':
                    filtered = [c for c in filtered if c['status'] == status_filter.value]
                if search_input.value:
                    s = search_input.value.lower()
                    filtered = [c for c in filtered if s in c['company_name'].lower() or s in (c.get('hotline') or '').lower()]

                with container:
                    if not filtered:
                        ui.label("Không tìm thấy đơn vị nào").classes("w-full text-center py-10 text-gray-400 italic")
                    else:
                        for c in filtered:
                            _render_company_card(c)
            except Exception as e:
                ui.notify(f"Lỗi: {e}", type="negative")
            finally:
                refresh_btn.props(remove="loading")

        def _render_company_card(c):
            status_map = {
                "active": ("Hoạt động", "green"),
                "pending": ("Chờ duyệt", "amber"),
                "suspended": ("Tạm dừng", "red"),
            }
            label, color = status_map.get(c['status'], (c['status'], "gray"))

            with ui.card().classes("w-full rounded-2xl p-6 shadow-sm border border-gray-100 hover:border-indigo-200 transition-all"):
                with ui.row().classes("w-full items-start justify-between"):
                    with ui.row().classes("items-center gap-4"):
                        ui.avatar(icon="business").classes(f"bg-{color}-100 text-{color}-600")
                        with ui.column().classes("gap-0"):
                            ui.label(c['company_name']).classes("font-bold text-xl text-gray-800")
                            ui.label(f"GPKD: {c.get('license_number', 'N/A')}").classes("text-xs text-gray-400 font-mono")
                    
                    with ui.column().classes("items-end gap-2"):
                        ui.label(label).classes(f"text-[10px] font-bold uppercase px-3 py-1 rounded-full bg-{color}-50 text-{color}-600 border border-{color}-100")
                        with ui.row().classes("items-center gap-1"):
                            ui.label(f"{c.get('rating_avg', 0)}").classes("font-bold text-amber-500")
                            ui.icon("star", color="amber", size="1rem")

                with ui.row().classes("mt-4 gap-10"):
                    with ui.column().classes("gap-1"):
                        ui.label("Hotline").classes("text-[10px] text-gray-400 uppercase font-bold")
                        ui.label(c.get('hotline', 'N/A')).classes("font-bold text-indigo-600")
                    
                    with ui.column().classes("gap-1"):
                        ui.label("Địa chỉ").classes("text-[10px] text-gray-400 uppercase font-bold")
                        ui.label(c.get('address', 'N/A')).classes("text-sm text-gray-600 max-w-md")
                    
                    with ui.column().classes("gap-1"):
                        ui.label("Phạm vi phục vụ").classes("text-[10px] text-gray-400 uppercase font-bold")
                        ui.label(f"{c.get('service_radius_km', 0)} km").classes("text-sm text-gray-600")

                ui.separator().classes("my-4 opacity-50")
                
                with ui.row().classes("w-full justify-end gap-2"):
                    if c['status'] == 'pending':
                        ui.button("DUYỆT ĐƠN VỊ", icon="check", on_click=lambda: _update_status(c, 'active')).classes("bg-green-600 text-white font-bold rounded-xl px-6")
                    
                    if c['status'] == 'active':
                        ui.button("TẠM DỪNG", icon="block", on_click=lambda: _update_status(c, 'suspended')).classes("bg-red-50 text-red-600 font-bold rounded-xl px-6").props("flat")
                    
                    if c['status'] == 'suspended':
                        ui.button("KÍCH HOẠT LẠI", icon="play_arrow", on_click=lambda: _update_status(c, 'active')).classes("bg-green-50 text-green-600 font-bold rounded-xl px-6").props("flat")

        async def _update_status(company, status):
            try:
                await update_company_status(company['id'], status)
                ui.notify(f"Đã cập nhật trạng thái: {status}", type="info")
                await _load_data()
            except Exception as e:
                ui.notify(f"Lỗi: {e}", type="negative")

        await _load_data()
