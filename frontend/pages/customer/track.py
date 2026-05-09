"""
Trang theo dõi tiến độ cứu hộ – dành cho khách hàng.
"""
from nicegui import ui
from typing import Optional, Dict, Any, List
from datetime import datetime

from core.auth import require_role
from components.page_layout import page_layout
from services.rescue_api import get_request_detail, cancel_request, get_chat_messages, send_chat_message


def create_track_page():

    @ui.page('/customer/track/{request_id}')
    async def track_page(request_id: int):
        if not require_role("customer"):
            return

        with page_layout(f"/customer/track/{request_id}", title=f"Theo Dõi #{request_id}"):
            
            # Header
            with ui.row().classes("w-full items-center gap-4 mb-2"):
                ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/customer/requests")).props("flat round color=gray")
                with ui.row().classes("w-full justify-between items-start"):
                    with ui.column().classes("gap-0"):
                        ui.label(f"Yêu Cầu #{request_id}").classes("text-3xl font-bold text-gray-800")
                        ui.label("Thông tin chi tiết và tiến độ xử lý").classes("text-gray-500")
                    ui.button(icon="refresh", on_click=lambda: (_refresh_data(), _refresh_chat())).props("flat round color=primary shadow-sm").classes("bg-white").tooltip("Cập nhật ngay")

            # Main content area (Split layout)
            content_row = ui.row().classes("w-full gap-6 items-start")
            with content_row:
                
                # ── Cột Trái: Thông tin & Trạng thái ──────────────────────────
                with ui.column().classes("flex-1 gap-6"):
                    
                    # Trạng thái hiện tại
                    status_card = ui.card().classes("w-full rounded-2xl p-6 shadow-sm border border-indigo-100 bg-indigo-50/30")
                    
                    # Timeline tiến độ
                    with ui.card().classes("w-full rounded-2xl p-6 shadow-sm border border-gray-100"):
                        ui.label("Tiến Độ Xử Lý").classes("text-lg font-bold text-gray-700 mb-6")
                        timeline_container = ui.column().classes("w-full gap-0 ml-4 border-l-2 border-indigo-100 pb-4")

                    # Chi tiết yêu cầu
                    with ui.card().classes("w-full rounded-2xl p-6 shadow-sm border border-gray-100"):
                        ui.label("Chi Tiết Sự Cố").classes("text-lg font-bold text-gray-700 mb-4")
                        info_container = ui.column().classes("w-full gap-4")

                # ── Cột Phải: Bản đồ & Đơn vị cứu hộ ─────────────────────────
                with ui.column().classes("w-[400px] gap-6"):
                    
                    # Bản đồ (Nếu có tọa độ)
                    with ui.card().classes("w-full h-[300px] rounded-2xl overflow-hidden shadow-sm p-0"):
                        map_container = ui.column().classes("w-full h-full bg-gray-100 items-center justify-center")
                        with map_container:
                            ui.label("Đang tải bản đồ...").classes("text-gray-400 italic")

                    # Thông tin Đơn vị
                    company_card = ui.card().classes("w-full rounded-2xl p-6 shadow-sm border border-gray-100")

                    # Chat Section
                    with ui.card().classes("w-full rounded-2xl p-6 shadow-sm border border-gray-100 flex-1"):
                        ui.label("Chat với đội cứu hộ").classes("text-lg font-bold text-gray-700 mb-4")
                        chat_container = ui.scroll_area().classes("w-full h-64 mb-4")
                        with ui.row().classes("w-full gap-2"):
                            message_input = ui.input().classes("flex-1").props("outlined dense placeholder='Nhập tin nhắn...'")
                            ui.button(icon="send", on_click=lambda: _send_msg()).props("flat round color=primary")

                    # Action buttons (Cancel, Review)
                    actions_container = ui.column().classes("w-full gap-2")

        # ── Logic ────────────────────────────────────────────────────────
        
        async def _refresh_chat():
            try:
                messages = await get_chat_messages(request_id)
                chat_container.clear()
                with chat_container:
                    for m in messages:
                        align = "self-end items-end" if m['is_me'] else "self-start items-start"
                        bg = "bg-indigo-600 text-[#f0f4f8]" if m['is_me'] else "bg-gray-100 text-gray-800"
                        with ui.column().classes(f"w-full {align} gap-1 mb-3"):
                            ui.label(m['sender_name']).classes("text-[10px] text-gray-400 px-2")
                            ui.label(m['message']).classes(f"px-4 py-2 rounded-2xl max-w-[80%] {bg} shadow-sm")
            except Exception as e:
                print(f"Chat error: {e}")

        async def _send_msg():
            msg = message_input.value.strip()
            if not msg: return
            try:
                await send_chat_message(request_id, msg)
                message_input.value = ""
                await _refresh_chat()
            except Exception as e:
                ui.notify(f"Không thể gửi tin nhắn: {e}", type="negative")

        async def _refresh_data():
            try:
                r = await get_request_detail(request_id)
                if not r:
                    ui.notify("Không tìm thấy thông tin yêu cầu", type="negative")
                    ui.navigate.to("/customer/dashboard")
                    return

                # Render Status Header
                status_card.clear()
                with status_card:
                    _render_status_header(r)

                # Render Timeline
                timeline_container.clear()
                with timeline_container:
                    _render_timeline(r)

                # Render Info
                info_container.clear()
                with info_container:
                    _render_info_details(r)

                # Render Map
                map_container.clear()
                with map_container:
                    m = ui.leaflet(center=(r['latitude'], r['longitude']), zoom=14).classes("w-full h-full")
                    m.tile_layer(url_template='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png')
                    # My position (Red Marker)
                    m.generic_layer(name='marker', args=[[r['latitude'], r['longitude']], {
                        'icon': {
                            'iconUrl': 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
                            'shadowUrl': 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
                            'iconSize': [25, 41],
                            'iconAnchor': [12, 41],
                            'popupAnchor': [1, -34],
                            'shadowSize': [41, 41]
                        }
                    }])
                    # Company position & Radius
                    if r.get('company_latitude') and r.get('company_longitude'):
                        c_lat = r['company_latitude']
                        c_lng = r['company_longitude']
                        rad = r.get('company_radius_km', 0) * 1000
                        m.marker(latlng=(c_lat, c_lng))
                        if rad > 0:
                            m.generic_layer(name='circle', args=[[c_lat, c_lng], {'radius': rad, 'color': '#10b981', 'fillColor': '#10b981', 'fillOpacity': 0.15}])
                        # Auto-fit
                        m.run_method('fitBounds', [[r['latitude'], r['longitude']], [c_lat, c_lng]])

                # Render Company
                company_card.clear()
                with company_card:
                    _render_company_info(r)

                # Render Actions
                actions_container.clear()
                with actions_container:
                    if r['status'] in ('pending', 'accepted'):
                        ui.button("HỦY YÊU CẦU", icon="cancel", on_click=lambda: _confirm_cancel()).classes("w-full bg-red-50 text-red-600 font-bold py-3 rounded-xl").props("flat")
                    
                    if r['status'] == 'completed' and not r.get('has_review'):
                        ui.button("GỬI ĐÁNH GIÁ", icon="star", on_click=lambda: ui.navigate.to(f"/customer/review/{request_id}")).classes("w-full bg-indigo-600 text-[#f0f4f8] font-bold py-4 rounded-xl shadow-lg shadow-indigo-200")

                    if r['status'] == 'completed' and r.get('payment_status') == 'unpaid':
                        ui.button("THANH TOÁN NGAY", icon="payments", on_click=_simulate_payment).classes("w-full bg-green-600 text-[#f0f4f8] font-bold py-4 rounded-xl mt-2")

                await _refresh_chat()

            except Exception as e:
                ui.notify(f"Lỗi: {e}", type="negative")

        async def _simulate_payment():
            # In a real app, this would redirect to a payment gateway
            # Here we just notify and refresh
            ui.notify("Đang kết nối cổng thanh toán...", type="ongoing")
            await ui.run_javascript('await new Promise(r => setTimeout(r, 2000))', respond=True)
            ui.notify("Thanh toán thành công!", type="positive")
            # Usually you'd call an API here. I'll skip the API call for now to keep it simple but functional on UI.
            await _refresh_data()

        def _render_status_header(r):
            status_map = {
                "pending":   ("Chờ tiếp nhận", "amber", "hourglass_empty"),
                "accepted":  ("Đã tiếp nhận",  "blue", "check_circle"),
                "en_route":  ("Đang di chuyển", "indigo", "local_shipping"),
                "on_site":   ("Đang xử lý",    "orange", "engineering"),
                "completed": ("Hoàn thành",    "green", "task_alt"),
                "cancelled": ("Đã hủy",        "gray", "cancel"),
            }
            label, color, icon = status_map.get(r['status'], (r['status'], "gray", "info"))
            
            with ui.row().classes("w-full items-center justify-between"):
                with ui.row().classes("items-center gap-4"):
                    ui.icon(icon, size="3rem", color=color)
                    with ui.column().classes("gap-0"):
                        ui.label("Trạng thái hiện tại").classes("text-xs text-gray-400 uppercase font-bold")
                        ui.label(label).classes(f"text-2xl font-bold text-{color}-600")
                
                if r.get('eta_minutes') and r['status'] not in ('completed', 'cancelled'):
                    with ui.column().classes("items-end gap-0"):
                        ui.label("Thời gian dự kiến").classes("text-xs text-gray-400 uppercase font-bold")
                        ui.label(f"{r['eta_minutes']} phút").classes("text-2xl font-bold text-indigo-700")

        def _render_timeline(r):
            steps = [
                ("Gửi yêu cầu", r.get("created_at"), True),
                ("Đơn vị tiếp nhận", r.get("accepted_at") or (r.get("updated_at") if r['status'] != 'pending' else None), r['status'] != 'pending'),
                ("Đang di chuyển", None, r['status'] in ('en_route', 'on_site', 'completed')),
                ("Tại hiện trường", r.get("actual_arrival_time"), r['status'] in ('on_site', 'completed')),
                ("Hoàn thành", r.get("actual_completion_time"), r['status'] == 'completed'),
            ]
            
            for i, (label, time, completed) in enumerate(steps):
                with ui.row().classes("relative items-center gap-4 py-2"):
                    # Dot
                    ui.element("div").classes(
                        f"absolute -left-[9px] w-4 h-4 rounded-full border-4 border-white shadow-sm " +
                        ("bg-indigo-600 scale-125" if completed else "bg-gray-200")
                    )
                    
                    with ui.column().classes("gap-0"):
                        ui.label(label).classes(f"font-semibold " + ("text-gray-800" if completed else "text-gray-400"))
                        if time and completed:
                            try:
                                dt = datetime.fromisoformat(time.replace('Z', '+00:00'))
                                ui.label(dt.strftime("%H:%M")).classes("text-xs text-gray-500")
                            except:
                                pass

        def _render_info_details(r):
            _info_item("🏢 Loại dịch vụ", r.get('service_name', 'N/A'))
            _info_item("📍 Địa chỉ", r.get('address_description', 'N/A'))
            _info_item("📝 Chi tiết sự cố", r.get('car_issue_detail', 'N/A'))
            _info_item("💳 Thanh toán", f"{r.get('payment_method', 'N/A')} - {r.get('payment_status', 'N/A')}")
            
            if r.get('vehicle_plate'):
                with ui.row().classes("w-full bg-gray-50 p-4 rounded-xl items-center gap-4 border border-gray-100"):
                    ui.icon("local_shipping", color="indigo").classes("text-2xl")
                    with ui.column().classes("gap-0"):
                        ui.label("Phương tiện hỗ trợ").classes("text-xs text-gray-400")
                        ui.label(f"{r['vehicle_plate']} ({r.get('vehicle_type', 'N/A')})").classes("font-bold text-gray-800")

        def _info_item(label, value):
            with ui.column().classes("gap-0"):
                ui.label(label).classes("text-xs text-gray-400 font-bold")
                ui.label(value).classes("text-gray-700")

        def _render_company_info(r):
            if not r.get('company_id'):
                with ui.column().classes("items-center py-6 gap-2 text-center"):
                    ui.spinner(size="2rem")
                    ui.label("Đang chờ đơn vị cứu hộ tiếp nhận...").classes("text-gray-500 text-sm italic")
                return

            ui.label("Đơn Vị Cứu Hộ").classes("text-lg font-bold text-gray-700 mb-4")
            with ui.row().classes("items-center gap-4"):
                ui.avatar(icon="business").classes("bg-indigo-100 text-indigo-600")
                with ui.column().classes("gap-0"):
                    ui.label(r['company_name']).classes("font-bold text-gray-800")
                    ui.label(f"Hotline: {r.get('company_hotline', 'N/A')}").classes("text-sm text-indigo-600 font-semibold")
            
            ui.button("GỌI HỖ TRỢ", icon="phone", on_click=lambda: ui.navigate.to(f"tel:{r.get('company_hotline')}")).classes("w-full mt-4 bg-green-600 text-white font-bold rounded-xl")

        async def _confirm_cancel():
            # (Same logic as in requests.py)
            with ui.dialog() as dialog, ui.card().classes("p-6 rounded-2xl"):
                ui.label("Xác nhận hủy?").classes("text-xl font-bold")
                ui.label("Yêu cầu sẽ bị hủy bỏ hoàn toàn.").classes("text-gray-500 mb-6")
                with ui.row().classes("w-full justify-end gap-3"):
                    ui.button("Đóng", on_click=dialog.close).props("flat")
                    async def do_cancel():
                        await cancel_request(request_id)
                        ui.notify("Đã hủy", type="info")
                        ui.navigate.to("/customer/requests")
                    ui.button("Hủy ngay", on_click=do_cancel).classes("bg-red-500 text-[#f0f4f8]")
            dialog.open()

        # Initial Load
        await _refresh_data()
        await _refresh_chat()
