"""
Find Rescue Page - NiceGUI (Multi-step Stepper)
"""
import asyncio
from nicegui import ui
from typing import Dict, Any, List, Optional
from core.auth import require_role
from components.page_layout import page_layout
from services.rescue_api import (
    get_services,
    find_nearby_companies,
    create_rescue_request,
    get_customer_vehicles,
    add_customer_vehicle,
)
import httpx
# Hàm xác định vị trí thực
async def get_location_text(lat, lng):
    async with httpx.AsyncClient(headers={
        "User-Agent": "nicegui-app (learning project)"
    }) as client:

        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "lat": lat,
            "lon": lng,
            "format": "json"
        }

        res = await client.get(url, params=params)

        if res.status_code == 200:
            try:
                data = res.json()
                return data.get("display_name") or "Không xác định vị trí"
            except:
                return "Không xác định vị trí"

        return "Không xác định vị trí"
def create_find_rescue_page():
    """Register /customer/find-rescue route."""

    @ui.page('/customer/find-rescue')
    async def find_rescue_page():
        if not require_role("customer"):
            return

        # --- State ---
        state = {
            'step': 1,
            'selected_vehicle': None,
            'service_id': None,
            'service_name': None,
            'lat': 21.0285,
            'lng': 105.8542,
            'address': "",
            'issue_detail': "",
            'selected_company': None,
            'companies': [],
            'company_sort': 'recommended',
            'submitting': False,
        }

        def vehicle_fuel_label(vehicle: Dict[str, Any]) -> str:
            return vehicle.get('fuel_type') or vehicle.get('fuel') or 'Chưa cập nhật'

        with page_layout("/customer/find-rescue", title="Yêu Cầu Cứu Hộ"):
            ui.add_head_html("""
            <style>
                .rescue-stepper .q-stepper__header {
                    border-bottom: 1px solid #e2e8f0;
                    padding: 8px 10px 12px;
                    gap: 6px;
                }
                .rescue-stepper .q-stepper__line:before,
                .rescue-stepper .q-stepper__line:after {
                    height: 1px !important;
                    background: #cbd5e1 !important;
                }
                .rescue-stepper .q-stepper__tab--active .q-stepper__dot {
                    background: #2563eb !important;
                    box-shadow: 0 8px 18px rgba(37, 99, 235, 0.28);
                    transform: scale(1.08);
                }
                .rescue-stepper .q-stepper__tab--active .q-stepper__title {
                    color: #1d4ed8 !important;
                    font-weight: 800 !important;
                }
                .rescue-stepper .q-stepper__dot {
                    transition: all 0.2s ease;
                }
            </style>
            """)
            
            with ui.stepper().classes(
                'rescue-stepper w-full rounded-2xl bg-white/80 p-4 shadow-sm border border-slate-100'
            ).props('flat animated') as stepper:
                # ── STEP 1: CHỌN XE ───────────────────────────────────────────
                with ui.step('Chọn Xe'):
                    with ui.column().classes('w-full gap-6'):
                        # Header
                        ui.label('Chọn phương tiện đang gặp sự cố').classes('text-2xl font-bold text-primary')
                        with ui.row().classes('w-full items-center justify-between gap-3 flex-wrap mb-2'):
                            ui.label('Bạn có thể chọn xe của mình hoặc tạo nhanh thông tin xe đang mượn').classes('text-sm text-gray-600')
                            ui.button(
                                'TẠO XE',
                                icon='add_circle',
                                on_click=lambda: open_quick_vehicle_dialog(),
                            ).classes('bg-blue-600 text-white px-5 rounded-xl font-bold').props('unelevated no-caps')
                        
                        # Vehicles Grid
                        vehicles_grid = ui.row().classes('w-full gap-4 flex-wrap')
                        
                        async def load_vehicles():
                            vehicles_grid.clear()
                            vehicles = await get_customer_vehicles()
                            with vehicles_grid:
                                if not vehicles:
                                    with ui.card().classes('w-full p-8 rounded-2xl bg-blue-50 border-2 border-blue-200'):
                                        with ui.column().classes('items-center gap-4'):
                                            ui.icon('directions_car', size='lg').classes('text-blue-600')
                                            ui.label('Bạn chưa có xe nào').classes('font-bold text-gray-700')
                                            ui.button('THÊM XE MỚI', on_click=lambda: ui.navigate.to('/customer/vehicles')).classes(
                                                'bg-primary text-white px-6 py-2 rounded-lg font-bold'
                                            )
                                else:
                                    for v in vehicles:
                                        is_selected = state['selected_vehicle'] and state['selected_vehicle']['id'] == v['id']
                                        with ui.card().classes(
                                            f"flex-1 min-w-[280px] cursor-pointer p-6 rounded-2xl transition-all "
                                            f"{'border-2 border-primary bg-primary/5' if is_selected else 'border border-gray-200 hover:shadow-lg hover:border-primary'}"
                                        ).on('click', lambda v=v: select_vehicle(v)):
                                            with ui.row().classes('w-full justify-between items-start mb-4'):
                                                with ui.column().classes('gap-1'):
                                                    ui.label(v['license_plate']).classes('font-bold text-lg text-primary')
                                                    ui.label(f"{v['brand']} {v['model']}").classes('text-sm text-gray-600')
                                                if is_selected:
                                                    ui.icon('check_circle', color='primary').classes('text-2xl')
                                            with ui.row().classes('w-full text-xs text-gray-500 gap-4'):
                                                with ui.row().classes('items-center gap-1'):
                                                    ui.icon('local_gas_station', size='1rem').classes('text-blue-500')
                                                    ui.label(vehicle_fuel_label(v))
                                                with ui.row().classes('items-center gap-1'):
                                                    ui.icon('event', size='1rem').classes('text-slate-500')
                                                    ui.label(str(v.get('year') or 'Chưa cập nhật'))

                        def select_vehicle(v):
                            state['selected_vehicle'] = v
                            update_selected_vehicle_summary()
                            ui.notify(f"✓ Đã chọn xe: {v['license_plate']}", type='positive')
                            stepper.next()

                        def open_quick_vehicle_dialog():
                            with ui.dialog() as dialog, ui.card().classes('w-[480px] max-w-[94vw] rounded-3xl p-7 shadow-xl'):
                                with ui.row().classes('items-center gap-3 mb-3'):
                                    with ui.element('div').classes('h-12 w-12 rounded-2xl bg-blue-50 flex items-center justify-center'):
                                        ui.icon('directions_car', size='1.8rem').classes('text-blue-600')
                                    with ui.column().classes('gap-0'):
                                        ui.label('Tạo thông tin xe').classes('text-2xl font-black text-slate-900')
                                        ui.label('Dùng cho xe mượn hoặc xe chưa có trong danh sách').classes('text-sm text-slate-500')

                                plate = ui.input('Biển số *').classes('w-full').props('outlined rounded stack-label maxlength=20')
                                brand = ui.input('Hãng xe *').classes('w-full mt-3').props('outlined rounded stack-label maxlength=50')
                                model = ui.input('Dòng xe *').classes('w-full mt-3').props('outlined rounded stack-label maxlength=50')
                                year = ui.number('Năm sản xuất *', value=2024, min=1901, max=2100).classes('w-full mt-3').props('outlined rounded stack-label')
                                fuel = ui.select(
                                    ['Xăng', 'Dầu', 'Điện', 'Hybrid'],
                                    label='Loại nhiên liệu',
                                    value='Xăng',
                                ).classes('w-full mt-3').props('outlined rounded stack-label')

                                with ui.row().classes('w-full justify-end gap-3 mt-6'):
                                    ui.button('Hủy', on_click=dialog.close).props('flat no-caps').classes('font-bold')

                                    async def save_vehicle():
                                        if not all([(plate.value or '').strip(), (brand.value or '').strip(), (model.value or '').strip(), year.value]):
                                            ui.notify('Vui lòng điền đầy đủ thông tin xe', type='warning')
                                            return
                                        data = {
                                            'license_plate': plate.value.strip().upper(),
                                            'brand': brand.value.strip(),
                                            'model': model.value.strip(),
                                            'year': int(year.value),
                                            'fuel_type': fuel.value,
                                        }
                                        try:
                                            created = await add_customer_vehicle(data)
                                            if created and created.get('id'):
                                                selected = {**data, 'id': created['id']}
                                                state['selected_vehicle'] = selected
                                                dialog.close()
                                                await load_vehicles()
                                                update_selected_vehicle_summary()
                                                ui.notify(f"Đã tạo và chọn xe {data['license_plate']}", type='positive')
                                                stepper.next()
                                        except Exception as e:
                                            ui.notify(f'Lỗi tạo xe: {e}', type='negative')

                                    ui.button('Lưu và chọn xe', icon='save', on_click=save_vehicle).classes(
                                        'bg-blue-600 text-white px-6 rounded-xl font-bold'
                                    ).props('unelevated no-caps')
                            dialog.open()

                        ui.timer(0.1, load_vehicles, once=True)
                        
                    with ui.stepper_navigation():
                        ui.button('Tiếp theo', on_click=stepper.next).classes(
                            'bg-primary text-white px-8 py-3 rounded-lg font-bold hover:shadow-lg transition-all'
                        )

                # ── STEP 2: VỊ TRÍ & DỊCH VỤ ──────────────────────────────────
                with ui.step('Vị trí & Sự cố'):
                    services = await get_services()
                    service_mapping = {}
                    for s in services:
                        service_name = (s.get('service_name') or '').strip()
                        if service_name and service_name not in service_mapping:
                            service_mapping[service_name] = service_name

                    with ui.column().classes('w-full gap-5'):
                        with ui.row().classes('w-full items-start justify-between gap-4'):
                            with ui.column().classes('gap-1'):
                                ui.label('Thông tin vị trí và sự cố').classes(
                                    'text-3xl font-bold text-slate-900 font-outfit'
                                )
                                ui.label(
                                    'Cho Rescue24 biết bạn đang ở đâu và xe đang gặp vấn đề gì.'
                                ).classes('text-sm text-slate-500')

                        with ui.row().classes('w-full gap-5 items-start flex-col lg:flex-row'):
                            with ui.column().classes('w-full lg:flex-1 gap-5'):
                                with ui.card().classes(
                                    'w-full rounded-3xl border border-slate-100 bg-white p-6 shadow-sm'
                                ):
                                    with ui.row().classes('items-center gap-3 mb-5'):
                                        with ui.element('div').classes(
                                            'h-11 w-11 rounded-2xl bg-blue-50 flex items-center justify-center'
                                        ):
                                            ui.icon('medical_services', size='1.5rem').classes('text-blue-600')
                                        with ui.column().classes('gap-0'):
                                            ui.label('Chi tiết sự cố').classes(
                                                'text-xl font-bold text-slate-900 font-outfit'
                                            )
                                            ui.label('Chọn loại dịch vụ và mô tả ngắn gọn tình trạng xe.').classes(
                                                'text-sm text-slate-500'
                                            )

                                    svc_select = ui.select(
                                        options=service_mapping,
                                        label='Loại sự cố *',
                                    ).classes('w-full').props('outlined rounded stack-label')

                                    issue_input = ui.textarea(
                                        label='Mô tả tình trạng *',
                                        placeholder='Ví dụ: Xe chết máy giữa đường, cần kiểm tra ắc quy và kéo về gara gần nhất.',
                                    ).classes('w-full mt-4').props('outlined rounded rows=3 stack-label')

                                with ui.card().classes(
                                    'w-full rounded-3xl border border-slate-100 bg-white p-6 shadow-sm'
                                ):
                                    with ui.row().classes('w-full items-center justify-between gap-3 mb-4'):
                                        with ui.row().classes('items-center gap-3'):
                                            with ui.element('div').classes(
                                                'h-11 w-11 rounded-2xl bg-emerald-50 flex items-center justify-center'
                                            ):
                                                ui.icon('my_location', size='1.5rem').classes('text-emerald-600')
                                            with ui.column().classes('gap-0'):
                                                ui.label('Vị trí cứu hộ').classes(
                                                    'text-xl font-bold text-slate-900 font-outfit'
                                                )
                                                ui.label('Dùng GPS để xác định địa chỉ hiện tại của bạn.').classes(
                                                    'text-sm text-slate-500'
                                                )

                                        gps_button = ui.button(
                                            'Lấy GPS',
                                            icon='gps_fixed',
                                            on_click=lambda: _get_gps(
                                                address_label,
                                                gps_status_label,
                                                gps_status_icon,
                                                gps_button,
                                                m,
                                                summary_address,
                                            ),
                                        ).classes(
                                            'rounded-xl bg-blue-600 px-4 py-2 font-bold text-white shadow-sm '
                                            'hover:bg-blue-700'
                                        ).props('unelevated')

                                    with ui.element('div').classes(
                                        'w-full rounded-2xl border border-slate-100 bg-slate-50 p-4'
                                    ):
                                        with ui.row().classes('items-start gap-3'):
                                            gps_status_icon = ui.icon('radio_button_unchecked', size='1.25rem').classes(
                                                'text-slate-400 mt-0.5'
                                            )
                                            with ui.column().classes('flex-1 gap-1'):
                                                gps_status_label = ui.label('Chưa lấy vị trí GPS').classes(
                                                    'text-sm font-bold text-slate-700'
                                                )
                                                address_label = ui.label(
                                                    'Nhấn “Lấy GPS” để tự động xác định địa chỉ cứu hộ.'
                                                ).classes('text-sm text-slate-500 leading-relaxed')

                                    with ui.element('div').classes(
                                        'w-full h-[220px] mt-4 overflow-hidden rounded-2xl border border-slate-100'
                                    ):
                                        m = ui.leaflet(center=(state['lat'], state['lng']), zoom=13).classes(
                                            'w-full h-full'
                                        )
                                        m.tile_layer(
                                            url_template='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
                                        )

                                    ui.timer(
                                        0.5,
                                        lambda: asyncio.ensure_future(_invalidate_map_size(m.id)),
                                        once=True,
                                    )

                            with ui.card().classes(
                                'w-full lg:w-[360px] rounded-3xl border border-slate-100 bg-white p-6 shadow-sm'
                            ):
                                with ui.row().classes('items-center gap-3 mb-4'):
                                    with ui.element('div').classes(
                                        'h-10 w-10 rounded-2xl bg-amber-50 flex items-center justify-center'
                                    ):
                                        ui.icon('receipt_long', size='1.35rem').classes('text-amber-500')
                                    with ui.column().classes('gap-0'):
                                        ui.label('Tóm tắt yêu cầu').classes(
                                            'text-lg font-bold text-slate-900 font-outfit'
                                        )
                                        ui.label('Thông tin sẽ được dùng để tìm đơn vị phù hợp.').classes(
                                            'text-xs text-slate-500'
                                        )

                                ui.separator().classes('mb-3')

                                with ui.column().classes('w-full gap-3'):
                                    with ui.row().classes('w-full items-start gap-3'):
                                        ui.icon('directions_car', size='1.2rem').classes('text-blue-600 mt-0.5')
                                        with ui.column().classes('gap-0 flex-1'):
                                            ui.label('Phương tiện').classes(
                                                'text-xs font-bold uppercase text-slate-400'
                                            )
                                            selected_vehicle = state.get('selected_vehicle') or {}
                                            summary_vehicle_plate = ui.label(
                                                selected_vehicle.get('license_plate', 'Chưa chọn xe')
                                            ).classes('text-sm font-bold text-slate-800')
                                            summary_vehicle_detail = ui.label(
                                                f"{selected_vehicle.get('brand', '')} {selected_vehicle.get('model', '')}".strip()
                                                if selected_vehicle else ''
                                            ).classes('text-xs text-slate-500')

                                    with ui.row().classes('w-full items-start gap-3'):
                                        ui.icon('place', size='1.2rem').classes('text-emerald-600 mt-0.5')
                                        with ui.column().classes('gap-0 flex-1'):
                                            ui.label('Địa chỉ cứu hộ').classes(
                                                'text-xs font-bold uppercase text-slate-400'
                                            )
                                            summary_address = ui.label(
                                                state.get('address') or 'Chưa lấy GPS'
                                            ).classes('text-sm font-semibold text-slate-700 leading-snug')

                                    with ui.row().classes('w-full items-start gap-3'):
                                        ui.icon('build_circle', size='1.2rem').classes('text-amber-500 mt-0.5')
                                        with ui.column().classes('gap-0 flex-1'):
                                            ui.label('Loại sự cố').classes(
                                                'text-xs font-bold uppercase text-slate-400'
                                            )
                                            summary_service = ui.label('Chưa chọn').classes(
                                                'text-sm font-semibold text-slate-700'
                                            )

                                    with ui.row().classes('w-full items-start gap-3'):
                                        ui.icon('notes', size='1.2rem').classes('text-slate-500 mt-0.5')
                                        with ui.column().classes('gap-0 flex-1'):
                                            ui.label('Mô tả').classes(
                                                'text-xs font-bold uppercase text-slate-400'
                                            )
                                            summary_issue = ui.label('Chưa nhập mô tả').classes(
                                                'text-sm font-semibold text-slate-700 leading-snug'
                                            )

                                def update_step2_summary():
                                    summary_service.set_text(
                                        service_mapping.get(svc_select.value, 'Chưa chọn')
                                    )
                                    summary_issue.set_text(issue_input.value or 'Chưa nhập mô tả')

                                def update_selected_vehicle_summary():
                                    selected_vehicle = state.get('selected_vehicle') or {}
                                    if not selected_vehicle:
                                        summary_vehicle_plate.set_text('Chưa chọn xe')
                                        summary_vehicle_detail.set_text('')
                                        return
                                    summary_vehicle_plate.set_text(
                                        selected_vehicle.get('license_plate') or 'Chưa có biển số'
                                    )
                                    summary_vehicle_detail.set_text(
                                        f"{selected_vehicle.get('brand', '')} {selected_vehicle.get('model', '')}".strip()
                                    )

                                svc_select.on('update:model-value', lambda: update_step2_summary())
                                issue_input.on('update:model-value', lambda: update_step2_summary())

                    with ui.stepper_navigation():
                        ui.button(
                            'Tìm cứu hộ',
                            icon='search',
                            on_click=lambda: _search_companies(
                                stepper,
                                svc_select.value,
                                issue_input.value,
                                state['lat'],
                                state['lng'],
                            )
                        ).classes(
                            'bg-blue-600 text-white px-6 py-3 rounded-xl font-bold hover:bg-blue-700 '
                            'shadow-sm transition-all'
                        ).props('unelevated')
                        ui.button('Quay lại', icon='arrow_back', on_click=stepper.previous).classes(
                            'px-6 py-3 rounded-xl font-bold text-slate-600 hover:bg-slate-100'
                        ).props('flat')

                # ── STEP 3: CHỌN ĐƠN VỊ ────────────────────────────────────────
                with ui.step('Chọn Đơn Vị'):
                    with ui.column().classes('w-full gap-4'):
                        with ui.row().classes(
                            'w-full items-center justify-between gap-3 rounded-2xl border border-slate-100 '
                            'bg-white px-5 py-4 shadow-sm'
                        ):
                            with ui.column().classes('gap-1'):
                                ui.label('Chọn đơn vị cứu hộ').classes(
                                    'text-2xl font-bold text-slate-900 font-outfit'
                                )
                                results_count_label = ui.label('Chưa có đơn vị phù hợp').classes(
                                    'text-sm font-semibold text-slate-500'
                                )
                            sort_select = ui.select(
                                options={
                                    'recommended': 'Đề xuất tốt nhất',
                                    'nearest': 'Gần nhất',
                                    'price': 'Giá thấp nhất',
                                    'rating': 'Đánh giá cao nhất',
                                },
                                value='recommended',
                                label='Sắp xếp',
                            ).classes('w-full sm:w-[240px]').props('outlined dense rounded')
                        
                        # Companies Container
                        companies_container = ui.column().classes('w-full gap-3')
                    
                    with ui.stepper_navigation():
                        ui.button('Tìm lại', on_click=stepper.previous).classes(
                            'px-8 py-3 rounded-lg font-bold border border-primary text-primary'
                        )

                # ── STEP 4: XÁC NHẬN ──────────────────────────────────────────
                with ui.step('Xác Nhận'):
                    with ui.column().classes('w-full gap-4'):
                        # Header
                        with ui.row().classes('w-full items-center justify-between gap-3'):
                            with ui.column().classes('gap-1'):
                                ui.label('Xác nhận yêu cầu cứu hộ').classes(
                                    'text-2xl font-black text-slate-900 font-outfit'
                                )
                                ui.label('Kiểm tra thông tin trước khi gửi yêu cầu').classes(
                                    'text-sm font-semibold text-slate-500'
                                )
                        
                        # Summary Container
                        summary_container = ui.column().classes(
                            'w-full gap-4 rounded-2xl border border-blue-100 bg-gradient-to-br '
                            'from-blue-50 via-white to-cyan-50 p-4 sm:p-6 shadow-sm'
                        )
                    
                    with ui.stepper_navigation():
                        with ui.row().classes(
                            'w-full flex-col items-stretch justify-end gap-3 rounded-2xl border border-slate-100 '
                            'bg-white px-4 py-4 shadow-sm'
                            ' sm:flex-row sm:items-center'
                        ):
                            ui.button('Quay lại', icon='arrow_back', on_click=stepper.previous).classes(
                                'h-12 w-full min-w-[150px] rounded-2xl border border-blue-600 bg-white px-6 '
                                'text-sm font-bold text-blue-700 shadow-sm transition-all hover:bg-blue-50 '
                                'active:scale-[0.98] sm:w-auto'
                            ).props('outline unelevated no-caps')
                            submit_button = ui.button('Gửi yêu cầu', icon='send', on_click=lambda: _do_submit()).classes(
                                'h-12 w-full min-w-[180px] rounded-2xl bg-blue-700 px-6 text-sm font-black '
                                'text-white shadow-lg shadow-blue-200 transition-all hover:bg-blue-800 '
                                'active:scale-[0.98] disabled:opacity-60 disabled:shadow-none sm:w-auto'
                            ).props('unelevated no-caps')

        # --- Helper Logic ---
        async def _invalidate_map_size(map_id):
            try:
                await ui.run_javascript(f"""
                    setTimeout(function() {{
                        var el = getElement({map_id});
                        if (!el) return;
                        var map = el._leaflet_map ?? el.leaflet ?? el._map;
                        if (map) map.invalidateSize();
                    }}, 120);
                """, timeout=5.0)
            except Exception:
                pass

        async def _sync_user_marker(map_widget, lat, lng):
            await map_widget.initialized()
            if state.get('user_marker') is not None:
                try:
                    map_widget.remove_layer(state['user_marker'])
                except Exception:
                    pass

            state['user_marker'] = map_widget.generic_layer(
                name='circleMarker',
                args=[
                    {'lat': lat, 'lng': lng},
                    {
                        'radius': 10,
                        'color': '#ffffff',
                        'weight': 3,
                        'fillColor': '#2563eb',
                        'fillOpacity': 1,
                    },
                ],
            )
            map_widget.run_map_method('setView', (lat, lng), 16)
            map_widget.run_map_method('invalidateSize')

        async def _get_gps(address_label, gps_status_label, gps_status_icon, gps_button, map_widget, summary_address):
            try:
                gps_button.props("loading")
                gps_status_icon.props("name=sync")
                gps_status_icon.classes(remove="text-slate-400 text-emerald-600 text-red-500")
                gps_status_icon.classes("text-blue-600")
                gps_status_label.set_text("Đang lấy vị trí GPS...")
                address_label.set_text("Trình duyệt đang xác định vị trí hiện tại của bạn.")

                pos = await ui.run_javascript('''
                    new Promise((resolve, reject) => {
                        if (!navigator.geolocation) {
                            reject('Trình duyệt không hỗ trợ định vị GPS.');
                            return;
                        }
                        navigator.geolocation.getCurrentPosition(
                            position => {
                                resolve({
                                    lat: position.coords.latitude,
                                    lng: position.coords.longitude,
                                    accuracy: position.coords.accuracy
                                });
                            },
                            error => {
                                var messages = {
                                    1: 'Bạn chưa cấp quyền truy cập vị trí.',
                                    2: 'Không thể xác định vị trí hiện tại.',
                                    3: 'Lấy vị trí quá thời gian chờ.'
                                };
                                reject(messages[error.code] || error.message || 'Không thể lấy GPS.');
                            },
                            { timeout: 10000, enableHighAccuracy: true }
                        );
                    });
                ''', timeout=15)
                if pos:
                    state['lat'] = pos['lat']
                    state['lng'] = pos['lng']

                    try:
                        await _sync_user_marker(map_widget, pos['lat'], pos['lng'])
                    except Exception:
                        pass

                    fallback_address = f"Vĩ độ {pos['lat']:.6f}, kinh độ {pos['lng']:.6f}"
                    try:
                        address = await get_location_text(pos['lat'], pos['lng'])
                    except Exception:
                        address = fallback_address
                    if not address or address == "Không xác định vị trí":
                        address = fallback_address
                    state['address'] = address
                    gps_status_icon.props("name=check_circle")
                    gps_status_icon.classes(remove="text-blue-600 text-slate-400 text-red-500")
                    gps_status_icon.classes("text-emerald-600")
                    gps_status_label.set_text("Đã xác định vị trí")
                    address_label.set_text(address)
                    summary_address.set_text(address)
                    ui.notify("Đã lấy GPS và cập nhật bản đồ thành công", type='positive')

            except Exception as e:
                gps_status_icon.props("name=error")
                gps_status_icon.classes(remove="text-blue-600 text-slate-400 text-emerald-600")
                gps_status_icon.classes("text-red-500")
                gps_status_label.set_text("Không thể lấy vị trí")
                address_label.set_text(str(e))
                ui.notify(f"Không thể lấy GPS: {str(e)}", type='negative')
            finally:
                gps_button.props(remove="loading")

        def _format_price(value: float) -> str:
            return f"{float(value or 0):,.0f} đ"

        def _company_initials(company_name: str) -> str:
            words = [word[0] for word in (company_name or "").split() if word]
            return "".join(words[:2]).upper() or "CH"

        def _sorted_companies(companies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            sort_key = state.get('company_sort') or 'recommended'
            if sort_key == 'nearest':
                return sorted(companies, key=lambda c: float(c.get('distance_km') or 9999))
            if sort_key == 'price':
                return sorted(companies, key=lambda c: float(c.get('estimated_price') or 0))
            if sort_key == 'rating':
                return sorted(companies, key=lambda c: float(c.get('rating_avg') or 0), reverse=True)
            return sorted(
                companies,
                key=lambda c: (
                    float(c.get('estimated_price') or 0),
                    float(c.get('eta_minutes') or 9999),
                    float(c.get('distance_km') or 9999),
                    -float(c.get('rating_avg') or 0),
                ),
            )

        def _company_tags(company: Dict[str, Any], companies: List[Dict[str, Any]], index: int) -> List[Dict[str, str]]:
            if not companies:
                return []
            min_distance = min(float(c.get('distance_km') or 9999) for c in companies)
            min_eta = min(float(c.get('eta_minutes') or 9999) for c in companies)
            min_price = min(float(c.get('estimated_price') or 0) for c in companies)
            tags = []
            if index == 0:
                tags.append({'label': 'Đề xuất', 'classes': 'bg-blue-600 text-white'})
            if float(company.get('distance_km') or 9999) == min_distance:
                tags.append({'label': 'Gần nhất', 'classes': 'bg-cyan-50 text-cyan-700 border border-cyan-100'})
            if float(company.get('eta_minutes') or 9999) == min_eta:
                tags.append({'label': 'Đến nhanh', 'classes': 'bg-emerald-50 text-emerald-700 border border-emerald-100'})
            if float(company.get('estimated_price') or 0) == min_price:
                tags.append({'label': 'Giá tốt', 'classes': 'bg-amber-50 text-amber-700 border border-amber-100'})
            return tags[:4]

        def _show_company_detail(company: Dict[str, Any]):
            with ui.dialog() as dialog, ui.card().classes(
                'w-[min(92vw,640px)] rounded-2xl p-0 overflow-hidden'
            ).props('flat'):
                with ui.element('div').classes(
                    'w-full bg-gradient-to-r from-blue-700 via-blue-600 to-cyan-500 px-5 py-4 text-white'
                ):
                    with ui.row().classes('w-full items-center gap-3'):
                        with ui.element('div').classes(
                            'h-12 w-12 min-w-[48px] rounded-2xl bg-white/20 flex items-center justify-center text-lg font-black shadow-sm'
                        ):
                            ui.label(_company_initials(company.get('company_name', ''))).classes('text-white')
                        with ui.column().classes('gap-0 flex-1'):
                            ui.label(company.get('company_name', 'Đơn vị cứu hộ')).classes('text-lg font-bold')
                            ui.label(company.get('address') or 'Chưa cập nhật địa chỉ').classes('text-xs text-white/70')
                with ui.column().classes('w-full gap-4 p-5'):
                    with ui.element('div').classes('grid w-full grid-cols-3 gap-3'):
                        for icon, label, value, color in [
                            ('star', 'Đánh giá', f"{float(company.get('rating_avg') or 0):.1f}", 'text-amber-500'),
                            ('near_me', 'Khoảng cách', f"{company.get('distance_km', 0)} km", 'text-blue-600'),
                            ('payments', 'Giá dự kiến', _format_price(company.get('estimated_price')), 'text-emerald-600'),
                        ]:
                            with ui.element('div').classes('min-w-0 rounded-2xl bg-slate-50 p-3'):
                                ui.icon(icon, size='1.2rem').classes(color)
                                ui.label(label).classes('mt-1 text-xs font-bold uppercase text-slate-400')
                                ui.label(value).classes('text-sm font-bold text-slate-900')
                    with ui.column().classes('w-full gap-2'):
                        ui.label('Dịch vụ phù hợp').classes('text-xs font-bold uppercase text-slate-400')
                        for service in company.get('services', []):
                            with ui.row().classes('w-full items-center justify-between rounded-xl bg-blue-50 px-3 py-2'):
                                ui.label(service.get('service_name') or state.get('service_name')).classes('text-sm font-bold text-slate-800')
                                ui.label(_format_price(service.get('base_price'))).classes('text-sm font-bold text-blue-700')
                    with ui.row().classes('w-full justify-end gap-2 pt-2'):
                        ui.button('Đóng', on_click=dialog.close).classes(
                            'rounded-xl px-4 py-2 font-bold text-slate-600'
                        ).props('flat')
                        ui.button('Chọn đơn vị', icon='check_circle', on_click=lambda: (dialog.close(), _select_company(stepper, company))).classes(
                            'rounded-xl bg-blue-600 px-4 py-2 font-bold text-white hover:bg-blue-700'
                        ).props('unelevated')
            dialog.open()

        def _render_company_cards():
            companies_container.clear()
            companies = _sorted_companies(state.get('companies', []))
            results_count_label.set_text(f"Tìm thấy {len(companies)} đơn vị cung cấp {state.get('service_name')}")
            with companies_container:
                if not companies:
                    with ui.element('div').classes(
                        'w-full rounded-2xl border border-amber-200 bg-amber-50 p-6 text-center'
                    ):
                        ui.icon('info', size='lg').classes('text-amber-600')
                        ui.label('Không tìm thấy đơn vị nào phù hợp').classes('mt-2 font-bold text-slate-800')
                        ui.label('Vui lòng thử thay đổi vị trí hoặc loại sự cố').classes('text-sm text-slate-600')
                    return

                for index, company in enumerate(companies):
                    is_best = index == 0
                    wrapper_classes = (
                        'w-full rounded-[16px] p-[1px] transition-all duration-200 hover:-translate-y-0.5 '
                        + ('bg-gradient-to-r from-blue-500 via-cyan-400 to-emerald-400 shadow-xl shadow-blue-200/70'
                           if is_best else 'bg-slate-200 shadow-md shadow-slate-200/60 hover:shadow-lg')
                    )
                    inner_classes = (
                        'relative w-full rounded-[15px] px-4 pb-3 sm:px-5 sm:pb-4 '
                        + ('pt-12 sm:pt-4 ' if is_best else 'pt-3 sm:pt-4 ')
                        + ('bg-gradient-to-br from-blue-50 via-white to-cyan-50' if is_best else 'bg-white')
                    )
                    with ui.element('div').classes(wrapper_classes):
                        with ui.element('div').classes(inner_classes):
                            if is_best:
                                ui.label('🏆 Đề xuất tốt nhất').classes(
                                    'absolute right-4 top-3 rounded-full bg-blue-600 px-3 py-1 text-xs font-black text-white shadow-lg'
                                )
                            with ui.row().classes('w-full items-start gap-3 pr-0 sm:pr-36'):
                                with ui.element('div').classes(
                                    'h-[52px] w-[52px] min-w-[52px] rounded-2xl bg-gradient-to-br from-blue-600 to-cyan-500 flex items-center justify-center shadow-sm shadow-blue-200'
                                ):
                                    ui.label(_company_initials(company.get('company_name', ''))).classes(
                                        'text-base font-black text-white'
                                    )
                                with ui.column().classes('min-w-0 flex-1 gap-1'):
                                    ui.label(company.get('company_name', 'Đơn vị cứu hộ')).classes(
                                        'text-base sm:text-lg font-black text-slate-900 leading-tight'
                                    )
                                    with ui.row().classes('items-center gap-1'):
                                        rating = float(company.get('rating_avg') or 0)
                                        filled_stars = max(0, min(5, int(round(rating))))
                                        for star_index in range(5):
                                            ui.icon('star', size='1rem').classes(
                                                'text-amber-400' if star_index < filled_stars else 'text-slate-200'
                                            )
                                        ui.label(f"{rating:.1f}").classes('ml-1 text-sm font-bold text-slate-700')
                                        ui.label(f"({int(company.get('rating_count') or 0)})").classes('text-xs text-slate-400')
                                    with ui.row().classes('mt-1 gap-1.5 flex-wrap'):
                                        for tag in _company_tags(company, companies, index):
                                            ui.label(tag['label']).classes(
                                                f"rounded-full px-2.5 py-1 text-xs font-bold {tag['classes']}"
                                            )

                            with ui.element('div').classes('mt-3 grid w-full grid-cols-3 gap-2'):
                                for icon, label, value, color in [
                                    ('near_me', 'Khoảng cách', f"{company.get('distance_km', 0)} km", 'text-blue-600'),
                                    ('schedule', 'ETA', f"{company.get('eta_minutes', 0)} phút", 'text-violet-600'),
                                    ('payments', 'Giá dự kiến', _format_price(company.get('estimated_price')), 'text-emerald-600'),
                                ]:
                                    with ui.element('div').classes(
                                        'min-w-0 rounded-xl border border-slate-100 bg-white/85 px-2 py-2 sm:px-3 shadow-sm'
                                    ):
                                        with ui.row().classes('items-center gap-1.5'):
                                            ui.icon(icon, size='1rem').classes(color)
                                            ui.label(label).classes('text-[10px] sm:text-[11px] font-bold uppercase text-slate-400')
                                        ui.label(value).classes('mt-1 text-xs sm:text-sm font-black text-slate-900')

                            with ui.row().classes('mt-3 w-full items-center justify-between gap-2 border-t border-slate-100 pt-3'):
                                ui.label(company.get('hotline') or 'Hotline chưa cập nhật').classes(
                                    'text-xs font-semibold text-slate-500'
                                )
                                with ui.row().classes('gap-2'):
                                    ui.button('Xem chi tiết', icon='visibility', on_click=lambda company=company: _show_company_detail(company)).classes(
                                        'rounded-xl border border-slate-200 px-3 py-2 text-xs font-bold text-slate-700 hover:bg-slate-50'
                                    ).props('flat')
                                    ui.button('Chọn đơn vị', icon='check_circle', on_click=lambda company=company: _select_company(stepper, company)).classes(
                                        'rounded-xl bg-blue-600 px-3 py-2 text-xs font-bold text-white shadow-sm hover:bg-blue-700'
                                    ).props('unelevated')

        sort_select.on(
            'update:model-value',
            lambda: (state.update({'company_sort': sort_select.value}), _render_company_cards()),
        )

        # Tìm kiếm công ty 
        async def _search_companies(stepper, svc_id, issue, lat, lng):
            if not svc_id or not issue:
                ui.notify("Vui lòng điền đủ thông tin", type='warning')
                return
            if not state.get('address'):
                ui.notify("Vui lòng lấy vị trí GPS trước khi tìm cứu hộ", type='warning')
                return
            
            # Get service name from mapping
            svc_name = service_mapping.get(svc_id, svc_id or 'Không xác định')
            state.update({'service_id': None, 'service_name': svc_name, 'issue_detail': issue, 'lat': lat, 'lng': lng})
            
            companies_container.clear()
            with companies_container:
                loading = ui.spinner(size='lg').classes('self-center')
                loading.delete()
            res= None
            try:
                res = await find_nearby_companies(lat, lng, service_names=[svc_name])
            except Exception as e:
                companies_container.clear()
                ui.notify(f"Lỗi API: {e}", type='negative')
                return
            if not res:
                state['companies'] = []
                stepper.next()
                _render_company_cards()
                return
            state['companies'] = res
            state['company_sort'] = sort_select.value or 'recommended'
            stepper.next()
            _render_company_cards()

        def _select_company(stepper, c):
            matched_svc = next(
                (
                    s
                    for s in c.get('services', [])
                    if (s.get('service_name') or '').strip() == state.get('service_name')
                ),
                None,
            )
            if not matched_svc:
                ui.notify("Công ty này chưa có dịch vụ phù hợp", type='negative')
                return
            state['service_id'] = matched_svc['id']
            state['selected_company'] = c
            _render_summary()
            stepper.next()

        def _render_summary():
            summary_container.clear()
            with summary_container:
                # Validate required state
                if not state['selected_vehicle']:
                    ui.label("❌ Chưa chọn xe. Vui lòng quay lại Step 1.").classes("text-error text-sm")
                    return
                if not state['service_id']:
                    ui.label("❌ Chưa chọn dịch vụ. Vui lòng quay lại Step 2.").classes("text-error text-sm")
                    return
                if not state['selected_company']:
                    ui.label("❌ Chưa chọn công ty. Vui lòng chọn lại.").classes("text-error text-sm")
                    return
                
                def summary_card(icon: str, title: str, primary: str, secondary: str = "", color: str = "text-blue-600"):
                    with ui.element('div').classes(
                        'min-h-[132px] rounded-2xl border border-slate-100 bg-white p-4 shadow-sm '
                        'transition-shadow hover:shadow-md'
                    ):
                        with ui.row().classes('h-full w-full items-start gap-3'):
                            with ui.element('div').classes(
                                'h-11 w-11 min-w-[44px] rounded-2xl bg-blue-50 flex items-center justify-center'
                            ):
                                ui.icon(icon, size='1.35rem').classes(color)
                            with ui.column().classes('min-w-0 flex-1 gap-1'):
                                ui.label(title).classes('text-xs font-black uppercase tracking-wide text-slate-400')
                                ui.label(primary).classes('break-words text-base font-black leading-snug text-slate-900')
                                if secondary:
                                    ui.label(secondary).classes('line-clamp-2 text-sm font-medium leading-snug text-slate-500')

                selected_vehicle = state['selected_vehicle']
                selected_company = state['selected_company']
                with ui.element('div').classes('grid w-full grid-cols-1 gap-4 lg:grid-cols-3'):
                    summary_card(
                        'directions_car',
                        'Phương tiện',
                        f"{selected_vehicle['license_plate']}",
                        f"{selected_vehicle['brand']} {selected_vehicle['model']}",
                        'text-blue-600',
                    )
                    summary_card(
                        'build_circle',
                        'Loại sự cố',
                        state['service_name'],
                        state['issue_detail'],
                        'text-amber-500',
                    )
                    summary_card(
                        'business',
                        'Đơn vị cứu hộ',
                        selected_company['company_name'],
                        selected_company.get('hotline') or 'Hotline chưa cập nhật',
                        'text-cyan-600',
                    )

                with ui.element('div').classes(
                    'w-full rounded-2xl border border-emerald-200 bg-gradient-to-r from-emerald-50 '
                    'via-white to-blue-50 p-4 shadow-sm sm:p-5'
                ):
                    with ui.row().classes('w-full items-center justify-between gap-4 flex-wrap'):
                        with ui.row().classes('items-center gap-3'):
                            with ui.element('div').classes(
                                'h-12 w-12 min-w-[48px] rounded-2xl bg-emerald-100 flex items-center justify-center'
                            ):
                                ui.icon('payments', size='1.4rem').classes('text-emerald-700')
                            with ui.column().classes('gap-0'):
                                ui.label('Tổng phí dự kiến').classes('text-sm font-black uppercase text-slate-500')
                                ui.label('Bao gồm phí cứu hộ và ước tính quãng đường').classes(
                                    'text-xs font-medium text-slate-500'
                                )
                        with ui.element('div').classes('ml-auto rounded-2xl bg-white px-5 py-3 shadow-sm'):
                            ui.label(f"{selected_company['estimated_price']:,.0f} đ").classes(
                                'text-right text-2xl font-black text-emerald-700 sm:text-3xl'
                            )

        async def _do_submit():
            if state.get('submitting'):
                return
            # Find service_id
            company = state['selected_company']
            matched_svc = next(
                (
                    s
                    for s in company['services']
                    if (s.get('service_name') or '').strip() == state['service_name']
                ),
                    None
                )
            if not matched_svc:
                ui.notify("Không tìm thấy dịch vụ", type='negative')
                return
            incident_type = matched_svc['service_name']
            state['service_id'] = matched_svc['id']
            state['submitting'] = True
            submit_button.props('loading disable')
            try:
                address = await get_location_text(
                    state['lat'],
                    state['lng']
                )
                res = await create_rescue_request(
                    service_id=matched_svc['id'],
                    vehicle_id=state['selected_vehicle']['id'],
                    latitude=state['lat'],
                    longitude=state['lng'],
                    address_description=address,
                    incident_type=incident_type,
                    description=state['issue_detail'],
                    company_id=company['id'],
                    #agreed_price=company['estimated_price'],
                )
                print("CREATE RESPONSE =", res)
                if not res:
                    ui.notify("Không nhận được dữ liệu từ server", type='negative')
                    return
                request_id = res.get("id")
                if not request_id:
                    ui.notify(f"Dữ liệu không hợp lệ: {res}", type='negative')
                    return
                ui.notify("Đã gửi yêu cầu thành công!", type='positive')
                ui.navigate.to(f"/customer/track/{res['id']}")
            except Exception as e:
                print("SUBMIT ERROR =", e)
                ui.notify(f"Lỗi: {e}", type='negative')
            finally:
                state['submitting'] = False
                submit_button.props(remove='loading disable')
