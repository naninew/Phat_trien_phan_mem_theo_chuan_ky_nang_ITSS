"""
Trang danh sách yêu cầu cứu hộ của khách hàng.
"""
from nicegui import ui
from typing import Optional, Dict, Any, List
from datetime import datetime

from core.auth import require_role
from components.page_layout import page_layout
from services.rescue_api import get_my_requests, cancel_request


def create_requests_page():

    @ui.page('/customer/requests')
    async def requests_page():
        if not require_role("customer"):
            return

        with page_layout("/customer/requests", title="Yêu Cầu Của Tôi"):
            
            with ui.row().classes("w-full items-center justify-between mb-2"):
                with ui.column().classes("gap-0"):
                    ui.label("📋 Danh Sách Yêu Cầu").classes("text-3xl font-bold text-gray-800")
                    ui.label("Theo dõi và quản lý các yêu cầu cứu hộ của bạn").classes("text-gray-500")
                
                ui.button("GỬI YÊU CẦU MỚI", icon="add", on_click=lambda: ui.navigate.to("/customer/find-rescue")).classes("rounded-xl bg-indigo-600 text-white font-bold px-6 py-3 shadow-lg hover:bg-indigo-700")

            # Bộ lọc & Refresh
            with ui.row().classes("w-full items-center gap-4 bg-white p-4 rounded-2xl shadow-sm border border-gray-100"):
                ui.label("Lọc trạng thái:").classes("text-gray-600 font-medium")
                status_filter = ui.select(
                    options={
                        'all': 'Tất cả',
                        'pending': 'Chờ tiếp nhận',
                        'accepted': 'Đã tiếp nhận',
                        'en_route': 'Đang di chuyển',
                        'on_site': 'Đang xử lý',
                        'completed': 'Hoàn thành',
                        'cancelled': 'Đã hủy'
                    },
                    value='all',
                    on_change=lambda: _load_data()
                ).classes("w-64").props("outlined dense")
                
                ui.space()
                
                refresh_btn = ui.button(icon="refresh", on_click=lambda: _load_data()).props("flat round color=indigo")
                ui.label("Tự động cập nhật mỗi 30s").classes("text-[10px] text-gray-400 italic")

            # Container danh sách
            list_container = ui.column().classes("w-full gap-4")

        # ── Logic ────────────────────────────────────────────────────────
        
        async def _load_data():
            refresh_btn.props("loading")
            list_container.clear()
            
            try:
                all_reqs = await get_my_requests()
                
                # Filter
                f = status_filter.value
                if f != 'all':
                    reqs = [r for r in all_reqs if r['status'] == f]
                else:
                    reqs = all_reqs

                with list_container:
                    if not reqs:
                        with ui.column().classes("w-full items-center py-20 gap-4 bg-white rounded-3xl border border-dashed border-gray-300"):
                            ui.icon("inbox", size="5rem").classes("text-gray-200")
                            ui.label("Không tìm thấy yêu cầu nào phù hợp").classes("text-gray-400 text-lg")
                            if f != 'all':
                                ui.button("Xem tất cả", on_click=lambda: status_filter.set_value('all')).props("flat")
                    else:
                        for r in reqs:
                            _render_request_item(r)
            except Exception as e:
                ui.notify(f"Lỗi tải dữ liệu: {e}", type="negative")
            finally:
                refresh_btn.props(remove="loading")

        def _render_request_item(r):
            status_map = {
                "pending":   ("Chờ tiếp nhận", "text-amber-600 bg-amber-50 border-amber-200"),
                "accepted":  ("Đã tiếp nhận",  "text-blue-600 bg-blue-50 border-blue-200"),
                "en_route":  ("Đang di chuyển","text-indigo-600 bg-indigo-50 border-indigo-200"),
                "on_site":   ("Đang xử lý",    "text-orange-600 bg-orange-50 border-orange-200"),
                "completed": ("Hoàn thành",    "text-green-600 bg-green-50 border-green-200"),
                "cancelled": ("Đã hủy",        "text-gray-500 bg-gray-50 border-gray-200"),
            }
            label, style = status_map.get(r['status'], (r['status'], "text-gray-600 bg-gray-50"))
            
            # Format time
            try:
                dt = datetime.fromisoformat(r['created_at'].replace('Z', '+00:00'))
                time_str = dt.strftime("%H:%M - %d/%m/%Y")
            except:
                time_str = r['created_at']

            with ui.card().classes("w-full rounded-2xl p-0 overflow-hidden shadow-sm hover:shadow-md transition-all border border-gray-100"):
                with ui.row().classes("w-full no-wrap h-full"):
                    # Left accent
                    ui.element("div").classes(f"w-2 h-full {style.split(' ')[2].replace('bg-', 'bg-').replace('50', '500')}")
                    
                    with ui.column().classes("flex-1 p-5 gap-3"):
                        # Header
                        with ui.row().classes("w-full justify-between items-center"):
                            with ui.row().classes("items-center gap-2"):
                                ui.label(f"Mã: #{r['id']}").classes("font-bold text-gray-400 text-sm")
                                ui.label(label).classes(f"text-[10px] font-bold uppercase px-3 py-1 rounded-full border {style}")
                            
                            ui.label(time_str).classes("text-xs text-gray-400")

                        # Content
                        with ui.row().classes("w-full gap-4"):
                            with ui.column().classes("flex-1 gap-1"):
                                ui.label(r.get('service_name', 'Dịch vụ cứu hộ')).classes("text-xl font-bold text-gray-800")
                                with ui.row().classes("items-center gap-1 text-gray-500 text-sm"):
                                    ui.icon("place", size="1rem")
                                    ui.label(r.get('address_description', 'N/A')).classes("truncate max-w-md")
                            
                            if r.get('total_cost'):
                                with ui.column().classes("items-end gap-0"):
                                    ui.label("Tổng phí").classes("text-[10px] uppercase text-gray-400")
                                    ui.label(f"{r['total_cost']:,.0f} đ").classes("text-lg font-bold text-green-600")

                        # Assigned Company
                        if r.get('company_name'):
                            with ui.row().classes("items-center gap-2 bg-indigo-50 p-2 rounded-xl w-fit"):
                                ui.icon("business", size="1.2rem", color="indigo")
                                ui.label(f"Đơn vị: {r['company_name']}").classes("text-sm font-semibold text-indigo-700")

                        # Actions
                        ui.separator().classes("my-1 opacity-50")
                        with ui.row().classes("w-full justify-end gap-2"):
                            if r['status'] == 'pending':
                                ui.button("Hủy Yêu Cầu", on_click=lambda rid=r['id']: _confirm_cancel(rid)).classes("rounded-lg").props("flat color=red dense")
                            
                            ui.button("CHI TIẾT & THEO DÕI", icon="visibility", on_click=lambda rid=r['id']: ui.navigate.to(f"/customer/track/{rid}")).classes("rounded-lg bg-indigo-50 text-indigo-600 hover:bg-indigo-100 font-bold px-4 py-1").props("unelevated dense")

        async def _confirm_cancel(request_id):
            with ui.dialog() as dialog, ui.card().classes("p-6 rounded-2xl"):
                ui.label("Xác nhận hủy yêu cầu?").classes("text-xl font-bold mb-2")
                ui.label("Bạn có chắc chắn muốn hủy yêu cầu cứu hộ này không?").classes("text-gray-500 mb-6")
                with ui.row().classes("w-full justify-end gap-3"):
                    ui.button("Đóng", on_click=dialog.close).props("flat")
                    async def do_cancel():
                        try:
                            await cancel_request(request_id)
                            ui.notify("Đã hủy yêu cầu", type="info")
                            dialog.close()
                            await _load_data()
                        except Exception as e:
                            ui.notify(f"Lỗi: {e}", type="negative")
                    ui.button("Xác nhận hủy", on_click=do_cancel).classes("bg-red-500 text-white font-bold px-6")
            dialog.open()

        await _load_data()
        ui.timer(30, _load_data)
