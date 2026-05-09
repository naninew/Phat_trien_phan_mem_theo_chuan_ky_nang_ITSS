"""
Trang gửi đánh giá dịch vụ – dành cho khách hàng.
"""
from nicegui import ui
from core.auth import require_role
from components.page_layout import page_layout
from services.rescue_api import get_request_detail, submit_review


def create_review_page():

    @ui.page('/customer/review/{request_id}')
    async def review_page(request_id: int):
        if not require_role("customer"):
            return

        # Fetch details to ensure it's completed
        req = await get_request_detail(request_id)
        if not req or req['status'] != 'completed':
            ui.notify("Yêu cầu chưa hoàn thành hoặc không hợp lệ để đánh giá", type="warning")
            ui.navigate.to(f"/customer/track/{request_id}")
            return

        with page_layout(f"/customer/review/{request_id}", title="Đánh giá dịch vụ"):
            
            with ui.column().classes("w-full max-w-xl mx-auto py-10"):
                with ui.card().classes("w-full rounded-3xl p-8 shadow-xl border border-gray-100"):
                    
                    with ui.column().classes("items-center w-full gap-2 mb-8"):
                        ui.icon("star_outline", size="4rem", color="amber")
                        ui.label("Đánh giá dịch vụ").classes("text-3xl font-bold text-gray-800")
                        ui.label(f"Mã yêu cầu: #{request_id}").classes("text-gray-400")
                        ui.label(f"Đơn vị: {req.get('company_name', 'N/A')}").classes("font-semibold text-indigo-600")

                    ui.separator().classes("mb-8")
                    
                    # Star Rating
                    ui.label("Bạn hài lòng thế nào về dịch vụ?").classes("text-lg font-bold text-gray-700 text-center w-full")
                    
                    rating_state = {'value': 5}
                    with ui.row().classes("w-full justify-center gap-2 my-6") as star_row:
                        stars = []
                        for i in range(1, 6):
                            btn = ui.button(icon="star" if i <= rating_state['value'] else "star_border").props("flat round color=amber size=lg")
                            btn.on("click", lambda i=i: _set_rating(i))
                            stars.append(btn)

                    comment_area = ui.textarea(
                        label="Ý kiến đóng góp (không bắt buộc)",
                        placeholder="Hãy chia sẻ trải nghiệm của bạn để chúng tôi phục vụ tốt hơn..."
                    ).classes("w-full mt-4").props("outlined rows=4")

                    submit_btn = ui.button(
                        "GỬI ĐÁNH GIÁ NGAY", 
                        on_click=lambda: _do_submit()
                    ).classes("w-full mt-8 py-4 rounded-2xl bg-indigo-600 text-white font-bold text-lg shadow-lg hover:bg-indigo-700")

        # ── Logic ────────────────────────────────────────────────────────
        
        def _set_rating(val):
            rating_state['value'] = val
            for i, star in enumerate(stars):
                star.props(f"icon={'star' if i < val else 'star_border'}")

        async def _do_submit():
            submit_btn.props("loading")
            try:
                await submit_review(
                    request_id=request_id,
                    rating=rating_state['value'],
                    comment=comment_area.value
                )
                ui.notify("Cảm ơn bạn đã đóng góp ý kiến! ❤️", type="positive")
                ui.navigate.to("/customer/requests")
            except Exception as e:
                ui.notify(f"Lỗi: {e}", type="negative")
            finally:
                submit_btn.props(remove="loading")
