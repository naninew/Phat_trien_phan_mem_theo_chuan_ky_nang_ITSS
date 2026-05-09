"""
Trang quản lý hàng đợi yêu cầu cứu hộ – dành cho công ty.
"""
from nicegui import ui
from typing import Optional, Dict, Any, List
from datetime import datetime

from core.auth import require_role
from components.page_layout import page_layout
from services.rescue_api import (
    get_company_queue, 
    accept_request, 
    update_request_status, 
    get_my_vehicles
)


def create_queue_page():

    @ui.page('/company/queue')
    async def queue_page():
        if not require_role("company_staff"):
            return

        with page_layout("/company/queue", title="Hàng Đợi Cứu Hộ"):
            
            with ui.row().classes("w-full items-center justify-between mb-4"):
                with ui.column().classes("gap-0"):
                    ui.label("📊 Hàng Đợi Yêu Cầu").classes("text-3xl font-bold text-gray-800")
                    ui.label("Tiếp nhận và cập nhật trạng thái cứu hộ").classes("text-gray-500")
                
                refresh_btn = ui.button(icon="refresh", on_click=lambda: _load_data()).props("flat round color=indigo")

            # Bộ lọc
            with ui.row().classes("w-full items-center gap-4 bg-white p-4 rounded-2xl shadow-sm border border-gray-100 mb-4"):
                ui.label("Trạng thái:").classes("text-gray-600 font-medium")
                status_filter = ui.select(
                    options={
                        'all': 'Tất cả',
                        'pending': 'Mới (Chờ duyệt)',
                        'accepted': 'Đã nhận (Chờ di chuyển)',
                        'en_route': 'Đang di chuyển',
                        'on_site': 'Đang xử lý',
                        'completed': 'Đã hoàn thành'
                    },
                    value='all',
                    on_change=lambda: _load_data()
                ).classes("w-64").props("outlined dense")

            # Container
            queue_container = ui.column().classes("w-full gap-4")

        # ── Logic ────────────────────────────────────────────────────────
        
        async def _load_data():
            refresh_btn.props("loading")
            queue_container.clear()
            try:
                queue = await get_company_queue(status_filter.value)
                vehicles = await get_my_vehicles()
                
                with queue_container:
                    if not queue:
                        with ui.column().classes("w-full items-center py-20 bg-white rounded-3xl border border-dashed border-gray-300"):
                            ui.icon("assignment_late", size="5rem", color="gray-200")
                            ui.label("Không có yêu cầu nào trong hàng đợi").classes("text-gray-400 text-lg")
                    else:
                        for r in queue:
                            _render_queue_item(r, vehicles)
            except Exception as e:
                ui.notify(f"Lỗi: {e}", type="negative")
            finally:
                refresh_btn.props(remove="loading")

        def _render_queue_item(r, vehicles):
            status_map = {
                "pending":   ("MỚI", "amber"),
                "accepted":  ("ĐÃ NHẬN", "blue"),
                "en_route":  ("DI CHUYỂN", "indigo"),
                "on_site":   ("XỬ LÝ", "orange"),
                "completed": ("XONG", "green"),
            }
            label, color = status_map.get(r['status'], (r['status'], "gray"))

            with ui.card().classes("w-full rounded-2xl p-6 shadow-sm border border-gray-100"):
                with ui.row().classes("w-full justify-between items-start"):
                    with ui.column().classes("gap-1 flex-1"):
                        with ui.row().classes("items-center gap-2"):
                            ui.label(f"#{r['id']}").classes("font-bold text-gray-400")
                            ui.label(label).classes(f"text-[10px] font-bold px-2 py-0.5 rounded bg-{color}-100 text-{color}-700")
                        
                        ui.label(r.get('service_name', 'Cứu hộ')).classes("text-xl font-bold text-gray-800")
                        
                        with ui.row().classes("items-center gap-4 mt-2"):
                            with ui.row().classes("items-center gap-1 text-sm text-gray-600"):
                                ui.icon("person", size="1.2rem")
                                ui.label(r.get('customer_name', 'N/A'))
                            with ui.row().classes("items-center gap-1 text-sm text-indigo-600 font-bold"):
                                ui.icon("phone", size="1.2rem")
                                ui.label(r.get('customer_phone', 'N/A'))
                    
                    with ui.column().classes("items-end"):
                        ui.label("Khách báo vị trí:").classes("text-[10px] uppercase text-gray-400 font-bold")
                        ui.label(r.get('address_description', 'N/A')).classes("text-sm text-gray-600 max-w-xs text-right")

                ui.separator().classes("my-4")

                # Action Area
                with ui.row().classes("w-full items-center justify-between"):
                    # Thông tin xe đang nhận (nếu có)
                    if r.get('vehicle_plate'):
                        with ui.row().classes("items-center gap-2 text-indigo-700 bg-indigo-50 px-3 py-1.5 rounded-lg"):
                            ui.icon("local_shipping", size="1.2rem")
                            ui.label(f"Xe: {r['vehicle_plate']}").classes("text-sm font-bold")
                    else:
                        ui.label("Chưa gán xe").classes("text-xs text-gray-400 italic")

                    # Buttons
                    with ui.row().classes("gap-2"):
                        if r['status'] == 'pending':
                            ui.button("TIẾP NHẬN", icon="check", on_click=lambda: _show_accept_dialog(r, vehicles)).classes("bg-green-600 text-white font-bold rounded-xl px-6")
                        
                        elif r['status'] == 'accepted':
                            ui.button("BẮT ĐẦU DI CHUYỂN", icon="map", on_click=lambda: _update_status(r['id'], 'en_route')).classes("bg-indigo-600 text-white font-bold rounded-xl px-6")
                        
                        elif r['status'] == 'en_route':
                            ui.button("ĐÃ ĐẾN HIỆN TRƯỜNG", icon="place", on_click=lambda: _update_status(r['id'], 'on_site')).classes("bg-orange-500 text-white font-bold rounded-xl px-6")
                        
                        elif r['status'] == 'on_site':
                            ui.button("HOÀN THÀNH", icon="done_all", on_click=lambda: _update_status(r['id'], 'completed')).classes("bg-green-700 text-white font-bold rounded-xl px-6")

        async def _show_accept_dialog(req, vehicles):
            with ui.dialog() as dialog, ui.card().classes("p-6 rounded-2xl w-[400px]"):
                ui.label("Tiếp nhận cứu hộ").classes("text-xl font-bold mb-4")
                
                eta = ui.number(label="Thời gian đến dự kiến (phút)", value=20, format="%d").classes("w-full").props("outlined")
                cost = ui.number(label="Báo giá sơ bộ (VNĐ)", value=200000).classes("w-full mt-2").props("outlined")
                
                v_options = {v['id']: f"{v['license_plate']} ({v['vehicle_type']})" for v in vehicles if v['status'] == 'available'}
                v_select = ui.select(options=v_options, label="Chọn phương tiện đi cứu hộ").classes("w-full mt-2").props("outlined")
                
                with ui.row().classes("w-full justify-end gap-3 mt-6"):
                    ui.button("Hủy", on_click=dialog.close).props("flat")
                    async def do_accept():
                        if not v_select.value:
                            ui.notify("Vui lòng chọn xe", type="warning")
                            return
                        try:
                            await accept_request(req['id'], int(eta.value), v_select.value, cost.value)
                            ui.notify("Đã tiếp nhận yêu cầu", type="positive")
                            dialog.close()
                            await _load_data()
                        except Exception as e:
                            ui.notify(f"Lỗi: {e}", type="negative")
                    ui.button("XÁC NHẬN", on_click=do_accept).classes("bg-green-600 text-white px-6 font-bold rounded-lg")
            dialog.open()

        async def _update_status(req_id, status):
            try:
                await update_request_status(req_id, status)
                ui.notify(f"Đã cập nhật trạng thái: {status}", type="info")
                await _load_data()
            except Exception as e:
                ui.notify(f"Lỗi: {e}", type="negative")

        await _load_data()
        ui.timer(30, _load_data)
