"""
Staff Management - NiceGUI
"""
import re
from datetime import date, datetime

from nicegui import ui
from core.auth import require_role
from components.page_layout import page_layout
from components.company_ui import (
    donut,
    empty_state,
    inject_company_styles,
    kpi_card,
    page_header,
    section_heading,
    status_badge,
)
from services.rescue_api import get_company_staff, add_company_staff, update_company_staff, delete_company_staff


def _parse_valid_birth_date(value: str | None) -> date | None:
    try:
        parsed = datetime.strptime(value or "", "%Y-%m-%d").date()
    except ValueError:
        return None
    today = date.today()
    age = today.year - parsed.year - ((today.month, today.day) < (parsed.month, parsed.day))
    return parsed if parsed.year >= 1940 and age >= 18 else None


def create_staff_page():
    """Register /company/staff route."""

    @ui.page('/company/staff')
    async def staff_page():
        if not require_role("company_staff"):
            return

        inject_company_styles()

        with page_layout("/company/staff", title=""):
            with ui.column().classes("company-page gap-6"):
                page_header(
                    "Quản lý nhân sự",
                    "Theo dõi năng lực, trạng thái và phân bổ đội ngũ cứu hộ.",
                    "groups",
                    "Thêm nhân viên",
                    "person_add",
                    lambda: _show_add_dialog(),
                )

                stats_row = ui.row().classes("w-full gap-4 flex-wrap")
                with ui.row().classes("w-full gap-5 items-start"):
                    staff_container = ui.row().classes("flex-[1.6] gap-4 flex-wrap")
                    with ui.element("div").classes("company-card p-5 flex-1 min-w-[300px] max-w-[380px]"):
                        section_heading("Tỷ lệ sẵn sàng", "Nhân sự có thể nhận nhiệm vụ")
                        donut_slot = ui.row().classes("w-full items-center justify-center py-6")
                        legend_slot = ui.column().classes("w-full gap-2")

        async def refresh_staff():
            staff_container.clear()
            stats_row.clear()
            donut_slot.clear()
            legend_slot.clear()

            try:
                staff = await get_company_staff()
                total_staff = len(staff)
                available_staff = sum(1 for s in staff if s.get('status') == 'AVAILABLE')
                busy_staff = sum(1 for s in staff if s.get('status') == 'BUSY')
                pct = round((available_staff / total_staff) * 100) if total_staff else 0

                with stats_row:
                    kpi_card("Tổng nhân viên", total_staff, "Nhân sự trong đội", "groups", "#2563eb")
                    kpi_card("Sẵn sàng", available_staff, "Có thể nhận nhiệm vụ", "check_circle", "#10b981")
                    kpi_card("Đang làm nhiệm vụ", busy_staff, "Đang được phân công", "engineering", "#f59e0b")

                with donut_slot:
                    donut(pct, f"{pct}%", "#10b981")
                with legend_slot:
                    _legend_row("Sẵn sàng", available_staff, "emerald")
                    _legend_row("Đang làm nhiệm vụ", busy_staff, "amber")

                with staff_container:
                    if not staff:
                        empty_state("group_off", "Chưa có nhân viên nào", "Thêm nhân viên đầu tiên để bắt đầu điều phối đội ngũ.")
                    for s in staff:
                        _render_staff_card(s)
            except Exception as e:
                ui.notify(f"Lỗi tải danh sách: {e}", type="negative")

        def _legend_row(label, value, tone):
            with ui.row().classes("w-full items-center justify-between rounded-xl bg-slate-50 px-3 py-2"):
                ui.label(label).classes("text-sm font-bold text-slate-600")
                status_badge(str(value), tone)

        def _render_staff_card(s):
            status = s.get("status")
            status_text = "Sẵn sàng" if status == "AVAILABLE" else "Đang nhiệm vụ"
            status_tone = "emerald" if status == "AVAILABLE" else "amber"

            with ui.element("div").classes("company-card company-card-hover w-[340px] p-5"):
                with ui.row().classes("w-full items-start justify-between gap-3"):
                    with ui.row().classes("items-center gap-3"):
                        ui.avatar(icon="person", size="48px").classes("bg-blue-50 text-blue-600")
                        with ui.column().classes("gap-1"):
                            ui.label(s.get("full_name") or f"Nhân viên #{s.get('id')}").classes("text-lg font-black text-slate-900")
                            ui.label(f"Trình độ {s.get('skill_level', 'Junior')}").classes("text-xs font-bold text-slate-500")
                    status_badge(status_text, status_tone)

                with ui.column().classes("w-full gap-2 mt-4 rounded-2xl bg-blue-50/70 p-3"):
                    with ui.row().classes("items-center gap-2"):
                        ui.icon("phone", size="17px").classes("text-blue-600")
                        ui.label(s.get("phone") or "Chưa cập nhật SĐT").classes("text-sm font-bold text-slate-700")
                    with ui.row().classes("items-center gap-2"):
                        ui.icon("cake", size="17px").classes("text-blue-600")
                        parsed_birth_date = _parse_valid_birth_date(s.get("birth_date"))
                        if parsed_birth_date:
                            today = date.today()
                            age = today.year - parsed_birth_date.year - (
                                (today.month, today.day) < (parsed_birth_date.month, parsed_birth_date.day)
                            )
                            birth_text = f"{parsed_birth_date.strftime('%d/%m/%Y')} • {age} tuổi"
                        else:
                            birth_text = "Chưa cập nhật ngày sinh"
                        ui.label(birth_text).classes("text-sm font-bold text-slate-700")

                with ui.row().classes("w-full gap-2 mt-4"):
                    with ui.column().classes("flex-1 rounded-2xl bg-slate-50 p-3 gap-1"):
                        ui.label("Nhiệm vụ").classes("text-xs font-black uppercase text-slate-400")
                        ui.label(str(s.get("tasks_count", 0))).classes("text-xl font-black text-slate-900")
                    with ui.column().classes("flex-1 rounded-2xl bg-slate-50 p-3 gap-1"):
                        ui.label("Trạng thái").classes("text-xs font-black uppercase text-slate-400")
                        ui.label(status_text).classes("text-sm font-bold text-slate-700")

                ui.separator().classes("my-4")
                with ui.row().classes("w-full justify-end gap-2"):
                    ui.button(icon="edit", on_click=lambda staff=s: _show_edit_dialog(staff)).props(
                        "flat round dense color=blue-7"
                    ).classes("bg-blue-50").tooltip("Sửa hồ sơ")
                    if status != "AVAILABLE":
                        ui.button(icon="check_circle", on_click=lambda sid=s['id']: _update_s(sid, status='AVAILABLE')).props(
                            "flat round dense color=green-7"
                        ).classes("bg-green-50").tooltip("Đặt sẵn sàng")
                    if status != "BUSY":
                        ui.button(icon="engineering", on_click=lambda sid=s['id']: _update_s(sid, status='BUSY')).props(
                            "flat round dense color=orange-8"
                        ).classes("bg-orange-50").tooltip("Đặt đang làm nhiệm vụ")
                    ui.button(icon="delete_outline", on_click=lambda sid=s['id']: _confirm_delete(sid)).props(
                        "flat round dense color=red-6"
                    ).classes("bg-red-50").tooltip("Xóa nhân viên")

        def _show_add_dialog():
            with ui.dialog() as d, ui.card().classes("p-8 rounded-[24px] w-[480px] max-w-[94vw] shadow-2xl"):
                ui.label("Thêm nhân viên mới").classes("text-2xl font-bold font-outfit text-slate-900 mb-6")
                full_name = ui.input("Họ và tên", placeholder="Nguyễn Văn An").classes("w-full company-field").props("outlined rounded maxlength=100")
                with ui.row().classes("w-full gap-3 mt-3"):
                    birth_date = ui.input("Ngày sinh").classes("flex-1 company-field").props("type=date outlined rounded")
                    phone = ui.input("Số điện thoại", placeholder="0901234567").classes("flex-1 company-field").props("outlined rounded maxlength=10")
                level = ui.select(["Junior", "Senior", "Expert"], label="Trình độ", value="Junior").classes("w-full company-field").props("outlined rounded")

                with ui.row().classes("w-full justify-end gap-3 mt-8"):
                    ui.button("Hủy", on_click=d.close).props("flat no-caps").classes("rounded-xl font-bold text-slate-600")

                    async def submit():
                        try:
                            normalized_name = " ".join((full_name.value or "").split())
                            normalized_phone = re.sub(r"[\s-]", "", phone.value or "")
                            if len(normalized_name) < 2:
                                ui.notify("Vui lòng nhập họ và tên nhân viên", type="warning")
                                return
                            if not re.fullmatch(r"0\d{9}", normalized_phone):
                                ui.notify("Số điện thoại phải gồm 10 chữ số và bắt đầu bằng 0", type="warning")
                                return
                            parsed_birth_date = _parse_valid_birth_date(birth_date.value)
                            if not parsed_birth_date:
                                ui.notify("Vui lòng nhập ngày sinh hợp lệ; nhân viên phải từ 18 tuổi trở lên", type="warning")
                                return

                            if await add_company_staff(normalized_name, parsed_birth_date.isoformat(), normalized_phone, level.value):
                                ui.notify("Đã thêm nhân viên thành công", type="positive")
                                d.close()
                                await refresh_staff()
                        except Exception as e:
                            ui.notify(f"Lỗi: {e}", type="negative")

                    ui.button("Lưu", icon="save", on_click=submit).classes("company-primary-btn px-5").props("unelevated no-caps")
            d.open()

        def _show_edit_dialog(staff):
            with ui.dialog() as d, ui.card().classes("p-8 rounded-[24px] w-[480px] max-w-[94vw] shadow-2xl"):
                ui.label("Cập nhật hồ sơ nhân viên").classes("text-2xl font-bold font-outfit text-slate-900 mb-6")
                full_name = ui.input("Họ và tên", value=staff.get("full_name") or "").classes("w-full company-field").props("outlined rounded maxlength=100")
                with ui.row().classes("w-full gap-3 mt-3"):
                    birth_date = ui.input(
                        "Ngày sinh",
                        value=staff.get("birth_date") or "",
                    ).classes("flex-1 company-field").props("type=date outlined rounded")
                    phone = ui.input("Số điện thoại", value=staff.get("phone") or "").classes("flex-1 company-field").props("outlined rounded maxlength=10")
                level = ui.select(
                    ["Junior", "Senior", "Expert"],
                    label="Trình độ",
                    value=staff.get("skill_level") or "Junior",
                ).classes("w-full company-field").props("outlined rounded")

                with ui.row().classes("w-full justify-end gap-3 mt-8"):
                    ui.button("Hủy", on_click=d.close).props("flat no-caps").classes("rounded-xl font-bold text-slate-600")

                    async def submit_edit():
                        normalized_name = " ".join((full_name.value or "").split())
                        normalized_phone = re.sub(r"[\s-]", "", phone.value or "")
                        if len(normalized_name) < 2:
                            ui.notify("Vui lòng nhập họ và tên nhân viên", type="warning")
                            return
                        if not re.fullmatch(r"0\d{9}", normalized_phone):
                            ui.notify("Số điện thoại phải gồm 10 chữ số và bắt đầu bằng 0", type="warning")
                            return
                        parsed_birth_date = _parse_valid_birth_date(birth_date.value)
                        if not parsed_birth_date:
                            ui.notify("Vui lòng nhập ngày sinh hợp lệ; nhân viên phải từ 18 tuổi trở lên", type="warning")
                            return
                        try:
                            updated = await update_company_staff(
                                staff["id"],
                                skill_level=level.value,
                                full_name=normalized_name,
                                birth_date=parsed_birth_date.isoformat(),
                                phone=normalized_phone,
                            )
                            if updated:
                                ui.notify("Đã cập nhật hồ sơ nhân viên", type="positive")
                                d.close()
                                await refresh_staff()
                        except Exception as e:
                            ui.notify(f"Lỗi: {e}", type="negative")

                    ui.button("Lưu thay đổi", icon="save", on_click=submit_edit).classes("company-primary-btn px-5").props("unelevated no-caps")
            d.open()

        def _confirm_delete(sid):
            with ui.dialog() as dlg, ui.card().classes('rounded-[24px] p-8 shadow-2xl w-[400px]'):
                with ui.column().classes('w-full items-center gap-3'):
                    ui.icon('warning', size='3.5rem').classes('text-red-500 mb-2')
                    ui.label('Xác nhận xóa?').classes('text-2xl font-bold text-slate-900 font-outfit')
                    ui.label(f'Bạn có chắc chắn muốn xóa nhân viên #{sid}?').classes('text-sm text-gray-500 text-center mb-4 leading-relaxed')
                    with ui.row().classes('w-full gap-3'):
                        ui.button('Hủy', on_click=dlg.close).props('no-caps flat').classes('flex-1 rounded-xl font-bold py-3 text-slate-600')

                        async def do_delete():
                            try:
                                if await delete_company_staff(sid):
                                    ui.notify("Đã xóa nhân viên", type="info")
                                    dlg.close()
                                    await refresh_staff()
                            except Exception as e:
                                ui.notify(f"Lỗi: {e}", type="negative")

                        ui.button('Xóa', icon='delete', on_click=do_delete).props('no-caps').classes('flex-1 bg-red-600 hover:bg-red-700 text-white rounded-xl font-bold py-3')
            dlg.open()

        async def _update_s(sid, **kwargs):
            try:
                if await update_company_staff(sid, **kwargs):
                    ui.notify("Cập nhật trạng thái thành công", type="positive")
                    await refresh_staff()
            except Exception as e:
                ui.notify(f"Lỗi: {e}", type="negative")

        await refresh_staff()
