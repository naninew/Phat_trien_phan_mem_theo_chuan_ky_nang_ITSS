"""
Company Dashboard - NiceGUI
"""
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
from services.rescue_api import get_company_queue, get_my_vehicles, get_company_staff


def _vehicle_label(vehicle):
    return vehicle.get("plate_number") or vehicle.get("license_plate") or "Chưa có biển số"


def create_company_dashboard():
    """Register /company/dashboard route."""

    @ui.page('/company/dashboard')
    async def dashboard_page():
        if not require_role("company_staff"):
            return

        inject_company_styles()

        with page_layout("/company/dashboard", title=""):
            with ui.column().classes("company-page gap-6"):
                page_header(
                    "Bảng điều khiển công ty",
                    "Theo dõi yêu cầu, tài nguyên và năng lực vận hành cứu hộ trong thời gian thực.",
                    "space_dashboard",
                    "Điều phối ngay",
                    "bolt",
                    lambda: ui.navigate.to("/company/queue"),
                )

                kpi_row = ui.row().classes("w-full gap-4 flex-wrap")

                with ui.element("div").classes("company-two-column"):
                    with ui.column().classes("company-two-column-main gap-4"):
                        with ui.element("div").classes("company-card p-5"):
                            with ui.row().classes("w-full items-center justify-between mb-4"):
                                section_heading("Dòng yêu cầu mới", "Các yêu cầu chờ tiếp nhận gần nhất")
                                ui.button("Xem hàng đợi", icon="arrow_forward", on_click=lambda: ui.navigate.to("/company/queue")).classes("company-muted-btn").props("flat no-caps")
                            queue_container = ui.column().classes("w-full gap-3")

                    with ui.column().classes("company-two-column-side gap-4"):
                        vehicle_panel = ui.element("div").classes("company-card p-5")
                        staff_panel = ui.element("div").classes("company-card p-5")

        async def refresh_dashboard():
            try:
                queue = await get_company_queue()
                vehicles = await get_my_vehicles()
                staff = await get_company_staff()

                pending = [r for r in queue if r.get('status') == 'PENDING']
                active = [r for r in queue if r.get('status') in ('ACCEPTED', 'ASSIGNED', 'ON_THE_WAY', 'IN_PROGRESS')]
                completed = [r for r in queue if r.get('status') == 'COMPLETED']
                v_avail = len([v for v in vehicles if v.get('status') == 'available'])
                s_avail = len([s for s in staff if s.get('status') == 'AVAILABLE'])

                kpi_row.clear()
                with kpi_row:
                    kpi_card("Đang chờ", len(pending), "Yêu cầu mới cần tiếp nhận", "pending_actions", "#f59e0b")
                    kpi_card("Đang xử lý", len(active), "Đang điều phối hoặc thực hiện", "route", "#2563eb")
                    kpi_card("Hoàn thành", len(completed), "Yêu cầu đã kết thúc", "task_alt", "#10b981")
                    kpi_card("Tài nguyên", f"{s_avail}/{len(staff)} NV", f"{v_avail}/{len(vehicles)} xe sẵn sàng", "inventory_2", "#8b5cf6")

                queue_container.clear()
                with queue_container:
                    if not pending:
                        empty_state("inbox", "Không có yêu cầu mới", "Khi khách hàng gửi yêu cầu, danh sách sẽ xuất hiện tại đây.")
                    for r in pending[:5]:
                        with ui.element("div").classes("rounded-2xl border border-slate-100 bg-slate-50/70 p-4 hover:bg-white hover:shadow-sm transition-all cursor-pointer").on("click", lambda: ui.navigate.to("/company/queue")):
                            with ui.row().classes("w-full items-start justify-between gap-3"):
                                with ui.column().classes("gap-2 flex-1"):
                                    with ui.row().classes("items-center gap-2"):
                                        status_badge("Mới", "amber")
                                        ui.label(f"#{r.get('id')}").classes("text-xs font-bold text-slate-400")
                                    ui.label(r.get('service_name') or "Dịch vụ cứu hộ").classes("text-base font-black text-slate-900")
                                    ui.label(r.get('address_description') or "Chưa có địa chỉ").classes("text-sm text-slate-500 leading-snug")
                                ui.label(str(r.get('created_at') or '')[:16]).classes("text-xs font-semibold text-slate-400")

                vehicle_panel.clear()
                with vehicle_panel:
                    with ui.row().classes("w-full items-center justify-between gap-3"):
                        section_heading("Trạng thái đội xe", "Tỷ lệ phương tiện sẵn sàng")
                        pct = round((v_avail / len(vehicles)) * 100) if vehicles else 0
                        donut(pct, f"{pct}%", "#10b981")
                    with ui.column().classes("w-full gap-2 mt-4"):
                        for v in vehicles[:5]:
                            tone = "emerald" if v.get('status') == 'available' else "amber" if v.get('status') == 'on_mission' else "red"
                            text = "Sẵn sàng" if v.get('status') == 'available' else "Đang làm nhiệm vụ" if v.get('status') == 'on_mission' else "Bảo trì"
                            with ui.row().classes("w-full items-center justify-between gap-3 rounded-xl bg-slate-50 px-3 py-2"):
                                ui.label(_vehicle_label(v)).classes("text-sm font-bold text-slate-700")
                                status_badge(text, tone)

                staff_panel.clear()
                with staff_panel:
                    with ui.row().classes("w-full items-center justify-between gap-3"):
                        section_heading("Trạng thái nhân sự", "Tỷ lệ nhân viên sẵn sàng")
                        pct = round((s_avail / len(staff)) * 100) if staff else 0
                        donut(pct, f"{pct}%", "#2563eb")
                    with ui.column().classes("w-full gap-2 mt-4"):
                        for s in staff[:5]:
                            tone = "emerald" if s.get('status') == 'AVAILABLE' else "amber"
                            text = "Sẵn sàng" if s.get('status') == 'AVAILABLE' else "Đang làm nhiệm vụ"
                            with ui.row().classes("w-full items-center justify-between gap-3 rounded-xl bg-slate-50 px-3 py-2"):
                                ui.label(f"Nhân viên #{s.get('id')}").classes("text-sm font-bold text-slate-700")
                                status_badge(text, tone)
            except Exception as e:
                ui.notify(f"Lỗi tải dashboard: {e}", type="negative")

        timer = ui.timer(15, refresh_dashboard)
        ui.context.client.on_disconnect(timer.deactivate)
        await refresh_dashboard()
