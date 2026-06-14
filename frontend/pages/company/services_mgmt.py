"""
Trang quản lý dịch vụ cứu hộ của công ty.
"""
from nicegui import ui
from core.auth import require_role
from components.page_layout import page_layout
from components.company_ui import donut, inject_company_styles, kpi_card, page_header, section_heading
from services import rescue_api
import asyncio


def create_services_management_page():

    @ui.page('/company/services')
    async def company_services_page():
        if not require_role("company_staff"):
            return

        inject_company_styles()

        with page_layout("/company/services", "services"):
            with ui.column().classes("company-page gap-5"):
                page_header(
                    "Quản lý dịch vụ cứu hộ",
                    "Thiết lập danh mục dịch vụ, giá cơ bản và trạng thái cung cấp.",
                    "handyman",
                    "Thêm dịch vụ",
                    "add",
                    lambda: open_form(),
                )

                stats_row = ui.row().classes("w-full gap-4 flex-wrap")
                with ui.row().classes("w-full gap-5 items-start"):
                    with ui.element("div").classes("company-card p-5 flex-1 min-w-[320px]"):
                        section_heading("Tỷ lệ dịch vụ", "Hoạt động và tạm dừng")
                        service_donut = ui.row().classes("w-full items-center justify-center py-5")
                    with ui.element("div").classes("company-card p-5 flex-[1.4] min-w-[420px]"):
                        section_heading("Số lượt theo dịch vụ", "Hiển thị khi có dữ liệu sử dụng")
                        service_bars = ui.row().classes("w-full items-end gap-3 h-32 mt-5")

            # State
            services = []
            table = None

            async def load_services():
                nonlocal services
                services = await rescue_api.get_company_services()
                active = sum(1 for s in services if s.get("is_active"))
                paused = len(services) - active
                stats_row.clear()
                service_donut.clear()
                service_bars.clear()
                with stats_row:
                    kpi_card("Tổng dịch vụ", len(services), "Dịch vụ đã cấu hình", "format_list_bulleted", "#2563eb")
                    kpi_card("Đang hoạt động", active, "Có thể nhận yêu cầu", "check_circle", "#10b981")
                    kpi_card("Tạm dừng", paused, "Không hiển thị với khách", "pause_circle", "#f59e0b")
                pct = round(active / len(services) * 100) if services else 0
                with service_donut:
                    donut(pct, f"{pct}%", "#10b981")
                max_use = max([int(s.get("usage_count") or s.get("request_count") or 0) for s in services] + [1])
                with service_bars:
                    for s in services[:8]:
                        value = int(s.get("usage_count") or s.get("request_count") or 0)
                        height = max(10, round((value / max_use) * 92))
                        with ui.column().classes("flex-1 h-full justify-end items-center gap-2"):
                            ui.label(str(value)).classes("text-xs font-bold text-slate-500")
                            ui.element("div").classes("w-full rounded-t-xl bg-blue-500/80").style(f"height:{height}px;")
                            ui.label((s.get("service_name") or "DV")[:12]).classes("text-[10px] font-bold text-slate-400 truncate max-w-[80px]")
                if table:
                    table.rows = services
                    table.update()

            def open_form(service=None):
                is_edit = bool(service)
                with ui.dialog() as dlg, ui.card().classes('w-full max-w-md p-6 rounded-2xl'):
                    ui.label("Chỉnh Sửa Dịch Vụ" if is_edit else "Thêm Dịch Vụ Mới").classes('text-xl font-bold mb-4')
                    
                    name_input = ui.input("Tên dịch vụ (*)", value=service['service_name'] if is_edit else "").props("outlined").classes("w-full mb-2")
                    price_input = ui.number("Giá cơ bản (VNĐ) (*)", value=float(service['base_price']) if is_edit else 0.0, min=0).props("outlined").classes("w-full mb-2")
                    duration_input = ui.number("Thời gian ước tính (phút)", value=int(service.get('estimated_duration', 30)) if is_edit else 30, min=0).props("outlined").classes("w-full mb-2")
                    desc_input = ui.textarea("Mô tả", value=service.get('description', '') if is_edit else "").props("outlined").classes("w-full mb-4")

                    async def save():
                        name = name_input.value
                        try:
                            price = float(price_input.value or 0)
                            duration = int(duration_input.value or 0)
                        except (TypeError, ValueError):
                            ui.notify("Giá và thời gian phải là số hợp lệ", type="negative")
                            return
                        desc = desc_input.value or ""

                        if not name.strip():
                            ui.notify("Tên dịch vụ không được để trống", type="negative")
                            return
                        if price < 0:
                            ui.notify("Giá cơ bản phải lớn hơn hoặc bằng 0", type="negative")
                            return

                        if is_edit:
                            success = await rescue_api.update_company_service(
                                service['service_id'], name, price, duration, desc
                            )
                            if success:
                                ui.notify("Cập nhật thành công", type="positive")
                                dlg.close()
                                await load_services()
                            else:
                                ui.notify("Lỗi khi cập nhật", type="negative")
                        else:
                            res = await rescue_api.add_company_service(
                                name, price, duration, desc
                            )
                            if res.get("service_id"):
                                ui.notify("Thêm mới thành công", type="positive")
                                dlg.close()
                                await load_services()
                            else:
                                ui.notify("Lỗi khi thêm mới", type="negative")

                    with ui.row().classes('w-full justify-end gap-2 mt-4'):
                        ui.button("Hủy", on_click=dlg.close).props("flat").classes("text-gray-500")
                        ui.button("Lưu", on_click=save).props("unelevated").classes("bg-primary text-white")
                
                dlg.open()

            async def toggle_status(row):
                service_id = row['service_id']
                current_status = row['is_active']
                success = await rescue_api.toggle_company_service_status(service_id, not current_status)
                if success:
                    ui.notify("Đã cập nhật trạng thái", type="positive")
                    await load_services()
                else:
                    ui.notify("Lỗi khi cập nhật trạng thái", type="negative")

            def confirm_delete(row):
                service_id = row['service_id']
                with ui.dialog() as dlg, ui.card().classes('p-6 rounded-2xl w-80 text-center'):
                    ui.icon('warning', size='3rem').classes('text-red-500 mx-auto mb-2')
                    ui.label('Xóa Dịch Vụ?').classes('text-xl font-bold mb-2')
                    ui.label('Bạn có chắc chắn muốn xóa dịch vụ này? Nếu dịch vụ đã từng được sử dụng, nó sẽ bị vô hiệu hóa thay vì xóa hoàn toàn để bảo vệ dữ liệu.').classes('text-sm text-gray-600 mb-6')
                    
                    async def do_delete():
                        success = await rescue_api.delete_company_service(service_id)
                        if success:
                            ui.notify("Đã xóa dịch vụ", type="positive")
                            dlg.close()
                            await load_services()
                        else:
                            ui.notify("Lỗi khi xóa", type="negative")
                            
                    with ui.row().classes('w-full gap-2'):
                        ui.button('Hủy', on_click=dlg.close).props('outline').classes('flex-1')
                        ui.button('Xóa', on_click=do_delete).props('unelevated color=negative').classes('flex-1')
                dlg.open()

            with ui.element("div").classes("company-card p-5"):
                with ui.row().classes("w-full items-center justify-between mb-4"):
                    section_heading("Danh sách dịch vụ", "Quản lý giá, thời gian và trạng thái cung cấp")
                    ui.button("Thêm dịch vụ", icon="add", on_click=lambda: open_form()).classes("company-primary-btn px-5").props("unelevated no-caps")

                columns = [
                    {'name': 'service_name', 'label': 'Tên dịch vụ', 'field': 'service_name', 'align': 'left'},
                    {'name': 'base_price', 'label': 'Giá cơ bản', 'field': 'base_price', 'align': 'right'},
                    {'name': 'estimated_duration', 'label': 'Thời gian', 'field': 'estimated_duration', 'align': 'center'},
                    {'name': 'description', 'label': 'Mô tả', 'field': 'description', 'align': 'left'},
                    {'name': 'is_active', 'label': 'Trạng thái', 'field': 'is_active', 'align': 'center'},
                    {'name': 'actions', 'label': 'Thao tác', 'field': 'actions', 'align': 'center'},
                ]

                table = ui.table(columns=columns, rows=[], row_key='service_id').classes('company-table w-full')
            
            table.add_slot('body-cell-base_price', '''
                <q-td :props="props">
                    {{ props.row.base_price.toLocaleString('vi-VN') }} ₫
                </q-td>
            ''')
            
            table.add_slot('body-cell-is_active', '''
                <q-td :props="props">
                    <q-chip :color="props.row.is_active ? 'positive' : 'negative'" text-color="white" size="sm" class="font-bold">
                        {{ props.row.is_active ? 'Hoạt Động' : 'Tạm Ngưng' }}
                    </q-chip>
                </q-td>
            ''')
            
            table.add_slot('body-cell-actions', '''
                <q-td :props="props">
                    <div class="row gap-2 justify-center">
                        <q-btn flat dense icon="edit" color="primary" @click="() => $parent.$emit('edit', props.row)">
                            <q-tooltip>Sửa</q-tooltip>
                        </q-btn>
                        <q-btn flat dense icon="power_settings_new" :color="props.row.is_active ? 'negative' : 'positive'" @click="() => $parent.$emit('toggle', props.row)">
                            <q-tooltip>Bật/Tắt</q-tooltip>
                        </q-btn>
                        <q-btn flat dense icon="delete" color="negative" @click="() => $parent.$emit('delete', props.row)">
                            <q-tooltip>Xóa</q-tooltip>
                        </q-btn>
                    </div>
                </q-td>
            ''')

            table.on('edit', lambda e: open_form(e.args))
            table.on('toggle', lambda e: toggle_status(e.args))
            table.on('delete', lambda e: confirm_delete(e.args))

            # Initial load
            ui.timer(0, load_services, once=True)
