"""
Trang danh sách yêu cầu cứu hộ của khách hàng.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List

from nicegui import ui

from core.auth import require_role
from components.page_layout import page_layout
from services.rescue_api import cancel_request, get_my_requests


STATUS_MAP = {
    "PENDING": {
        "label": "Chờ tiếp nhận",
        "badge": "bg-amber-50 text-amber-700 border-amber-100",
        "bar": "bg-amber-400",
        "icon": "schedule",
    },
    "ACCEPTED": {
        "label": "Đã tiếp nhận",
        "badge": "bg-blue-50 text-blue-700 border-blue-100",
        "bar": "bg-blue-400",
        "icon": "verified",
    },
    "ASSIGNED": {
        "label": "Đã phân công",
        "badge": "bg-sky-50 text-sky-700 border-sky-100",
        "bar": "bg-sky-400",
        "icon": "assignment",
    },
    "ON_THE_WAY": {
        "label": "Đang di chuyển",
        "badge": "bg-cyan-50 text-cyan-700 border-cyan-100",
        "bar": "bg-cyan-400",
        "icon": "local_shipping",
    },
    "IN_PROGRESS": {
        "label": "Đang xử lý",
        "badge": "bg-indigo-50 text-indigo-700 border-indigo-100",
        "bar": "bg-indigo-400",
        "icon": "build_circle",
    },
    "COMPLETED": {
        "label": "Hoàn thành",
        "badge": "bg-emerald-50 text-emerald-700 border-emerald-100",
        "bar": "bg-emerald-400",
        "icon": "check_circle",
    },
    "CANCELLED": {
        "label": "Đã hủy",
        "badge": "bg-slate-100 text-slate-600 border-slate-200",
        "bar": "bg-slate-400",
        "icon": "cancel",
    },
    "REJECTED": {
        "label": "Bị từ chối",
        "badge": "bg-red-50 text-red-700 border-red-100",
        "bar": "bg-red-400",
        "icon": "block",
    },
}

STATUS_TABS = [
    ("all", "Tất cả"),
    ("PENDING", "Chờ tiếp nhận"),
    ("IN_PROGRESS_GROUP", "Đang xử lý"),
    ("COMPLETED", "Hoàn thành"),
    ("CANCELLED", "Đã hủy"),
]

ACTIVE_STATUSES = {"ACCEPTED", "ASSIGNED", "ON_THE_WAY", "IN_PROGRESS"}

TIMELINE_STEPS = [
    ("Gửi yêu cầu", "PENDING"),
    ("Tiếp nhận", "ACCEPTED"),
    ("Phân công", "ASSIGNED"),
    ("Đang đi", "ON_THE_WAY"),
    ("Xử lý", "IN_PROGRESS"),
    ("Hoàn tất", "COMPLETED"),
]


def create_requests_page():

    @ui.page('/customer/requests')
    async def requests_page():

        if not require_role("customer"):
            return

        state = {
            "all_requests": [],
            "status": "all",
            "search": "",
            "time": "all",
            "service": "all",
        }

        def status_config(status: str) -> Dict[str, str]:
            return STATUS_MAP.get(status, STATUS_MAP["PENDING"])

        def service_name(r: Dict[str, Any]) -> str:
            services = r.get("services") or []
            if services:
                return services[0].get("service_name") or "Dịch vụ cứu hộ"
            return r.get("incident_type") or "Dịch vụ cứu hộ"

        def parse_created_at(r: Dict[str, Any]):
            try:
                return datetime.fromisoformat(r["created_at"].replace("Z", "+00:00")).replace(tzinfo=None)
            except Exception:
                return None

        def format_time(value: str) -> str:
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%H:%M • %d/%m/%Y")
            except Exception:
                return value or "--"

        def format_money(value) -> str:
            if value is None:
                return "--"
            return f"{float(value):,.0f}".replace(",", ".") + " đ"

        def request_price(r: Dict[str, Any]):
            if r.get("agreed_price"):
                return r["agreed_price"], "Giá thực tế"
            services = r.get("services") or []
            estimated = sum((s.get("price") or 0) for s in services)
            if estimated:
                return estimated, "Giá dự kiến"
            return None, "Giá"

        def request_matches_status(r: Dict[str, Any], selected: str) -> bool:
            if selected == "all":
                return True
            if selected == "IN_PROGRESS_GROUP":
                return r.get("status") in ACTIVE_STATUSES
            if selected == "CANCELLED":
                return r.get("status") in {"CANCELLED", "REJECTED"}
            return r.get("status") == selected

        def time_matches(r: Dict[str, Any]) -> bool:
            selected = state["time"]
            if selected == "all":
                return True
            created = parse_created_at(r)
            if not created:
                return False
            now = datetime.now()
            if selected == "today":
                return created.date() == now.date()
            if selected == "7d":
                return created >= now - timedelta(days=7)
            if selected == "30d":
                return created >= now - timedelta(days=30)
            return True

        def filtered_requests() -> List[Dict[str, Any]]:
            query = state["search"].strip().lower()
            result = []
            for r in state["all_requests"]:
                if not request_matches_status(r, state["status"]):
                    continue
                if not time_matches(r):
                    continue
                if state["service"] != "all" and service_name(r) != state["service"]:
                    continue
                if query:
                    haystack = " ".join([
                        str(r.get("id", "")),
                        r.get("address_description") or "",
                        r.get("company_name") or "",
                        service_name(r),
                    ]).lower()
                    if query not in haystack:
                        continue
                result.append(r)
            return result

        def tab_count(key: str) -> int:
            return sum(1 for r in state["all_requests"] if request_matches_status(r, key))

        def status_group_count(*statuses: str) -> int:
            return sum(1 for r in state["all_requests"] if r.get("status") in statuses)

        def update_service_options():
            names = sorted({service_name(r) for r in state["all_requests"] if service_name(r)})
            service_filter.options = {"all": "Tất cả dịch vụ", **{name: name for name in names}}
            service_filter.update()

        with page_layout("/customer/requests", title="Yêu Cầu Của Tôi"):
            with ui.column().classes("w-full gap-5"):
                with ui.row().classes("w-full items-center justify-between gap-4"):
                    with ui.column().classes("gap-1"):
                        ui.label("Danh sách yêu cầu").classes(
                            "text-3xl font-bold text-slate-900 font-outfit"
                        )
                        ui.label("Theo dõi, lọc và quản lý lịch sử cứu hộ của bạn.").classes(
                            "text-sm text-slate-500"
                        )
                    ui.button(
                        "Gửi yêu cầu mới",
                        icon="add",
                        on_click=lambda: ui.navigate.to("/customer/find-rescue"),
                    ).classes(
                        "rounded-xl bg-blue-600 px-5 py-3 font-bold text-white shadow-sm hover:bg-blue-700"
                    ).props("unelevated")

                stats_container = ui.row().classes("w-full gap-3 flex-wrap")

                with ui.card().classes("w-full rounded-2xl border border-slate-100 bg-white p-4 shadow-sm"):
                    with ui.row().classes("w-full items-center gap-3 flex-wrap"):
                        search_input = ui.input(
                            placeholder="Tìm theo mã yêu cầu, địa chỉ, đơn vị cứu hộ..."
                        ).classes("min-w-[280px] flex-1").props("outlined dense rounded clearable")
                        search_input.on("update:model-value", lambda: _set_search(search_input.value))

                        time_filter = ui.select(
                            options={
                                "all": "Mọi thời gian",
                                "today": "Hôm nay",
                                "7d": "7 ngày gần đây",
                                "30d": "30 ngày gần đây",
                            },
                            value="all",
                            label="Thời gian",
                            on_change=lambda: _set_filter("time", time_filter.value),
                        ).classes("w-48").props("outlined dense rounded")

                        service_filter = ui.select(
                            options={"all": "Tất cả dịch vụ"},
                            value="all",
                            label="Dịch vụ",
                            on_change=lambda: _set_filter("service", service_filter.value),
                        ).classes("w-56").props("outlined dense rounded")

                        refresh_btn = ui.button(
                            icon="refresh",
                            on_click=lambda: _load_data(),
                        ).props("flat round color=primary")

                    tabs_container = ui.row().classes("w-full gap-2 mt-4 overflow-x-auto no-wrap")

                list_container = ui.column().classes("w-full gap-3")

        def _set_search(value):
            state["search"] = value or ""
            _render()

        def _set_filter(key: str, value):
            state[key] = value or "all"
            _render()

        def _set_status(value: str):
            state["status"] = value
            _render()

        def _render_stats():
            stats_container.clear()
            stat_items = [
                ("Tất cả", len(state["all_requests"]), "article", "text-blue-600", "bg-blue-50"),
                ("Chờ tiếp nhận", status_group_count("PENDING"), "schedule", "text-amber-600", "bg-amber-50"),
                ("Đang xử lý", status_group_count(*ACTIVE_STATUSES), "bolt", "text-indigo-600", "bg-indigo-50"),
                ("Hoàn thành", status_group_count("COMPLETED"), "check_circle", "text-emerald-600", "bg-emerald-50"),
                ("Đã hủy", status_group_count("CANCELLED", "REJECTED"), "cancel", "text-slate-600", "bg-slate-100"),
            ]
            with stats_container:
                for label, value, icon, icon_color, bg in stat_items:
                    with ui.card().classes(
                        "flex-1 min-w-[160px] rounded-2xl border border-slate-100 bg-white p-4 shadow-sm"
                    ):
                        with ui.row().classes("items-center justify-between gap-3"):
                            with ui.column().classes("gap-0"):
                                ui.label(label).classes("text-xs font-bold uppercase text-slate-400")
                                ui.label(str(value)).classes("text-2xl font-bold text-slate-900")
                            with ui.element("div").classes(
                                f"h-10 w-10 rounded-2xl {bg} flex items-center justify-center"
                            ):
                                ui.icon(icon, size="1.25rem").classes(icon_color)

        def _render_tabs():
            tabs_container.clear()
            with tabs_container:
                for key, label in STATUS_TABS:
                    active = state["status"] == key
                    count = tab_count(key)
                    classes = (
                        "bg-blue-600 text-white shadow-sm"
                        if active
                        else "bg-white text-slate-600 border border-slate-200 hover:bg-blue-50"
                    )
                    badge_classes = (
                        "bg-white/20 text-white"
                        if active
                        else "bg-slate-100 text-slate-600"
                    )
                    with ui.row().classes(
                        f"items-center gap-2 rounded-full px-4 py-2 text-sm font-bold "
                        f"whitespace-nowrap cursor-pointer transition-all {classes}"
                    ).on("click", lambda key=key: _set_status(key)):
                        ui.label(label)
                        ui.badge(str(count)).classes(f"rounded-full px-2 {badge_classes}")

        def _render_empty():
            with list_container:
                with ui.card().classes(
                    "w-full rounded-3xl border border-dashed border-slate-300 bg-white p-12 shadow-sm"
                ):
                    with ui.column().classes("items-center gap-3"):
                        ui.icon("inbox", size="4rem").classes("text-slate-200")
                        ui.label("Không tìm thấy yêu cầu phù hợp").classes(
                            "text-xl font-bold text-slate-600"
                        )
                        ui.label("Thử đổi bộ lọc hoặc tạo yêu cầu cứu hộ mới.").classes(
                            "text-sm text-slate-400"
                        )
                        ui.button(
                            "Tạo yêu cầu mới",
                            icon="add",
                            on_click=lambda: ui.navigate.to("/customer/find-rescue"),
                        ).classes("mt-2 rounded-xl bg-blue-600 px-5 py-2.5 font-bold text-white")

        def _render():
            _render_stats()
            _render_tabs()
            list_container.clear()
            reqs = filtered_requests()
            if not reqs:
                _render_empty()
                return
            with list_container:
                for request in reqs:
                    _render_request_item(request)

        async def _load_data():
            refresh_btn.props("loading")
            try:
                state["all_requests"] = await get_my_requests()
                update_service_options()
                _render()
            except Exception as e:
                ui.notify(f"Lỗi tải dữ liệu: {e}", type="negative")
            finally:
                refresh_btn.props(remove="loading")

        def _render_company(r: Dict[str, Any]):
            company_name = r.get("company_name")
            if not company_name:
                return

            logo = r.get("company_logo") or r.get("company_logo_url") or r.get("logo_url")
            rating = r.get("company_rating_avg") or r.get("rating_avg")
            rating_count = r.get("company_rating_count") or r.get("rating_count")

            with ui.row().classes("items-center gap-3"):
                if logo:
                    ui.image(logo).classes("h-10 w-10 rounded-xl object-cover border border-slate-100")
                else:
                    with ui.element("div").classes(
                        "h-10 w-10 rounded-xl bg-blue-50 flex items-center justify-center"
                    ):
                        ui.icon("business", size="1.25rem").classes("text-blue-600")
                with ui.column().classes("gap-0 min-w-0"):
                    ui.label(company_name).classes("text-sm font-bold text-slate-800 truncate")
                    if rating:
                        with ui.row().classes("items-center gap-1"):
                            ui.icon("star", size="0.9rem").classes("text-amber-500")
                            ui.label(f"{float(rating):.1f}").classes("text-xs font-bold text-amber-600")
                            if rating_count:
                                ui.label(f"({rating_count} đánh giá)").classes("text-xs text-slate-400")
                    else:
                        ui.label("Đơn vị cứu hộ").classes("text-xs text-slate-400")

        def _render_timeline(status: str):
            if status in ("CANCELLED", "REJECTED"):
                config = status_config(status)
                with ui.row().classes("items-center gap-2"):
                    ui.icon(config["icon"], size="1rem").classes("text-slate-500")
                    ui.label(config["label"]).classes("text-xs font-bold text-slate-500")
                return

            current_index = next(
                (i for i, (_, step_status) in enumerate(TIMELINE_STEPS) if step_status == status),
                0,
            )
            with ui.row().classes("w-full items-center gap-1 overflow-x-auto no-wrap"):
                for index, (label, _) in enumerate(TIMELINE_STEPS):
                    done = index <= current_index
                    ui.icon(
                        "check_circle" if done else "radio_button_unchecked",
                        size="0.95rem",
                    ).classes("text-blue-600" if done else "text-slate-300")
                    ui.label(label).classes(
                        "text-[11px] font-semibold whitespace-nowrap "
                        + ("text-slate-700" if done else "text-slate-400")
                    )
                    if index < len(TIMELINE_STEPS) - 1:
                        ui.element("div").classes(
                            "h-px w-5 " + ("bg-blue-200" if done else "bg-slate-200")
                        )

        def _render_request_item(r: Dict[str, Any]):
            config = status_config(r.get("status"))
            price, price_label = request_price(r)
            needs_review = r.get("status") == "COMPLETED" and not r.get("has_review")
            target_url = f"/customer/review/{r['id']}" if needs_review else f"/customer/track/{r['id']}"
            button_text = "Đánh giá" if needs_review else "Theo dõi"
            button_icon = "rate_review" if needs_review else "visibility"

            with ui.card().classes(
                "w-full overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-sm "
                "transition-all hover:border-blue-100 hover:shadow-md"
            ):
                with ui.row().classes("w-full no-wrap"):
                    ui.element("div").classes(f"w-1.5 {config['bar']}")
                    with ui.column().classes("flex-1 gap-3 p-4"):
                        with ui.row().classes("w-full items-start justify-between gap-4"):
                            with ui.column().classes("gap-1 min-w-0"):
                                with ui.row().classes("items-center gap-2 flex-wrap"):
                                    ui.label(f"#{r['id']}").classes("text-sm font-bold text-slate-400")
                                    with ui.row().classes(
                                        f"items-center gap-1 rounded-full border px-2.5 py-1 {config['badge']}"
                                    ):
                                        ui.icon(config["icon"], size="0.85rem")
                                        ui.label(config["label"]).classes("text-xs font-bold")
                                ui.label(service_name(r)).classes(
                                    "text-lg font-bold text-slate-900 leading-tight"
                                )
                                ui.label(format_time(r.get("created_at"))).classes("text-xs text-slate-400")

                            with ui.column().classes("items-end gap-0 shrink-0"):
                                ui.label(price_label).classes("text-xs font-bold uppercase text-slate-400")
                                ui.label(format_money(price) if price else "--").classes(
                                    "text-xl font-bold text-emerald-600"
                                )

                        with ui.row().classes("w-full gap-3 items-start flex-col lg:flex-row"):
                            with ui.row().classes(
                                "flex-1 items-start gap-2 rounded-xl bg-slate-50 px-3 py-2 min-w-0"
                            ):
                                ui.icon("place", size="1rem").classes("text-red-500 mt-0.5")
                                with ui.column().classes("gap-0 min-w-0"):
                                    ui.label("Vị trí").classes("text-[11px] font-bold uppercase text-slate-400")
                                    ui.label(r.get("address_description") or "N/A").classes(
                                        "text-sm font-semibold text-slate-700 leading-snug"
                                    )
                            with ui.element("div").classes("w-full lg:w-[260px] rounded-xl bg-blue-50/60 px-3 py-2"):
                                _render_company(r)

                        _render_timeline(r.get("status"))

                        with ui.row().classes("w-full items-center justify-end gap-2 pt-1"):
                            if r.get("status") == "PENDING":
                                ui.button(
                                    "Hủy",
                                    icon="close",
                                    on_click=lambda rid=r["id"]: _confirm_cancel(rid),
                                ).classes("rounded-xl px-3 font-semibold text-red-600").props("flat")

                            ui.button(
                                button_text,
                                icon=button_icon,
                                on_click=lambda url=target_url: ui.navigate.to(url),
                            ).classes(
                                "rounded-xl bg-blue-600 px-4 py-2 font-bold text-white hover:bg-blue-700"
                            ).props("unelevated")

        async def _confirm_cancel(request_id: int):
            with ui.dialog() as dialog, ui.card().classes("w-[420px] max-w-full rounded-3xl p-7"):
                ui.icon("warning", size="3rem").classes("text-red-500 mx-auto")
                ui.label("Xác nhận hủy yêu cầu").classes("text-2xl font-bold text-center mt-3")
                ui.label("Bạn có chắc chắn muốn hủy yêu cầu cứu hộ này không?").classes(
                    "text-center text-slate-500"
                )
                with ui.row().classes("w-full justify-end gap-3 mt-6"):
                    ui.button("Đóng", on_click=dialog.close).props("flat")

                    async def do_cancel():
                        try:
                            await cancel_request(request_id)
                            ui.notify("Đã hủy yêu cầu", type="info")
                            dialog.close()
                            await _load_data()
                        except Exception as e:
                            ui.notify(f"Lỗi: {e}", type="negative")

                    ui.button("Xác nhận hủy", icon="delete", on_click=do_cancel).classes(
                        "rounded-xl bg-red-500 px-5 font-bold text-white"
                    )

            dialog.open()

        await _load_data()
        timer = ui.timer(30, _load_data)
        ui.context.client.on_disconnect(timer.deactivate)
