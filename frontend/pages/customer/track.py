"""
Tracking Page - NiceGUI
Professional Rescue Tracking UI with real-time WebSocket chat
"""

import asyncio
import json
import requests
from datetime import datetime
from nicegui import ui, app as nicegui_app
from core.auth import require_role, get_access_token
from core.config import BACKEND_URL
from components.page_layout import page_layout
from services.rescue_api import (
    get_request_detail,
    cancel_request,
)

try:
    import websockets
    _HAS_WEBSOCKETS = True
except ImportError:
    _HAS_WEBSOCKETS = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ws_url(request_id: int, token: str) -> str:
    """Build WebSocket URL from BACKEND_URL (http→ws)."""
    base = BACKEND_URL.replace("https://", "wss://").replace("http://", "ws://")
    return f"{base}/ws/chat/{request_id}?token={token}"


def _notification_ws_url(token: str) -> str:
    """Build notification WebSocket URL from BACKEND_URL (http→ws)."""
    base = BACKEND_URL.replace("https://", "wss://").replace("http://", "ws://")
    return f"{base}/ws/notifications?token={token}"


def get_route(start: tuple, end: tuple) -> tuple[list[list[float]], float, float]:
    """
    Fetch a real driving route from OSRM.
    Returns: (route_points, distance_km, duration_minutes)
    """
    url = (
        f"https://router.project-osrm.org/route/v1/driving/"
        f"{start[1]},{start[0]};{end[1]},{end[0]}"
        "?overview=full&geometries=geojson"
    )
    try:
        data = requests.get(url, timeout=8).json()
        route = data["routes"][0]
        coords = route["geometry"]["coordinates"]
        distance_km = route["distance"] / 1000
        duration_min = route["duration"] / 60
        return [[c[1], c[0]] for c in coords], distance_km, duration_min
    except Exception:
        import math
        lat1, lon1 = start
        lat2, lon2 = end
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        distance = R * 2 * math.asin(math.sqrt(a))
        duration = distance / 30
        return [list(start), list(end)], distance, duration


STATUS_COLORS: dict[str, str] = {
    "PENDING":   "warning",
    "ACCEPTED":  "info",
    "ASSIGNED":  "primary",
    "ON_THE_WAY": "primary",
    "IN_PROGRESS": "secondary",
    "COMPLETED": "positive",
    "CANCELLED": "negative",
    "REJECTED":  "negative",
}

TIMELINE_STEPS = [
    ("Gửi yêu cầu",    "PENDING",   "history"),
    ("Tiếp nhận",       "ACCEPTED",  "check_circle"),
    ("Phân công",        "ASSIGNED",  "assignment"),
    ("Đang di chuyển",  "ON_THE_WAY",  "local_shipping"),
    ("Đang xử lý",      "IN_PROGRESS",   "engineering"),
    ("Hoàn thành",      "COMPLETED", "task_alt"),
]


# ---------------------------------------------------------------------------
# Page factory
# ---------------------------------------------------------------------------

def create_track_page() -> None:

    @ui.page("/customer/track/{request_id}")
    async def track_page(request_id: int) -> None:

        if not require_role("customer"):
            return

        token = get_access_token()
        if not token:
            ui.navigate.to("/login")
            return

        # ── mutable state ────────────────────────────────────────────────
        state = {
            "user_marker":    None,
            "company_marker": None,
            "ws_task":        None,  # asyncio task for WS connection
            "connected":      False,
        }

        # ────────────────────────────────────────────────────────────────
        # LAYOUT
        # ────────────────────────────────────────────────────────────────
        with page_layout(
            f"/customer/track/{request_id}",
            title=f"Theo Dõi #{request_id}",
        ):

            # ── header ───────────────────────────────────────────────────
            with ui.row().classes("w-full items-center gap-4 mb-6"):

                ui.button(
                    icon="arrow_back",
                    on_click=lambda: ui.navigate.to("/customer/requests"),
                ).props("flat round color=primary")

                with ui.column().classes("gap-0"):
                    ui.label(f"Yêu Cầu Cứu Hộ #{request_id}").classes(
                        "text-3xl font-bold font-outfit"
                    )
                    ui.label("Theo dõi trạng thái cứu hộ realtime").classes(
                        "text-sm opacity-60"
                    )

                ui.space()

                status_chip = ui.chip(
                    "ĐANG TẢI", icon="radio_button_checked"
                ).classes("px-4 py-2 text-sm font-bold")

            # ── two-column body ──────────────────────────────────────────
            with ui.row().classes("w-full gap-6 items-start"):

                # ── LEFT ─────────────────────────────────────────────────
                with ui.column().classes("flex-1 gap-6"):

                    # MAP card
                    with ui.card().classes(
                        "w-full rounded-[28px] shadow-2xl "
                        "border border-gray-200 overflow-hidden p-0"
                    ):
                        with ui.column().classes("w-full gap-0"):

                            # map header
                            with ui.row().classes(
                                "w-full items-center justify-between "
                                "px-6 py-4 border-b"
                            ):
                                with ui.column().classes("gap-0"):
                                    ui.label("Theo Dõi Vị Trí").classes(
                                        "text-xl font-bold"
                                    )
                                    ui.label("Realtime GPS tracking").classes(
                                        "text-sm opacity-60"
                                    )

                                with ui.row().classes("gap-3 items-center"):
                                    eta_label = ui.label("ETA: -- phút").classes(
                                        "text-sm font-medium"
                                    )
                                    distance_label = ui.label("-- km").classes(
                                        "text-sm font-medium"
                                    )

                            # leaflet map
                            map_widget = ui.leaflet(
                                center=(21.0285, 105.8542), zoom=13
                            ).classes("w-full h-[520px] z-0")

                            map_widget.tile_layer(
                                url_template=(
                                    "https://{s}.tile.openstreetmap.org"
                                    "/{z}/{x}/{y}.png"
                                )
                            )

                    # CHAT card
                    with ui.card().classes(
                        "w-full rounded-[28px] shadow-lg "
                        "border border-gray-200 p-6 flex flex-col"
                    ):
                        with ui.row().classes(
                            "w-full items-center justify-between mb-4"
                        ):
                            ui.label("Trao đổi với đội cứu hộ").classes(
                                "text-xl font-bold font-outfit"
                            )
                            with ui.row().classes("items-center gap-2"):
                                ws_status_dot = ui.icon("circle").classes(
                                    "text-xs text-gray-400"
                                )
                                ws_status_label = ui.label("Đang kết nối...").classes(
                                    "text-xs opacity-60"
                                )
                                ui.icon("chat").classes("text-primary")

                        # Chat messages container
                        chat_messages_container = ui.scroll_area().classes(
                            "w-full"
                        ).style("height: 340px").props("visible-axis=vertical")

                        # Chat input area
                        with ui.row().classes("w-full gap-3 mt-4"):
                            chat_input = ui.input(
                                placeholder="Nhập tin nhắn..."
                            ).classes("flex-1").props("outlined rounded dense")

                            send_btn = ui.button(
                                icon="send",
                            ).props("round unelevated color=primary")
                        chat_lock_notice = ui.label(
                            "Yêu cầu đã hoàn thành, cuộc trò chuyện đã được khóa."
                        ).classes("hidden mt-2 text-xs font-semibold text-slate-500")

                # ── RIGHT ────────────────────────────────────────────────
                with ui.column().classes("w-[360px] gap-6"):

                    # Timeline card
                    with ui.card().classes(
                        "w-full rounded-[28px] shadow-lg "
                        "border border-primary/20 bg-primary/5 p-8"
                    ):
                        ui.label("Tiến Độ Cứu Hộ").classes(
                            "text-2xl font-bold text-primary mb-6"
                        )
                        timeline = ui.column().classes("w-full gap-0")

                    # Company info card
                    company_info = ui.card().classes(
                        "w-full rounded-[28px] shadow-lg "
                        "border border-gray-200 p-6"
                    )

                    # Action buttons area
                    actions_area = ui.column().classes("w-full gap-4")

        # ────────────────────────────────────────────────────────────────
        # CHAT STATE & HELPERS
        # ────────────────────────────────────────────────────────────────

        chat_messages_list = []
        chat_state = {
            "sending": False,
            "next_temp_id": 1,
            "locked": False,
        }

        @ui.refreshable
        async def render_chat_messages() -> None:
            """Render chat messages Messenger-style."""
            if not chat_messages_list:
                ui.label("Chưa có tin nhắn").classes("mx-auto my-8 opacity-50")
            else:
                for msg in chat_messages_list:
                    is_sent = msg.get("sent", False)
                    sender_name = "Bạn" if is_sent else msg.get("sender_name", "Đội cứu hộ")

                    with ui.row().classes(
                        "w-full items-end gap-2 mb-3" + (" justify-end" if is_sent else "")
                    ):
                        if not is_sent:
                            with ui.avatar(size="sm").classes("text-xs bg-blue-500/20 text-blue-600"):
                                ui.label(sender_name[0].upper() if sender_name else "?")

                        with ui.column().classes("gap-1 max-w-xs" + (" items-end" if is_sent else "")):
                            with ui.row().classes("gap-2 px-3" + (" flex-row-reverse" if is_sent else "")):
                                ui.label(sender_name).classes("text-xs font-semibold opacity-75")
                                ui.label(msg.get("stamp", "")).classes("text-xs opacity-50")

                            with ui.card().classes(
                                "w-full rounded-3xl px-4 py-2 shadow-sm border-0 " +
                                ("bg-blue-100 text-gray-900" if is_sent else "bg-gray-200 text-gray-900")
                            ):
                                ui.label(msg["message"]).classes("text-sm leading-relaxed break-words")

        async def scroll_chat_to_bottom() -> None:
            """Auto-scroll chat area to bottom."""
            try:
                await asyncio.sleep(0.1)
                chat_messages_container.scroll_to(percent=1.0)
            except Exception as e:
                print(f"[scroll error] {e}")

        def _append_message(
            message: str,
            sender_name: str,
            is_me: bool,
            stamp: str,
            msg_id: int = None,
            temp_id: str = None,
        ):
            """Thêm tin nhắn vào danh sách (tránh trùng lặp)."""
            if msg_id is not None:
                for m in chat_messages_list:
                    if m.get("id") == msg_id:
                        return

            if temp_id is not None:
                for m in chat_messages_list:
                    if m.get("temp_id") == temp_id:
                        return

            # Gộp tin tạm optimistic với tin thật trả về từ server.
            for m in chat_messages_list:
                if m["message"] == message and m.get("id") is None:
                    if msg_id is not None:
                        m["id"] = msg_id
                        m["sent"] = is_me
                        m["sender_name"] = sender_name
                        if stamp:
                            m["stamp"] = stamp
                        m.pop("temp_id", None)
                    return

            chat_messages_list.append({
                "id": msg_id,
                "temp_id": temp_id,
                "message": message,
                "sent": is_me,
                "sender_name": sender_name,
                "stamp": stamp,
            })

        def _remove_temp_message(temp_id: str) -> None:
            chat_messages_list[:] = [
                m for m in chat_messages_list if m.get("temp_id") != temp_id
            ]

        # ────────────────────────────────────────────────────────────────
        # WEBSOCKET CLIENT
        # ────────────────────────────────────────────────────────────────

        async def _ws_listener() -> None:
            """
            Kết nối WebSocket tới backend và xử lý messages.
            Tự động reconnect nếu bị ngắt (tối đa 5 lần).
            """
            ws_url = _ws_url(request_id, token)
            retry = 0
            max_retry = 5

            while retry <= max_retry:
                try:
                    async with websockets.connect(
                        ws_url,
                        ping_interval=20,
                        ping_timeout=10,
                        close_timeout=5,
                    ) as ws:
                        state["connected"] = True
                        retry = 0  # reset on successful connect

                        # Update UI: connected
                        ws_status_dot.classes(remove="text-gray-400 text-red-500")
                        ws_status_dot.classes(add="text-green-500")
                        ws_status_label.set_text("Đang kết nối")

                        async for raw in ws:
                            try:
                                data = json.loads(raw)
                            except json.JSONDecodeError:
                                continue

                            msg_type = data.get("type")

                            if msg_type == "pong":
                                continue

                            elif msg_type == "history":
                                # Nhận lịch sử – load toàn bộ
                                chat_messages_list.clear()
                                for m in data.get("messages", []):
                                    _append_message(
                                        message=m["message"],
                                        sender_name=m.get("sender_name", ""),
                                        is_me=m.get("is_me", False),
                                        stamp=m.get("created_at", ""),
                                        msg_id=m.get("id"),
                                    )
                                await render_chat_messages.refresh()
                                await scroll_chat_to_bottom()

                            elif msg_type == "message":
                                # Tin nhắn mới real-time
                                _append_message(
                                    message=data["message"],
                                    sender_name=data.get("sender_name", ""),
                                    is_me=data.get("is_me", False),
                                    stamp=data.get("created_at", ""),
                                    msg_id=data.get("id"),
                                )
                                await render_chat_messages.refresh()
                                await scroll_chat_to_bottom()

                            elif msg_type == "error":
                                ui.notify(data.get("message", "Không thể gửi tin nhắn"), type="negative")

                except Exception as e:
                    state["connected"] = False
                    ws_status_dot.classes(remove="text-green-500 text-gray-400")
                    ws_status_dot.classes(add="text-red-500")
                    ws_status_label.set_text(f"Mất kết nối, thử lại ({retry+1}/{max_retry})...")
                    print(f"[WS] Connection error: {e}")

                    retry += 1
                    if retry > max_retry:
                        ws_status_label.set_text("Không thể kết nối real-time")
                        break
                    await asyncio.sleep(min(2 ** retry, 30))  # Exponential backoff

        # WS task ref để cleanup
        _ws_task_ref = {"task": None}

        async def start_ws():
            if not _HAS_WEBSOCKETS:
                ws_status_label.set_text("⚠ websockets chưa cài – dùng polling")
                ws_status_dot.classes(add="text-yellow-500")
                # Fallback polling
                ui.timer(3.0, lambda: asyncio.ensure_future(_poll_fallback()))
                return
            task = asyncio.ensure_future(_ws_listener())
            _ws_task_ref["task"] = task

        async def _poll_fallback():
            """Fallback polling nếu websockets không cài được."""
            from services.rescue_api import get_chat_messages
            try:
                server_msgs = await get_chat_messages(request_id)
                if len(server_msgs) != len(chat_messages_list):
                    chat_messages_list.clear()
                    for msg in server_msgs:
                        _append_message(
                            message=msg["message"],
                            sender_name=msg.get("sender_name", ""),
                            is_me=msg.get("is_me", False),
                            stamp=msg.get("created_at", ""),
                            msg_id=msg.get("id"),
                        )
                    await render_chat_messages.refresh()
            except Exception as e:
                print(f"[poll fallback] {e}")

        # ── SEND MESSAGE ─────────────────────────────────────────────────

        async def do_send(client_context) -> None:
            if chat_state["sending"] or chat_state["locked"]:
                return

            val = chat_input.value.strip()
            if not val:
                return

            chat_state["sending"] = True
            send_btn.disable()
            temp_id = f"pending-{chat_state['next_temp_id']}"
            chat_state["next_temp_id"] += 1

            # Optimistic update
            _append_message(
                message=val,
                sender_name="Bạn",
                is_me=True,
                stamp=datetime.now().strftime("%H:%M"),
                temp_id=temp_id,
            )
            chat_input.value = ""
            await render_chat_messages.refresh()
            await scroll_chat_to_bottom()

            # Gửi qua REST API (WS server sẽ broadcast đến company)
            from services.rescue_api import send_chat_message
            try:
                result = await send_chat_message(request_id, val)
                if not result:
                    _remove_temp_message(temp_id)
                    await render_chat_messages.refresh()
                    with client_context:
                        ui.notify("Gửi tin nhắn thất bại", type="negative")
                    return

                _append_message(
                    message=result.get("content", val),
                    sender_name="Bạn",
                    is_me=True,
                    stamp=datetime.now().strftime("%H:%M"),
                    msg_id=result.get("id"),
                )
                await render_chat_messages.refresh()
            except Exception as e:
                _remove_temp_message(temp_id)
                await render_chat_messages.refresh()
                with client_context:
                    ui.notify(f"Lỗi: {str(e)}", type="negative")
            finally:
                chat_state["sending"] = False
                send_btn.enable()

        def _send_handler():
            from nicegui import context
            client_context = context.client
            asyncio.ensure_future(do_send(client_context))

        send_btn.on_click(_send_handler)
        chat_input.on("keydown.enter", _send_handler)

        # ────────────────────────────────────────────────────────────────
        # MAP UPDATE
        # ────────────────────────────────────────────────────────────────

        async def update_map(req: dict) -> None:
            user_pos = (req["latitude"], req["longitude"])
            company_pos = None
            if req.get("company_latitude"):
                company_pos = (req["company_latitude"], req["company_longitude"])

            if state["user_marker"] is None:
                state["user_marker"] = map_widget.marker(latlng=user_pos)
            else:
                state["user_marker"].move(*user_pos)

            if company_pos:
                if state["company_marker"] is None:
                    state["company_marker"] = map_widget.marker(latlng=company_pos)
                else:
                    state["company_marker"].move(*company_pos)

                route_points, distance_km, duration_min = await asyncio.get_event_loop().run_in_executor(
                    None, get_route, company_pos, user_pos
                )

                distance_label.set_text(f"{distance_km:.1f} km")
                eta_label.set_text(f"ETA: {int(duration_min)} phút")

                await ui.run_javascript(
                    f"""
                    (function() {{
                        var el = getElement({map_widget.id});
                        if (!el) return;
                        var map = el._leaflet_map ?? el.leaflet ?? el._map;
                        if (!map) return;
                        if (window._rescueRoute) {{
                            map.removeLayer(window._rescueRoute);
                            window._rescueRoute = null;
                        }}
                        window._rescueRoute = L.polyline(
                            {route_points},
                            {{
                                color: '#dc2626',
                                weight: 8,
                                opacity: 0.9,
                                lineCap: 'round',
                                lineJoin: 'round'
                            }}
                        ).addTo(map);
                        map.fitBounds(
                            window._rescueRoute.getBounds(),
                            {{ padding: [60, 60] }}
                        );
                    }})();
                    """,
                    timeout=10.0,
                )

        # ────────────────────────────────────────────────────────────────
        # TIMELINE
        # ────────────────────────────────────────────────────────────────

        def render_timeline(req: dict) -> None:
            timeline.clear()
            current = req["status"]
            active = True
            with timeline:
                for label, status, icon_name in TIMELINE_STEPS:
                    with ui.row().classes("items-center gap-4 py-4"):
                        ui.icon(
                            icon_name,
                            color="primary" if active else "grey-4",
                        ).classes("transition-all duration-300")
                        ui.label(label).classes(
                            "font-bold transition-all duration-300 "
                            + ("text-primary" if active else "opacity-40")
                        )
                    if status == current:
                        active = False

        # ────────────────────────────────────────────────────────────────
        # COMPANY INFO
        # ────────────────────────────────────────────────────────────────

        def render_company(req: dict) -> None:
            company_info.clear()
            with company_info:
                if not req.get("company_name"):
                    ui.label("Đang chờ đơn vị cứu hộ...").classes("italic opacity-50")
                    return

                ui.label("Đơn Vị Cứu Hộ").classes("text-xl font-bold mb-5")

                with ui.row().classes("items-center gap-4"):
                    ui.avatar(icon="business").classes("bg-primary/10 text-primary")
                    with ui.column().classes("gap-0"):
                        ui.label(req["company_name"]).classes("font-bold text-lg")
                        ui.label(
                            f"Hotline: {req.get('company_hotline', '--')}"
                        ).classes("text-sm text-primary")

                hotline = req.get("company_hotline", "")
                ui.button(
                    "GỌI HỖ TRỢ",
                    icon="phone",
                    on_click=lambda: ui.navigate.to(f"tel:{hotline}"),
                ).classes(
                    "w-full mt-6 bg-green-600 text-white rounded-2xl font-bold py-4"
                )

        # ────────────────────────────────────────────────────────────────
        # ACTIONS
        # ────────────────────────────────────────────────────────────────

        def render_actions(req: dict) -> None:
            actions_area.clear()
            with actions_area:
                if req["status"] in ("PENDING", "ACCEPTED"):
                    ui.button(
                        "HỦY YÊU CẦU",
                        icon="cancel",
                        on_click=confirm_cancel,
                    ).classes("w-full rounded-2xl font-bold py-4").props(
                        "outline color=negative"
                    )
                elif req["status"] == "COMPLETED":
                    price = req.get("agreed_price")
                    invoice_desc = req.get("invoice_description")
                    with ui.card().classes("w-full rounded-[28px] border-2 border-emerald-500 bg-emerald-50 p-6 shadow-lg"):
                        with ui.column().classes("w-full items-center text-center gap-2"):
                            ui.icon("payments", size="3rem").classes("text-emerald-500")
                            ui.label("Số tiền cần trả").classes("text-xl font-bold text-emerald-700")
                            if price is not None:
                                ui.label(f"{price:,.0f} đ").classes("text-3xl font-bold text-emerald-800")
                                if invoice_desc:
                                    ui.label("Chi tiết hoá đơn:").classes("text-xs text-emerald-600 mt-2 font-semibold")
                                    ui.label(invoice_desc).classes("text-sm text-emerald-800 italic")
                            else:
                                ui.label("Đang chờ cập nhật chi phí...").classes("italic opacity-70")

                    ui.button(
                        "XEM ĐÁNH GIÁ" if req.get("has_review") else "OK",
                        icon="check",
                        on_click=lambda: ui.navigate.to(f"/customer/review/{request_id}"),
                    ).classes(
                        "w-full rounded-2xl font-bold py-4 bg-emerald-600 text-white"
                    ).props("unelevated")

        async def confirm_cancel() -> None:
            with ui.dialog() as dlg, ui.card().classes("p-8 rounded-[28px] w-[420px]"):
                ui.label("Xác nhận hủy yêu cầu?").classes("text-2xl font-bold mb-2")
                ui.label("Đơn cứu hộ sẽ bị dừng ngay lập tức.").classes("mb-6 opacity-70")
                with ui.row().classes("w-full justify-end gap-3"):
                    ui.button("Đóng", on_click=dlg.close).props("flat").classes(
                    "rounded-xl px-5 py-2 font-medium"
                )
                    async def do_cancel() -> None:
                        try:
                            data = await cancel_request(request_id)
                            ui.notify("Đã hủy yêu cầu", type="info")
                            dlg.close()
                            await update_ui()
                            if data.get("status") == "CANCELLED":
                                status_chip.set_text("CANCELLED")
                        except Exception as e:
                            ui.notify(f"Lỗi: {str(e)}", type="negative")

                    ui.button("HỦY NGAY", on_click=do_cancel).classes(
                       "bg-red-600 hover:bg-red-700 "
                        "text-white rounded-xl px-6 py-2 "
                        "font-bold transition-all"
                    )
            dlg.open()

        # ────────────────────────────────────────────────────────────────
        # MAIN UPDATE LOOP
        # ────────────────────────────────────────────────────────────────

        async def update_ui() -> None:
            try:
                req = await get_request_detail(request_id)
            except Exception:
                return
            if not req:
                return

            status_chip.set_text(req["status"])
            status_chip.props(f"color={STATUS_COLORS.get(req['status'], 'grey')}")
            if req["status"] == "COMPLETED":
                chat_state["locked"] = True
                chat_input.disable()
                send_btn.disable()
                chat_input.props('placeholder="Cuộc trò chuyện đã khóa"')
                chat_lock_notice.classes(remove="hidden")
            else:
                chat_state["locked"] = False
                chat_input.enable()
                if not chat_state["sending"]:
                    send_btn.enable()
                chat_input.props('placeholder="Nhập tin nhắn..."')
                chat_lock_notice.classes(add="hidden")

            try:
                await update_map(req)
            except Exception as exc:
                print(f"[track] map update error: {exc}")

            render_timeline(req)
            render_company(req)
            render_actions(req)

        async def _status_ws_listener() -> None:
            if not _HAS_WEBSOCKETS:
                return

            while get_access_token():
                try:
                    async with websockets.connect(
                        _notification_ws_url(token),
                        ping_interval=20,
                        ping_timeout=10,
                        close_timeout=5,
                    ) as ws:
                        async for raw in ws:
                            try:
                                data = json.loads(raw)
                            except json.JSONDecodeError:
                                continue

                            notification = data.get("notification") or {}
                            event_request_id = notification.get("request_id") or data.get("request_id")
                            if data.get("type") == "notification" and int(event_request_id or 0) == int(request_id):
                                await update_ui()
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    print(f"[track status ws] {exc}")
                    await asyncio.sleep(3)

        # ────────────────────────────────────────────────────────────────
        # TIMERS & CLEANUP
        # ────────────────────────────────────────────────────────────────

        update_timer = ui.timer(5.0, update_ui)
        status_ws_task = asyncio.create_task(_status_ws_listener()) if _HAS_WEBSOCKETS else None

        def cleanup() -> None:
            update_timer.deactivate()
            task = _ws_task_ref.get("task")
            if task and not task.done():
                task.cancel()
            if status_ws_task and not status_ws_task.done():
                status_ws_task.cancel()

        ui.context.client.on_disconnect(cleanup)

        # ────────────────────────────────────────────────────────────────
        # INITIAL LOAD
        # ────────────────────────────────────────────────────────────────

        await update_ui()

        # Render empty chat container (WS sẽ load history)
        with chat_messages_container:
            await render_chat_messages()

        # Khởi động WebSocket listener
        await start_ws()
