"""
Service Management - NiceGUI
"""
from nicegui import ui
from typing import Dict, Any, List
from core.auth import require_role
from components.page_layout import page_layout
from services.rescue_api import get_company_services, add_company_service, update_company_service, delete_company_service

def create_services_management_page():
    """Register /company/services route."""

    @ui.page('/company/services')
    async def services_page():
        if not require_role("company_staff"):
            return

        with page_layout("/company/services", title="Quản Lý Dịch Vụ"):
            
            with ui.row().classes("w-full items-center justify-between mb-8"):
                with ui.column().classes("gap-0"):
                    ui.label("🛠️ Danh Mục Dịch Vụ").classes("text-3xl font-bold font-outfit text-primary")
                    ui.label("Thiết lập loại hình cứu hộ và báo giá cơ bản").classes("opacity-60")
                
                ui.button("THÊM DỊCH VỤ", icon="add_task", on_click=lambda: _show_add_dialog()) \
                    .classes("bg-primary text-white px-6 py-3 rounded-2xl shadow-lg font-bold")

            services_container = ui.row().classes("w-full gap-6 flex-wrap")

            # --- Logic ---
            async def refresh_services():
                services_container.clear()
                services = await get_company_services()
                with services_container:
                    if not services:
                        ui.label("Chưa thiết lập dịch vụ nào.").classes("italic opacity-50 py-10 w-full text-center")
                    for s in services:
                        _render_service_card(s)

            def _render_service_card(s):
                is_active = s.get('is_active', True)
                with ui.card().classes(f"w-80 rounded-3xl p-6 border border-surface-variant/30 {'opacity-60 bg-gray-50' if not is_active else 'hover:border-primary/50'} transition-all"):
                    with ui.row().classes("w-full justify-between items-start mb-4"):
                        ui.label(s['service_name']).classes("text-xl font-bold font-outfit")
                        ui.switch(value=is_active, on_change=lambda e: _update_s(s['id'], s['base_price'], e.value)).props("dense")
                    
                    with ui.row().classes("w-full items-end gap-1 mb-6"):
                        ui.label(f"{s['base_price']:,.0f}").classes("text-3xl font-bold text-primary font-outfit")
                        ui.label("VNĐ / km").classes("text-xs opacity-50 mb-1")
                    
                    with ui.row().classes("w-full justify-end gap-2"):
                        ui.button(icon="edit", on_click=lambda: _show_edit_dialog(s)).props("flat round color=primary")
                        ui.button(icon="delete", on_click=lambda: _delete_s(s['id'])).props("flat round color=error")

            def _show_add_dialog():
                with ui.dialog() as d, ui.card().classes("p-8 rounded-3xl w-[450px]"):
                    ui.label("Thiết lập dịch vụ mới").classes("text-2xl font-bold mb-6 font-outfit text-primary")
                    name = ui.input("Tên dịch vụ (VD: Kéo xe ô tô)").classes("w-full mb-4").props("outlined rounded")
                    price = ui.number("Giá cơ bản (VNĐ)", value=100000).classes("w-full mb-8").props("outlined rounded")
                    
                    with ui.row().classes("w-full justify-end gap-3"):
                        ui.button("HỦY", on_click=d.close).props("flat")
                        async def submit():
                            if await add_company_service(name.value, price.value):
                                ui.notify("Đã thêm dịch vụ", type="positive")
                                d.close()
                                await refresh_services()
                        ui.button("LƯU", on_click=submit).classes("bg-primary text-white px-8 rounded-xl font-bold")
                d.open()

            def _show_edit_dialog(s):
                with ui.dialog() as d, ui.card().classes("p-8 rounded-3xl w-[400px]"):
                    ui.label(f"Sửa {s['service_name']}").classes("text-2xl font-bold mb-6 font-outfit text-primary")
                    price = ui.number("Giá cơ bản (VNĐ)", value=s['base_price']).classes("w-full mb-8").props("outlined rounded")
                    
                    with ui.row().classes("w-full justify-end gap-3"):
                        ui.button("HỦY", on_click=d.close).props("flat")
                        async def submit():
                            if await update_company_service(s['id'], price.value, s.get('is_active', True)):
                                ui.notify("Đã cập nhật giá")
                                d.close()
                                await refresh_services()
                        ui.button("CẬP NHẬT", on_click=submit).classes("bg-primary text-white px-8 rounded-xl")
                d.open()

            async def _update_s(sid, price, active):
                if await update_company_service(sid, price, active):
                    ui.notify("Trạng thái đã cập nhật")
                    await refresh_services()

            async def _delete_s(sid):
                if await delete_company_service(sid):
                    ui.notify("Đã xóa dịch vụ")
                    await refresh_services()

            await refresh_services()
