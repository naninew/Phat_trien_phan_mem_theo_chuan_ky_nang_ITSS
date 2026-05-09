"""
Trang báo cáo và thống kê dành cho Admin.
"""
from nicegui import ui
from core.auth import require_role
from components.page_layout import page_layout
import httpx
from core.config import BACKEND_URL
from core.auth import get_access_token

def create_reports_page():

    @ui.page('/admin/reports')
    async def reports_page():
        if not require_role("admin"):
            return

        with page_layout("/admin/reports", title="Báo Cáo & Thống Kê"):
            
            with ui.row().classes("w-full items-center justify-between mb-6"):
                with ui.column().classes("gap-0"):
                    ui.label("📊 Báo Cáo Hệ Thống").classes("text-3xl font-bold text-gray-800")
                    ui.label("Tổng quan hoạt động và hiệu quả kinh doanh").classes("text-gray-500")
                
                ui.button("XUẤT BÁO CÁO (EXCEL)", icon="download", on_click=lambda: ui.notify("Chức năng đang phát triển")).classes("rounded-xl btn-primary")

            # --- Stats Grid ---
            with ui.row().classes("w-full gap-6 mb-8"):
                _stat_card("Tổng doanh thu", "1.280.000.000 đ", "trending_up", "green")
                _stat_card("Yêu cầu hoàn thành", "1,248", "task_alt", "blue")
                _stat_card("Thời gian chờ TB", "14.5 phút", "timer", "amber")
                _stat_card("Đối tác hoạt động", "24/28", "business", "indigo")

            # --- Charts Placeholder ---
            with ui.row().classes("w-full gap-6"):
                with ui.card().classes("flex-1 m3-card p-6 h-96"):
                    ui.label("Doanh thu theo tháng").classes("text-lg font-bold mb-4")
                    # Placeholder for chart
                    with ui.column().classes("w-full h-full items-center justify-center bg-gray-50 rounded-2xl border border-dashed border-gray-200"):
                        ui.icon("bar_chart", size="4rem", color="gray-300")
                        ui.label("Biểu đồ đang được tải...").classes("text-gray-400")

                with ui.card().classes("w-80 m3-card p-6 h-96"):
                    ui.label("Tỉ lệ trạng thái").classes("text-lg font-bold mb-4")
                    # Placeholder for pie chart
                    with ui.column().classes("w-full h-full items-center justify-center bg-gray-50 rounded-2xl border border-dashed border-gray-200"):
                        ui.icon("pie_chart", size="4rem", color="gray-300")
                        ui.label("Biểu đồ...").classes("text-gray-400")

def _stat_card(label, value, icon, color):
    with ui.card().classes(f"flex-1 m3-card p-6 border-l-4 border-{color}-500"):
        with ui.row().classes("w-full items-center justify-between"):
            with ui.column().classes("gap-0"):
                ui.label(label).classes("text-xs text-gray-400 uppercase font-bold")
                ui.label(value).classes("text-2xl font-bold text-gray-800")
            ui.icon(icon, size="2.5rem", color=color).classes("opacity-20")
