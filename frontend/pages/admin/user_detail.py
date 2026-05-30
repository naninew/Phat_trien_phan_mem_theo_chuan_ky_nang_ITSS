"""
Trang chi tiết khách hàng.
"""
from nicegui import ui
from typing import Optional, Dict, Any

from core.auth import require_admin_auth
from components.page_layout import page_layout
from services.admin_api import get_user_detail
from services.api_client import api_client

def create_user_detail_page():

    @ui.page('/admin/users/{user_id}')
    async def user_detail_page(user_id: str):
        if not require_admin_auth():
            return

        with page_layout(f"/admin/users/{user_id}", title="Chi Tiết Khách Hàng"):
            container = ui.column().classes("w-full gap-4")

            async def _load_data():
                container.clear()
                try:
                    user = await get_user_detail(int(user_id))
                    if not user:
                        with container:
                            ui.label("Không tìm thấy khách hàng").classes("text-xl text-red-500")
                        return
                    _render_content(user)
                except Exception as e:
                    with container:
                        ui.label(f"Lỗi tải dữ liệu: {e}").classes("text-xl text-red-500")

            def _render_content(u: Dict[str, Any]):
                with container:
                    # Header
                    with ui.row().classes("w-full items-center justify-between mb-4 bg-white p-4 rounded-2xl shadow-sm border border-gray-100"):
                        with ui.row().classes("items-center gap-4"):
                            ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/admin/users")).props("flat round")
                            with ui.column().classes("gap-0"):
                                ui.label(f"{u['full_name']}").classes("text-2xl font-bold text-gray-800")
                                ui.label(f"ID: {u['id']} • Đăng ký: {u['created_at'][:10]}").classes("text-gray-500")
                        
                        with ui.row().classes("gap-2"):
                            if u['status'] == "ACTIVE":
                                ui.button("Khóa tài khoản", on_click=lambda: _show_suspend_dialog(u), icon="lock").classes("bg-red-500 text-white")
                            elif u['status'] == "SUSPENDED":
                                ui.button("Mở khóa", on_click=lambda: _show_activate_dialog(u), icon="lock_open").classes("bg-green-500 text-white")
                    
                    # Status Warning
                    if u['status'] == "SUSPENDED" and u.get('suspend_reason'):
                        with ui.row().classes("w-full bg-red-50 text-red-700 p-4 rounded-xl border border-red-200 mb-4 items-center gap-2"):
                            ui.icon("warning", size="1.5rem")
                            ui.label(f"Tài khoản đang bị khóa. Lý do: {u['suspend_reason']}").classes("font-medium")

                    # Grid layout cho Thông tin cá nhân và Xe
                    with ui.row().classes("w-full gap-4"):
                        # Info card
                        with ui.card().classes("flex-1 p-6 rounded-2xl shadow-sm border border-gray-100"):
                            ui.label("Thông tin cá nhân").classes("text-lg font-bold mb-4")
                            with ui.column().classes("gap-2"):
                                ui.label(f"Họ tên: {u['full_name']}")
                                ui.label(f"Email: {u['email']}")
                                ui.label(f"SĐT: {u['phone']}")
                                ui.label(f"Địa chỉ: {u.get('address', 'N/A')}")
                                ui.label(f"Trạng thái: {u['status']}").classes("font-bold")
                        
                        # Vehicles
                        with ui.card().classes("flex-1 p-6 rounded-2xl shadow-sm border border-gray-100"):
                            ui.label(f"Xe đã đăng ký ({len(u.get('vehicles', []))})").classes("text-lg font-bold mb-4")
                            if not u.get('vehicles'):
                                ui.label("Chưa có xe nào").classes("text-gray-500 italic")
                            else:
                                cols = [
                                    {'name': 'plate', 'label': 'Biển số', 'field': 'plate', 'align': 'left'},
                                    {'name': 'brand', 'label': 'Hãng', 'field': 'brand', 'align': 'left'},
                                    {'name': 'model', 'label': 'Mẫu', 'field': 'model', 'align': 'left'},
                                    {'name': 'year', 'label': 'Năm', 'field': 'year', 'align': 'left'},
                                ]
                                ui.table(columns=cols, rows=u['vehicles']).classes("w-full").props("flat bordered")
                    
                    # Lịch sử yêu cầu
                    with ui.card().classes("w-full mt-4 p-6 rounded-2xl shadow-sm border border-gray-100"):
                        ui.label("Lịch sử yêu cầu (5 gần nhất)").classes("text-lg font-bold mb-4")
                        if not u.get('recent_requests'):
                            ui.label("Chưa có yêu cầu nào").classes("text-gray-500 italic")
                        else:
                            cols = [
                                {'name': 'id', 'label': 'ID', 'field': 'id', 'align': 'left'},
                                {'name': 'date', 'label': 'Ngày', 'field': 'created_at', 'align': 'left'},
                                {'name': 'type', 'label': 'Loại sự cố', 'field': 'incident_type', 'align': 'left'},
                                {'name': 'company', 'label': 'Công ty', 'field': 'company_name', 'align': 'left'},
                                {'name': 'status', 'label': 'Trạng thái', 'field': 'status', 'align': 'left'},
                                {'name': 'cost', 'label': 'Tổng tiền', 'field': 'total_cost', 'align': 'right'},
                            ]
                            # Format date and cost
                            rows = []
                            for r in u['recent_requests']:
                                r2 = r.copy()
                                r2['created_at'] = r2['created_at'][:16].replace('T', ' ')
                                if r2['total_cost'] is not None:
                                    r2['total_cost'] = f"{r2['total_cost']:,.0f} đ"
                                else:
                                    r2['total_cost'] = "N/A"
                                rows.append(r2)
                            ui.table(columns=cols, rows=rows).classes("w-full").props("flat bordered")
                            
                    # Lịch sử thanh toán
                    with ui.card().classes("w-full mt-4 p-6 rounded-2xl shadow-sm border border-gray-100"):
                        ui.label("Lịch sử thanh toán").classes("text-lg font-bold mb-4")
                        if not u.get('payment_history'):
                            ui.label("Chưa có giao dịch").classes("text-gray-500 italic")
                        else:
                            cols = [
                                {'name': 'req_id', 'label': 'Yêu cầu ID', 'field': 'request_id', 'align': 'left'},
                                {'name': 'date', 'label': 'Ngày', 'field': 'created_at', 'align': 'left'},
                                {'name': 'method', 'label': 'PTTT', 'field': 'method', 'align': 'left'},
                                {'name': 'status', 'label': 'Trạng thái', 'field': 'status', 'align': 'left'},
                                {'name': 'amount', 'label': 'Số tiền', 'field': 'amount', 'align': 'right'},
                            ]
                            rows = []
                            for p in u['payment_history']:
                                p2 = p.copy()
                                p2['created_at'] = p2['created_at'][:16].replace('T', ' ')
                                p2['amount'] = f"{p2['amount']:,.0f} đ"
                                rows.append(p2)
                            ui.table(columns=cols, rows=rows).classes("w-full").props("flat bordered")
                            
                    # Đánh giá đã viết
                    with ui.card().classes("w-full mt-4 p-6 rounded-2xl shadow-sm border border-gray-100"):
                        ui.label(f"Đánh giá đã viết ({len(u.get('reviews_written', []))})").classes("text-lg font-bold mb-4")
                        if not u.get('reviews_written'):
                            ui.label("Chưa có đánh giá").classes("text-gray-500 italic")
                        else:
                            with ui.column().classes("w-full gap-2"):
                                for rv in u['reviews_written']:
                                    with ui.card().classes("w-full p-4 border border-gray-200 shadow-none"):
                                        with ui.row().classes("w-full justify-between"):
                                            ui.label(f"Công ty: {rv['company_name']}").classes("font-bold")
                                            ui.label(rv['created_at'][:10]).classes("text-sm text-gray-500")
                                        ui.label("⭐" * rv['rating']).classes("text-amber-400 text-xs")
                                        ui.label(rv.get('comment', '')).classes("text-gray-700 mt-2")

            async def _show_suspend_dialog(user):
                with ui.dialog() as dialog, ui.card().classes("p-6 rounded-2xl w-96"):
                    ui.label(f"Khóa tài khoản {user['full_name']}").classes("text-xl font-bold text-red-600 mb-2")
                    reason_input = ui.textarea("Lý do khóa (Bắt buộc)").classes("w-full").props("outlined autofocus")
                    
                    error_label = ui.label().classes("text-red-500 text-sm mt-2")
                    
                    with ui.row().classes("w-full justify-end gap-3 mt-4"):
                        ui.button("Hủy", on_click=dialog.close).props("flat")
                        
                        async def do_suspend():
                            reason = reason_input.value.strip() if reason_input.value else ""
                            if len(reason) < 10:
                                error_label.text = "Vui lòng nhập lý do (ít nhất 10 ký tự)"
                                return
                            try:
                                await api_client.put(f"/admin/users/{user['id']}/suspend", data={"reason": reason})
                                ui.notify("Đã khóa tài khoản", type="positive")
                                dialog.close()
                                await _load_data()
                            except Exception as e:
                                error_label.text = str(e)
                                
                        ui.button("Khóa", on_click=do_suspend).classes("bg-red-600 text-white")
                dialog.open()

            async def _show_activate_dialog(user):
                with ui.dialog() as dialog, ui.card().classes("p-6 rounded-2xl"):
                    ui.label(f"Mở khóa tài khoản {user['full_name']}?").classes("text-xl font-bold mb-4")
                    with ui.row().classes("w-full justify-end gap-3 mt-4"):
                        ui.button("Hủy", on_click=dialog.close).props("flat")
                        async def do_activate():
                            try:
                                await api_client.put(f"/admin/users/{user['id']}/activate")
                                ui.notify("Đã mở khóa tài khoản", type="positive")
                                dialog.close()
                                await _load_data()
                            except Exception as e:
                                ui.notify(f"Lỗi: {e}", type="negative")
                        ui.button("Mở khóa", on_click=do_activate).classes("bg-green-600 text-white")
                dialog.open()

            await _load_data()
