"""
Tracking Page - NiceGUI
"""
from nicegui import ui
from typing import Dict, Any, List, Optional
from datetime import datetime
from core.auth import require_role
from components.page_layout import page_layout
from services.rescue_api import (
    get_request_detail,
    cancel_request,
    get_chat_messages,
    send_chat_message,
    submit_review
)

def create_track_page():
    """Register /customer/track/{request_id} route."""

    @ui.page('/customer/track/{request_id}')
    async def track_page(request_id: int):
        if not require_role("customer"):
            return

        with page_layout(f"/customer/track/{request_id}", title=f"Theo Dõi #{request_id}"):
            
            with ui.row().classes("w-full items-center gap-4 mb-4"):
                ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/customer/requests")) \
                    .props("flat round color=primary")
                ui.label(f"Yêu Cầu Cứu Hộ #{request_id}").classes("text-3xl font-bold font-outfit")
                ui.space()
                status_chip = ui.badge("ĐANG TẢI").classes("px-4 py-2 rounded-full font-bold")

            with ui.row().classes("w-full gap-8 items-start"):
                # --- Left: Map & Chat ---
                with ui.column().classes("flex-1 gap-6"):
                    with ui.card().classes("w-full h-[450px] p-0 overflow-hidden rounded-3xl shadow-xl"):
                        m = ui.leaflet(center=(21.0285, 105.8542), zoom=13).classes("w-full h-full")
                        m.tile_layer(url_template='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png')
                        user_marker = m.marker(latlng=(21.0285, 105.8542))
                        # Red icon for user
                        user_marker.run_method('setIcon', ui.run_javascript('''
                            L.icon({
                                iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
                                shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
                                iconSize: [25, 41],
                                iconAnchor: [12, 41],
                                popupAnchor: [1, -34],
                                shadowSize: [41, 41]
                            })
                        '''))
                        company_marker = m.marker(latlng=(21.0285, 105.8542))
                        company_marker.set_visibility(False)

                    # Chat Card
                    with ui.card().classes("w-full rounded-3xl p-6 border border-surface-variant/30"):
                        ui.label("Trao đổi với đội cứu hộ").classes("text-lg font-bold mb-4 font-outfit")
                        chat_area = ui.scroll_area().classes("w-full h-64 bg-surface-variant/10 rounded-2xl p-4")
                        with ui.row().classes("w-full gap-2 mt-4"):
                            chat_input = ui.input().classes("flex-1").props("outlined rounded dense placeholder='Nhập tin nhắn...'") \
                                .on('keydown.enter', lambda: do_send())
                            ui.button(icon="send", on_click=lambda: do_send()).props("round unelevated color=primary")

                # --- Right: Timeline & Info ---
                with ui.column().classes("w-96 gap-6"):
                    # Status Timeline
                    with ui.card().classes("w-full rounded-3xl p-8 border border-primary/20 bg-primary/5"):
                        ui.label("Tiến Độ").classes("text-xl font-bold mb-6 font-outfit text-primary")
                        timeline = ui.column().classes("w-full gap-0 ml-2 border-l-2 border-primary/30 pb-4")

                    # Company Info
                    company_info = ui.card().classes("w-full rounded-3xl p-6 border border-surface-variant/30")
                    
                    # Actions
                    actions_area = ui.column().classes("w-full gap-4")

            # --- Logic ---
            async def do_send():
                val = chat_input.value.strip()
                if not val: return
                if await send_chat_message(request_id, val):
                    chat_input.value = ""
                    await refresh_chat()

            async def refresh_chat():
                msgs = await get_chat_messages(request_id)
                chat_area.clear()
                with chat_area:
                    for msg in msgs:
                        is_me = msg['is_me']
                        align = "items-end" if is_me else "items-start"
                        bg = "bg-primary text-white" if is_me else "bg-surface-variant text-on-surface"
                        with ui.column().classes(f"w-full {align} mb-3"):
                            ui.label(msg['message']).classes(f"px-4 py-2 rounded-2xl max-w-[80%] {bg} shadow-sm")
                            ui.label(msg.get('created_at', '')).classes("text-[10px] opacity-50 px-2")

            async def update_ui():
                req = await get_request_detail(request_id)
                if not req: return
                
                # Status chip
                colors = {"PENDING": "warning", "ACCEPTED": "info", "EN_ROUTE": "primary", "ON_SITE": "secondary", "COMPLETED": "positive", "CANCELLED": "negative"}
                status_chip.set_text(req['status'])
                status_chip.props(f"color={colors.get(req['status'], 'gray')}")

                # Map markers
                user_marker.set_latlng((req['latitude'], req['longitude']))
                if req.get('company_latitude'):
                    company_marker.set_visibility(True)
                    company_marker.set_latlng((req['company_latitude'], req['company_longitude']))
                    # Auto fit bounds first time or if significant change
                    # m.run_method('fitBounds', [[req['latitude'], req['longitude']], [req['company_latitude'], req['company_longitude']]])

                # Timeline
                _render_timeline(req)
                
                # Company & Actions
                _render_company(req)
                _render_actions(req)

            def _render_timeline(req):
                timeline.clear()
                steps = [
                    ("Gửi yêu cầu", "pending", "history"),
                    ("Tiếp nhận", "accepted", "check_circle"),
                    ("Đang di chuyển", "en_route", "local_shipping"),
                    ("Đang xử lý", "on_site", "engineering"),
                    ("Hoàn thành", "completed", "task_alt")
                ]
                current_status = req['status']
                reached = True
                with timeline:
                    for label, status, icon in steps:
                        color = "text-primary" if reached else "text-on-surface-variant opacity-30"
                        with ui.row().classes("relative items-center gap-4 py-3"):
                            ui.element('div').classes(f"absolute -left-[9px] w-4 h-4 rounded-full border-4 border-white {'bg-primary shadow-lg' if reached else 'bg-surface-variant'}")
                            ui.icon(icon, color='primary' if reached else 'gray').classes("ml-4")
                            ui.label(label).classes(f"font-bold {color}")
                        if status == current_status: reached = False

            def _render_company(req):
                company_info.clear()
                with company_info:
                    if not req.get('company_name'):
                        ui.label("Đang chờ đơn vị cứu hộ...").classes("italic opacity-50")
                    else:
                        ui.label("Đơn Vị Cứu Hộ").classes("text-lg font-bold mb-4 font-outfit")
                        with ui.row().classes("items-center gap-4"):
                            ui.avatar(icon="business").classes("bg-primary/10 text-primary")
                            with ui.column().classes("gap-0"):
                                ui.label(req['company_name']).classes("font-bold")
                                ui.label(f"Hotline: {req.get('company_hotline')}").classes("text-sm text-primary")
                        ui.button("GỌI HỖ TRỢ", icon="phone", on_click=lambda: ui.navigate.to(f"tel:{req.get('company_hotline')}")) \
                            .classes("w-full mt-4 bg-green-600 text-white rounded-xl font-bold")

            def _render_actions(req):
                actions_area.clear()
                with actions_area:
                    if req['status'] in ('PENDING', 'ACCEPTED'):
                        ui.button("HỦY YÊU CẦU", icon="cancel", on_click=lambda: _confirm_cancel()) \
                            .classes("w-full").props("flat color=error")
                    
                    if req['status'] == 'COMPLETED' and not req.get('has_review'):
                        ui.button("ĐÁNH GIÁ DỊCH VỤ", icon="star", on_click=lambda: _open_review_dialog()) \
                            .classes("w-full bg-primary text-white font-bold py-4 rounded-2xl shadow-lg shadow-primary/30")

            async def _confirm_cancel():
                with ui.dialog() as d, ui.card().classes("p-8 rounded-3xl"):
                    ui.label("Xác nhận hủy?").classes("text-xl font-bold mb-2")
                    ui.label("Yêu cầu cứu hộ sẽ bị dừng ngay lập tức.").classes("mb-6")
                    with ui.row().classes("w-full justify-end gap-3"):
                        ui.button("Đóng", on_click=d.close).props("flat")
                        async def cancel():
                            if await cancel_request(request_id):
                                ui.notify("Đã hủy yêu cầu", type='info')
                                d.close()
                                await update_ui()
                        ui.button("HỦY NGAY", on_click=cancel).classes("bg-error text-white")
                d.open()

            def _open_review_dialog():
                with ui.dialog() as d, ui.card().classes("p-8 rounded-3xl w-96"):
                    ui.label("Đánh giá dịch vụ").classes("text-2xl font-bold mb-4 font-outfit text-primary")
                    rating = ui.slider(min=1, max=5, value=5).classes("w-full mb-2")
                    ui.label().bind_text_from(rating, 'value', backward=lambda v: f"⭐ {v}/5 sao").classes("self-center text-lg font-bold")
                    comment = ui.textarea("Nhận xét (không bắt buộc)").classes("w-full mb-6").props("outlined rounded")
                    with ui.row().classes("w-full justify-end gap-4"):
                        ui.button("ĐÓNG", on_click=d.close).props("flat")
                        async def send():
                            if await submit_review(request_id, int(rating.value), comment.value):
                                ui.notify("Cảm ơn bạn đã đánh giá!", type='positive')
                                d.close()
                                await update_ui()
                        ui.button("GỬI", on_click=send).classes("bg-primary text-white px-8 rounded-xl")
                d.open()

            # --- Polling ---
            ui.timer(5, update_ui)
            ui.timer(3, refresh_chat)
            await update_ui()
            await refresh_chat()
