"""
Trang quản lý dịch vụ cứu hộ của công ty.
"""
from nicegui import ui
from core.auth import require_role
from components.page_layout import page_layout
from services import rescue_api
import asyncio


def create_services_management_page():

    @ui.page('/company/services')
    async def company_services_page():
        if not require_role("company_staff"):
            return

        with page_layout("/company/services", title="Quản Lý Dịch Vụ Cứu Hộ"):
            # State
            services = []
            table = None

            async def load_services():
                nonlocal services
                services = await rescue_api.get_company_services()
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

            # Header & Add Button
            with ui.row().classes("w-full justify-between items-center mb-6 mt-2"):
                ui.label("Danh sách các dịch vụ bạn cung cấp").classes("text-lg font-medium text-gray-600")
                ui.button("Thêm Dịch Vụ", icon="add", on_click=lambda: open_form()).props("unelevated").classes("bg-primary text-white rounded-xl shadow")

            # Table Definition
            columns = [
                {'name': 'service_name', 'label': 'Tên Dịch Vụ', 'field': 'service_name', 'align': 'left'},
                {'name': 'base_price', 'label': 'Giá Cơ Bản (VNĐ)', 'field': 'base_price', 'align': 'right'},
                {'name': 'estimated_duration', 'label': 'T/G (phút)', 'field': 'estimated_duration', 'align': 'center'},
                {'name': 'description', 'label': 'Mô Tả', 'field': 'description', 'align': 'left'},
                {'name': 'is_active', 'label': 'Trạng Thái', 'field': 'is_active', 'align': 'center'},
                {'name': 'actions', 'label': 'Thao Tác', 'field': 'actions', 'align': 'center'},
            ]

            table = ui.table(columns=columns, rows=[], row_key='service_id').classes('w-full shadow rounded-2xl border border-gray-100')
            
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
