"""
Customer overview dashboard.
"""
from collections import Counter, defaultdict
from datetime import datetime
from typing import Any, Dict, List

from nicegui import ui

from components.page_layout import page_layout
from core.auth import require_role
from services.rescue_api import get_my_requests


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return None


def _month_key(value: str | None) -> str:
    parsed = _parse_time(value) or datetime.now()
    return f"{parsed.year}-{parsed.month:02d}"


def _shift_month(key: str, offset: int) -> str:
    year, month = (int(part) for part in key.split("-"))
    month += offset
    while month <= 0:
        year -= 1
        month += 12
    while month > 12:
        year += 1
        month -= 12
    return f"{year}-{month:02d}"


def _month_label(key: str) -> str:
    try:
        year, month = key.split("-")
        return f"T{int(month)}/{year[-2:]}"
    except Exception:
        return key


def _format_money(value: float | int | None) -> str:
    if not value:
        return "0 đ"
    return f"{float(value):,.0f}".replace(",", ".") + " đ"


def _format_date(value: str | None) -> str:
    parsed = _parse_time(value)
    if not parsed:
        return "--"
    return parsed.strftime("%d/%m/%Y")


def _service_name(request: Dict[str, Any]) -> str:
    services = request.get("services") or []
    if services:
        return services[0].get("service_name") or request.get("incident_type") or "Dịch vụ cứu hộ"
    return request.get("incident_type") or "Sự cố khác"


def _request_price(request: Dict[str, Any]) -> float:
    if request.get("agreed_price"):
        return float(request.get("agreed_price") or 0)
    services = request.get("services") or []
    return float(sum((item.get("price") or 0) for item in services))


def _last_months(requests: List[Dict[str, Any]], minimum: int = 6) -> List[str]:
    date_values = []
    for request in requests:
        date_values.extend([
            request.get("created_at"),
            request.get("actual_completion_time"),
            request.get("updated_at"),
        ])
    parsed = [_parse_time(value) for value in date_values if value]
    latest = max((item for item in parsed if item), default=datetime.now())
    end_key = f"{latest.year}-{latest.month:02d}"
    return [_shift_month(end_key, offset) for offset in range(-(minimum - 1), 1)]


def _trend(current: float, previous: float, positive_good: bool = True) -> Dict[str, str]:
    if previous == 0:
        if current == 0:
            return {"text": "0% so với tháng trước", "classes": "bg-slate-100 text-slate-500", "icon": "remove"}
        classes = "bg-emerald-50 text-emerald-700" if positive_good else "bg-amber-50 text-amber-700"
        return {"text": "Mới trong tháng này", "classes": classes, "icon": "trending_up"}

    percent = round(((current - previous) / previous) * 100)
    if percent == 0:
        return {"text": "Không đổi so với tháng trước", "classes": "bg-slate-100 text-slate-500", "icon": "remove"}

    is_up = percent >= 0
    good = is_up if positive_good else not is_up
    classes = "bg-emerald-50 text-emerald-700" if good else "bg-red-50 text-red-700"
    icon = "trending_up" if is_up else "trending_down"
    arrow = "↑" if is_up else "↓"
    return {"text": f"{arrow} {abs(percent)}% so với tháng trước", "classes": classes, "icon": icon}


def _overview_data(requests: List[Dict[str, Any]]) -> Dict[str, Any]:
    completed = [r for r in requests if r.get("status") == "COMPLETED"]
    reviewed = [r for r in requests if r.get("rating")]
    paid_total = sum(_request_price(r) for r in completed)
    avg_rating = round(sum(float(r.get("rating") or 0) for r in reviewed) / len(reviewed), 1) if reviewed else 0

    months = _last_months(requests, minimum=6)
    current_month = months[-1]
    previous_month = _shift_month(current_month, -1)

    request_by_month = defaultdict(int)
    completed_by_month = defaultdict(int)
    payment_by_month = defaultdict(float)
    rating_values_by_month = defaultdict(list)
    type_counter = Counter()
    company_counter = Counter()

    for request in requests:
        created_month = _month_key(request.get("created_at"))
        request_by_month[created_month] += 1
        type_counter[_service_name(request)] += 1

        company_name = request.get("company_name")
        if company_name:
            company_counter[company_name] += 1

        if request.get("rating"):
            rating_values_by_month[created_month].append(float(request.get("rating") or 0))

        if request.get("status") == "COMPLETED":
            completed_month = _month_key(request.get("actual_completion_time") or request.get("updated_at") or request.get("created_at"))
            completed_by_month[completed_month] += 1
            payment_by_month[completed_month] += _request_price(request)

    def avg_for_month(month: str) -> float:
        values = rating_values_by_month.get(month) or []
        return round(sum(values) / len(values), 1) if values else 0

    recent_reviews = sorted(
        reviewed,
        key=lambda r: _parse_time(r.get("updated_at") or r.get("created_at")) or datetime.min,
        reverse=True,
    )[:3]

    most_service = type_counter.most_common(1)[0] if type_counter else ("Chưa có dữ liệu", 0)
    most_company = company_counter.most_common(1)[0] if company_counter else ("Chưa có dữ liệu", 0)

    return {
        "total": len(requests),
        "completed": len(completed),
        "paid_total": paid_total,
        "avg_rating": avg_rating,
        "months": months,
        "month_labels": [_month_label(month) for month in months],
        "requests_series": [request_by_month[month] for month in months],
        "payment_series": [payment_by_month[month] for month in months],
        "type_series": [{"name": name, "value": value} for name, value in type_counter.most_common()],
        "recent_reviews": recent_reviews,
        "range_request_total": sum(request_by_month[month] for month in months),
        "range_payment_total": sum(payment_by_month[month] for month in months),
        "most_service": {"name": most_service[0], "count": most_service[1]},
        "most_company": {"name": most_company[0], "count": most_company[1]},
        "trends": {
            "total": _trend(request_by_month[current_month], request_by_month[previous_month]),
            "completed": _trend(completed_by_month[current_month], completed_by_month[previous_month]),
            "paid_total": _trend(payment_by_month[current_month], payment_by_month[previous_month], positive_good=False),
            "avg_rating": _trend(avg_for_month(current_month), avg_for_month(previous_month)),
        },
    }


def _line_options(labels: List[str], values: List[int]) -> Dict[str, Any]:
    return {
        "tooltip": {"trigger": "axis", "backgroundColor": "#0f172a", "borderWidth": 0, "textStyle": {"color": "#fff"}},
        "grid": {"left": 36, "right": 20, "top": 36, "bottom": 34},
        "xAxis": {"type": "category", "boundaryGap": False, "data": labels, "axisTick": {"show": False}},
        "yAxis": {"type": "value", "minInterval": 1, "splitLine": {"lineStyle": {"color": "#e2e8f0"}}},
        "series": [{
            "name": "Yêu cầu",
            "type": "line",
            "smooth": True,
            "data": values,
            "symbolSize": 9,
            "label": {"show": True, "position": "top", "color": "#2563eb", "fontWeight": 700},
            "lineStyle": {"width": 4, "color": "#2563eb"},
            "itemStyle": {"color": "#2563eb"},
            "areaStyle": {"color": "rgba(37, 99, 235, 0.12)"},
        }],
    }


def _pie_options(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    chart_data = data or [{"name": "Chưa có dữ liệu", "value": 1}]
    return {
        "tooltip": {"trigger": "item", "formatter": "{b}<br/>Số lượng: {c}<br/>Tỷ lệ: {d}%"},
        "legend": {"type": "scroll", "bottom": 0, "left": "center", "itemGap": 14, "textStyle": {"width": 160, "overflow": "break"}},
        "series": [{
            "name": "Loại yêu cầu",
            "type": "pie",
            "radius": ["42%", "68%"],
            "center": ["50%", "42%"],
            "avoidLabelOverlap": True,
            "data": chart_data,
            "label": {"show": True, "formatter": "{b}: {d}%", "overflow": "break", "width": 150},
            "labelLine": {"length": 14, "length2": 10},
        }],
    }


def _bar_options(labels: List[str], values: List[float]) -> Dict[str, Any]:
    formatted_values = [
        {"value": value, "label": {"show": True, "position": "top", "formatter": _format_money(value), "color": "#047857", "fontWeight": 700}}
        for value in values
    ]
    return {
        "tooltip": {"trigger": "axis", "backgroundColor": "#0f172a", "borderWidth": 0, "textStyle": {"color": "#fff"}},
        "grid": {"left": 50, "right": 20, "top": 44, "bottom": 34},
        "xAxis": {"type": "category", "data": labels, "axisTick": {"show": False}},
        "yAxis": {"type": "value", "axisLabel": {"formatter": "{value} đ"}, "splitLine": {"lineStyle": {"color": "#e2e8f0"}}},
        "series": [{
            "name": "Chi phí",
            "type": "bar",
            "data": formatted_values,
            "barWidth": "46%",
            "label": {"show": True, "position": "top", "color": "#047857", "fontWeight": 700},
            "itemStyle": {"color": "#10b981", "borderRadius": [8, 8, 0, 0]},
        }],
    }


def create_overview_page():

    @ui.page("/customer/overview")
    async def overview_page():
        if not require_role("customer"):
            return

        requests = await get_my_requests()
        data = _overview_data(requests or [])

        ui.add_head_html("""
        <style>
            @media (max-width: 1024px) {
                .overview-chart-grid,
                .overview-insight-grid {
                    flex-direction: column;
                }
                .overview-chart-card,
                .overview-insight-card {
                    min-width: 100% !important;
                }
            }
        </style>
        """)

        with page_layout("/customer/overview", title="Tổng quan"):
            with ui.column().classes("w-full max-w-[1280px] mx-auto gap-5 px-1 pb-8"):
                with ui.row().classes("w-full items-center justify-between gap-4 flex-wrap"):
                    with ui.column().classes("gap-1"):
                        ui.label("Tổng quan").classes("text-3xl font-bold text-slate-900 font-outfit")
                        ui.label("Theo dõi hoạt động cứu hộ, chi phí và đánh giá dịch vụ của bạn").classes("text-sm text-slate-500")
                    ui.button(
                        "Gửi yêu cầu mới",
                        icon="add",
                        on_click=lambda: ui.navigate.to("/customer/find-rescue"),
                    ).classes("rounded-xl bg-blue-600 px-5 py-3 font-bold text-white shadow-sm hover:bg-blue-700").props("unelevated")

                if not requests:
                    _empty_dashboard()
                    return

                with ui.row().classes("w-full gap-3 flex-wrap"):
                    _stat_card("Tổng yêu cầu", str(data["total"]), "article", "text-blue-600", "bg-blue-50", data["trends"]["total"])
                    _stat_card("Hoàn thành", str(data["completed"]), "check_circle", "text-emerald-600", "bg-emerald-50", data["trends"]["completed"])
                    _stat_card("Tổng chi phí", _format_money(data["paid_total"]), "payments", "text-green-600", "bg-green-50", data["trends"]["paid_total"])
                    _stat_card("Đánh giá TB", f"{data['avg_rating']:.1f}/5" if data["avg_rating"] else "--", "star", "text-amber-600", "bg-amber-50", data["trends"]["avg_rating"])

                with ui.row().classes("w-full gap-4 overview-insight-grid"):
                    _insight_card("Dịch vụ sử dụng nhiều nhất", data["most_service"]["name"], f"{data['most_service']['count']} lần sử dụng", "build_circle", "bg-indigo-50", "text-indigo-600")
                    _insight_card("Đơn vị cứu hộ sử dụng nhiều nhất", data["most_company"]["name"], f"{data['most_company']['count']} lần sử dụng", "business", "bg-cyan-50", "text-cyan-600")

                with ui.row().classes("w-full gap-5 items-stretch overview-chart-grid"):
                    with ui.card().classes("flex-[1.45] min-w-[420px] rounded-2xl border border-slate-100 bg-white p-5 shadow-sm overview-chart-card"):
                        with ui.row().classes("w-full items-start justify-between gap-3"):
                            with ui.column().classes("gap-0"):
                                ui.label("Yêu cầu theo tháng").classes("text-lg font-bold text-slate-900")
                                ui.label("Số yêu cầu cứu hộ được tạo trong 6 tháng gần nhất").classes("text-xs text-slate-400")
                            with ui.column().classes("items-end gap-0"):
                                ui.label(str(data["range_request_total"])).classes("text-2xl font-bold text-blue-600")
                                ui.label("yêu cầu").classes("text-xs font-bold uppercase text-slate-400")
                        ui.echart(_line_options(data["month_labels"], data["requests_series"])).classes("w-full h-80 mt-3")

                    with ui.card().classes("flex-1 min-w-[320px] rounded-2xl border border-slate-100 bg-white p-5 shadow-sm overview-chart-card"):
                        ui.label("Tỷ lệ loại yêu cầu").classes("text-lg font-bold text-slate-900")
                        ui.label("Phân bổ theo dịch vụ hoặc loại sự cố").classes("text-xs text-slate-400")
                        ui.echart(_pie_options(data["type_series"])).classes("w-full h-96 mt-3")

                with ui.card().classes("w-full rounded-2xl border border-slate-100 bg-white p-5 shadow-sm"):
                    with ui.row().classes("w-full items-start justify-between gap-3"):
                        with ui.column().classes("gap-0"):
                            ui.label("Chi phí theo tháng").classes("text-lg font-bold text-slate-900")
                            ui.label("Tổng số tiền đã trả cho các yêu cầu hoàn thành").classes("text-xs text-slate-400")
                        with ui.column().classes("items-end gap-0"):
                            ui.label(_format_money(data["range_payment_total"])).classes("text-2xl font-bold text-emerald-600")
                            ui.label("trong 6 tháng").classes("text-xs font-bold uppercase text-slate-400")
                    ui.echart(_bar_options(data["month_labels"], data["payment_series"])).classes("w-full h-80 mt-3")

                with ui.card().classes("w-full rounded-2xl border border-slate-100 bg-white p-5 shadow-sm"):
                    with ui.row().classes("w-full items-center justify-between gap-3 flex-wrap"):
                        with ui.column().classes("gap-0"):
                            ui.label("Đánh giá gần đây").classes("text-lg font-bold text-slate-900")
                            ui.label("3 phản hồi dịch vụ cứu hộ gần nhất bạn đã gửi").classes("text-xs text-slate-400")
                        ui.button("Xem tất cả đánh giá", icon="rate_review", on_click=lambda: ui.navigate.to("/customer/requests")).props("flat no-caps").classes("rounded-xl font-bold text-blue-600")

                    with ui.column().classes("w-full gap-3 mt-4"):
                        if not data["recent_reviews"]:
                            _empty_reviews()
                        else:
                            for review in data["recent_reviews"]:
                                _review_item(review)


def _stat_card(label: str, value: str, icon: str, icon_color: str, bg: str, trend: Dict[str, str]) -> None:
    with ui.card().classes("flex-1 min-w-[210px] rounded-2xl border border-slate-100 bg-white p-5 shadow-sm"):
        with ui.row().classes("items-start justify-between gap-3"):
            with ui.column().classes("gap-2 min-w-0"):
                ui.label(label).classes("text-xs font-bold uppercase text-slate-400")
                ui.label(value).classes("text-3xl font-black text-slate-900 truncate")
                with ui.row().classes(f"items-center gap-1 rounded-full px-2.5 py-1 w-fit {trend['classes']}"):
                    ui.icon(trend["icon"], size="0.9rem")
                    ui.label(trend["text"]).classes("text-[11px] font-bold")
            with ui.element("div").classes(f"h-12 w-12 rounded-2xl {bg} flex items-center justify-center shrink-0"):
                ui.icon(icon, size="1.35rem").classes(icon_color)


def _insight_card(title: str, value: str, subtitle: str, icon: str, bg: str, icon_color: str) -> None:
    with ui.card().classes("overview-insight-card flex-1 min-w-[300px] rounded-2xl border border-slate-100 bg-white p-5 shadow-sm"):
        with ui.row().classes("items-center gap-4"):
            with ui.element("div").classes(f"h-12 w-12 rounded-2xl {bg} flex items-center justify-center shrink-0"):
                ui.icon(icon, size="1.4rem").classes(icon_color)
            with ui.column().classes("gap-0 min-w-0"):
                ui.label(title).classes("text-xs font-bold uppercase text-slate-400")
                ui.label(value).classes("text-lg font-black text-slate-900 truncate")
                ui.label(subtitle).classes("text-sm font-semibold text-slate-500")


def _review_item(request: Dict[str, Any]) -> None:
    rating = int(request.get("rating") or 0)
    with ui.element("div").classes("w-full rounded-2xl border border-slate-100 bg-slate-50/70 p-4"):
        with ui.row().classes("w-full items-start justify-between gap-4 flex-wrap"):
            with ui.row().classes("items-start gap-3 min-w-0 flex-1"):
                with ui.element("div").classes("h-10 w-10 rounded-2xl bg-blue-50 flex items-center justify-center shrink-0"):
                    ui.icon("build", size="1.1rem").classes("text-blue-600")
                with ui.column().classes("gap-1 min-w-0 flex-1"):
                    ui.label(request.get("company_name") or "Đơn vị cứu hộ").classes("text-sm font-bold text-slate-900")
                    with ui.row().classes("items-center gap-2 flex-wrap"):
                        ui.badge(_service_name(request)).classes("rounded-full bg-white text-slate-600 px-2.5 py-1 font-bold")
                        with ui.row().classes("items-center gap-1"):
                            ui.icon("star", size="1rem").classes("text-amber-500")
                            ui.label(f"{rating}/5").classes("text-xs font-bold text-amber-600")
                    ui.label(request.get("feedback") or "Không có nhận xét.").classes("text-sm text-slate-700 leading-relaxed mt-1")
            ui.label(_format_date(request.get("updated_at") or request.get("created_at"))).classes("text-xs text-slate-400 shrink-0")


def _empty_reviews() -> None:
    with ui.column().classes("w-full items-center gap-3 py-10 rounded-2xl border border-dashed border-slate-200 bg-slate-50"):
        ui.icon("rate_review", size="3rem").classes("text-slate-300")
        ui.label("Chưa có đánh giá nào").classes("text-lg font-bold text-slate-700")
        ui.label("Sau khi hoàn thành yêu cầu, đánh giá của bạn sẽ xuất hiện tại đây.").classes("text-sm text-slate-400 text-center")


def _empty_dashboard() -> None:
    with ui.card().classes("w-full rounded-3xl border border-dashed border-slate-300 bg-white p-12 shadow-sm"):
        with ui.column().classes("items-center gap-3 text-center"):
            with ui.element("div").classes("h-16 w-16 rounded-3xl bg-blue-50 flex items-center justify-center"):
                ui.icon("dashboard", size="2rem").classes("text-blue-600")
            ui.label("Bạn chưa có yêu cầu cứu hộ nào.").classes("text-2xl font-black text-slate-800")
            ui.label("Hãy tạo yêu cầu đầu tiên để xem thống kê hoạt động, chi phí và đánh giá dịch vụ.").classes("text-sm text-slate-500 max-w-xl")
            ui.button("Tạo yêu cầu đầu tiên", icon="add", on_click=lambda: ui.navigate.to("/customer/find-rescue")).classes("mt-2 rounded-xl bg-blue-600 px-5 py-2.5 font-bold text-white").props("unelevated")
