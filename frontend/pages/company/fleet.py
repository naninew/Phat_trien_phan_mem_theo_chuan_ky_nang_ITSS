"""
Trang quản lý đội xe – dành cho công ty.
"""
# pyrefly: ignore [missing-import]
from nicegui import ui
from typing import Optional, Dict, Any, List
from core.auth import require_role
from components.page_layout import page_layout
from services.rescue_api import get_my_vehicles, add_vehicle, update_vehicle_status, delete_vehicle, update_vehicle


def create_fleet_page():

    @ui.page('/company/fleet')
    async def fleet_page():
        if not require_role("company_staff"):
            return

        with page_layout("/company/fleet", title="Quản Lý Đội Xe"):
            
            with ui.row().classes("w-full items-center justify-between mb-4"):
                ui.label("Quản lý danh sách phương tiện và trạng thái sẵn sàng").classes("text-lg font-medium text-gray-500")
                
                ui.button("THÊM XE MỚI", icon="add", on_click=lambda: _show_add_dialog()).classes("bg-indigo-600 text-white font-bold rounded-xl px-6 py-3 shadow-lg hover:bg-indigo-700")

            # Danh sách xe
            fleet_container = ui.row().classes("w-full gap-6 flex-wrap")

        # ── Logic ────────────────────────────────────────────────────────
        
        async def _load_data():
            fleet_container.clear()
            try:
                vehicles = await get_my_vehicles()
                with fleet_container:
                    if not vehicles:
                        with ui.column().classes("w-full items-center py-20 bg-white rounded-3xl border border-dashed border-gray-300"):
                            ui.icon("no_transportation", size="5rem", color="gray-200")
                            ui.label("Chưa có phương tiện nào trong đội xe").classes("text-gray-400 text-lg")
                    else:
                        for v in vehicles:
                            _render_vehicle_card(v)
            except Exception as e:
                ui.notify(f"Lỗi: {e}", type="negative")

        def _render_vehicle_card(v):
            status_map = {
                "available": ("Sẵn sàng", "green", "check_circle"),
                "on_mission": ("Đang làm nhiệm vụ", "amber", "local_shipping"),
                "maintenance": ("Bảo trì", "red", "build"),
            }
            label, color, icon = status_map.get(v['status'], (v['status'], "gray", "help"))

            with ui.card().classes("w-72 rounded-2xl p-6 shadow-sm border border-gray-100 hover:shadow-md transition-all"):
                with ui.column().classes("items-center w-full gap-2 text-center"):
                    ui.icon(icon, size="3rem", color=color)
                    ui.label(v.get('plate_number', v.get('license_plate', 'N/A'))).classes("text-2xl font-bold text-gray-800 tracking-wider")
                    ui.label(v['vehicle_type']).classes("text-sm text-gray-500 font-medium")
                    
                    ui.label(label).classes(f"text-[10px] font-bold uppercase px-3 py-1 rounded-full bg-{color}-50 text-{color}-600 border border-{color}-100 mt-2")

                ui.separator().classes("my-4")
                
                with ui.column().classes("w-full gap-2"):
                    if v.get('capacity'):
                        with ui.row().classes("w-full justify-between text-xs"):
                            ui.label("Tải trọng:").classes("text-gray-400")
                            ui.label(v['capacity']).classes("font-semibold text-gray-600")

                # Actions
                with ui.row().classes("w-full justify-center gap-2 mt-4"):
                    # Change status dropdown
                    with ui.button(icon="settings").classes("rounded-lg").props("flat color=gray dense") as opt_btn:
                        with ui.menu() as menu:
                            ui.menu_item("Đánh dấu: Sẵn sàng", on_click=lambda: _update_v_status(v['id'], 'available'))
                            ui.menu_item("Đánh dấu: Bảo trì", on_click=lambda: _update_v_status(v['id'], 'maintenance'))
                            ui.menu_item("Sửa thông tin xe", on_click=lambda v=v: _show_edit_dialog(v))
                            ui.separator()
                            ui.menu_item("Xóa xe", on_click=lambda v=v: _confirm_delete(v))
                    
                    if v['status'] == 'available':
                        ui.label("Có thể gán việc").classes("text-[10px] text-green-600 font-bold")

        async def _show_add_dialog():
            with ui.dialog() as dialog, ui.card().classes("p-6 rounded-2xl w-[400px]"):
                ui.label("Thêm phương tiện mới").classes("text-xl font-bold mb-4")
                
                plate = ui.input(label="Biển kiểm soát *", placeholder="VD: 29A-12345").classes("w-full").props("outlined")
                vtype = ui.select(
                    options=['Xe cẩu hạng nhẹ', 'Xe cẩu hạng nặng', 'Xe bán tải hỗ trợ', 'Xe máy cứu hộ'],
                    label="Loại phương tiện *",
                    value='Xe cẩu hạng nhẹ'
                ).classes("w-full mt-2").props("outlined")
                cap = ui.input(label="Tải trọng / Ghi chú", placeholder="VD: 2 tấn").classes("w-full mt-2").props("outlined")
                
                with ui.row().classes("w-full justify-end gap-3 mt-6"):
                    ui.button("Hủy", on_click=dialog.close).props("flat")
                    async def do_add():
                        if not plate.value:
                            ui.notify("Vui lòng nhập biển số", type="warning")
                            return
                        try:
                            await add_vehicle(plate.value, vtype.value, cap.value)
                            ui.notify("Đã thêm xe mới", type="positive")
                            dialog.close()
                            await _load_data()
                        except Exception as e:
                            ui.notify(f"Lỗi: {e}", type="negative")
                    ui.button("LƯU", on_click=do_add).classes("bg-indigo-600 text-white px-8 font-bold rounded-lg")
            dialog.open()

        async def _show_edit_dialog(v):
            with ui.dialog() as dialog, ui.card().classes("p-6 rounded-2xl w-[400px]"):
                ui.label("Sửa thông tin phương tiện").classes("text-xl font-bold mb-4")
                
                plate = ui.input(label="Biển kiểm soát *", value=v.get('plate_number', v.get('license_plate', ''))).classes("w-full").props("outlined")
                vtype = ui.select(
                    options=['Xe cẩu hạng nhẹ', 'Xe cẩu hạng nặng', 'Xe bán tải hỗ trợ', 'Xe máy cứu hộ'],
                    label="Loại phương tiện *",
                    value=v['vehicle_type']
                ).classes("w-full mt-2").props("outlined")
                cap = ui.input(label="Tải trọng / Ghi chú", value=v.get('capacity', '')).classes("w-full mt-2").props("outlined")
                
                with ui.row().classes("w-full justify-end gap-3 mt-6"):
                    ui.button("Hủy", on_click=dialog.close).props("flat")
                    async def do_edit():
                        if not plate.value:
                            ui.notify("Vui lòng nhập biển số", type="warning")
                            return
                        try:
                            await update_vehicle(v['id'], plate.value, vtype.value, cap.value)
                            ui.notify("Đã cập nhật thông tin xe", type="positive")
                            dialog.close()
                            await _load_data()
                        except Exception as e:
                            ui.notify(f"Lỗi: {e}", type="negative")
                    ui.button("CẬP NHẬT", on_click=do_edit).classes("bg-indigo-600 text-white px-8 font-bold rounded-lg")
            dialog.open()

        async def _update_v_status(vid, status):
            try:
                await update_vehicle_status(vid, status)
                ui.notify("Đã cập nhật trạng thái", type="positive")
                await _load_data()
            except Exception as e:
                ui.notify(f"Lỗi: {e}", type="negative")

        async def _confirm_delete(v):
            with ui.dialog() as dialog, ui.card().classes("p-6 rounded-2xl"):
                ui.label(f"Xóa xe {v.get('plate_number', v.get('license_plate', ''))}?").classes("text-xl font-bold")
                ui.label("Hành động này không thể hoàn tác.").classes("text-gray-500 mb-6")
                with ui.row().classes("w-full justify-end gap-3"):
                    ui.button("Đóng", on_click=dialog.close).props("flat")
                    async def do_del():
                        success = await delete_vehicle(v['id'])
                        if success:
                            ui.notify("Đã xóa xe", type="info")
                            dialog.close()
                            await _load_data()
                        else:
                            ui.notify("Không thể xóa xe (có thể đang có nhiệm vụ)", type="negative")
                    ui.button("Xóa ngay", on_click=do_del).classes("bg-red-500 text-white px-6")
            dialog.open()

        await _load_data()
