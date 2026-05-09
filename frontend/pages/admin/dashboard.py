"""
Trang Dashboard dành cho Quản trị viên (Admin).
"""
from nicegui import ui
from typing import Optional, Dict, Any, List

from core.auth import require_role, get_user_name
from components.page_layout import page_layout
from services.admin_api import get_stats, get_all_requests


def create_admin_dashboard():

    @ui.page('/admin/dashboard')
    async def admin_dashboard():
        if not require_role("admin"):
            return

        with page_layout("/admin/dashboard", title="Hệ Thống Quản Trị"):
            name = get_user_name()
            
            # Header section
            with ui.card().classes("w-full rounded-3xl bg-indigo-900 text-white p-8 shadow-xl border-none"):
                with ui.row().classes("w-full justify-between items-center"):
                    with ui.column().classes("gap-1"):
                        ui.label(f"Chào mừng Admin, {name}!").classes("text-3xl font-bold")
                        ui.label("Hệ thống quản lý cứu hộ xe toàn quốc").classes("text-indigo-300")
                    
                    with ui.row().classes("gap-2"):
                        ui.button("Người Dùng", icon="people", on_click=lambda: ui.navigate.to("/admin/users")).classes("bg-white/10 rounded-xl font-bold")
                        ui.button("Công Ty", icon="business", on_click=lambda: ui.navigate.to("/admin/companies")).classes("bg-white/10 rounded-xl font-bold")

            # Thống kê hệ thống
            ui.label("Thống kê toàn hệ thống").classes("text-xl font-bold text-gray-700 mt-4 ml-2")
            stats_row = ui.row().classes("w-full gap-4")
            with stats_row:
                user_card = _stat_card("Người dùng", "...", "people", "blue")
                company_card = _stat_card("Công ty", "...", "business", "green")
                request_card = _stat_card("Yêu cầu", "...", "assignment", "purple")
                pending_card = _stat_card("Đang chờ", "...", "pending", "amber")

            # Quick Actions
            ui.label("Quản lý nhanh").classes("text-xl font-bold text-gray-700 mt-6 ml-2")
            with ui.row().classes("w-full gap-6"):
                _action_card("Quản lý Người dùng", "people", "/admin/users", "Danh sách khách hàng & nhân viên", "blue")
                _action_card("Quản lý Công ty", "business", "/admin/companies", "Duyệt và kiểm soát các đơn vị", "green")
                _action_card("Báo cáo hệ thống", "analytics", "/admin/reports", "Thống kê doanh thu & hiệu quả", "purple")

            # Recent Requests Table
            ui.label("Hoạt động gần đây").classes("text-xl font-bold text-gray-700 mt-8 ml-2")
            with ui.card().classes("w-full rounded-2xl p-0 overflow-hidden shadow-sm border border-gray-100 mt-2"):
                requests_table = ui.table(
                    columns=[
                        {'name': 'id', 'label': 'ID', 'field': 'id', 'align': 'left'},
                        {'name': 'customer', 'label': 'Khách hàng', 'field': 'customer_name', 'align': 'left'},
                        {'name': 'company', 'label': 'Công ty', 'field': 'company_name', 'align': 'left'},
                        {'name': 'status', 'label': 'Trạng thái', 'field': 'status', 'align': 'center'},
                        {'name': 'cost', 'label': 'Chi phí', 'field': 'total_cost', 'align': 'right'},
                        {'name': 'payment', 'label': 'Thanh toán', 'field': 'payment_status', 'align': 'center'},
                    ],
                    rows=[]
                ).classes("w-full shadow-none").props("flat")

        # ── Logic ────────────────────────────────────────────────────────
        
        async def _load_stats():
            try:
                s = await get_stats()
                user_card.clear()
                with user_card: _stat_card("Người dùng", str(s.get('total_users', 0)), "people", "blue")
                
                company_card.clear()
                with company_card: _stat_card("Công ty", str(s.get('active_companies', 0)), "business", "green")
                
                request_card.clear()
                with request_card: _stat_card("Yêu cầu", str(s.get('total_requests', 0)), "assignment", "purple")
                
                pending_card.clear()
                with pending_card: _stat_card("Đang chờ", str(s.get('pending_requests', 0)), "pending", "amber")

                # Load recent requests
                reqs = await get_all_requests()
                requests_table.rows = reqs[:10] # Show latest 10
            except Exception as e:
                ui.notify(f"Lỗi tải thống kê: {e}", type="negative")

        await _load_stats()
        ui.timer(60, _load_stats)


def _stat_card(title, value, icon, color):
    with ui.card().classes(f"flex-1 rounded-2xl p-6 shadow-sm border border-{color}-100 bg-white items-center gap-1") as card:
        ui.icon(icon, size="2rem", color=color)
        ui.label(value).classes(f"text-3xl font-bold text-{color}-700")
        ui.label(title).classes("text-xs text-gray-400 font-bold uppercase")
    return card


def _action_card(title, icon, route, desc, color):
    with ui.card().classes("flex-1 min-w-[280px] rounded-2xl p-6 shadow-sm border border-gray-100 hover:border-indigo-300 transition-all cursor-pointer").on("click", lambda: ui.navigate.to(route)):
        with ui.row().classes("items-center gap-4"):
            ui.avatar(icon=icon).classes(f"bg-{color}-100 text-{color}-600")
            with ui.column().classes("gap-0"):
                ui.label(title).classes("font-bold text-gray-800")
                ui.label(desc).classes("text-xs text-gray-500")
