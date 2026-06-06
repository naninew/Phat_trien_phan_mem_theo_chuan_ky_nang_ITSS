"""
Trang gửi đánh giá dịch vụ – dành cho khách hàng.
"""
from datetime import datetime

from nicegui import ui

from core.auth import require_role
from components.page_layout import page_layout
from services.rescue_api import get_request_detail, submit_review


RATING_LABELS = {
    1: "Rất không hài lòng",
    2: "Chưa hài lòng",
    3: "Bình thường",
    4: "Hài lòng",
    5: "Rất hài lòng",
}


def create_review_page():

    @ui.page('/customer/review/{request_id}')
    async def review_page(request_id: int):
        if not require_role("customer"):
            return

        req = await get_request_detail(request_id)
        if not req or req['status'] != 'COMPLETED':
            ui.notify("Yêu cầu chưa hoàn thành hoặc không hợp lệ để đánh giá", type="warning")
            ui.navigate.to(f"/customer/track/{request_id}")
            return

        services = req.get("services") or []
        service_name = (
            services[0].get("service_name", req.get("incident_type", "Dịch vụ cứu hộ"))
            if services
            else req.get("incident_type", "Dịch vụ cứu hộ")
        )
        price = req.get("agreed_price") or 0

        def format_money(value):
            if not value:
                return "Chưa cập nhật"
            return f"{float(value):,.0f}".replace(",", ".") + " đ"

        def format_time(value):
            if not value:
                return "--"
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%H:%M • %d/%m/%Y")
            except Exception:
                return value

        def info_row(icon, label, value, color_class="text-blue-600"):
            with ui.row().classes("w-full items-start gap-3 py-3"):
                with ui.element("div").classes(
                    "h-9 w-9 shrink-0 rounded-xl bg-slate-50 flex items-center justify-center"
                ):
                    ui.icon(icon, size="1.15rem").classes(color_class)
                with ui.column().classes("flex-1 min-w-0 gap-0"):
                    ui.label(label).classes("text-xs font-semibold uppercase text-slate-400")
                    ui.label(str(value or "--")).classes(
                        "text-sm font-semibold text-slate-700 leading-snug break-words"
                    )

        with page_layout(f"/customer/review/{request_id}", title="Đánh giá dịch vụ"):

            with ui.column().classes("w-full max-w-6xl mx-auto py-6 gap-5"):
                with ui.row().classes("w-full items-center justify-between gap-4"):
                    with ui.column().classes("gap-1"):
                        ui.label("Đánh giá dịch vụ cứu hộ").classes(
                            "text-3xl font-bold text-slate-900 font-outfit"
                        )
                        ui.label(
                            f"Yêu cầu #{request_id} đã hoàn thành. Hãy chia sẻ trải nghiệm của bạn."
                        ).classes("text-sm text-slate-500")

                    ui.button(
                        "Danh sách yêu cầu",
                        icon="list_alt",
                        on_click=lambda: ui.navigate.to("/customer/requests"),
                    ).classes(
                        "rounded-xl px-4 py-2 font-semibold text-blue-700 hover:bg-blue-50"
                    ).props("flat")

                with ui.row().classes("w-full gap-5 items-start flex-col lg:flex-row"):
                    with ui.card().classes(
                        "w-full lg:flex-1 rounded-2xl border border-slate-100 bg-white "
                        "p-6 md:p-7 shadow-sm"
                    ):
                        with ui.row().classes("w-full items-center gap-4 mb-5"):
                            with ui.element("div").classes(
                                "h-12 w-12 rounded-2xl bg-amber-100 flex items-center justify-center"
                            ):
                                ui.icon("star", size="1.9rem").classes("text-amber-500")
                            with ui.column().classes("gap-0"):
                                ui.label("Form đánh giá").classes(
                                    "text-xl font-bold text-slate-900 font-outfit"
                                )
                                ui.label("Đánh giá chất lượng phục vụ và trải nghiệm cứu hộ.").classes(
                                    "text-sm text-slate-500"
                                )

                        ui.separator().classes("mb-5")

                        if req.get("has_review") and not req.get("can_review", False):
                            with ui.column().classes("w-full items-center gap-3 py-4"):
                                ui.icon("check_circle", size="3rem", color="positive")
                                ui.label("Đánh giá của bạn").classes(
                                    "text-xl font-bold text-emerald-700"
                                )
                                if req.get("rating"):
                                    with ui.row().classes("justify-center gap-1"):
                                        for i in range(1, 6):
                                            ui.icon(
                                                "star" if i <= req["rating"] else "star_border",
                                                size="2.25rem",
                                            ).classes("text-amber-500")
                                    ui.label(RATING_LABELS.get(req["rating"], "")).classes(
                                        "text-sm font-semibold text-slate-500"
                                    )
                                if req.get("feedback"):
                                    ui.label(req["feedback"]).classes(
                                        "w-full rounded-2xl bg-slate-50 p-4 text-sm leading-relaxed text-slate-600"
                                    )
                                ui.button(
                                    "Quay lại danh sách",
                                    icon="arrow_back",
                                    on_click=lambda: ui.navigate.to(f"/customer/track/{request_id}"),
                                ).classes(
                                    "mt-2 rounded-xl bg-blue-600 px-5 py-2 font-semibold text-white hover:bg-blue-700"
                                ).props("unelevated")
                        elif not req.get("can_review", True):
                            with ui.column().classes("w-full items-center gap-3 py-4"):
                                ui.icon("event_busy", size="3rem").classes("text-slate-400")
                                ui.label("Đã quá hạn đánh giá").classes(
                                    "text-xl font-bold text-slate-700"
                                )
                                ui.label(
                                    "Bạn chỉ có thể đánh giá dịch vụ trong vòng 7 ngày kể từ khi hoàn thành."
                                ).classes("max-w-md text-center text-sm text-slate-500")
                                if req.get("review_deadline"):
                                    ui.label(f"Hạn đánh giá: {format_time(req.get('review_deadline'))}").classes(
                                        "rounded-xl bg-slate-50 px-3 py-2 text-sm font-semibold text-slate-600"
                                    )
                                ui.button(
                                    "Quay lại chi tiết",
                                    icon="arrow_back",
                                    on_click=lambda: ui.navigate.to(f"/customer/track/{request_id}"),
                                ).classes(
                                    "mt-2 rounded-xl bg-blue-600 px-5 py-2 font-semibold text-white hover:bg-blue-700"
                                ).props("unelevated")
                        else:
                            ui.label("Mức độ hài lòng").classes(
                                "text-sm font-bold uppercase text-slate-500"
                            )

                            rating_state = {'value': int(req.get("rating") or 5)}
                            rating_text = ui.label(RATING_LABELS[rating_state['value']]).classes(
                                "mt-2 text-lg font-bold text-amber-600"
                            )

                            with ui.row().classes("w-full gap-2 my-4"):
                                stars = []
                                for i in range(1, 6):
                                    btn = ui.button(
                                        icon="star" if i <= rating_state['value'] else "star_border"
                                    ).classes(
                                        "h-12 w-12 rounded-2xl text-amber-500 transition-all "
                                        "hover:bg-amber-50 hover:scale-105"
                                    ).props("flat")
                                    btn.on("click", lambda i=i: _set_rating(i))
                                    stars.append(btn)

                            comment_area = ui.textarea(
                                label="Nhận xét chi tiết",
                                placeholder=(
                                    "Ví dụ: đội cứu hộ đến đúng giờ, tư vấn rõ ràng, "
                                    "xử lý chuyên nghiệp và chi phí minh bạch..."
                                ),
                                value=req.get("feedback") or "",
                            ).classes("w-full mt-2").props("outlined rows=6 maxlength=500 counter")

                            if req.get("review_deadline"):
                                ui.label(f"Hạn đánh giá: {format_time(req.get('review_deadline'))}").classes(
                                    "mt-2 text-xs font-semibold text-slate-500"
                                )

                            with ui.row().classes("w-full justify-end mt-5"):
                                submit_btn = ui.button(
                                    "Cập nhật đánh giá" if req.get("has_review") else "Gửi đánh giá",
                                    icon="send",
                                    on_click=lambda: _do_submit(),
                                ).classes(
                                    "rounded-xl bg-blue-600 px-5 py-2.5 font-bold text-white "
                                    "shadow-sm hover:bg-blue-700"
                                ).props("unelevated")

                    with ui.card().classes(
                        "w-full lg:w-[390px] rounded-2xl border border-slate-100 bg-white "
                        "p-6 shadow-sm"
                    ):
                        with ui.row().classes("w-full items-start justify-between gap-3 mb-4"):
                            with ui.column().classes("gap-0"):
                                ui.label("Thông tin đơn cứu hộ").classes(
                                    "text-xl font-bold text-slate-900 font-outfit"
                                )
                                ui.label(f"Mã yêu cầu #{request_id}").classes("text-sm text-slate-400")
                            ui.chip("Hoàn thành", icon="task_alt").classes(
                                "bg-emerald-50 text-emerald-700 font-bold"
                            )

                        with ui.element("div").classes(
                            "rounded-2xl bg-emerald-50 px-4 py-4 mb-4 border border-emerald-100"
                        ):
                            ui.label("Giá thực tế").classes(
                                "text-xs font-bold uppercase text-emerald-700"
                            )
                            ui.label(format_money(price)).classes(
                                "mt-1 text-3xl font-bold text-emerald-700"
                            )

                        ui.separator().classes("mb-2")

                        with ui.column().classes("w-full gap-0 divide-y divide-slate-100"):
                            info_row("medical_services", "Dịch vụ", service_name, "text-blue-600")
                            info_row("business", "Đơn vị cứu hộ", req.get("company_name", "N/A"), "text-blue-600")
                            info_row("directions_car", "Xe của khách", req.get("customer_vehicle_plate", "--"), "text-slate-500")
                            info_row("place", "Vị trí yêu cầu", req.get("address_description", "--"), "text-red-500")
                            info_row(
                                "schedule",
                                "Thời gian hoàn thành",
                                format_time(req.get("actual_completion_time")),
                                "text-emerald-600",
                            )

                        if req.get("payment_method"):
                            ui.separator().classes("my-4")
                            with ui.row().classes("w-full items-center justify-between"):
                                ui.label("Thanh toán").classes("text-sm font-semibold text-slate-500")
                                ui.label(req.get("payment_method")).classes(
                                    "rounded-lg bg-slate-50 px-3 py-1 text-sm font-bold text-slate-700"
                                )

        def _set_rating(val):
            rating_state['value'] = val
            rating_text.set_text(RATING_LABELS[val])
            for index, star in enumerate(stars, start=1):
                star.props(f"icon={'star' if index <= val else 'star_border'}")
                if index <= val:
                    star.classes("bg-amber-50")
                else:
                    star.classes(remove="bg-amber-50")

        async def _do_submit():
            submit_btn.props("loading")
            try:
                comment = (comment_area.value or "").strip()
                if len(comment) > 500:
                    ui.notify("Nhận xét tối đa 500 ký tự", type="warning")
                    return
                await submit_review(
                    request_id=request_id,
                    rating=rating_state['value'],
                    comment=comment,
                )
                ui.notify("Cảm ơn bạn đã gửi đánh giá!", type="positive")
                ui.navigate.to("/customer/requests")
            except Exception as e:
                ui.notify(f"Lỗi: {e}", type="negative")
            finally:
                submit_btn.props(remove="loading")
