"""
Trang báo cáo và thống kê dành cho Admin (UC-61 → UC-64).
"""
from datetime import date, timedelta

from nicegui import ui

from core.auth import require_admin_auth
from components.page_layout import page_layout
from services.admin_api import (
    get_companies,
    get_request_report,
    get_revenue_report,
    get_satisfaction_report,
    export_excel,
    export_pdf,
)

INCIDENT_OPTIONS = {
    "all": "Tất cả loại sự cố",
    "Hỏng máy": "Hỏng máy",
    "Thủng lốp": "Thủng lốp",
    "Hết xăng": "Hết xăng",
    "Tai nạn": "Tai nạn",
    "Chết máy": "Chết máy",
    "Khác": "Khác",
}

STATUS_OPTIONS = {
    "all": "Tất cả trạng thái",
    "PENDING": "Chờ xử lý",
    "IN_PROGRESS": "Đang xử lý",
    "COMPLETED": "Hoàn thành",
    "CANCELLED": "Đã hủy",
    "REJECTED": "Từ chối",
}

def create_reports_page():

    @ui.page("/admin/reports")
    async def reports_page():
        if not require_admin_auth():
            return

        today = date.today()
        default_from = (today - timedelta(days=30)).isoformat()
        default_to = today.isoformat()

        state = {
            "from_date": default_from,
            "to_date": default_to,
            "company_id": "all",
            "incident_type": "all",
            "status": "all",
        }

        companies = await get_companies()
        company_options = {"all": "Tất cả công ty"}
        for c in companies:
            company_options[str(c["id"])] = c.get("company_name", f"Công ty #{c['id']}")

        with page_layout("/admin/reports", title="Báo Cáo & Thống Kê"):
            with ui.row().classes("w-full items-center justify-between mb-4 flex-wrap gap-4"):
                with ui.column().classes("gap-0"):
                    ui.label("📊 Báo Cáo Hệ Thống").classes("text-3xl font-bold text-gray-800")
                    ui.label("Phân tích yêu cầu, doanh thu và mức độ hài lòng").classes("text-gray-500")

                with ui.row().classes("gap-2"):
                    ui.button(
                        "Xuất Excel",
                        icon="table_view",
                        on_click=lambda: _do_export("excel"),
                    ).props("outline").classes("rounded-xl")
                    ui.button(
                        "Xuất PDF",
                        icon="picture_as_pdf",
                        on_click=lambda: _do_export("pdf"),
                    ).props("outline").classes("rounded-xl")

            with ui.row().classes("w-full items-end gap-4 bg-white p-4 rounded-2xl shadow-sm border mb-4 flex-wrap"):
                from_input = ui.input("Từ ngày", value=default_from).props("type=date outlined dense").classes("w-40")
                to_input = ui.input("Đến ngày", value=default_to).props("type=date outlined dense").classes("w-40")

            with ui.tabs().classes("w-full") as tabs:
                tab_requests = ui.tab("Yêu cầu cứu hộ")
                tab_revenue = ui.tab("Doanh thu")
                tab_satisfaction = ui.tab("Mức độ hài lòng")

            with ui.tab_panels(tabs, value=tab_requests).classes("w-full bg-transparent"):
                with ui.tab_panel(tab_requests):
                    req_filters = ui.row().classes("w-full gap-4 mb-4 flex-wrap")
                    with req_filters:
                        company_sel = ui.select(
                            company_options, value="all", label="Công ty"
                        ).props("outlined dense").classes("min-w-[180px]")
                        incident_sel = ui.select(
                            INCIDENT_OPTIONS, value="all", label="Loại sự cố"
                        ).props("outlined dense").classes("min-w-[160px]")
                        status_sel = ui.select(
                            STATUS_OPTIONS, value="all", label="Trạng thái"
                        ).props("outlined dense").classes("min-w-[160px]")
                        ui.button("Áp dụng", icon="filter_alt", on_click=lambda: _load_requests()).classes(
                            "rounded-xl btn-primary"
                        )

                    req_summary = ui.row().classes("w-full gap-4 mb-4 flex-wrap")
                    req_status_table = ui.column().classes("w-full mb-4")
                    with ui.row().classes("w-full gap-6"):
                        with ui.card().classes("flex-1 m3-card p-6"):
                            ui.label("Phân bổ loại sự cố").classes("text-lg font-bold mb-2")
                            incident_chart = ui.echart(_pie_options([])).classes("w-full h-72")
                        with ui.card().classes("flex-1 m3-card p-6"):
                            ui.label("Yêu cầu theo ngày").classes("text-lg font-bold mb-2")
                            req_line_chart = ui.echart(_line_options([], [])).classes("w-full h-72")

                with ui.tab_panel(tab_revenue):
                    ui.button("Áp dụng bộ lọc ngày", icon="refresh", on_click=lambda: _load_revenue()).classes(
                        "rounded-xl mb-4"
                    )
                    rev_summary = ui.row().classes("w-full gap-4 mb-4")
                    with ui.card().classes("w-full m3-card p-6 mb-4"):
                        ui.label("Xếp hạng công ty theo doanh thu").classes("text-lg font-bold mb-4")
                        rev_company_table = ui.column().classes("w-full")
                    with ui.row().classes("w-full gap-6"):
                        with ui.card().classes("flex-1 m3-card p-6"):
                            ui.label("Doanh thu theo ngày").classes("text-lg font-bold mb-2")
                            rev_bar_chart = ui.echart(_bar_options([], [])).classes("w-full h-72")
                        with ui.card().classes("flex-1 m3-card p-6"):
                            ui.label("Phương thức thanh toán").classes("text-lg font-bold mb-2")
                            rev_pie_chart = ui.echart(_pie_options([])).classes("w-full h-72")

                with ui.tab_panel(tab_satisfaction):
                    ui.button("Áp dụng bộ lọc ngày", icon="refresh", on_click=lambda: _load_satisfaction()).classes(
                        "rounded-xl mb-4"
                    )
                    sat_header = ui.row().classes("w-full mb-4")
                    sat_star_bars = ui.column().classes("w-full mb-6")
                    with ui.row().classes("w-full gap-6 mb-6"):
                        with ui.card().classes("flex-1 m3-card p-6"):
                            ui.label("Top 5 rating cao nhất").classes("text-lg font-bold mb-4")
                            sat_top_table = ui.column().classes("w-full")
                        with ui.card().classes("flex-1 m3-card p-6"):
                            ui.label("Top 5 rating thấp nhất").classes("text-lg font-bold mb-4")
                            sat_bottom_table = ui.column().classes("w-full")
                    with ui.card().classes("w-full m3-card p-6"):
                        ui.label("Số đánh giá theo thời gian").classes("text-lg font-bold mb-2")
                        sat_line_chart = ui.echart(_line_options([], [], "Số đánh giá")).classes("w-full h-72")

        def _sync_filters():
            state["from_date"] = from_input.value or default_from
            state["to_date"] = to_input.value or default_to
            state["company_id"] = company_sel.value
            state["incident_type"] = incident_sel.value
            state["status"] = status_sel.value

        def _company_id_int():
            cid = state.get("company_id", "all")
            if cid and cid != "all":
                return int(cid)
            return None

        async def _load_requests():
            data = await get_request_report(
                from_date=state["from_date"],
                to_date=state["to_date"],
                company_id=_company_id_int(),
                incident_type=state["incident_type"],
                status=state["status"],
            )
            by_status = data.get("by_status", {})
            completed = by_status.get("COMPLETED", 0)
            cancelled = by_status.get("CANCELLED", 0)

            req_summary.clear()
            with req_summary:
                _mini_stat("Tổng yêu cầu", str(data.get("total_requests", 0)), "blue")
                _mini_stat("Đã hoàn thành", str(completed), "green")
                _mini_stat("Đã hủy", str(cancelled), "orange")
                _mini_stat("Tỉ lệ hủy", f"{data.get('cancel_rate', 0)}%", "red")

            req_status_table.clear()
            with req_status_table:
                with ui.card().classes("w-full m3-card p-6"):
                    ui.label("Theo trạng thái").classes("text-lg font-bold mb-4")
                    columns = [
                        {"name": "status", "label": "Trạng thái", "field": "status", "align": "left"},
                        {"name": "count", "label": "Số lượng", "field": "count", "align": "right"},
                    ]
                    rows = [{"status": k, "count": v} for k, v in by_status.items()]
                    ui.table(columns=columns, rows=rows, row_key="status").classes("w-full")

            pie_data = [
                {"name": item.get("type", "?"), "value": item.get("count", 0)}
                for item in data.get("by_incident_type", [])
            ]
            incident_chart.options = _pie_options(pie_data)
            incident_chart.update()

            by_date = data.get("by_date", [])
            req_line_chart.options = _line_options(
                [d["date"] for d in by_date],
                [d["count"] for d in by_date],
            )
            req_line_chart.update()

        async def _load_revenue():
            data = await get_revenue_report(
                from_date=state["from_date"],
                to_date=state["to_date"],
            )
            rev_summary.clear()
            with rev_summary:
                _mini_stat(
                    "Tổng doanh thu",
                    f"{int(data.get('total_revenue', 0)):,} đ",
                    "green",
                )

            rev_company_table.clear()
            with rev_company_table:
                columns = [
                    {"name": "company_name", "label": "Công ty", "field": "company_name", "align": "left"},
                    {"name": "revenue", "label": "Doanh thu", "field": "revenue", "align": "right"},
                    {"name": "request_count", "label": "Số yêu cầu", "field": "request_count", "align": "right"},
                ]
                rows = []
                for i, row in enumerate(data.get("by_company", [])[:20], 1):
                    rows.append({
                        "rank": i,
                        "company_name": row.get("company_name", ""),
                        "revenue": f"{int(row.get('revenue', 0)):,} đ",
                        "request_count": row.get("request_count", 0),
                    })
                ui.table(columns=columns, rows=rows, row_key="company_name").classes("w-full")

            by_date = data.get("by_date", [])
            rev_bar_chart.options = _bar_options(
                [d["date"] for d in by_date],
                [d["revenue"] for d in by_date],
            )
            rev_bar_chart.update()

            method_data = [
                {"name": m.get("method", "?"), "value": m.get("total_amount", 0)}
                for m in data.get("by_payment_method", [])
            ]
            rev_pie_chart.options = _pie_options(method_data)
            rev_pie_chart.update()

        async def _load_satisfaction():
            data = await get_satisfaction_report(
                from_date=state["from_date"],
                to_date=state["to_date"],
            )
            avg = data.get("system_avg_rating", 0)

            sat_header.clear()
            with sat_header:
                with ui.card().classes("m3-card p-8 border-l-4 border-yellow-500"):
                    ui.label("Rating trung bình hệ thống").classes("text-sm text-gray-500 uppercase font-bold")
                    ui.label(f"{avg:.1f}").classes("text-5xl font-bold text-yellow-600")
                    ui.label("★ / 5.0").classes("text-gray-400")

            sat_star_bars.clear()
            with sat_star_bars:
                with ui.card().classes("w-full m3-card p-6"):
                    ui.label("Phân phối số sao").classes("text-lg font-bold mb-4")
                    by_star = data.get("by_star", {})
                    max_count = max(by_star.values()) if by_star else 1
                    for star in ("5", "4", "3", "2", "1"):
                        cnt = by_star.get(star, 0)
                        pct = int((cnt / max_count) * 100) if max_count else 0
                        with ui.row().classes("w-full items-center gap-3 mb-2"):
                            ui.label(f"{star}★").classes("w-10 font-bold text-yellow-600")
                            ui.linear_progress(value=pct / 100).classes("flex-1").props("color=amber")
                            ui.label(str(cnt)).classes("w-12 text-right text-gray-600")

            def _fill_rank_table(container, rows, empty_msg):
                container.clear()
                with container:
                    if not rows:
                        ui.label(empty_msg).classes("text-gray-400")
                        return
                    for row in rows:
                        with ui.row().classes("w-full justify-between py-2 border-b border-gray-100"):
                            ui.label(row.get("company_name", "")).classes("font-medium")
                            ui.label(
                                f"{row.get('rating_avg', 0):.1f}★ ({row.get('rating_count', 0)} đánh giá)"
                            ).classes("text-gray-600")

            _fill_rank_table(sat_top_table, data.get("top5_highest", []), "Chưa có dữ liệu")
            _fill_rank_table(sat_bottom_table, data.get("top5_lowest", []), "Chưa có dữ liệu")

            reviews_by_date = data.get("reviews_by_date", [])
            sat_line_chart.options = _line_options(
                [d["date"] for d in reviews_by_date],
                [d["count"] for d in reviews_by_date],
                "Số đánh giá",
            )
            sat_line_chart.update()

        def _active_report_type() -> str:
            if tabs.value == tab_revenue:
                return "revenue"
            if tabs.value == tab_satisfaction:
                return "satisfaction"
            return "requests"

        async def _do_export(fmt: str):
            _sync_filters()
            report_type = _active_report_type()
            try:
                if fmt == "excel":
                    content, filename = await export_excel(
                        report_type,
                        from_date=state["from_date"],
                        to_date=state["to_date"],
                        company_id=_company_id_int(),
                        incident_type=state.get("incident_type"),
                        status=state.get("status"),
                    )
                else:
                    content, filename = await export_pdf(
                        report_type,
                        from_date=state["from_date"],
                        to_date=state["to_date"],
                        company_id=_company_id_int(),
                        incident_type=state.get("incident_type"),
                        status=state.get("status"),
                    )
                ui.download(content, filename)
                ui.notify(f"Đã tải {filename}", type="positive")
            except Exception as e:
                ui.notify(f"Lỗi xuất báo cáo: {e}", type="negative")

        async def _on_tab_change(_=None):
            _sync_filters()
            if tabs.value == tab_revenue:
                await _load_revenue()
            elif tabs.value == tab_satisfaction:
                await _load_satisfaction()
            else:
                await _load_requests()

        tabs.on_value_change(_on_tab_change)

        await _load_requests()


def _mini_stat(label: str, value: str, color: str):
    with ui.card().classes(f"flex-1 m3-card p-5 border-l-4 border-{color}-500 min-w-[140px]"):
        ui.label(label).classes("text-xs text-gray-400 uppercase font-bold")
        ui.label(value).classes("text-2xl font-bold text-gray-800")


def _pie_options(data):
    return {
        "tooltip": {"trigger": "item"},
        "series": [{"type": "pie", "radius": "65%", "data": data}],
    }


def _line_options(labels, values, series_name="Số lượng"):
    return {
        "tooltip": {"trigger": "axis"},
        "xAxis": {"type": "category", "data": labels},
        "yAxis": {"type": "value"},
        "series": [
            {
                "name": series_name,
                "type": "line",
                "smooth": True,
                "data": values,
                "areaStyle": {},
                "itemStyle": {"color": "#3b82f6"},
            }
        ],
    }


def _bar_options(labels, values):
    return {
        "tooltip": {"trigger": "axis"},
        "xAxis": {"type": "category", "data": labels},
        "yAxis": {"type": "value"},
        "series": [
            {
                "type": "bar",
                "data": values,
                "itemStyle": {"color": "#10b981"},
            }
        ],
    }
