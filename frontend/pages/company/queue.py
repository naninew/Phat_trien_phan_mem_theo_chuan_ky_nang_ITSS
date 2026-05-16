"""
Company Queue Management - NiceGUI
"""
from nicegui import ui
from typing import Optional, Dict, Any, List
from datetime import datetime
from core.auth import require_role
from components.page_layout import page_layout
from services.rescue_api import (
    get_company_queue, 
    accept_request, 
    reject_request,
    update_request_status, 
    get_my_vehicles,
    get_company_staff,
    assign_request
)

def create_queue_page():
    """Register /company/queue route."""

    @ui.page('/company/queue')
    async def queue_page():
        if not require_role("company_staff"):
            return

        with page_layout("/company/queue", title="Hàng Đợi Cứu Hộ"):
            
            with ui.row().classes("w-full items-center justify-between mb-6"):
                with ui.column().classes("gap-0"):
                    ui.label("📊 Hàng Đợi Yêu Cầu").classes("text-3xl font-bold font-outfit text-primary")
                    ui.label("Tiếp nhận và điều phối nhân sự, phương tiện").classes("opacity-60")
                
                refresh_btn = ui.button(icon="refresh", on_click=lambda: _load_data()).props("flat round color=primary")

            # Filters
            with ui.row().classes("w-full items-center gap-4 bg-surface-variant/5 p-4 rounded-2xl mb-6"):
                ui.label("Trạng thái:").classes("font-bold text-sm")
                status_filter = ui.select(
                    options={
                        'all': 'Tất cả',
                        'PENDING': 'Mới (Chờ duyệt)',
                        'ACCEPTED': 'Đã nhận (Chờ điều phối)',
                        'ASSIGNED': 'Đã phân công',
                        'ON_THE_WAY': 'Đang di chuyển',
                        'IN_PROGRESS': 'Đang xử lý',
                        'COMPLETED': 'Đã hoàn thành'
                    },
                    value='all',
                    on_change=lambda: _load_data()
                ).classes("w-64").props("outlined rounded dense")

            # Main Queue List
            queue_container = ui.column().classes("w-full gap-4")

        # ── Logic ────────────────────────────────────────────────────────
        
        async def _load_data():
            refresh_btn.props("loading")
            queue_container.clear()
            try:
                queue = await get_company_queue(status_filter.value)
                vehicles = await get_my_vehicles()
                staff = await get_company_staff()
                
                with queue_container:
                    if not queue:
                        ui.label("Hàng đợi trống.").classes("italic opacity-50 py-20 self-center")
                    for r in queue:
                        _render_queue_item(r, vehicles, staff)
            except Exception as e:
                ui.notify(f"Lỗi: {e}", type="negative")
            finally:
                refresh_btn.props(remove="loading")

        def _render_queue_item(r, vehicles, staff):
            status_map = {
                "PENDING":     ("MỚI", "warning"),
                "ACCEPTED":    ("ĐÃ NHẬN", "info"),
                "ASSIGNED":    ("PHÂN CÔNG", "indigo"),
                "ON_THE_WAY":  ("DI CHUYỂN", "primary"),
                "IN_PROGRESS": ("XỬ LÝ", "secondary"),
                "COMPLETED":   ("XONG", "positive"),
                "REJECTED":    ("TỪ CHỐI", "error"),
                "CANCELLED":   ("HỦY", "gray"),
            }
            label, color = status_map.get(r['status'], (r['status'], "gray"))

            with ui.card().classes("w-full rounded-3xl p-6 border border-surface-variant/30 shadow-sm hover:shadow-md transition-all"):
                with ui.row().classes("w-full justify-between items-start"):
                    with ui.column().classes("gap-1 flex-1"):
                        with ui.row().classes("items-center gap-3"):
                            ui.label(f"#{r['id']}").classes("font-bold opacity-30 text-sm")
                            ui.badge(label, color=color).classes("rounded-full px-3")
                        
                        ui.label(r.get('service_name', 'Dịch vụ cứu hộ')).classes("text-2xl font-bold font-outfit mt-2")
                        
                        with ui.row().classes("items-center gap-4 mt-2"):
                            with ui.row().classes("items-center gap-2"):
                                ui.icon("person", size="sm").classes("opacity-50")
                                ui.label(r.get('customer_name', 'N/A')).classes("font-medium")
                            with ui.row().classes("items-center gap-2 text-primary font-bold"):
                                ui.icon("phone", size="sm")
                                ui.label(r.get('customer_phone', 'N/A'))
                    
                    with ui.column().classes("items-end"):
                        ui.label("Vị trí yêu cầu:").classes("text-[10px] uppercase font-bold opacity-50")
                        ui.label(r.get('address_description', 'N/A')).classes("text-sm text-right max-w-xs")

                ui.separator().classes("my-6 opacity-30")

                # Action Area
                with ui.row().classes("w-full items-center justify-between"):
                    # Assignment Info
                    with ui.row().classes("gap-4"):
                        assignment = r.get('assignment')
                        if assignment:
                            if assignment.get('rescue_vehicle_plate'):
                                _info_chip("local_shipping", assignment['rescue_vehicle_plate'])
                            if assignment.get('staff_name'):
                                _info_chip("person_pin", assignment['staff_name'])
                        elif r.get('rescue_vehicle_plate') or r.get('staff_name'): # Fallback for old API structure
                             if r.get('rescue_vehicle_plate'): _info_chip("local_shipping", r['rescue_vehicle_plate'])
                             if r.get('staff_name'): _info_chip("person_pin", r['staff_name'])

                    # Status Actions
                    with ui.row().classes("gap-3"):
                        if r['status'] == 'PENDING':
                            ui.button("TỪ CHỐI", on_click=lambda: _do_reject(r['id'])).props("flat color=error")
                            ui.button("TIẾP NHẬN", icon="check", on_click=lambda: _do_accept(r['id'])) \
                                .classes("bg-primary text-white font-bold rounded-xl px-6 py-3")
                        
                        elif r['status'] == 'ACCEPTED':
                            ui.button("PHÂN CÔNG", icon="assignment", on_click=lambda: _show_assign_dialog(r, vehicles, staff)) \
                                .classes("bg-indigo-600 text-white font-bold rounded-xl px-6")
                        
                        elif r['status'] == 'ASSIGNED':
                            ui.button("BẮT ĐẦU DI CHUYỂN", icon="navigation", on_click=lambda: _update_status(r['id'], 'ON_THE_WAY')) \
                                .classes("bg-primary text-white font-bold rounded-xl px-6")
                        
                        elif r['status'] == 'ON_THE_WAY':
                            ui.button("ĐÃ ĐẾN HIỆN TRƯỜNG", icon="place", on_click=lambda: _update_status(r['id'], 'IN_PROGRESS')) \
                                .classes("bg-secondary text-white font-bold rounded-xl px-6")
                        
                        elif r['status'] == 'IN_PROGRESS':
                            ui.button("XÁC NHẬN HOÀN THÀNH", icon="check_circle", on_click=lambda: _show_complete_dialog(r)) \
                                .classes("bg-positive text-white font-bold rounded-xl px-6")

        def _info_chip(icon, text):
            with ui.row().classes("items-center gap-2 bg-surface-variant/10 px-3 py-1.5 rounded-full"):
                ui.icon(icon, size="1rem").classes("text-primary")
                ui.label(text).classes("text-xs font-bold")

        async def _do_accept(req_id):
            try:
                # Backend accept_request takes eta_minutes
                await accept_request(req_id, eta_minutes=20)
                ui.notify("Đã tiếp nhận yêu cầu", type="positive")
                await _load_data()
            except Exception as e:
                ui.notify(f"Lỗi: {e}", type="negative")

        async def _show_assign_dialog(req, vehicles, staff):
            with ui.dialog() as d, ui.card().classes("p-8 rounded-3xl w-[450px]"):
                ui.label("Phân công cứu hộ").classes("text-2xl font-bold mb-6 font-outfit text-primary")
                
                v_opts = {v['id']: f"{v['plate_number']} ({v['vehicle_type']})" for v in vehicles if v['status'] == 'available'}
                v_sel = ui.select(v_opts, label="Chọn Phương Tiện").classes("w-full mb-4").props("outlined rounded")
                
                s_opts = {s['id']: f"NV #{s['id']} (Level {s['skill_level']})" for s in staff if s['status'] == 'AVAILABLE'}
                s_sel = ui.select(s_opts, label="Chọn Nhân Viên").classes("w-full mb-8").props("outlined rounded")
                
                with ui.row().classes("w-full justify-end gap-3"):
                    ui.button("HỦY", on_click=d.close).props("flat")
                    async def assign():
                        if not v_sel.value or not s_sel.value:
                            ui.notify("Vui lòng chọn đủ nhân sự và phương tiện", type="warning")
                            return
                        try:
                            await assign_request(req['id'], s_sel.value, v_sel.value)
                            ui.notify("Đã phân công thành công!", type="positive")
                            d.close()
                            await _load_data()
                        except Exception as e:
                            ui.notify(f"Lỗi: {e}", type="negative")
                    ui.button("XÁC NHẬN", on_click=assign).classes("bg-primary text-white px-8 rounded-xl font-bold")
            d.open()

        async def _show_complete_dialog(req):
            with ui.dialog() as d, ui.card().classes("p-8 rounded-3xl w-[400px]"):
                ui.label("Hoàn thành cứu hộ").classes("text-2xl font-bold mb-6 font-outfit text-primary")
                price = ui.number(label="Giá thực tế (VNĐ)", value=req.get('agreed_price', 200000)).classes("w-full mb-8").props("outlined rounded")
                
                with ui.row().classes("w-full justify-end gap-3"):
                    ui.button("HỦY", on_click=d.close).props("flat")
                    async def complete():
                        try:
                            await update_request_status(req['id'], 'COMPLETED', agreed_price=price.value)
                            ui.notify("Đã hoàn thành yêu cầu cứu hộ", type="positive")
                            d.close()
                            await _load_data()
                        except Exception as e:
                            ui.notify(f"Lỗi: {e}", type="negative")
                    ui.button("XÁC NHẬN", on_click=complete).classes("bg-positive text-white px-8 rounded-xl font-bold")
            d.open()

        async def _do_reject(req_id):
            try:
                if await reject_request(req_id):
                    ui.notify("Đã từ chối yêu cầu", type="info")
                    await _load_data()
            except Exception as e:
                ui.notify(f"Lỗi: {e}", type="negative")

        async def _update_status(req_id, status):
            try:
                if await update_request_status(req_id, status):
                    ui.notify(f"Trạng thái mới: {status}", type="info")
                    await _load_data()
            except Exception as e:
                ui.notify(f"Lỗi: {e}", type="negative")

        await _load_data()
        ui.timer(15, _load_data)
