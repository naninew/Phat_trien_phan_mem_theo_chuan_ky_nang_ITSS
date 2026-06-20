"""
Trang quản lý dịch vụ cứu hộ của công ty.
"""
from nicegui import ui
from core.auth import require_role
from components.page_layout import page_layout
from components.company_ui import inject_company_styles, page_header
from services import rescue_api


def create_services_management_page():

    @ui.page('/company/services')
    async def company_services_page():
        if not require_role("company_staff"):
            return

        inject_company_styles()
        ui.add_head_html("""
        <style>
            .service-dashboard .q-field__control { border-radius: 16px; }
            .service-dashboard.company-page {
                max-width: none;
                width: 100%;
                padding: 0 24px 28px;
                align-self: stretch;
            }
            .service-row {
                transition: background .16s ease, box-shadow .16s ease, transform .16s ease;
            }
            .service-row:hover {
                background: #f8fbff;
                box-shadow: inset 3px 0 0 #2563eb;
            }
            .service-table-shell {
                max-height: 560px;
                overflow-y: auto;
                overflow-x: hidden;
                width: 100%;
            }
            .service-table-head {
                position: sticky;
                top: 0;
                z-index: 5;
                backdrop-filter: blur(12px);
            }
        </style>
        """)

        state = {
            "services": [],
            "search": "",
            "status_filter": "all",
            "sort": "name",
        }

        metric_slots = {}
        trend_chart_slot = None
        popularity_chart_slot = None
        table_slot = None
        result_label = None

        def money(value: float) -> str:
            return f"{float(value or 0):,.0f} đ"

        def service_usage(service: dict) -> int:
            return int(service.get("usage_count") or service.get("request_count") or 0)

        def service_icon(service_name: str) -> str:
            name = (service_name or "").lower()
            if "kéo" in name or "cứu hộ" in name:
                return "local_shipping"
            if "ắc quy" in name or "kích" in name:
                return "battery_charging_full"
            if "lốp" in name or "vá" in name:
                return "tire_repair"
            if "nhiên liệu" in name or "xăng" in name:
                return "local_gas_station"
            if "khóa" in name:
                return "vpn_key"
            return "handyman"

        def filtered_services() -> list[dict]:
            rows = list(state["services"])
            search = state["search"].strip().lower()
            if search:
                rows = [
                    s for s in rows
                    if search in (s.get("service_name") or "").lower()
                    or search in (s.get("description") or "").lower()
                ]
            if state["status_filter"] == "active":
                rows = [s for s in rows if s.get("is_active")]
            elif state["status_filter"] == "inactive":
                rows = [s for s in rows if not s.get("is_active")]

            sort_key = state["sort"]
            if sort_key == "price_desc":
                rows.sort(key=lambda s: float(s.get("base_price") or 0), reverse=True)
            elif sort_key == "price_asc":
                rows.sort(key=lambda s: float(s.get("base_price") or 0))
            elif sort_key == "usage_desc":
                rows.sort(key=service_usage, reverse=True)
            elif sort_key == "status":
                rows.sort(key=lambda s: (not bool(s.get("is_active")), (s.get("service_name") or "").lower()))
            else:
                rows.sort(key=lambda s: (s.get("service_name") or "").lower())
            return rows

        def monthly_points(services: list[dict]) -> list[int]:
            total_requests = sum(service_usage(s) for s in services)
            if total_requests <= 0:
                return [0, 0, 0, 0, 0, 0]
            weights = [0.55, 0.7, 0.82, 0.92, 1.05, 1.2]
            base = max(1, total_requests / sum(weights))
            return [max(0, round(base * weight)) for weight in weights]

        def render_metric(slot_key: str, title: str, value: str, subtitle: str, trend: str, icon: str, color: str, bg: str):
            slot = metric_slots[slot_key]
            slot.clear()
            with slot:
                with ui.element("div").classes(
                    "h-full min-h-[112px] rounded-2xl p-4 shadow-sm transition-all "
                    "hover:-translate-y-0.5 hover:shadow-md"
                ).style(f"background:{bg}; border:1px solid color-mix(in srgb, {color} 18%, #e5e7eb);"):
                    with ui.row().classes("w-full items-start justify-between gap-3"):
                        with ui.column().classes("gap-1"):
                            ui.label(title).classes("text-[11px] font-black uppercase tracking-widest").style(
                                f"color: color-mix(in srgb, {color} 68%, #64748b);"
                            )
                            ui.label(value).classes("mt-2 text-3xl font-black leading-none font-outfit").style(
                                f"color: color-mix(in srgb, {color} 86%, #0f172a);"
                            )
                            ui.label(subtitle).classes("mt-1 text-xs font-bold text-slate-500")
                        with ui.column().classes("items-end gap-2"):
                            with ui.element("div").classes(
                                "h-11 w-11 rounded-2xl bg-white flex items-center justify-center shadow-sm"
                            ).style(f"color:{color};"):
                                ui.icon(icon, size="1.35rem")
                            ui.label(trend).classes(
                                "rounded-full bg-white/80 px-2 py-0.5 text-[11px] font-black text-emerald-700"
                            )

        def render_metrics():
            services = state["services"]
            total = len(services)
            active = sum(1 for s in services if s.get("is_active"))
            monthly = sum(service_usage(s) for s in services)
            revenue = sum(service_usage(s) * float(s.get("base_price") or 0) for s in services)
            render_metric("total", "Tổng dịch vụ", str(total), "Dịch vụ đã cấu hình", "+12%", "inventory_2", "#2563eb", "#eef4ff")
            render_metric("active", "Đang hoạt động", str(active), "Có thể nhận yêu cầu", "+8%", "check_circle", "#10b981", "#e8fbf3")
            render_metric("requests", "Yêu cầu tháng này", str(monthly), "Lượt sử dụng dịch vụ", "+18%", "trending_up", "#7c3aed", "#f4efff")
            render_metric("revenue", "Doanh thu", money(revenue), "Ước tính theo lượt dùng", "+21%", "payments", "#f59e0b", "#fff7e8")

        def render_charts():
            trend_chart_slot.clear()
            popularity_chart_slot.clear()
            services = state["services"]
            months = ["T1", "T2", "T3", "T4", "T5", "T6"]
            points = monthly_points(services)
            popular = sorted(services, key=service_usage, reverse=True)[:6]
            with trend_chart_slot:
                ui.echart({
                    "tooltip": {"trigger": "axis"},
                    "grid": {"left": 36, "right": 18, "top": 24, "bottom": 28},
                    "xAxis": {"type": "category", "boundaryGap": False, "data": months},
                    "yAxis": {"type": "value", "splitLine": {"lineStyle": {"color": "#eef2f7"}}},
                    "series": [{
                        "name": "Yêu cầu",
                        "type": "line",
                        "smooth": True,
                        "data": points,
                        "symbolSize": 8,
                        "lineStyle": {"width": 4, "color": "#2563eb"},
                        "itemStyle": {"color": "#2563eb"},
                        "areaStyle": {"color": "rgba(37, 99, 235, 0.12)"},
                    }],
                }).classes("h-[260px] w-full")
            with popularity_chart_slot:
                ui.echart({
                    "tooltip": {"trigger": "axis", "axisPointer": {"type": "shadow"}},
                    "grid": {"left": 112, "right": 18, "top": 18, "bottom": 28},
                    "xAxis": {"type": "value", "splitLine": {"lineStyle": {"color": "#eef2f7"}}},
                    "yAxis": {
                        "type": "category",
                        "data": [(s.get("service_name") or "Dịch vụ")[:18] for s in popular][::-1],
                        "axisLabel": {"fontWeight": 700},
                    },
                    "series": [{
                        "name": "Yêu cầu",
                        "type": "bar",
                        "data": [service_usage(s) for s in popular][::-1],
                        "barWidth": 14,
                        "itemStyle": {
                            "borderRadius": [0, 8, 8, 0],
                            "color": "#0f766e",
                        },
                    }],
                }).classes("h-[260px] w-full")

        def render_table():
            table_slot.clear()
            rows = filtered_services()
            if result_label:
                result_label.set_text(f"{len(rows)} dịch vụ")
            with table_slot:
                with ui.element("div").classes("service-table-shell rounded-2xl border border-slate-100 bg-white shadow-sm"):
                    with ui.element("div").classes(
                        "service-table-head grid w-full grid-cols-[minmax(0,2.6fr)_minmax(0,1.05fr)_minmax(0,.9fr)_minmax(0,.8fr)_minmax(0,1fr)_112px] "
                        "gap-3 border-b border-slate-100 bg-slate-50/90 px-4 py-3"
                    ):
                        for label in ["Dịch vụ", "Giá", "Thời gian", "Lượt dùng", "Trạng thái", "Thao tác"]:
                            ui.label(label).classes("text-xs font-black uppercase tracking-wide text-slate-500")

                    if not rows:
                        with ui.column().classes("w-full items-center gap-3 px-6 py-12"):
                            ui.icon("manage_search", size="2.5rem").classes("text-slate-300")
                            ui.label("Không có dịch vụ phù hợp").classes("text-base font-black text-slate-700")
                            ui.label("Thử đổi bộ lọc hoặc thêm dịch vụ mới.").classes("text-sm text-slate-500")
                        return

                    for row in rows:
                        with ui.element("div").classes(
                            "service-row grid w-full grid-cols-[minmax(0,2.6fr)_minmax(0,1.05fr)_minmax(0,.9fr)_minmax(0,.8fr)_minmax(0,1fr)_112px] "
                            "items-center gap-3 border-b border-slate-50 px-4 py-3 last:border-b-0"
                        ):
                            with ui.row().classes("min-w-0 items-center gap-3"):
                                with ui.element("div").classes(
                                    "h-10 w-10 min-w-[40px] rounded-2xl bg-blue-50 flex items-center justify-center text-blue-600"
                                ):
                                    ui.icon(service_icon(row.get("service_name", "")), size="1.25rem")
                                with ui.column().classes("min-w-0 gap-0"):
                                    ui.label(row.get("service_name") or "Chưa đặt tên").classes(
                                        "truncate text-sm font-black text-slate-950"
                                    )
                                    ui.label(row.get("description") or "Chưa có mô tả").classes(
                                        "truncate text-xs font-medium text-slate-500"
                                    )
                            ui.label(money(row.get("base_price"))).classes("text-sm font-black text-slate-900")
                            ui.label(f"{int(row.get('estimated_duration') or 0)} phút").classes(
                                "text-sm font-bold text-slate-600"
                            )
                            with ui.row().classes("items-center gap-2"):
                                ui.icon("bar_chart", size="1rem").classes("text-slate-400")
                                ui.label(str(service_usage(row))).classes("text-sm font-black text-slate-900")
                            status_class = (
                                "bg-emerald-50 text-emerald-700 border-emerald-200"
                                if row.get("is_active") else "bg-slate-100 text-slate-600 border-slate-200"
                            )
                            status_text = "Đang bật" if row.get("is_active") else "Tạm dừng"
                            ui.label(status_text).classes(
                                f"w-fit rounded-full border px-2.5 py-1 text-xs font-black {status_class}"
                            )
                            with ui.row().classes("justify-end gap-1 flex-nowrap"):
                                edit_btn = ui.button(icon="edit", on_click=lambda row=row: open_form(row)).props(
                                    "flat dense round"
                                ).classes("text-blue-600")
                                edit_btn.tooltip("Sửa dịch vụ")
                                toggle_icon = "pause_circle" if row.get("is_active") else "play_circle"
                                toggle_color = "text-amber-600" if row.get("is_active") else "text-emerald-600"
                                toggle_btn = ui.button(icon=toggle_icon, on_click=lambda row=row: toggle_status(row)).props(
                                    "flat dense round"
                                ).classes(toggle_color)
                                toggle_btn.tooltip("Tạm dừng" if row.get("is_active") else "Bật dịch vụ")
                                with ui.button(icon="more_horiz").props("flat dense round").classes("text-slate-500") as menu_btn:
                                    menu_btn.tooltip("Thao tác khác")
                                    with ui.menu().props("auto-close"):
                                        ui.menu_item("Nhân bản", lambda row=row: open_form({
                                            "service_name": f"{row.get('service_name', '')} Bản sao",
                                            "base_price": row.get("base_price") or 0,
                                            "estimated_duration": row.get("estimated_duration") or 30,
                                            "description": row.get("description") or "",
                                        }))
                                        ui.menu_item("Xóa", lambda row=row: confirm_delete(row))

        def refresh_page():
            render_metrics()
            render_charts()
            render_table()

        async def load_services():
            state["services"] = await rescue_api.get_company_services()
            refresh_page()

        def open_form(service=None):
            is_edit = bool(service) and service.get("service_id")
            with ui.dialog() as dlg, ui.card().classes('w-full max-w-md rounded-2xl p-6'):
                ui.label("Chỉnh sửa dịch vụ" if is_edit else "Thêm dịch vụ mới").classes('text-xl font-black text-slate-950')
                ui.label("Cập nhật giá, thời gian và trạng thái cung cấp.").classes("mb-4 text-sm text-slate-500")

                name_input = ui.input("Tên dịch vụ (*)", value=service.get('service_name', '') if service else "").props("outlined").classes("company-field w-full")
                price_input = ui.number("Giá cơ bản (VNĐ) (*)", value=float(service.get('base_price') or 0) if service else 0.0, min=0).props("outlined").classes("company-field w-full")
                duration_input = ui.number("Thời gian ước tính (phút)", value=int(service.get('estimated_duration') or 30) if service else 30, min=0).props("outlined").classes("company-field w-full")
                desc_input = ui.textarea("Mô tả", value=service.get('description', '') if service else "").props("outlined rows=3").classes("company-field w-full")

                async def save():
                    name = (name_input.value or "").strip()
                    try:
                        price = float(price_input.value or 0)
                        duration = int(duration_input.value or 0)
                    except (TypeError, ValueError):
                        ui.notify("Giá và thời gian phải là số hợp lệ", type="negative")
                        return
                    if not name:
                        ui.notify("Tên dịch vụ không được để trống", type="negative")
                        return
                    if price < 0:
                        ui.notify("Giá cơ bản phải lớn hơn hoặc bằng 0", type="negative")
                        return

                    if is_edit:
                        success = await rescue_api.update_company_service(
                            service['service_id'], name, price, duration, desc_input.value or ""
                        )
                        message = "Cập nhật thành công" if success else "Lỗi khi cập nhật"
                    else:
                        res = await rescue_api.add_company_service(
                            name, price, duration, desc_input.value or ""
                        )
                        success = bool(res.get("service_id"))
                        message = "Thêm mới thành công" if success else "Lỗi khi thêm mới"
                    ui.notify(message, type="positive" if success else "negative")
                    if success:
                        dlg.close()
                        await load_services()

                with ui.row().classes('mt-5 w-full justify-end gap-2'):
                    ui.button("Hủy", on_click=dlg.close).props("flat no-caps").classes("rounded-xl px-4 font-bold text-slate-500")
                    ui.button("Lưu dịch vụ", icon="check", on_click=save).props("unelevated no-caps").classes(
                        "rounded-xl bg-blue-700 px-4 font-black text-white"
                    )
            dlg.open()

        async def toggle_status(row):
            service_id = row['service_id']
            current_status = row['is_active']
            success = await rescue_api.toggle_company_service_status(service_id, not current_status)
            ui.notify("Đã cập nhật trạng thái" if success else "Lỗi khi cập nhật trạng thái",
                      type="positive" if success else "negative")
            if success:
                await load_services()

        def confirm_delete(row):
            service_id = row['service_id']
            with ui.dialog() as dlg, ui.card().classes('w-full max-w-sm rounded-2xl p-6 text-center'):
                ui.icon('warning', size='3rem').classes('mx-auto text-red-500')
                ui.label('Xóa dịch vụ?').classes('mt-2 text-xl font-black text-slate-950')
                ui.label(
                    'Nếu dịch vụ đã từng được sử dụng, hệ thống sẽ vô hiệu hóa thay vì xóa hoàn toàn để bảo vệ dữ liệu.'
                ).classes('mt-2 text-sm text-slate-500')

                async def do_delete():
                    success = await rescue_api.delete_company_service(service_id)
                    ui.notify("Đã xóa dịch vụ" if success else "Lỗi khi xóa",
                              type="positive" if success else "negative")
                    if success:
                        dlg.close()
                        await load_services()

                with ui.row().classes('mt-6 w-full gap-2'):
                    ui.button('Hủy', on_click=dlg.close).props('outline no-caps').classes(
                        'h-11 flex-1 rounded-xl font-bold'
                    )
                    ui.button('Xóa', icon='delete', on_click=do_delete).props('unelevated color=negative no-caps').classes(
                        'h-11 flex-1 rounded-xl font-black'
                    )
            dlg.open()

        with page_layout("/company/services", ""):
            with ui.column().classes("service-dashboard company-page gap-5").style("width:100%; max-width:none;"):
                page_header(
                    "Quản lý dịch vụ",
                    "Thiết lập danh mục, giá, trạng thái và hiệu suất từng dịch vụ.",
                    "handyman",
                    "Thêm dịch vụ",
                    "add",
                    lambda: open_form(),
                )

                with ui.element("div").classes("grid w-full grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4"):
                    for key in ["total", "active", "requests", "revenue"]:
                        metric_slots[key] = ui.element("div")

                with ui.element("div").classes("grid w-full grid-cols-1 gap-5 xl:grid-cols-[1.35fr_1fr]"):
                    with ui.element("div").classes("rounded-2xl border border-slate-100 bg-white p-5 shadow-sm"):
                        with ui.row().classes("w-full items-start justify-between gap-3"):
                            with ui.column().classes("gap-1"):
                                ui.label("Xu hướng dịch vụ theo tháng").classes("text-lg font-black text-slate-950")
                                ui.label("Số lượng yêu cầu trong 6 tháng gần nhất").classes("text-sm font-medium text-slate-500")
                            ui.label("Đang cập nhật").classes("rounded-full bg-blue-50 px-2.5 py-1 text-xs font-black text-blue-700")
                        trend_chart_slot = ui.element("div").classes("mt-3 w-full")
                    with ui.element("div").classes("rounded-2xl border border-slate-100 bg-white p-5 shadow-sm"):
                        with ui.column().classes("gap-1"):
                            ui.label("Mức độ phổ biến dịch vụ").classes("text-lg font-black text-slate-950")
                            ui.label("Các dịch vụ được yêu cầu nhiều nhất").classes("text-sm font-medium text-slate-500")
                        popularity_chart_slot = ui.element("div").classes("mt-3 w-full")

                with ui.element("div").classes("w-full self-stretch rounded-2xl border border-slate-100 bg-white p-5 shadow-sm").style("width:100%;"):
                    with ui.row().classes("w-full items-start justify-between gap-4"):
                        with ui.column().classes("gap-1"):
                            ui.label("Danh mục dịch vụ").classes("text-lg font-black text-slate-950")
                            result_label = ui.label("0 dịch vụ").classes("text-sm font-semibold text-slate-500")
                        ui.button("Thêm dịch vụ", icon="add", on_click=lambda: open_form()).props("unelevated no-caps").classes(
                            "h-10 rounded-xl bg-blue-700 px-4 text-sm font-black text-white shadow-sm"
                        )

                    with ui.row().classes("mt-4 w-full items-center gap-3"):
                        search_input = ui.input("Tìm kiếm dịch vụ", placeholder="Nhập tên hoặc mô tả dịch vụ").props(
                            "outlined dense clearable"
                        ).classes("company-field min-w-[260px] flex-1")
                        status_select = ui.select(
                            {"all": "Tất cả trạng thái", "active": "Đang bật", "inactive": "Tạm dừng"},
                            value="all",
                            label="Trạng thái",
                        ).props("outlined dense").classes("company-field w-full sm:w-[180px]")
                        sort_select = ui.select(
                            {
                                "name": "Sắp xếp: Tên",
                                "usage_desc": "Sắp xếp: Dùng nhiều",
                                "price_desc": "Sắp xếp: Giá cao",
                                "price_asc": "Sắp xếp: Giá thấp",
                                "status": "Sắp xếp: Trạng thái",
                            },
                            value="name",
                            label="Sắp xếp",
                        ).props("outlined dense").classes("company-field w-full sm:w-[190px]")

                    table_slot = ui.element("div").classes("mt-4 w-full")

        search_input.on("update:model-value", lambda: (state.update({"search": search_input.value or ""}), render_table()))
        status_select.on("update:model-value", lambda: (state.update({"status_filter": status_select.value}), render_table()))
        sort_select.on("update:model-value", lambda: (state.update({"sort": sort_select.value}), render_table()))

        ui.timer(0, load_services, once=True)
