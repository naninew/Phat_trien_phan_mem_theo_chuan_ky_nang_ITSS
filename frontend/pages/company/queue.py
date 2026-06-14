"""
Company Queue Management - NiceGUI
Includes embedded real-time chat panel per request (WebSocket)
"""
import asyncio
import json
from datetime import datetime, timedelta, timezone
from nicegui import ui, app as nicegui_app
from typing import Optional, Dict, Any, List
from core.auth import require_role, get_access_token
from core.config import BACKEND_URL
from components.page_layout import page_layout
from components.company_ui import inject_company_styles, page_header, status_badge
from services.rescue_api import (
    get_company_queue,
    accept_request,
    reject_request,
    update_request_status,
    get_my_vehicles,
    get_company_staff,
    assign_request,
)

try:
    import websockets
    _HAS_WEBSOCKETS = True
except ImportError:
    _HAS_WEBSOCKETS = False


def _ws_url(request_id: int, token: str) -> str:
    base = BACKEND_URL.replace("https://", "wss://").replace("http://", "ws://")
    return f"{base}/ws/chat/{request_id}?token={token}"


def create_queue_page():
    """Register /company/queue route."""

    @ui.page('/company/queue')
    async def queue_page():
        if not require_role("company_staff"):
            return

        token = get_access_token()
        dialog_open = False
        inject_company_styles()
        ui.add_head_html("""
        <style>
        .company-queue-page {
            max-width: none;
            padding-left: 32px;
            padding-right: 32px;
        }
        @media (max-width: 640px) {
            .company-queue-page {
                padding-left: 12px;
                padding-right: 12px;
            }
        }
        </style>
        """)

        # ── Chat State (per open dialog) ─────────────────────────────────────
        # Stores active WS tasks so we can cancel when dialog closes
        active_chat_tasks: Dict[int, asyncio.Task] = {}

        async def _load_from_event(_=None):
            await _load_data()

        with page_layout("/company/queue", title=""):

            with ui.column().classes("company-page company-queue-page gap-5"):
                page_header(
                    "Hàng đợi cứu hộ",
                    "Tiếp nhận, trò chuyện và phân công nhân sự/phương tiện cho từng yêu cầu.",
                    "support_agent",
                )

                with ui.element("div").classes("company-card p-4 w-full"):
                    with ui.row().classes("w-full items-center gap-3 flex-wrap"):
                        ui.icon("filter_list", size="20px").classes("text-blue-600 flex-shrink-0")
                        ui.label("Bộ lọc:").classes("text-sm font-black text-slate-700 flex-shrink-0")

                        # Rescue ID filter
                        rescue_id_filter = ui.input(
                            placeholder="Mã cứu hộ"
                        ).classes("min-w-[180px] flex-1 company-field").props("outlined rounded dense clearable")
                        rescue_id_filter.on("keydown.enter", _load_from_event)

                        # Status filter
                        status_filter = ui.select(
                            options={
                                'all': 'Tất cả trạng thái',
                                'PENDING': 'Chờ duyệt',
                                'ACCEPTED': 'Đã nhận',
                                'ASSIGNED': 'Đã phân công',
                                'ON_THE_WAY': 'Đang di chuyển',
                                'IN_PROGRESS': 'Đang xử lý',
                                'COMPLETED': 'Hoàn thành'
                            },
                            value='all',
                            on_change=_load_from_event
                        ).classes("min-w-[220px] flex-1 company-field").props("outlined rounded dense")

                        # Time range dropdown
                        time_range = ui.select(
                            options={
                                'all': 'Tất cả thời gian',
                                '7d':  '7 ngày qua',
                                '1m':  '1 tháng qua',
                                '3m':  '3 tháng qua',
                                '6m':  '6 tháng qua',
                            },
                            value='all',
                            on_change=_load_from_event
                        ).classes("min-w-[220px] flex-1 company-field").props("outlined rounded dense")

                        with ui.row().classes("items-center gap-2 ml-auto flex-shrink-0"):
                            ui.button(
                                "Tìm kiếm", icon="search", on_click=_load_from_event
                            ).classes("company-primary-btn px-4").props("unelevated no-caps")
                            refresh_btn = ui.button(
                                "Làm mới", icon="refresh", on_click=_load_from_event
                            ).classes("company-muted-btn").props("flat no-caps")

                queue_container = ui.column().classes("w-full gap-4")

        # ── Logic ─────────────────────────────────────────────────────────────

        queue_snapshot = None

        async def _load_data(auto_refresh: bool = False):
            nonlocal queue_snapshot
            if auto_refresh and dialog_open:
                return

            if not auto_refresh:
                refresh_btn.props("loading")
            try:
                queue = await get_company_queue(status_filter.value)
                vehicles = await get_my_vehicles()
                staff = await get_company_staff()

                # Client-side filtering by rescue ID and time range
                rid_text = (rescue_id_filter.value or "").strip()
                tr = time_range.value

                if tr == '7d':
                    d_from = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                elif tr == '1m':
                    d_from = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
                elif tr == '3m':
                    d_from = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
                elif tr == '6m':
                    d_from = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
                else:
                    d_from = ''

                filtered_queue = queue
                if rid_text:
                    try:
                        rid = int(rid_text)
                        filtered_queue = [r for r in filtered_queue if r.get('id') == rid]
                    except ValueError:
                        filtered_queue = [r for r in filtered_queue if rid_text.lower() in str(r.get('id', '')).lower()]
                if d_from:
                    filtered_queue = [r for r in filtered_queue if str(r.get('created_at') or '')[:10] >= d_from]

                new_snapshot = json.dumps(
                    {"queue": filtered_queue, "vehicles": vehicles, "staff": staff,
                     "rid": rid_text, "tr": tr},
                    sort_keys=True,
                    default=str,
                )
                if auto_refresh and new_snapshot == queue_snapshot:
                    return

                queue_snapshot = new_snapshot
                queue_container.clear()
                with queue_container:
                    if not filtered_queue:
                        ui.label("Hàng đợi trống.").classes("italic opacity-50 py-20 self-center")
                    for r in filtered_queue:
                        _render_queue_item(r, vehicles, staff)
            except Exception as e:
                ui.notify(f"Lỗi: {e}", type="negative")
            finally:
                if not auto_refresh:
                    refresh_btn.props(remove="loading")

        # ──────────────────────────────────────────────────────────────────────
        # CHAT PANEL (embedded in dialog)
        # ──────────────────────────────────────────────────────────────────────

        async def _open_chat_dialog(r: Dict[str, Any], ui_context):
            """Mở dialog chat với customer của request r."""
            req_id = r['id']
            customer_name = r.get('customer_name', 'Khách hàng')

            # Nếu đã có dialog cho request này, không mở thêm
            chat_messages: List[Dict] = []
            chat_state = {
                "sending": False,
                "next_temp_id": 1,
                "confirmed_outgoing_ids": set(),
            }
            chat_lifecycle = {"closed": False}

            def _is_deleted_client_error(exc: Exception) -> bool:
                return "client this element belongs to has been deleted" in str(exc).lower()

            def _mark_chat_closed() -> None:
                chat_lifecycle["closed"] = True

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
                    # Tránh trùng lặp nếu đã tồn tại ID này
                    for m in chat_messages:
                        if m.get("id") == msg_id:
                            return
                    if is_me and msg_id in chat_state["confirmed_outgoing_ids"]:
                        return

                if temp_id is not None:
                    for m in chat_messages:
                        if m.get("temp_id") == temp_id:
                            return

                # Gộp tin tạm optimistic với tin thật trả về từ REST/WebSocket.
                # Nếu socket echo về sai phía, vẫn giữ bubble "Bạn" cho tin vừa gửi.
                for m in chat_messages:
                    if m["message"] == message and m.get("id") is None:
                        if msg_id is not None:
                            m["id"] = msg_id
                            m["sent"] = bool(m.get("sent")) or is_me
                            m["sender_name"] = "Bạn" if m["sent"] else sender_name
                            if stamp:
                                m["stamp"] = stamp
                            m.pop("temp_id", None)
                        return

                chat_messages.append({
                    "id": msg_id,
                    "temp_id": temp_id,
                    "message": message,
                    "sent": is_me,
                    "sender_name": sender_name,
                    "stamp": stamp,
                })

            def _remove_temp_message(temp_id: str) -> None:
                chat_messages[:] = [
                    m for m in chat_messages if m.get("temp_id") != temp_id
                ]

            def _confirm_temp_message(
                temp_id: str,
                message: str,
                sender_name: str,
                is_me: bool,
                stamp: str,
                msg_id: int = None,
            ) -> None:
                if msg_id is not None:
                    chat_state["confirmed_outgoing_ids"].add(msg_id)
                    for m in chat_messages:
                        if m.get("id") == msg_id and m.get("temp_id") != temp_id:
                            _remove_temp_message(temp_id)
                            return

                for m in chat_messages:
                    if m.get("temp_id") == temp_id:
                        m["id"] = msg_id
                        m["message"] = message
                        m["sent"] = is_me
                        m["sender_name"] = "Bạn" if is_me else sender_name
                        if stamp:
                            m["stamp"] = stamp
                        m.pop("temp_id", None)
                        return

                _append_message(message, sender_name, is_me, stamp, msg_id=msg_id)

            with ui_context:
                with ui.dialog() as chat_dlg, ui.card().classes(
                    "w-[520px] rounded-3xl p-0 overflow-hidden"
                ):
                    # Header
                    with ui.row().classes(
                        "w-full items-center justify-between px-6 py-4 "
                        "bg-primary text-white"
                    ):
                        with ui.row().classes("items-center gap-3"):
                            ui.icon("chat_bubble").classes("text-white")
                            with ui.column().classes("gap-0"):
                                ui.label(f"Chat – Yêu cầu #{req_id}").classes(
                                    "font-bold text-lg"
                                )
                                ws_status_lbl = ui.label("Đang kết nối...").classes(
                                    "text-xs opacity-80"
                                )

                        ui.button(icon="close", on_click=chat_dlg.close).props(
                            "flat round dense"
                        ).classes("text-white")

                    # Request details box
                    with ui.column().classes("w-full bg-blue-50/50 p-4 border-b gap-1"):
                        with ui.row().classes("items-center gap-2"):
                            ui.icon("build", size="xs").classes("text-primary")
                            ui.label(f"Dịch vụ: {r.get('service_name', 'Cứu hộ')}").classes("font-bold text-sm text-primary")
                        ui.label(f"Loại sự cố: {r.get('incident_type', 'N/A')}").classes("text-xs font-semibold")
                        ui.label(f"Chi tiết: {r.get('description', 'N/A')}").classes("text-xs opacity-85")

                    # Messages area
                    msg_scroll = ui.scroll_area().classes("w-full px-4 pt-4").style(
                        "height: 380px"
                    ).props("visible-axis=vertical")

                    # Input row
                    with ui.row().classes("w-full items-center gap-3 px-4 py-4 border-t"):
                        chat_inp = ui.input(
                            placeholder="Nhập tin nhắn..."
                        ).classes("flex-1").props("outlined rounded dense")
                        chat_send_btn = ui.button(icon="send").props(
                            "round unelevated color=primary"
                        )

            # ── Refreshable message renderer ─────────────────────────────────

            @ui.refreshable
            async def _render_msgs():
                if not chat_messages:
                    ui.label("Chưa có tin nhắn").classes("text-center my-8 opacity-50")
                    return
                for msg in chat_messages:
                    is_me = msg.get("sent", False)
                    name = "Bạn" if is_me else msg.get("sender_name", customer_name)

                    with ui.row().classes(
                        "w-full items-end gap-2 mb-2" + (" justify-end" if is_me else "")
                    ):
                        if not is_me:
                            with ui.avatar(size="sm").classes("text-xs bg-orange-100 text-orange-600"):
                                ui.label(name[0].upper() if name else "?")

                        with ui.column().classes(
                            "gap-0.5 max-w-[280px]" + (" items-end" if is_me else "")
                        ):
                            with ui.row().classes(
                                "gap-2 px-3" + (" flex-row-reverse" if is_me else "")
                            ):
                                ui.label(name).classes("text-xs font-semibold opacity-70")
                                ui.label(msg.get("stamp", "")).classes("text-xs opacity-40")

                            with ui.card().classes(
                                "rounded-3xl px-4 py-2 shadow-sm border-0 " +
                                ("bg-primary text-white" if is_me else "bg-gray-100 text-gray-800")
                            ):
                                ui.label(msg["message"]).classes(
                                    "text-sm leading-relaxed break-words"
                                )

            async def _scroll_bottom():
                try:
                    await asyncio.sleep(0.1)
                    msg_scroll.scroll_to(percent=1.0)
                except Exception as e:
                    print(f"[scroll error] {e}")

            def _set_ws_status(text: str) -> bool:
                if chat_lifecycle["closed"]:
                    return False
                try:
                    with ui_context:
                        ws_status_lbl.set_text(text)
                    return True
                except RuntimeError as e:
                    if _is_deleted_client_error(e):
                        _mark_chat_closed()
                        return False
                    raise

            async def _refresh_chat_view(scroll: bool = True) -> bool:
                if chat_lifecycle["closed"]:
                    return False
                try:
                    with ui_context:
                        await _render_msgs.refresh()
                        if scroll:
                            await _scroll_bottom()
                    return True
                except RuntimeError as e:
                    if _is_deleted_client_error(e):
                        _mark_chat_closed()
                        return False
                    raise

            def _notify_chat(message: str, type_: str = "info") -> bool:
                if chat_lifecycle["closed"]:
                    return False
                try:
                    with ui_context:
                        ui.notify(message, type=type_)
                    return True
                except RuntimeError as e:
                    if _is_deleted_client_error(e):
                        _mark_chat_closed()
                        return False
                    raise

            # ── Send handler ─────────────────────────────────────────────────

            async def _do_send():
                if chat_lifecycle["closed"]:
                    return
                if chat_state["sending"]:
                    return

                val = chat_inp.value.strip()
                if not val:
                    return

                chat_state["sending"] = True
                chat_send_btn.disable()
                temp_id = ""
                try:
                    temp_id = f"pending-{chat_state['next_temp_id']}"
                    chat_state["next_temp_id"] += 1

                    # Optimistic
                    _append_message(
                        message=val,
                        sender_name="Bạn",
                        is_me=True,
                        stamp=datetime.now().strftime("%H:%M"),
                        temp_id=temp_id,
                    )
                    chat_inp.value = ""
                    if not await _refresh_chat_view():
                        return

                    # Gửi REST API
                    from services.rescue_api import send_chat_message
                    result = await send_chat_message(req_id, val)
                    if not result:
                        _remove_temp_message(temp_id)
                        await _refresh_chat_view(scroll=False)
                        _notify_chat("Gửi thất bại", "negative")
                        return

                    _confirm_temp_message(
                        temp_id=temp_id,
                        message=result.get("content", val),
                        sender_name="Bạn",
                        is_me=True,
                        stamp=datetime.now().strftime("%H:%M"),
                        msg_id=result.get("id"),
                    )
                    await _refresh_chat_view(scroll=False)
                except Exception as e:
                    if temp_id:
                        _remove_temp_message(temp_id)
                    await _refresh_chat_view(scroll=False)
                    _notify_chat(f"Lỗi: {e}", "negative")
                finally:
                    chat_state["sending"] = False
                    if not chat_lifecycle["closed"]:
                        chat_send_btn.enable()

            chat_send_btn.on_click(lambda: asyncio.ensure_future(_do_send()))
            chat_inp.on("keydown.enter", lambda: asyncio.ensure_future(_do_send()))

            # ── WebSocket listener ───────────────────────────────────────────

            async def _ws_listener():
                ws_url = _ws_url(req_id, token)
                retry = 0
                max_retry = 5

                while retry <= max_retry and not chat_lifecycle["closed"]:
                    try:
                        async with websockets.connect(
                            ws_url,
                            ping_interval=20,
                            ping_timeout=10,
                            close_timeout=5,
                        ) as ws:
                            retry = 0
                            if not _set_ws_status("Real-time ✓"):
                                return

                            async for raw in ws:
                                if chat_lifecycle["closed"]:
                                    return
                                try:
                                    data = json.loads(raw)
                                except json.JSONDecodeError:
                                    continue

                                t = data.get("type")
                                if t == "pong":
                                    continue
                                elif t == "history":
                                    chat_messages.clear()
                                    for m in data.get("messages", []):
                                        _append_message(
                                            message=m["message"],
                                            sender_name=m.get("sender_name", ""),
                                            is_me=m.get("is_me", False),
                                            stamp=m.get("created_at", ""),
                                            msg_id=m.get("id"),
                                        )
                                    if not await _refresh_chat_view():
                                        return
                                elif t == "message":
                                    _append_message(
                                        message=data["message"],
                                        sender_name=data.get("sender_name", ""),
                                        is_me=data.get("is_me", False),
                                        stamp=data.get("created_at", ""),
                                        msg_id=data.get("id"),
                                    )
                                    if not await _refresh_chat_view():
                                        return
                                elif t == "error":
                                    if not _notify_chat(data.get("message", "Không thể gửi tin nhắn"), "negative"):
                                        return

                    except asyncio.CancelledError:
                        return
                    except Exception as e:
                        if _is_deleted_client_error(e):
                            _mark_chat_closed()
                            return
                        retry += 1
                        if not _set_ws_status(f"Mất kết nối ({retry}/{max_retry})..."):
                            return
                        if retry > max_retry:
                            _set_ws_status("Không kết nối được")
                            break
                        await asyncio.sleep(min(2 ** retry, 30))

            # Khởi động WebSocket (chỉ khi websockets cài được)
            ws_task = None
            if _HAS_WEBSOCKETS and token:
                ws_task = asyncio.ensure_future(_ws_listener())
                active_chat_tasks[req_id] = ws_task
            else:
                _set_ws_status("Polling mode")
                # Fallback: load history 1 lần
                from services.rescue_api import get_chat_messages
                try:
                    msgs = await get_chat_messages(req_id)
                    chat_messages.clear()
                    for m in msgs:
                        _append_message(
                            message=m["message"],
                            sender_name=m.get("sender_name", ""),
                            is_me=m.get("is_me", False),
                            stamp=m.get("created_at", ""),
                            msg_id=m.get("id"),
                        )
                except Exception as e:
                    print(f"[fallback] {e}")

            # Render lần đầu (WS sẽ override qua history event)
            try:
                with ui_context:
                    with msg_scroll:
                        await _render_msgs()
            except RuntimeError as e:
                if _is_deleted_client_error(e):
                    _mark_chat_closed()
                    if ws_task and not ws_task.done():
                        ws_task.cancel()
                    return
                raise

            # Cleanup khi dialog đóng
            def _on_close():
                _mark_chat_closed()
                if ws_task and not ws_task.done():
                    ws_task.cancel()
                active_chat_tasks.pop(req_id, None)
                print(f"[chat] Dialog #{req_id} closed, cleanup done")

            chat_dlg.on("hide", lambda: _on_close())
            chat_dlg.open()

        # ── Queue Item renderer ────────────────────────────────────────────────

        def _format_request_time(value) -> str:
            if not value:
                return "Chưa có thời gian"
            vietnam_tz = timezone(timedelta(hours=7))
            if isinstance(value, datetime):
                dt = value
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(vietnam_tz).strftime("%H:%M %d/%m/%Y")

            raw = str(value).strip()
            try:
                dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(vietnam_tz).strftime("%H:%M %d/%m/%Y")
            except ValueError:
                return raw.replace("T", " ")[:16]

        def _render_queue_item(r, vehicles, staff):
            status_map = {
                "PENDING":     ("Mới", "amber"),
                "ACCEPTED":    ("Đã nhận", "blue"),
                "ASSIGNED":    ("Đã phân công", "blue"),
                "ON_THE_WAY":  ("Đang di chuyển", "blue"),
                "IN_PROGRESS": ("Đang xử lý", "amber"),
                "COMPLETED":   ("Hoàn thành", "emerald"),
                "REJECTED":    ("Từ chối", "red"),
                "CANCELLED":   ("Đã hủy", "slate"),
            }
            label, tone = status_map.get(r['status'], (r['status'], "slate"))
            customer_name = r.get('customer_name', 'Khách hàng')

            with ui.element("div").classes("company-card company-card-hover w-full p-5"):
                with ui.row().classes("w-full justify-between items-start"):
                    with ui.column().classes("gap-3 flex-1 min-w-[360px]"):
                        with ui.row().classes("items-center gap-3"):
                            ui.label(f"#{r['id']}").classes("text-xs font-black text-slate-400")
                            status_badge(label, tone)

                        ui.label(r.get('service_name', 'Dịch vụ cứu hộ')).classes(
                            "text-2xl font-black font-outfit text-slate-900"
                        )

                        with ui.row().classes("items-center gap-3 flex-wrap"):
                            with ui.row().classes("items-center gap-2 rounded-xl bg-slate-50 px-3 py-2"):
                                ui.icon("person", size="18px").classes("text-slate-400")
                                ui.label(customer_name).classes("text-sm font-bold text-slate-700")
                            with ui.row().classes("items-center gap-2 rounded-xl bg-blue-50 px-3 py-2 text-blue-700 font-bold"):
                                ui.icon("phone", size="18px")
                                ui.label(r.get('customer_phone', 'N/A'))
                            with ui.row().classes("items-center gap-2 rounded-xl bg-slate-50 px-3 py-2"):
                                ui.icon("schedule", size="18px").classes("text-slate-400")
                                ui.label(_format_request_time(r.get('created_at'))).classes("text-sm font-semibold text-slate-500")

                        if r.get('incident_type'):
                            with ui.row().classes("items-center gap-2"):
                                ui.icon("report_problem", size="18px").classes("text-amber-500")
                                ui.label(f"Sự cố: {r['incident_type']}").classes("font-bold text-sm text-amber-700")
                        if r.get('description'):
                            with ui.row().classes("items-start gap-2"):
                                ui.icon("notes", size="18px").classes("text-slate-400 mt-0.5")
                                ui.label(r['description']).classes("text-sm text-slate-600 leading-relaxed")

                    with ui.element("div").classes("rounded-2xl bg-slate-50 p-4 w-full max-w-sm"):
                        with ui.row().classes("items-start gap-2"):
                            ui.icon("location_on", size="20px").classes("text-blue-600 mt-0.5")
                            with ui.column().classes("gap-1"):
                                ui.label("Vị trí").classes("text-xs font-black uppercase text-slate-400")
                                ui.label(r.get('address_description', 'N/A')).classes("text-sm font-semibold text-slate-700 leading-snug")

                ui.separator().classes("my-6 opacity-30")

                with ui.row().classes("w-full items-center justify-between"):
                    with ui.row().classes("gap-2 flex-wrap"):
                        assignment = r.get('assignment')
                        if assignment:
                            if assignment.get('rescue_vehicle_plate'):
                                _info_chip("local_shipping", assignment['rescue_vehicle_plate'])
                            if assignment.get('staff_name'):
                                _info_chip("person_pin", assignment['staff_name'])
                        elif r.get('rescue_vehicle_plate') or r.get('staff_name'):
                            if r.get('rescue_vehicle_plate'):
                                _info_chip("local_shipping", r['rescue_vehicle_plate'])
                            if r.get('staff_name'):
                                _info_chip("person_pin", r['staff_name'])

                    with ui.row().classes("gap-3 items-center"):
                        if r['status'] not in ('PENDING', 'CANCELLED', 'REJECTED'):
                            client = ui.context.client
                            ui.button(
                                "Chat",
                                icon="chat_bubble_outline",
                                on_click=lambda req=r, client=client: (
                                    asyncio.create_task(_open_chat_dialog(req, client))
                                ),
                            ).classes("company-muted-btn").props("flat no-caps")

                        if r['status'] == 'PENDING':
                            async def reject_current(req_id=r['id']):
                                await _do_reject(req_id)

                            async def accept_current(req_id=r['id']):
                                await _do_accept(req_id)

                            ui.button(
                                "Từ chối",
                                icon="close",
                                on_click=reject_current
                            ).props("flat no-caps").classes("rounded-xl text-red-600 font-bold")
                            ui.button(
                                "Tiếp nhận",
                                icon="check",
                                on_click=accept_current
                            ).classes("company-primary-btn px-5").props("unelevated no-caps")

                        elif r['status'] == 'ACCEPTED':
                            ui.button(
                                "Phân công",
                                icon="assignment",
                                on_click=lambda req=r: _show_assign_dialog(req, vehicles, staff)
                            ).classes("company-primary-btn px-5").props("unelevated no-caps")

                        elif r['status'] == 'ASSIGNED':
                            async def start_moving(req_id=r['id']):
                                await _update_status(req_id, 'ON_THE_WAY')

                            ui.button(
                                "Bắt đầu di chuyển",
                                icon="navigation",
                                on_click=start_moving
                            ).classes("company-primary-btn px-5").props("unelevated no-caps")

                        elif r['status'] == 'ON_THE_WAY':
                            async def mark_in_progress(req_id=r['id']):
                                await _update_status(req_id, 'IN_PROGRESS')

                            ui.button(
                                "Đã đến hiện trường",
                                icon="place",
                                on_click=mark_in_progress
                            ).classes("company-primary-btn px-5").props("unelevated no-caps")

                        elif r['status'] == 'IN_PROGRESS':
                            ui.button(
                                "Xác nhận hoàn thành",
                                icon="check_circle",
                                on_click=lambda req=r: _show_complete_dialog(req)
                            ).classes("company-primary-btn px-5").props("unelevated no-caps")

        def _info_chip(icon, text):
            with ui.row().classes(
                "items-center gap-2 rounded-full bg-slate-50 border border-slate-100 px-3 py-1.5"
            ):
                ui.icon(icon, size="16px").classes("text-blue-600")
                ui.label(text).classes("text-xs font-bold text-slate-700")

        async def _do_accept(req_id):
            try:
                await accept_request(req_id, eta_minutes=20)
                ui.notify("Đã tiếp nhận yêu cầu", type="positive")
                await _load_data()
            except Exception as e:
                ui.notify(f"Lỗi: {e}", type="negative")

        def _show_assign_dialog(req, vehicles, staff):
            nonlocal dialog_open
            dialog_open = True

            def close_dialog():
                nonlocal dialog_open
                dialog_open = False
                d.close()

            with ui.dialog().props("persistent") as d, ui.card().classes("p-8 rounded-3xl w-[450px]"):
                ui.label("Phân công cứu hộ").classes(
                    "text-2xl font-bold mb-6 font-outfit text-primary"
                )
                v_opts = {
                    v['id']: f"{v['plate_number']} ({v['vehicle_type']})"
                    for v in vehicles if v['status'] == 'available'
                }
                if not v_opts:
                    ui.label("Chưa có xe nào đang sẵn sàng để phân công.").classes(
                        "mb-3 rounded-xl bg-amber-50 px-3 py-2 text-sm font-bold text-amber-700"
                    )
                v_sel = ui.select(v_opts, label="Chọn Phương Tiện").classes(
                    "w-full mb-4"
                ).props("outlined rounded")

                s_opts = {
                    s['id']: f"NV #{s['id']} (Level {s['skill_level']})"
                    for s in staff if s['status'] == 'AVAILABLE'
                }
                if not s_opts:
                    ui.label("Chưa có nhân viên nào đang sẵn sàng để phân công.").classes(
                        "mb-3 rounded-xl bg-amber-50 px-3 py-2 text-sm font-bold text-amber-700"
                    )
                s_sel = ui.select(s_opts, label="Chọn Nhân Viên").classes(
                    "w-full mb-8"
                ).props("outlined rounded")

                with ui.row().classes("w-full justify-end gap-3"):
                    ui.button("HỦY", on_click=close_dialog).props("flat")

                    async def assign():
                        if not v_sel.value or not s_sel.value:
                            ui.notify("Vui lòng chọn đủ nhân sự và phương tiện", type="warning")
                            return
                        try:
                            await assign_request(req['id'], s_sel.value, v_sel.value)
                            ui.notify("Đã phân công thành công!", type="positive")
                            close_dialog()
                            await _load_data()
                        except Exception as e:
                            ui.notify(f"Lỗi: {e}", type="negative")

                    assign_btn = ui.button("XÁC NHẬN", on_click=assign).classes(
                        "bg-primary text-white px-8 rounded-xl font-bold"
                    )
                    if not v_opts or not s_opts:
                        assign_btn.disable()
            d.open()

        def _show_complete_dialog(req):
            nonlocal dialog_open
            dialog_open = True

            def close_dialog():
                nonlocal dialog_open
                dialog_open = False
                d.close()

            with ui.dialog().props("persistent") as d, ui.card().classes("p-8 rounded-3xl w-[400px]"):
                ui.label("Hoàn thành cứu hộ").classes(
                    "text-2xl font-bold mb-6 font-outfit text-primary"
                )
                price = ui.number(
                    label="Giá thực tế (VNĐ)", value=req.get('agreed_price')
                ).classes("w-full mb-4").props("outlined rounded")
                
                desc = ui.textarea(
                    label="Mô tả chi tiết hoá đơn", placeholder="Vd: Vá 2 lốp, thay 1 ruột..."
                ).classes("w-full mb-8").props("outlined rounded rows=3")

                with ui.row().classes("w-full justify-end gap-3"):
                    ui.button("HỦY", on_click=close_dialog).props("flat")

                    async def complete():
                        if price.value is None or price.value == "":
                            ui.notify("Vui lòng nhập bổ sung giá tiền dịch vụ", type="negative")
                            return
                        if not desc.value or not desc.value.strip():
                            ui.notify("Vui lòng nhập mô tả chi tiết hoá đơn", type="negative")
                            return
                            
                        try:
                            await update_request_status(
                                req['id'], 'COMPLETED', agreed_price=price.value, invoice_description=desc.value.strip()
                            )
                            ui.notify("Đã hoàn thành yêu cầu cứu hộ", type="positive")
                            close_dialog()
                            await _load_data()
                        except Exception as e:
                            ui.notify(f"Lỗi: {e}", type="negative")

                    ui.button("XÁC NHẬN", on_click=complete).classes(
                        "bg-positive text-white px-8 rounded-xl font-bold"
                    )
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
                await update_request_status(req_id, status)
                ui.notify(f"Trạng thái mới: {status}", type="info")
                await _load_data()
            except Exception as e:
                ui.notify(f"Lỗi: {e}", type="negative")

        await _load_data()
        timer = ui.timer(15, lambda: _load_data(auto_refresh=True))

        def _cleanup_page_tasks():
            timer.deactivate()
            for task in list(active_chat_tasks.values()):
                if not task.done():
                    task.cancel()
            active_chat_tasks.clear()

        ui.context.client.on_disconnect(_cleanup_page_tasks)
