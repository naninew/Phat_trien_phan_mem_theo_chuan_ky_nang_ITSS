"""
Trang quản lý đơn vị cứu hộ – dành cho Quản trị viên (Admin).
"""
from nicegui import ui
from typing import Dict, Any

from core.auth import require_admin_auth
from components.page_layout import page_layout
from services.admin_api import (
    get_companies,
    approve_company,
    reject_company,
    suspend_company,
    activate_company,
)

AREA_OPTIONS = {
    "all": "Tất cả khu vực",
    "Hà Nội": "Hà Nội",
    "TP. Hồ Chí Minh": "TP. Hồ Chí Minh",
    "Đà Nẵng": "Đà Nẵng",
    "Hải Phòng": "Hải Phòng",
    "Cần Thơ": "Cần Thơ",
}


def create_companies_page():

    @ui.page('/admin/companies')
    async def companies_page():
        if not require_admin_auth():
            return

        with page_layout("/admin/companies", title="Quản Lý Đơn Vị"):

            with ui.row().classes("w-full items-center justify-between mb-4"):
                with ui.column().classes("gap-0"):
                    ui.label("🏢 Quản Lý Đơn Vị Cứu Hộ").classes("text-3xl font-bold text-gray-800")
                    ui.label("Duyệt và kiểm soát các đối tác cứu hộ trên hệ thống").classes("text-gray-500")

                refresh_btn = ui.button(icon="refresh", on_click=lambda: _load_data()).props("flat round color=indigo")

            with ui.row().classes("w-full items-center gap-4 bg-white p-4 rounded-2xl shadow-sm border border-gray-100 mb-6 flex-wrap"):
                search_input = ui.input(
                    placeholder="Tìm tên công ty, hotline, số giấy phép...",
                    on_change=lambda: _load_data(),
                ).classes("flex-1 min-w-[200px]").props("outlined dense clearable icon=search")

                ui.label("Trạng thái:").classes("text-gray-600 font-medium")
                status_filter = ui.select(
                    options={"all": "Tất cả", "active": "Đang hoạt động", "pending": "Chờ duyệt", "suspended": "Đang tạm dừng"},
                    value="all",
                    on_change=lambda: _load_data(),
                ).classes("w-48").props("outlined dense")

                ui.label("Xác minh:").classes("text-gray-600 font-medium")
                verified_filter = ui.select(
                    options={"all": "Tất cả", "pending": "Chờ duyệt", "verified": "Đã xác minh", "rejected": "Bị từ chối"},
                    value="all",
                    on_change=lambda: _load_data(),
                ).classes("w-48").props("outlined dense")

                ui.label("Khu vực:").classes("text-gray-600 font-medium")
                area_filter = ui.select(
                    options=AREA_OPTIONS,
                    value="all",
                    on_change=lambda: _load_data(),
                ).classes("w-48").props("outlined dense")

            container = ui.column().classes("w-full gap-4")

        async def _load_data():
            refresh_btn.props("loading")
            container.clear()
            try:
                filtered = await get_companies(
                    status_filter=status_filter.value,
                    verified_filter=verified_filter.value,
                    area=area_filter.value,
                    search=search_input.value or None,
                )

                with container:
                    if not filtered:
                        ui.label("Không tìm thấy đơn vị nào").classes("w-full text-center py-10 text-gray-400 italic")
                    else:
                        for c in filtered:
                            _render_company_card(c)
            except Exception as e:
                ui.notify(f"Lỗi: {e}", type="negative")
            finally:
                refresh_btn.props(remove="loading")

        def _render_company_card(c: Dict[str, Any]):
            status_map = {
                "active": ("Hoạt động", "green"),
                "pending": ("Chờ duyệt", "amber"),
                "suspended": ("Tạm dừng", "red"),
            }
            label, color = status_map.get(c["status"], (c["status"], "gray"))
            verified_badge = "✓ Đã xác minh" if c.get("status_verified") or c.get("is_verified") else "Chờ xác minh"

            with ui.card().classes(
                "w-full rounded-2xl p-6 shadow-sm border border-gray-100 hover:border-indigo-200 transition-all cursor-pointer"
            ).on("click", lambda cid=c["id"]: ui.navigate.to(f"/admin/companies/{cid}")):
                with ui.row().classes("w-full items-start justify-between"):
                    with ui.row().classes("items-center gap-4"):
                        ui.avatar(icon="business").classes(f"bg-{color}-100 text-{color}-600")
                        with ui.column().classes("gap-0"):
                            ui.label(c["company_name"]).classes("font-bold text-xl text-gray-800")
                            ui.label(f"GPKD: {c.get('business_license', 'N/A')}").classes("text-sm text-gray-400 font-mono")
                            ui.label(f"Người đại diện: {c.get('representative_name', 'N/A')}").classes("text-base text-gray-600 mt-1")

                    with ui.column().classes("items-end gap-2"):
                        ui.label(label).classes(
                            f"text-xs font-bold uppercase px-3 py-1 rounded-full bg-{color}-50 text-{color}-600 border border-{color}-100"
                        )
                        ui.label(verified_badge).classes("text-xs text-gray-500")
                        with ui.row().classes("items-center gap-1"):
                            ui.label(f"{c.get('rating', c.get('rating_avg', 0))}").classes("font-bold text-amber-500")
                            ui.icon("star", color="amber", size="1rem")

                with ui.row().classes("mt-4 gap-10 flex-wrap"):
                    with ui.column().classes("gap-1"):
                        ui.label("SĐT / Hotline").classes("text-xs text-gray-400 uppercase font-bold")
                        ui.label(c.get("phone", c.get("hotline", "N/A"))).classes("font-bold text-indigo-600")

                    with ui.column().classes("gap-1"):
                        ui.label("Ngày đăng ký").classes("text-xs text-gray-400 uppercase font-bold")
                        reg_date = c.get("registered_at", c.get("created_at", ""))[:10]
                        ui.label(reg_date).classes("text-sm text-gray-600")

                    with ui.column().classes("gap-1"):
                        ui.label("Khu vực").classes("text-xs text-gray-400 uppercase font-bold")
                        ui.label(c.get("area", "N/A")).classes("text-sm text-gray-600")

                    with ui.column().classes("gap-1"):
                        ui.label("Địa chỉ").classes("text-xs text-gray-400 uppercase font-bold")
                        ui.label(c.get("address", "N/A")).classes("text-sm text-gray-600 max-w-md")

                ui.separator().classes("my-4 opacity-50")

                with ui.row().classes("w-full justify-end gap-2").props("@click.stop"):
                    if not c.get("is_verified") and c.get("status") != "suspended":
                        ui.button(
                            "DUYỆT",
                            icon="check",
                            on_click=lambda comp=c: _show_approve_dialog(comp),
                        ).classes("bg-green-600 text-white font-bold rounded-xl px-6").props("dense")
                        ui.button(
                            "TỪ CHỐI",
                            icon="close",
                            on_click=lambda comp=c: _show_reject_dialog(comp),
                        ).classes("bg-red-50 text-red-600 font-bold rounded-xl px-6").props("flat dense")

                    if c.get("status") == "active":
                        ui.button(
                            "TẠM DỪNG",
                            icon="block",
                            on_click=lambda comp=c: _show_suspend_dialog(comp),
                        ).classes("bg-red-50 text-red-600 font-bold rounded-xl px-6").props("flat dense")

                    if c.get("status") == "suspended":
                        ui.button(
                            "KÍCH HOẠT LẠI",
                            icon="play_arrow",
                            on_click=lambda comp=c: _show_activate_dialog(comp),
                        ).classes("bg-green-50 text-green-600 font-bold rounded-xl px-6").props("flat dense")

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
