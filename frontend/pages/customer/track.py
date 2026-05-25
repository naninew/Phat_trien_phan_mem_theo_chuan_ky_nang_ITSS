"""
Tracking Page - NiceGUI
Professional Rescue Tracking UI
"""

import asyncio
import requests
from nicegui import ui
from core.auth import require_role
from components.page_layout import page_layout
from services.rescue_api import (
    get_request_detail,
    cancel_request,
    get_chat_messages,
    send_chat_message,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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
        distance_km = route["distance"] / 1000  # Convert meters to km
        duration_min = route["duration"] / 60   # Convert seconds to minutes
        return [[c[1], c[0]] for c in coords], distance_km, duration_min
    except Exception:
        # Fallback: straight line with rough estimate
        import math
        lat1, lon1 = start
        lat2, lon2 = end
        # Rough distance using Haversine (in km)
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        distance = R * 2 * math.asin(math.sqrt(a))
        duration = distance / 30  # Assume ~30 km/h average
        return [list(start), list(end)], distance, duration


STATUS_COLORS: dict[str, str] = {
    "PENDING":   "warning",
    "ACCEPTED":  "info",
    "EN_ROUTE":  "primary",
    "ON_SITE":   "secondary",
    "COMPLETED": "positive",
    "CANCELLED": "negative",
}

TIMELINE_STEPS = [
    ("Gửi yêu cầu",    "PENDING",   "history"),
    ("Tiếp nhận",       "ACCEPTED",  "check_circle"),
    ("Đang di chuyển",  "EN_ROUTE",  "local_shipping"),
    ("Đang xử lý",      "ON_SITE",   "engineering"),
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

        # ── mutable state ────────────────────────────────────────────────
        state = {
            "user_marker":    None,
            "company_marker": None,
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
                        "border border-gray-200 p-6"
                    ):
                        with ui.row().classes(
                            "w-full items-center justify-between mb-4"
                        ):
                            ui.label("Trao đổi với đội cứu hộ").classes(
                                "text-xl font-bold font-outfit"
                            )
                            ui.icon("chat").classes("text-primary")

                        chat_area = ui.scroll_area().classes(
                            "w-full h-72 rounded-2xl bg-gray-50 p-4"
                        )

                        with ui.row().classes("w-full gap-3 mt-4"):
                            chat_input = ui.input(
                                placeholder="Nhập tin nhắn..."
                            ).classes("flex-1").props("outlined rounded dense")

                            ui.button(
                                icon="send",
                                on_click=lambda: asyncio.ensure_future(do_send()),
                            ).props("round unelevated color=primary")

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
        # CHAT HELPERS
        # ────────────────────────────────────────────────────────────────

        async def do_send() -> None:
            val = chat_input.value.strip()
            if not val:
                return
            ok = await send_chat_message(request_id, val)
            if ok:
                chat_input.value = ""
                await refresh_chat()

        async def refresh_chat() -> None:
            msgs = await get_chat_messages(request_id)
            chat_area.clear()
            with chat_area:
                for msg in msgs:
                    is_me = msg.get("is_me", False)
                    align = "items-end" if is_me else "items-start"
                    bubble_cls = (
                        "bg-primary text-white"
                        if is_me
                        else "bg-white border border-gray-200"
                    )
                    with ui.column().classes(f"w-full {align} mb-3"):
                        ui.label(msg["message"]).classes(
                            f"px-4 py-3 rounded-[22px] max-w-[75%] "
                            f"shadow-sm leading-relaxed {bubble_cls}"
                        )
                        ui.label(msg.get("created_at", "")).classes(
                            "text-[10px] opacity-50 px-2"
                        )

        # ────────────────────────────────────────────────────────────────
        # MAP UPDATE
        # ────────────────────────────────────────────────────────────────

        async def update_map(req: dict) -> None:
            user_pos = (req["latitude"], req["longitude"])
            company_pos = None
            if req.get("company_latitude"):
                company_pos = (
                    req["company_latitude"],
                    req["company_longitude"],
                )

            # User marker
            if state["user_marker"] is None:
                state["user_marker"] = map_widget.marker(latlng=user_pos)
            else:
                state["user_marker"].move(*user_pos)

            # Company marker + route
            if company_pos:
                if state["company_marker"] is None:
                    state["company_marker"] = map_widget.marker(
                        latlng=company_pos
                    )
                else:
                    state["company_marker"].move(*company_pos)

                # Run OSRM in a thread to get route + metrics
                route_points, distance_km, duration_min = await asyncio.get_event_loop().run_in_executor(
                    None, get_route, company_pos, user_pos
                )

                # Update distance and ETA labels
                distance_label.set_text(f"{distance_km:.1f} km")
                eta_label.set_text(f"ETA: {int(duration_min)} phút")

                # Draw route line (red polyline like Google Maps)
                await ui.run_javascript(
                    f"""
                    (function() {{
                        var el = getElement({map_widget.id});
                        if (!el) return;
                        var map = el._leaflet_map ?? el.leaflet ?? el._map;
                        if (!map) return;

                        // Remove old route if exists
                        if (window._rescueRoute) {{
                            map.removeLayer(window._rescueRoute);
                            window._rescueRoute = null;
                        }}

                        // Draw red polyline from company to user
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

                        // Fit map to show entire route
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
                    ui.label("Đang chờ đơn vị cứu hộ...").classes(
                        "italic opacity-50"
                    )
                    return

                ui.label("Đơn Vị Cứu Hộ").classes("text-xl font-bold mb-5")

                with ui.row().classes("items-center gap-4"):
                    ui.avatar(icon="business").classes(
                        "bg-primary/10 text-primary"
                    )
                    with ui.column().classes("gap-0"):
                        ui.label(req["company_name"]).classes(
                            "font-bold text-lg"
                        )
                        ui.label(
                            f"Hotline: {req.get('company_hotline', '--')}"
                        ).classes("text-sm text-primary")

                hotline = req.get("company_hotline", "")
                ui.button(
                    "GỌI HỖ TRỢ",
                    icon="phone",
                    on_click=lambda: ui.navigate.to(f"tel:{hotline}"),
                ).classes(
                    "w-full mt-6 bg-green-600 text-white "
                    "rounded-2xl font-bold py-4"
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
                        on_click=lambda: asyncio.ensure_future(
                            confirm_cancel()
                        ),
                    ).classes("w-full rounded-2xl font-bold py-4").props(
                        "outline color=negative"
                    )

        async def confirm_cancel() -> None:
            with ui.dialog() as dlg, ui.card().classes(
                "p-8 rounded-[28px] w-[420px]"
            ):
                ui.label("Xác nhận hủy yêu cầu?").classes(
                    "text-2xl font-bold mb-2"
                )
                ui.label("Đơn cứu hộ sẽ bị dừng ngay lập tức.").classes(
                    "mb-6 opacity-70"
                )
                with ui.row().classes("w-full justify-end gap-3"):
                    ui.button("Đóng", on_click=dlg.close).props("flat")

                    async def do_cancel() -> None:
                        ok = await cancel_request(request_id)
                        if ok:
                            ui.notify("Đã hủy yêu cầu", type="info")
                            dlg.close()
                            await update_ui()

                    ui.button("HỦY NGAY", on_click=do_cancel).classes(
                        "bg-red-500 text-white"
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

            # Status chip
            status_chip.set_text(req["status"])
            status_chip.props(
                f"color={STATUS_COLORS.get(req['status'], 'grey')}"
            )

            # Map (errors are swallowed so the timer keeps running)
            try:
                await update_map(req)
            except Exception as exc:
                print(f"[track] map update error: {exc}")

            # Side-panel widgets
            render_timeline(req)
            render_company(req)
            render_actions(req)

        # ────────────────────────────────────────────────────────────────
        # TIMERS
        # ────────────────────────────────────────────────────────────────

        update_timer = ui.timer(5.0, update_ui)
        chat_timer   = ui.timer(3.0, refresh_chat)

        def cleanup() -> None:
            update_timer.deactivate()
            chat_timer.deactivate()

        ui.context.client.on_disconnect(cleanup)

        # ────────────────────────────────────────────────────────────────
        # INITIAL LOAD
        # ────────────────────────────────────────────────────────────────

        await update_ui()
        await refresh_chat()