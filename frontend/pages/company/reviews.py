"""
Company Reviews - NiceGUI
"""
from nicegui import ui
from typing import Dict, Any, List
from core.auth import require_role
from components.page_layout import page_layout
from services.rescue_api import get_company_reviews

def create_reviews_page():
    """Register /company/reviews route."""

    @ui.page('/company/reviews')
    async def reviews_page():
        if not require_role("company_staff"):
            return

        with page_layout("/company/reviews", title="Đánh Giá Từ Khách Hàng"):
            
            with ui.row().classes("w-full items-center justify-between mb-6"):
                ui.label("Theo dõi chất lượng dịch vụ qua đánh giá thực tế").classes("text-lg font-medium opacity-70")

            reviews_container = ui.column().classes("w-full gap-4")

            # --- Logic ---
            async def refresh_reviews():
                reviews_container.clear()
                reviews = await get_company_reviews()
                with reviews_container:
                    if not reviews:
                        ui.label("Chưa có đánh giá nào.").classes("italic opacity-50 py-20 self-center")
                    for r in reviews:
                        _render_review_card(r)

            def _render_review_card(r):
                with ui.card().classes("w-full rounded-3xl p-6 border border-surface-variant/30 shadow-sm"):
                    with ui.row().classes("w-full justify-between items-start"):
                        with ui.column().classes("gap-2"):
                            with ui.row().classes("items-center gap-2"):
                                ui.label(r.get('customer_name', 'Khách hàng ẩn danh')).classes("font-bold text-lg")
                                ui.label(f"• {r.get('service_name', 'Dịch vụ cứu hộ')}").classes("text-xs opacity-50")
                            
                            with ui.row().classes("gap-1"):
                                for i in range(5):
                                    color = "text-amber-400" if i < r['rating'] else "text-gray-200"
                                    ui.icon("star", size="sm").classes(color)
                        
                        ui.label(r['created_at'][:10]).classes("text-xs opacity-40")
                    
                    ui.label(r['comment'] or "Không có nhận xét.").classes("mt-4 text-on-surface-variant opacity-80 italic")

            await refresh_reviews()
