"""
Trang Dashboard dành cho công ty cứu hộ.
"""
from nicegui import ui
from typing import Optional, Dict, Any, List

from core.auth import require_role, get_user_name
from components.page_layout import page_layout
from services.rescue_api import get_company_queue


def create_company_dashboard():

    @ui.page('/company/dashboard')
    async def company_dashboard():
        if not require_role("company_staff"):
            return

        with page_layout("/company/dashboard", title="Dashboard Công Ty"):
            name = get_user_name()
            
            # Header section
            with ui.card().classes("w-full rounded-3xl bg-gradient-to-r from-slate-800 to-slate-900 text-white p-8 shadow-xl border-none"):
                with ui.row().classes("w-full justify-between items-center"):
                    with ui.column().classes("gap-1"):
                        ui.label(f"Xin chào, {name}!").classes("text-3xl font-bold")
                        ui.label("Hệ thống quản lý cứu hộ chuyên nghiệp").classes("text-slate-400")
                    
                    with ui.row().classes("gap-4"):
                        ui.button("XEM HÀNG ĐỢI", icon="list_alt", on_click=lambda: ui.navigate.to("/company/queue")).classes("bg-indigo-600 rounded-xl font-bold px-6 py-2 shadow-lg shadow-indigo-500/20")
                        ui.button("QUẢN LÝ ĐỘI XE", icon="local_shipping", on_click=lambda: ui.navigate.to("/company/fleet")).classes("bg-slate-700 rounded-xl font-bold px-6 py-2")

            # Thống kê nhanh
            ui.label("Tổng quan trong ngày").classes("text-xl font-bold text-gray-700 mt-4 ml-2")
            stats_row = ui.row().classes("w-full gap-4")
            with stats_row:
                pending_card = _stat_card("Chờ Tiếp Nhận", "...", "hourglass_empty", "amber")
                active_card  = _stat_card("Đang Thực Hiện", "...", "local_shipping", "indigo")
                done_card    = _stat_card("Đã Hoàn Thành", "...", "task_alt", "green")

            # Quick Actions & Recent
            with ui.row().classes("w-full gap-6 mt-2 items-start"):
                # Left column: Recent Requests
                with ui.column().classes("flex-1 gap-4"):
                    with ui.card().classes("w-full rounded-2xl p-6 shadow-sm border border-gray-100"):
                        with ui.row().classes("w-full justify-between items-center mb-4"):
                            ui.label("Yêu cầu mới nhất").classes("text-lg font-bold text-gray-700")
                            ui.button("Chi tiết", on_click=lambda: ui.navigate.to("/company/queue")).props("flat color=indigo dense")
                        
                        recent_container = ui.column().classes("w-full gap-3")

                # Right column: Quick info
                with ui.column().classes("w-[350px] gap-6"):
                    with ui.card().classes("w-full rounded-2xl p-6 shadow-sm border border-gray-100 bg-indigo-50/20"):
                        ui.label("Mẹo nhanh").classes("font-bold text-indigo-900 mb-2")
                        ui.label("Luôn cập nhật trạng thái 'Đang di chuyển' để khách hàng có thể theo dõi vị trí của bạn.").classes("text-xs text-indigo-700 leading-relaxed")

        # ── Logic ────────────────────────────────────────────────────────
        
        async def _load_stats():
            try:
                queue = await get_company_queue()
                
                pending = sum(1 for r in queue if r['status'] == 'pending')
                active  = sum(1 for r in queue if r['status'] in ('accepted', 'en_route', 'on_site'))
                done    = sum(1 for r in queue if r['status'] == 'completed')

                pending_card.clear()
                with pending_card: _stat_card("Chờ Tiếp Nhận", str(pending), "hourglass_empty", "amber")
                
                active_card.clear()
                with active_card: _stat_card("Đang Thực Hiện", str(active), "local_shipping", "indigo")
                
                done_card.clear()
                with done_card: _stat_card("Đã Hoàn Thành", str(done), "task_alt", "green")

                # Recent requests
                recent_container.clear()
                with recent_container:
                    if not queue:
                        ui.label("Không có hoạt động nào gần đây").classes("text-gray-400 italic text-sm py-4")
                    else:
                        for r in queue[:5]:
                            _render_simple_row(r)
            except Exception as e:
                ui.notify(f"Lỗi tải dữ liệu: {e}", type="negative")

        def _render_simple_row(r):
            with ui.row().classes("w-full items-center justify-between p-3 bg-gray-50 rounded-xl border border-gray-100"):
                with ui.column().classes("gap-0"):
                    ui.label(r.get('service_name', 'Cứu hộ')).classes("font-semibold text-sm")
                    ui.label(f"#{r['id']} - {r.get('customer_name', 'Khách hàng')}").classes("text-[10px] text-gray-400")
                
                ui.button(icon="chevron_right", on_click=lambda: ui.navigate.to("/company/queue")).props("flat round dense")

        await _load_stats()
        ui.timer(30, _load_stats)


def _stat_card(title, value, icon, color):
    with ui.card().classes(f"flex-1 rounded-2xl p-6 shadow-sm border border-{color}-100 bg-white items-center gap-2") as card:
        ui.icon(icon, size="2.5rem", color=color)
        ui.label(value).classes(f"text-3xl font-bold text-{color}-600")
        ui.label(title).classes("text-sm text-gray-500 font-medium")
    return card
