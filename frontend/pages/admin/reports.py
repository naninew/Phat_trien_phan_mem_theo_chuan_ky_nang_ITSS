"""
Trang báo cáo và thống kê dành cho Admin.
"""
from nicegui import ui
from core.auth import require_admin_auth
from components.page_layout import page_layout
import httpx
from core.config import BACKEND_URL
from core.auth import get_access_token

def create_reports_page():

    @ui.page('/admin/reports')
    async def reports_page():
        if not require_admin_auth():
            return

        with page_layout("/admin/reports", title="Báo Cáo & Thống Kê"):
            
            with ui.row().classes("w-full items-center justify-between mb-6"):
                with ui.column().classes("gap-0"):
                    ui.label("📊 Báo Cáo Hệ Thống").classes("text-3xl font-bold text-gray-800")
                    ui.label("Tổng quan hoạt động và hiệu quả kinh doanh").classes("text-gray-500")
                
                ui.button("XUẤT BÁO CÁO (CSV)", icon="download", on_click=lambda: _export_report()).classes("rounded-xl btn-primary")

            # --- Stats Grid ---
            with ui.row().classes("w-full gap-6 mb-8"):
                revenue_card = _stat_card("Tổng doanh thu", "...", "trending_up", "green")
                req_card = _stat_card("Yêu cầu hoàn thành", "...", "task_alt", "blue")
                company_card = _stat_card("Đối tác hoạt động", "...", "business", "indigo")

            # --- Charts ---
            with ui.row().classes("w-full gap-6"):
                with ui.card().classes("flex-1 m3-card p-6 h-96"):
                    ui.label("Doanh thu 6 tháng gần nhất").classes("text-lg font-bold mb-4")
                    revenue_chart = ui.echart({
                        'xAxis': {'type': 'category', 'data': []},
                        'yAxis': {'type': 'value'},
                        'series': [{'data': [], 'type': 'line', 'smooth': True, 'areaStyle': {}, 'itemStyle': {'color': '#10b981'}}]
                    }).classes("w-full h-64")

                with ui.card().classes("w-80 m3-card p-6 h-96"):
                    ui.label("Tỉ lệ trạng thái").classes("text-lg font-bold mb-4")
                    status_chart = ui.echart({
                        'tooltip': {'trigger': 'item'},
                        'series': [{
                            'type': 'pie',
                            'radius': '70%',
                            'data': []
                        }]
                    }).classes("w-full h-64")

        # ── Logic ────────────────────────────────────────────────────────
        
        async def _load_reports():
            try:
                from services.admin_api import get_stats, get_chart_stats
                s = await get_stats()
                revenue_card.clear()
                with revenue_card: _stat_card("Tổng doanh thu", f"{int(s.get('total_revenue', 0)):,} đ", "trending_up", "green")
                
                req_card.clear()
                with req_card: _stat_card("Tổng yêu cầu", str(s.get('total_requests', 0)), "task_alt", "blue")
                
                company_card.clear()
                with company_card: _stat_card("Đối tác hoạt động", str(s.get('active_companies', 0)), "business", "indigo")

                c = await get_chart_stats()
                revenue_chart.options['xAxis']['data'] = c.get('revenue_chart', {}).get('labels', [])
                revenue_chart.options['series'][0]['data'] = c.get('revenue_chart', {}).get('values', [])
                revenue_chart.update()

                status_chart.options['series'][0]['data'] = c.get('status_chart', [])
                status_chart.update()
            except Exception as e:
                ui.notify(f"Lỗi tải báo cáo: {e}", type="negative")

        async def _export_report():
            try:
                from services.admin_api import get_export_data
                import csv
                import io
                
                data = await get_export_data()
                if not data:
                    ui.notify("Không có dữ liệu để xuất")
                    return
                
                output = io.StringIO()
                writer = csv.DictWriter(output, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
                
                content = output.getvalue().encode('utf-8-sig')
                ui.download(content, "bao_cao_cuu_ho.csv")
                ui.notify("Đã xuất báo cáo thành công")
            except Exception as e:
                ui.notify(f"Lỗi xuất báo cáo: {e}", type="negative")

        await _load_reports()

def _stat_card(label, value, icon, color):
    with ui.card().classes(f"flex-1 m3-card p-6 border-l-4 border-{color}-500") as card:
        with ui.row().classes("w-full items-center justify-between"):
            with ui.column().classes("gap-0"):
                ui.label(label).classes("text-xs text-gray-400 uppercase font-bold")
                ui.label(value).classes("text-2xl font-bold text-gray-800")
            ui.icon(icon, size="2.5rem", color=color).classes("opacity-20")
    return card
