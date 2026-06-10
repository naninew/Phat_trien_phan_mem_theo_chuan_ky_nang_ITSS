"""
Company Dashboard - NiceGUI
"""
from nicegui import ui
from typing import Dict, Any, List
from core.auth import require_role
from components.page_layout import page_layout
from services.rescue_api import get_company_queue, get_my_vehicles, get_company_staff

def create_company_dashboard():
    """Register /company/dashboard route."""

    @ui.page('/company/dashboard')
    async def dashboard_page():
        if not require_role("company_staff"):
            return

        with page_layout("/company/dashboard", title="Bảng Điều Khiển Công Ty"):
            
            with ui.row().classes("w-full items-center justify-between mb-6 mt-2"):
                ui.label("Tổng quan hoạt động và điều phối cứu hộ").classes("text-lg font-medium text-on-surface-variant opacity-70")
                
                ui.button("ĐIỀU PHỐI NGAY", icon="bolt", on_click=lambda: ui.navigate.to("/company/queue")) \
                    .classes("bg-primary text-white px-8 py-4 rounded-2xl shadow-xl shadow-primary/30 font-bold")

            # --- KPI Cards ---
            with ui.row().classes("w-full gap-6 mb-10"):
                card_pending = _kpi_card("Đang Chờ", "0", "pending", "bg-amber-100 text-amber-700")
                card_active = _kpi_card("Đang Xử Lý", "0", "local_shipping", "bg-indigo-100 text-indigo-700")
                card_completed = _kpi_card("Hoàn Thành", "0", "task_alt", "bg-green-100 text-green-700")
                card_resources = _kpi_card("Tài Nguyên", "0/0", "group", "bg-purple-100 text-purple-700")

            with ui.row().classes("w-full gap-8 items-start"):
                # Left: Live Queue
                with ui.column().classes("flex-1 gap-6"):
                    ui.label("Dòng Yêu Cầu Mới").classes("text-xl font-bold font-outfit mb-2")
                    queue_container = ui.column().classes("w-full gap-4")

                # Right: Resource Status
                with ui.column().classes("w-96 gap-6"):
                    with ui.card().classes("w-full rounded-3xl p-6 border border-surface-variant/30 shadow-sm"):
                        ui.label("Trạng Thái Đội Xe").classes("text-lg font-bold mb-4 font-outfit")
                        vehicle_status_list = ui.column().classes("w-full gap-3")
                    
                    with ui.card().classes("w-full rounded-3xl p-6 border border-surface-variant/30 shadow-sm"):
                        ui.label("Trạng Thái Nhân Sự").classes("text-lg font-bold mb-4 font-outfit")
                        staff_status_list = ui.column().classes("w-full gap-3")

            # --- Logic ---
            async def refresh_dashboard():
                try:
                    # 1. Fetch Queue
                    q = await get_company_queue()
                    # Cập nhật status sang CHỮ HOA theo RequestStatus model
                    pending = [r for r in q if r['status'] == 'PENDING']
                    active = [r for r in q if r['status'] in ('ACCEPTED', 'ASSIGNED', 'ON_THE_WAY', 'IN_PROGRESS')]
                    completed = [r for r in q if r['status'] == 'COMPLETED']
                    
                    card_pending.content_label.set_text(str(len(pending)))
                    card_active.content_label.set_text(str(len(active)))
                    card_completed.content_label.set_text(str(len(completed)))
                    
                    # Render Queue Preview
                    queue_container.clear()
                    with queue_container:
                        if not pending:
                            ui.label("Không có yêu cầu mới.").classes("italic opacity-50 py-4")
                        for r in pending[:3]:
                            with ui.card().classes("w-full rounded-2xl p-4 border border-amber-200 bg-amber-50/30 hover:shadow-md transition-all cursor-pointer") \
                                .on('click', lambda: ui.navigate.to("/company/queue")):
                                with ui.row().classes("w-full items-center justify-between"):
                                    ui.label(r.get('service_name', 'Cứu hộ')).classes("font-bold text-lg")
                                    ui.label(r['created_at'][:16]).classes("text-xs opacity-50")
                                ui.label(r.get('address_description', 'N/A')).classes("text-xs opacity-70 truncate")

                    # 2. Fetch Resources
                    vs = await get_my_vehicles()
                    ss = await get_company_staff()
                    
                    v_avail = len([v for v in vs if v['status'] == 'available'])
                    s_avail = len([s for s in ss if s['status'] == 'AVAILABLE'])
                    card_resources.content_label.set_text(f"{s_avail}/{len(ss)} NV | {v_avail}/{len(vs)} Xe")

                    # Render Resource Status
                    vehicle_status_list.clear()
                    with vehicle_status_list:
                        for v in vs[:5]:
                            with ui.row().classes("w-full justify-between items-center"):
                                ui.label(v.get('license_plate') or v.get('plate_number', 'N/A')).classes("text-sm font-medium")
                                dot_color = "bg-green-500" if v['status'] == 'available' else "bg-amber-500"
                                ui.element('div').classes(f"w-2 h-2 rounded-full {dot_color}")

                    staff_status_list.clear()
                    with staff_status_list:
                        for s in ss[:5]:
                            with ui.row().classes("w-full justify-between items-center"):
                                ui.label(f"Nhân viên #{s['id']}").classes("text-sm font-medium")
                                dot_color = "bg-green-500" if s['status'] == 'AVAILABLE' else "bg-amber-500"
                                ui.element('div').classes(f"w-2 h-2 rounded-full {dot_color}")
                except Exception as e:
                    print(f"Dashboard refresh error: {e}")

            timer = ui.timer(15, refresh_dashboard)
            ui.context.client.on_disconnect(timer.deactivate)
            await refresh_dashboard()

    def _kpi_card(title, value, icon, style):
        with ui.card().classes(f"flex-1 rounded-3xl p-6 border border-surface-variant/30 shadow-sm") as card:
            with ui.row().classes("w-full items-center gap-4"):
                with ui.element('div').classes(f"p-4 rounded-2xl {style}"):
                    ui.icon(icon, size="2rem")
                with ui.column().classes("gap-0"):
                    ui.label(title).classes("text-xs opacity-50 font-bold uppercase")
                    card.content_label = ui.label(value).classes("text-2xl font-bold font-outfit")
        return card
