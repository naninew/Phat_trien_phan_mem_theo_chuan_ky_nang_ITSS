"""
Trang chi tiết công ty cứu hộ.
"""
from nicegui import ui
from typing import Dict, Any

from core.auth import require_admin_auth
from components.page_layout import page_layout
from services.admin_api import (
    get_company_detail,
    approve_company,
    reject_company,
    suspend_company,
    activate_company,
)


def create_company_detail_page():

    @ui.page('/admin/companies/{company_id}')
    async def company_detail_page(company_id: str):
        if not require_admin_auth():
            return

        with page_layout(f"/admin/companies/{company_id}", title="Chi Tiết Công Ty"):
            container = ui.column().classes("w-full gap-4")

            async def _load_data():
                container.clear()
                try:
                    company = await get_company_detail(int(company_id))
                    if not company:
                        with container:
                            ui.label("Không tìm thấy công ty").classes("text-xl text-red-500")
                        return
                    _render_content(company)
                except Exception as e:
                    with container:
                        ui.label(f"Lỗi tải dữ liệu: {e}").classes("text-xl text-red-500")

            def _render_content(c: Dict[str, Any]):
                with container:
                    verified_label = "Đã xác minh" if c.get("is_verified") else "Chưa xác minh"
                    status_map = {
                        "active": ("Hoạt động", "green"),
                        "pending": ("Chờ duyệt", "amber"),
                        "suspended": ("Tạm dừng", "red"),
                    }
                    status_label, status_color = status_map.get(c.get("status", ""), (c.get("status"), "gray"))

                    with ui.row().classes("w-full items-center justify-between mb-4 bg-white p-4 rounded-2xl shadow-sm border border-gray-100"):
                        with ui.row().classes("items-center gap-4"):
                            ui.button(icon="arrow_back", on_click=lambda: ui.navigate.to("/admin/companies")).props("flat round")
                            with ui.column().classes("gap-0"):
                                ui.label(c["company_name"]).classes("text-2xl font-bold text-gray-800")
                                ui.label(
                                    f"ID: {c['id']} • Đăng ký: {c['created_at'][:10]} • {verified_label}"
                                ).classes("text-gray-500")

                        with ui.row().classes("gap-2 flex-wrap"):
                            if not c.get("is_verified") and c.get("status") != "suspended":
                                ui.button("Xác minh / Duyệt", icon="check", on_click=lambda: _show_approve_dialog(c)).classes("bg-green-600 text-white")
                                ui.button("Từ chối", icon="close", on_click=lambda: _show_reject_dialog(c)).classes("bg-red-500 text-white")
                            if c.get("status") == "active":
                                ui.button("Khóa", icon="lock", on_click=lambda: _show_suspend_dialog(c)).classes("bg-red-500 text-white")
                            elif c.get("status") == "suspended":
                                ui.button("Mở khóa", icon="lock_open", on_click=lambda: _show_activate_dialog(c)).classes("bg-green-500 text-white")

                    if c.get("status") == "suspended" and c.get("suspend_reason"):
                        with ui.row().classes("w-full bg-red-50 text-red-700 p-4 rounded-xl border border-red-200 mb-4 items-center gap-2"):
                            ui.icon("warning", size="1.5rem")
                            ui.label(f"Công ty đang bị khóa. Lý do: {c['suspend_reason']}").classes("font-medium")

                    with ui.row().classes("w-full items-center gap-2 mb-2"):
                        ui.label(status_label).classes(
                            f"text-xs font-bold uppercase px-3 py-1 rounded-full bg-{status_color}-50 text-{status_color}-600"
                        )
                        with ui.row().classes("items-center gap-1"):
                            ui.label(f"{c.get('rating_avg', 0)}").classes("font-bold text-amber-500")
                            ui.icon("star", color="amber", size="1rem")
                            ui.label(f"({c.get('rating_count', 0)} đánh giá)").classes("text-sm text-gray-500")

                    with ui.tabs().classes("w-full") as tabs:
                        tab_info = ui.tab("Thông tin")
                        if c.get("status") != "pending":
                            tab_services = ui.tab("Dịch vụ & Xe")
                            tab_staff = ui.tab("Nhân sự")
                            tab_requests = ui.tab("Lịch sử yêu cầu")
                            tab_reviews = ui.tab("Đánh giá")
                        else:
                            tab_services = None
                            tab_staff = None
                            tab_requests = None
                            tab_reviews = None

                    with ui.tab_panels(tabs, value=tab_info).classes("w-full"):
                        with ui.tab_panel(tab_info):
                            with ui.card().classes("w-full p-6 rounded-2xl shadow-sm border border-gray-100"):
                                with ui.column().classes("gap-2"):
                                    ui.label(f"Người đại diện: {c.get('representative_name', 'N/A')}")
                                    ui.label(f"SĐT / Hotline: {c.get('phone', 'N/A')}")
                                    ui.label(f"Địa chỉ: {c.get('address', 'N/A')}")
                                    ui.label(f"Khu vực hoạt động: {c.get('area', 'N/A')}")
                                    ui.label(f"Giấy phép kinh doanh: {c.get('business_license', 'N/A')}")
                                    if c.get("business_license"):
                                        ui.link("Xem giấy phép kinh doanh", c["business_license"], new_tab=True).classes("text-indigo-600")

                        if tab_services:
                            with ui.tab_panel(tab_services):
                                with ui.row().classes("w-full gap-4"):
                                    with ui.card().classes("flex-1 p-6 rounded-2xl shadow-sm border border-gray-100"):
                                        ui.label(f"Dịch vụ ({len(c.get('services', []))})").classes("text-lg font-bold mb-4")
                                        if not c.get("services"):
                                            ui.label("Chưa có dịch vụ").classes("text-gray-500 italic")
                                        else:
                                            service_cols = [
                                                {"name": "name", "label": "Tên dịch vụ", "field": "name", "align": "left"},
                                                {"name": "price_range", "label": "Giá", "field": "price_range", "align": "right"},
                                            ]
                                            ui.table(columns=service_cols, rows=c["services"]).classes("w-full").props("flat bordered")

                                    with ui.card().classes("flex-1 p-6 rounded-2xl shadow-sm border border-gray-100"):
                                        ui.label(f"Xe cứu hộ ({len(c.get('vehicles', []))})").classes("text-lg font-bold mb-4")
                                        if not c.get("vehicles"):
                                            ui.label("Chưa có xe").classes("text-gray-500 italic")
                                        else:
                                            vehicle_cols = [
                                                {"name": "plate", "label": "Biển số", "field": "plate", "align": "left"},
                                                {"name": "type", "label": "Loại xe", "field": "type", "align": "left"},
                                                {"name": "status", "label": "Trạng thái", "field": "status", "align": "left"},
                                            ]
                                            ui.table(columns=vehicle_cols, rows=c["vehicles"]).classes("w-full").props("flat bordered")

                        if tab_staff:
                            with ui.tab_panel(tab_staff):
                                with ui.card().classes("w-full p-6 rounded-2xl shadow-sm border border-gray-100"):
                                    ui.label(f"Nhân sự ({len(c.get('staff', []))})").classes("text-lg font-bold mb-4")
                                    if not c.get("staff"):
                                        ui.label("Chưa có nhân viên").classes("text-gray-500 italic")
                                    else:
                                        staff_cols = [
                                            {"name": "name", "label": "Tên", "field": "name", "align": "left"},
                                            {"name": "role", "label": "Vai trò", "field": "role", "align": "left"},
                                            {"name": "status", "label": "Trạng thái", "field": "status", "align": "left"},
                                        ]
                                        ui.table(columns=staff_cols, rows=c["staff"]).classes("w-full").props("flat bordered")

                        if tab_requests:
                            with ui.tab_panel(tab_requests):
                                with ui.card().classes("w-full p-6 rounded-2xl shadow-sm border border-gray-100"):
                                    ui.label("Lịch sử yêu cầu (10 gần nhất)").classes("text-lg font-bold mb-4")
                                    if not c.get("recent_requests"):
                                        ui.label("Chưa có yêu cầu").classes("text-gray-500 italic")
                                    else:
                                        req_cols = [
                                            {"name": "id", "label": "ID", "field": "id", "align": "left"},
                                            {"name": "customer", "label": "Khách hàng", "field": "customer_name", "align": "left"},
                                            {"name": "type", "label": "Loại sự cố", "field": "incident_type", "align": "left"},
                                            {"name": "status", "label": "Trạng thái", "field": "status", "align": "left"},
                                            {"name": "date", "label": "Ngày", "field": "created_at", "align": "left"},
                                            {"name": "cost", "label": "Tổng tiền", "field": "total_cost", "align": "right"},
                                        ]
                                        rows = []
                                        for r in c["recent_requests"]:
                                            row = r.copy()
                                            row["created_at"] = row["created_at"][:16].replace("T", " ")
                                            if row["total_cost"] is not None:
                                                row["total_cost"] = f"{row['total_cost']:,.0f} đ"
                                            else:
                                                row["total_cost"] = "N/A"
                                            rows.append(row)
                                        ui.table(columns=req_cols, rows=rows).classes("w-full").props("flat bordered")

                        if tab_reviews:
                            with ui.tab_panel(tab_reviews):
                                with ui.card().classes("w-full p-6 rounded-2xl shadow-sm border border-gray-100"):
                                    ui.label(f"Đánh giá nhận được ({len(c.get('reviews', []))})").classes("text-lg font-bold mb-4")
                                    if not c.get("reviews"):
                                        ui.label("Chưa có đánh giá").classes("text-gray-500 italic")
                                    else:
                                        with ui.column().classes("w-full gap-2"):
                                            for rv in c["reviews"]:
                                                with ui.card().classes("w-full p-4 border border-gray-200 shadow-none"):
                                                    with ui.row().classes("w-full justify-between"):
                                                        ui.label(rv["customer_name"]).classes("font-bold")
                                                        ui.label(rv["created_at"][:10]).classes("text-sm text-gray-500")
                                                    ui.label("⭐" * rv["rating"]).classes("text-amber-400 text-xs")
                                                    ui.label(rv.get("comment", "")).classes("text-gray-700 mt-2")

            async def _show_approve_dialog(company):
                with ui.dialog() as dialog, ui.card().classes("p-6 rounded-2xl w-96"):
                    ui.label(f"Duyệt công ty {company['company_name']}?").classes("text-xl font-bold mb-4")
                    with ui.row().classes("w-full justify-end gap-3 mt-4"):
                        ui.button("Hủy", on_click=dialog.close).props("flat")

                        async def do_approve():
                            try:
                                await approve_company(company["id"])
                                ui.notify("Đã duyệt công ty", type="positive")
                                dialog.close()
                                await _load_data()
                            except Exception as e:
                                ui.notify(f"Lỗi: {e}", type="negative")

                        ui.button("Xác nhận duyệt", on_click=do_approve).classes("bg-green-600 text-white")
                dialog.open()

            async def _show_reject_dialog(company):
                with ui.dialog() as dialog, ui.card().classes("p-6 rounded-2xl w-96"):
                    ui.label(f"Từ chối xác minh {company['company_name']}").classes("text-xl font-bold text-red-600 mb-2")
                    reason_input = ui.textarea("Lý do từ chối (Bắt buộc)").classes("w-full").props("outlined autofocus")
                    error_label = ui.label().classes("text-red-500 text-sm mt-2")

                    with ui.row().classes("w-full justify-end gap-3 mt-4"):
                        ui.button("Hủy", on_click=dialog.close).props("flat")

                        async def do_reject():
                            reason = reason_input.value.strip() if reason_input.value else ""
                            if len(reason) < 5:
                                error_label.text = "Vui lòng nhập lý do (ít nhất 5 ký tự)"
                                return
                            try:
                                await reject_company(company["id"], reason)
                                ui.notify("Đã từ chối xác minh công ty", type="warning")
                                dialog.close()
                                await _load_data()
                            except Exception as e:
                                error_label.text = str(e)

                        ui.button("Xác nhận từ chối", on_click=do_reject).classes("bg-red-600 text-white")
                dialog.open()

            async def _show_suspend_dialog(company):
                with ui.dialog() as dialog, ui.card().classes("p-6 rounded-2xl w-96"):
                    ui.label(f"Khóa công ty {company['company_name']}").classes("text-xl font-bold text-red-600 mb-2")
                    reason_input = ui.textarea("Lý do khóa (Bắt buộc)").classes("w-full").props("outlined autofocus")
                    error_label = ui.label().classes("text-red-500 text-sm mt-2")

                    with ui.row().classes("w-full justify-end gap-3 mt-4"):
                        ui.button("Hủy", on_click=dialog.close).props("flat")

                        async def do_suspend():
                            reason = reason_input.value.strip() if reason_input.value else ""
                            if len(reason) < 5:
                                error_label.text = "Vui lòng nhập lý do (ít nhất 5 ký tự)"
                                return
                            try:
                                await suspend_company(company["id"], reason)
                                ui.notify("Đã khóa công ty", type="positive")
                                dialog.close()
                                await _load_data()
                            except Exception as e:
                                error_label.text = str(e)

                        ui.button("Xác nhận khóa", on_click=do_suspend).classes("bg-red-600 text-white")
                dialog.open()

            async def _show_activate_dialog(company):
                with ui.dialog() as dialog, ui.card().classes("p-6 rounded-2xl"):
                    ui.label(f"Mở khóa công ty {company['company_name']}?").classes("text-xl font-bold mb-4")
                    with ui.row().classes("w-full justify-end gap-3 mt-4"):
                        ui.button("Hủy", on_click=dialog.close).props("flat")

                        async def do_activate():
                            try:
                                await activate_company(company["id"])
                                ui.notify("Đã mở khóa công ty", type="positive")
                                dialog.close()
                                await _load_data()
                            except Exception as e:
                                ui.notify(f"Lỗi: {e}", type="negative")

                        ui.button("Mở khóa", on_click=do_activate).classes("bg-green-600 text-white")
                dialog.open()

            await _load_data()
