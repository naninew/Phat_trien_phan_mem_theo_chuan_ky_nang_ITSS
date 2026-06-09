"""
Company Queue Management - NiceGUI
Includes embedded real-time chat panel per request (WebSocket)
"""
import asyncio
import json
from datetime import datetime
from nicegui import ui, app as nicegui_app
from typing import Optional, Dict, Any, List
from core.auth import require_role, get_access_token
from core.config import BACKEND_URL
from components.page_layout import page_layout
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

        # ── Chat State (per open dialog) ─────────────────────────────────────
        # Stores active WS tasks so we can cancel when dialog closes
        active_chat_tasks: Dict[int, asyncio.Task] = {}

        with page_layout("/company/queue", title="Hàng Đợi Cứu Hộ"):

            with ui.row().classes("w-full items-center justify-between mb-6"):
                with ui.column().classes("gap-0"):
                    ui.label("📊 Hàng Đợi Yêu Cầu").classes(
                        "text-3xl font-bold font-outfit text-primary"
                    )
                    ui.label("Tiếp nhận và điều phối nhân sự, phương tiện").classes("opacity-60")

                refresh_btn = ui.button(
                    icon="refresh", on_click=lambda: _load_data()
                ).props("flat round color=primary")

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
                new_snapshot = json.dumps(
                    {"queue": queue, "vehicles": vehicles, "staff": staff},
                    sort_keys=True,
                    default=str,
                )
                if auto_refresh and new_snapshot == queue_snapshot:
                    return

                queue_snapshot = new_snapshot
                queue_container.clear()
                with queue_container:
                    if not queue:
                        ui.label("Hàng đợi trống.").classes("italic opacity-50 py-20 self-center")
                    for r in queue:
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

            # ── Send handler ─────────────────────────────────────────────────

            async def _do_send():
                if chat_state["sending"]:
                    return

                val = chat_inp.value.strip()
                if not val:
                    return

                chat_state["sending"] = True
                chat_send_btn.disable()
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
                await _render_msgs.refresh()
                await _scroll_bottom()

                # Gửi REST API
                from services.rescue_api import send_chat_message
                try:
                    result = await send_chat_message(req_id, val)
                    if not result:
                        _remove_temp_message(temp_id)
                        await _render_msgs.refresh()
                        with ui_context:
                            ui.notify("Gửi thất bại", type="negative")
                        return

                    _confirm_temp_message(
                        temp_id=temp_id,
                        message=result.get("content", val),
                        sender_name="Bạn",
                        is_me=True,
                        stamp=datetime.now().strftime("%H:%M"),
                        msg_id=result.get("id"),
                    )
                    await _render_msgs.refresh()
                except Exception as e:
                    _remove_temp_message(temp_id)
                    await _render_msgs.refresh()
                    with ui_context:
                        ui.notify(f"Lỗi: {e}", type="negative")
                finally:
                    chat_state["sending"] = False
                    chat_send_btn.enable()

            chat_send_btn.on_click(lambda: asyncio.ensure_future(_do_send()))
            chat_inp.on("keydown.enter", lambda: asyncio.ensure_future(_do_send()))

            # ── WebSocket listener ───────────────────────────────────────────

            async def _ws_listener():
                ws_url = _ws_url(req_id, token)
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
                            retry = 0
                            with ui_context:
                                ws_status_lbl.set_text("Real-time ✓")

                            async for raw in ws:
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
                                    with ui_context:
                                        await _render_msgs.refresh()
                                        await _scroll_bottom()
                                elif t == "message":
                                    _append_message(
                                        message=data["message"],
                                        sender_name=data.get("sender_name", ""),
                                        is_me=data.get("is_me", False),
                                        stamp=data.get("created_at", ""),
                                        msg_id=data.get("id"),
                                    )
                                    with ui_context:
                                        await _render_msgs.refresh()
                                        await _scroll_bottom()
                                elif t == "error":
                                    with ui_context:
                                        ui.notify(data.get("message", "Không thể gửi tin nhắn"), type="negative")

                    except asyncio.CancelledError:
                        return
                    except Exception as e:
                        retry += 1
                        with ui_context:
                            ws_status_lbl.set_text(f"Mất kết nối ({retry}/{max_retry})...")
                        if retry > max_retry:
                            with ui_context:
                                ws_status_lbl.set_text("Không kết nối được")
                            break
                        await asyncio.sleep(min(2 ** retry, 30))

            # Khởi động WebSocket (chỉ khi websockets cài được)
            ws_task = None
            if _HAS_WEBSOCKETS and token:
                ws_task = asyncio.ensure_future(_ws_listener())
                active_chat_tasks[req_id] = ws_task
            else:
                with ui_context:
                    ws_status_lbl.set_text("Polling mode")
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
            with ui_context:
                with msg_scroll:
                    await _render_msgs()

            # Cleanup khi dialog đóng
            def _on_close():
                if ws_task and not ws_task.done():
                    ws_task.cancel()
                active_chat_tasks.pop(req_id, None)
                print(f"[chat] Dialog #{req_id} closed, cleanup done")

            chat_dlg.on("hide", lambda: _on_close())
            chat_dlg.open()

        # ── Queue Item renderer ────────────────────────────────────────────────

        def _render_queue_item(r, vehicles, staff):
            status_map = {
                "PENDING":     ("MỚI",       "warning"),
                "ACCEPTED":    ("ĐÃ NHẬN",   "info"),
                "ASSIGNED":    ("PHÂN CÔNG", "indigo"),
                "ON_THE_WAY":  ("DI CHUYỂN", "primary"),
                "IN_PROGRESS": ("XỬ LÝ",     "secondary"),
                "COMPLETED":   ("XONG",      "positive"),
                "REJECTED":    ("TỪ CHỐI",   "error"),
                "CANCELLED":   ("HỦY",       "gray"),
            }
            label, color = status_map.get(r['status'], (r['status'], "gray"))
            customer_name = r.get('customer_name', 'Khách hàng')

            with ui.card().classes(
                "w-full rounded-3xl p-6 border border-surface-variant/30 "
                "shadow-sm hover:shadow-md transition-all"
            ):
                with ui.row().classes("w-full justify-between items-start"):
                    with ui.column().classes("gap-1 flex-1"):
                        with ui.row().classes("items-center gap-3"):
                            ui.label(f"#{r['id']}").classes("font-bold opacity-30 text-sm")
                            ui.badge(label, color=color).classes("rounded-full px-3")

                        ui.label(r.get('service_name', 'Dịch vụ cứu hộ')).classes(
                            "text-2xl font-bold font-outfit mt-2"
                        )

                        with ui.row().classes("items-center gap-4 mt-2"):
                            with ui.row().classes("items-center gap-2"):
                                ui.icon("person", size="sm").classes("opacity-50")
                                ui.label(customer_name).classes("font-medium")
                            with ui.row().classes("items-center gap-2 text-primary font-bold"):
                                ui.icon("phone", size="sm")
                                ui.label(r.get('customer_phone', 'N/A'))

                        if r.get('incident_type'):
                            with ui.row().classes("items-center gap-2 mt-2"):
                                ui.icon("error_outline", size="sm").classes("text-warning")
                                ui.label(f"Sự cố: {r['incident_type']}").classes("font-bold text-sm text-warning")
                        if r.get('description'):
                            with ui.row().classes("items-start gap-2 mt-1"):
                                ui.icon("description", size="sm").classes("opacity-60 mt-0.5")
                                ui.label(f"Chi tiết: {r['description']}").classes("text-sm opacity-80 italic")

                    with ui.column().classes("items-end"):
                        ui.label("Vị trí yêu cầu:").classes(
                            "text-[10px] uppercase font-bold opacity-50"
                        )
                        ui.label(r.get('address_description', 'N/A')).classes(
                            "text-sm text-right max-w-xs"
                        )

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
                        elif r.get('rescue_vehicle_plate') or r.get('staff_name'):
                            if r.get('rescue_vehicle_plate'):
                                _info_chip("local_shipping", r['rescue_vehicle_plate'])
                            if r.get('staff_name'):
                                _info_chip("person_pin", r['staff_name'])

                    # Actions row
                    with ui.row().classes("gap-3 items-center"):
                        # 💬 Chat button – chỉ hiện khi đã nhận request
                        if r['status'] not in ('PENDING', 'CANCELLED', 'REJECTED'):
                            ui.button(
                                "Chat",
                                icon="chat_bubble_outline",
                                on_click=lambda req=r: (
                                    asyncio.ensure_future(_open_chat_dialog(req, ui.context.client))
                                ),
                            ).props("flat color=primary").classes("font-bold")

                        # Status Actions
                        if r['status'] == 'PENDING':
                            ui.button(
                                "TỪ CHỐI",
                                on_click=lambda: _do_reject(r['id'])
                            ).props("flat color=error")
                            ui.button(
                                "TIẾP NHẬN",
                                icon="check",
                                on_click=lambda: _do_accept(r['id'])
                            ).classes("bg-primary text-white font-bold rounded-xl px-6 py-3")

                        elif r['status'] == 'ACCEPTED':
                            ui.button(
                                "PHÂN CÔNG",
                                icon="assignment",
                                on_click=lambda: _show_assign_dialog(r, vehicles, staff)
                            ).classes("bg-indigo-600 text-white font-bold rounded-xl px-6")

                        elif r['status'] == 'ASSIGNED':
                            ui.button(
                                "BẮT ĐẦU DI CHUYỂN",
                                icon="navigation",
                                on_click=lambda: _update_status(r['id'], 'ON_THE_WAY')
                            ).classes("bg-primary text-white font-bold rounded-xl px-6")

                        elif r['status'] == 'ON_THE_WAY':
                            ui.button(
                                "ĐÃ ĐẾN HIỆN TRƯỜNG",
                                icon="place",
                                on_click=lambda: _update_status(r['id'], 'IN_PROGRESS')
                            ).classes("bg-secondary text-white font-bold rounded-xl px-6")

                        elif r['status'] == 'IN_PROGRESS':
                            ui.button(
                                "XÁC NHẬN HOÀN THÀNH",
                                icon="check_circle",
                                on_click=lambda: _show_complete_dialog(r)
                            ).classes("bg-positive text-white font-bold rounded-xl px-6")

        def _info_chip(icon, text):
            with ui.row().classes(
                "items-center gap-2 bg-surface-variant/10 px-3 py-1.5 rounded-full"
            ):
                ui.icon(icon, size="1rem").classes("text-primary")
                ui.label(text).classes("text-xs font-bold")

        async def _do_accept(req_id):
            try:
                await accept_request(req_id, eta_minutes=20)
                ui.notify("Đã tiếp nhận yêu cầu", type="positive")
                await _load_data()
            except Exception as e:
                ui.notify(f"Lỗi: {e}", type="negative")

        async def _show_assign_dialog(req, vehicles, staff):
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
                v_sel = ui.select(v_opts, label="Chọn Phương Tiện").classes(
                    "w-full mb-4"
                ).props("outlined rounded")

                s_opts = {
                    s['id']: f"NV #{s['id']} (Level {s['skill_level']})"
                    for s in staff if s['status'] == 'AVAILABLE'
                }
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

                    ui.button("XÁC NHẬN", on_click=assign).classes(
                        "bg-primary text-white px-8 rounded-xl font-bold"
                    )
            d.open()

        async def _show_complete_dialog(req):
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
                if await update_request_status(req_id, status):
                    ui.notify(f"Trạng thái mới: {status}", type="info")
                    await _load_data()
            except Exception as e:
                ui.notify(f"Lỗi: {e}", type="negative")

        await _load_data()
        timer = ui.timer(15, lambda: _load_data(auto_refresh=True))
        ui.context.client.on_disconnect(timer.deactivate)
