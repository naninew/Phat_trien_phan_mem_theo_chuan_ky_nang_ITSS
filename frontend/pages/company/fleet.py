"""
Trang quản lý đội xe - dành cho công ty.
"""
import asyncio

from nicegui import ui
from core.auth import require_role
from components.page_layout import page_layout
from components.company_ui import (
    empty_state,
    inject_company_styles,
    kpi_card,
    page_header,
    status_badge,
)
from services.rescue_api import get_my_vehicles, add_vehicle, update_vehicle_status, delete_vehicle, update_vehicle


def _plate(v):
    return v.get('plate_number') or v.get('license_plate') or 'N/A'


def create_fleet_page():

    @ui.page('/company/fleet')
    async def fleet_page():
        if not require_role("company_staff"):
            return

        inject_company_styles()

        with page_layout("/company/fleet", title=""):
            with ui.column().classes("company-page gap-6"):
                page_header(
                    "Quản lý đội xe",
                    "Theo dõi phương tiện, trạng thái sẵn sàng và năng lực vận hành.",
                    "local_shipping",
                    "Thêm xe mới",
                    "add",
                    lambda: _show_add_dialog(),
                )

                stats_row = ui.row().classes("w-full gap-4 flex-wrap")
                with ui.element("div").classes("company-card p-4 w-full"):
                    with ui.row().classes("w-full items-center gap-3 flex-wrap"):
                        ui.icon("filter_list", size="20px").classes("text-blue-600")
                        ui.label("Bộ lọc:").classes("text-sm font-black text-slate-700")
                        type_filter = ui.select(
                            options={"all": "Tất cả loại xe"},
                            value="all",
                        ).classes("min-w-[220px] flex-1 company-field").props("outlined rounded dense")
                        status_filter = ui.select(
                            options={
                                "all": "Tất cả trạng thái",
                                "available": "Sẵn sàng",
                                "on_mission": "Đang làm nhiệm vụ",
                                "maintenance": "Bảo trì",
                            },
                            value="all",
                        ).classes("min-w-[220px] flex-1 company-field").props("outlined rounded dense")
                        ui.button("Lọc", icon="search", on_click=lambda: asyncio.create_task(_load_data())).classes(
                            "company-primary-btn px-5"
                        ).props("unelevated no-caps")
                        type_filter.on_value_change(lambda _: asyncio.create_task(_load_data()))
                        status_filter.on_value_change(lambda _: asyncio.create_task(_load_data()))

                fleet_container = ui.row().classes("w-full gap-5 flex-wrap items-stretch")

                edit_vehicle = {"data": None}
                with ui.dialog() as edit_dialog, ui.card().classes("p-6 rounded-2xl w-[420px]"):
                    ui.label("Sửa thông tin phương tiện").classes("text-xl font-bold mb-4 text-slate-900")
                    edit_plate = ui.input(label="Biển kiểm soát *").classes("w-full company-field").props("outlined")
                    edit_type = ui.select(
                        options=['Xe cẩu hạng nhẹ', 'Xe cẩu hạng nặng', 'Xe bán tải hỗ trợ', 'Xe máy cứu hộ'],
                        label="Loại phương tiện *",
                    ).classes("w-full mt-3 company-field").props("outlined")
                    edit_capacity = ui.input(label="Tải trọng / Ghi chú").classes("w-full mt-3 company-field").props("outlined")
                    edit_status = ui.select(
                        options={
                            "available": "Sẵn sàng",
                            "on_mission": "Đang làm nhiệm vụ",
                            "maintenance": "Bảo trì",
                        },
                        label="Trạng thái xe",
                    ).classes("w-full mt-3 company-field").props("outlined")
                    with ui.row().classes("w-full justify-end gap-3 mt-6"):
                        ui.button("Hủy", on_click=edit_dialog.close).props("flat no-caps")

                        async def do_edit():
                            vehicle = edit_vehicle["data"]
                            if not vehicle:
                                return
                            if not edit_plate.value:
                                ui.notify("Vui lòng nhập biển số", type="warning")
                                return
                            try:
                                await update_vehicle(
                                    vehicle["id"],
                                    edit_plate.value,
                                    edit_type.value,
                                    edit_capacity.value,
                                )
                                if edit_status.value != vehicle.get("status"):
                                    await update_vehicle_status(vehicle["id"], edit_status.value)
                                ui.notify("Đã cập nhật thông tin xe", type="positive")
                                edit_dialog.close()
                                await _load_data()
                            except Exception as e:
                                ui.notify(f"Lỗi: {e}", type="negative")

                        ui.button("Cập nhật", icon="save", on_click=do_edit).classes("company-primary-btn px-5").props("unelevated no-caps")

        async def _load_data():
            fleet_container.clear()
            stats_row.clear()
            try:
                vehicles = await get_my_vehicles()
                total = len(vehicles)
                available = sum(1 for v in vehicles if v.get('status') == 'available')
                on_mission = sum(1 for v in vehicles if v.get('status') == 'on_mission')
                maintenance = sum(1 for v in vehicles if v.get('status') == 'maintenance')
                type_options = {"all": "Tất cả loại xe"}
                for vehicle_type in sorted({v.get("vehicle_type") for v in vehicles if v.get("vehicle_type")}):
                    type_options[vehicle_type] = vehicle_type
                current_type = type_filter.value if type_filter.value in type_options else "all"
                type_filter.options = type_options
                type_filter.value = current_type
                type_filter.update()

                with stats_row:
                    kpi_card("Tổng số xe", total, "Phương tiện đang quản lý", "local_shipping", "#2563eb")
                    kpi_card("Xe sẵn sàng", available, "Có thể phân công", "check_circle", "#10b981")
                    kpi_card("Đang làm nhiệm vụ", on_mission, "Đang phục vụ yêu cầu", "route", "#f59e0b")
                    kpi_card("Bảo trì", maintenance, "Cần kiểm tra kỹ thuật", "build", "#ef4444")

                filtered = vehicles
                if type_filter.value != "all":
                    filtered = [v for v in filtered if v.get("vehicle_type") == type_filter.value]
                if status_filter.value != "all":
                    filtered = [v for v in filtered if v.get("status") == status_filter.value]

                with fleet_container:
                    if not filtered:
                        empty_state("no_transportation", "Không có phương tiện phù hợp", "Thử đổi loại xe hoặc trạng thái để xem thêm kết quả.")
                    for v in filtered:
                        _render_vehicle_card(v)
            except Exception as e:
                ui.notify(f"Lỗi: {e}", type="negative")

        def _status(v):
            status_map = {
                "available": ("Sẵn sàng", "emerald", "check_circle"),
                "on_mission": ("Đang làm nhiệm vụ", "amber", "route"),
                "maintenance": ("Bảo trì", "red", "build"),
            }
            return status_map.get(v.get('status'), (v.get('status', 'Không rõ'), "slate", "help"))

        def _render_vehicle_card(v):
            label, tone, icon = _status(v)
            with ui.element("div").classes("company-card company-card-hover w-[310px] p-5"):
                with ui.row().classes("w-full items-start justify-between gap-3"):
                    with ui.row().classes("items-center gap-3"):
                        with ui.element("div").classes("company-icon-box"):
                            ui.icon(icon, size="22px")
                        with ui.column().classes("gap-1"):
                            ui.label(_plate(v)).classes("text-xl font-black tracking-wide text-slate-900")
                            ui.label(v.get('vehicle_type') or 'Phương tiện cứu hộ').classes("text-sm font-bold text-slate-500")
                    status_badge(label, tone)

                with ui.row().classes("w-full gap-2 mt-4"):
                    with ui.column().classes("flex-1 rounded-2xl bg-slate-50 p-3 gap-1"):
                        ui.label("Tải trọng").classes("text-xs font-black uppercase text-slate-400")
                        ui.label(v.get('capacity') or 'Chưa cập nhật').classes("text-sm font-bold text-slate-700")
                    with ui.column().classes("flex-1 rounded-2xl bg-slate-50 p-3 gap-1"):
                        ui.label("Cập nhật").classes("text-xs font-black uppercase text-slate-400")
                        ui.label(str(v.get('updated_at') or v.get('created_at') or 'N/A')[:10]).classes("text-sm font-bold text-slate-700")

                ui.separator().classes("my-4")
                with ui.row().classes("w-full justify-between items-center gap-2"):
                    with ui.button("Thao tác", icon="more_horiz").classes("company-muted-btn").props("flat no-caps"):
                        with ui.menu():
                            ui.menu_item("Đánh dấu: Sẵn sàng", on_click=lambda vid=v['id']: asyncio.create_task(_update_v_status(vid, 'available')))
                            ui.menu_item("Đánh dấu: Đang làm nhiệm vụ", on_click=lambda vid=v['id']: asyncio.create_task(_update_v_status(vid, 'on_mission')))
                            ui.menu_item("Đánh dấu: Bảo trì", on_click=lambda vid=v['id']: asyncio.create_task(_update_v_status(vid, 'maintenance')))
                            ui.menu_item("Sửa thông tin xe", on_click=lambda v=v: _open_edit_dialog(v))
                            ui.separator()
                            ui.menu_item("Xóa xe", on_click=lambda v=v: _confirm_delete(v)).classes("text-red-500")
                    if v.get('status') == 'available':
                        ui.label("Có thể gán việc").classes("text-xs font-black text-emerald-600")

        def _show_add_dialog():
            with ui.dialog() as dialog, ui.card().classes("p-6 rounded-2xl w-[420px]"):
                ui.label("Thêm phương tiện mới").classes("text-xl font-bold mb-4 text-slate-900")
                plate = ui.input(label="Biển kiểm soát *", placeholder="VD: 29A-12345").classes("w-full company-field").props("outlined")
                vtype = ui.select(options=['Xe cẩu hạng nhẹ', 'Xe cẩu hạng nặng', 'Xe bán tải hỗ trợ', 'Xe máy cứu hộ'], label="Loại phương tiện *", value='Xe cẩu hạng nhẹ').classes("w-full mt-3 company-field").props("outlined")
                cap = ui.input(label="Tải trọng / Ghi chú", placeholder="VD: 2 tấn").classes("w-full mt-3 company-field").props("outlined")
                with ui.row().classes("w-full justify-end gap-3 mt-6"):
                    ui.button("Hủy", on_click=dialog.close).props("flat no-caps")

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

                    ui.button("Lưu", icon="save", on_click=do_add).classes("company-primary-btn px-5").props("unelevated no-caps")
            dialog.open()

        def _open_edit_dialog(v):
            edit_vehicle["data"] = dict(v)
            edit_plate.set_value(_plate(v))
            edit_type.set_value(v.get("vehicle_type") or "Xe cẩu hạng nhẹ")
            edit_capacity.set_value(v.get("capacity") or "")
            edit_status.set_value(v.get("status") or "available")
            edit_dialog.open()

        async def _update_v_status(vid, status):
            try:
                await update_vehicle_status(vid, status)
                ui.notify("Đã cập nhật trạng thái", type="positive")
                await _load_data()
            except Exception as e:
                ui.notify(f"Lỗi: {e}", type="negative")

        def _confirm_delete(v):
            with ui.dialog() as dialog, ui.card().classes("p-6 rounded-2xl"):
                ui.label(f"Xóa xe {_plate(v)}?").classes("text-xl font-bold text-slate-900")
                ui.label("Hành động này không thể hoàn tác.").classes("text-gray-500 mb-6")
                with ui.row().classes("w-full justify-end gap-3"):
                    ui.button("Đóng", on_click=dialog.close).props("flat no-caps")

                    async def do_del():
                        success = await delete_vehicle(v['id'])
                        if success:
                            ui.notify("Đã xóa xe", type="info")
                            dialog.close()
                            await _load_data()
                        else:
                            ui.notify("Không thể xóa xe (có thể đang có nhiệm vụ)", type="negative")

                    ui.button("Xóa ngay", icon="delete", on_click=do_del).classes("bg-red-600 text-white rounded-xl px-5 font-bold").props("unelevated no-caps")
            dialog.open()

        await _load_data()
