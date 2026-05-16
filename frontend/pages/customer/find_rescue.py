"""
Find Rescue Page - NiceGUI (Multi-step Stepper)
"""
from nicegui import ui
from typing import Dict, Any, List, Optional
from core.auth import require_role
from components.page_layout import page_layout
from services.rescue_api import (
    get_services,
    find_nearby_companies,
    create_rescue_request,
    get_customer_vehicles
)

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
            'service_name': None,
            'lat': 21.0285,
            'lng': 105.8542,
            'address': "",
            'issue_detail': "",
            'selected_company': None,
            'companies': []
        }

        with page_layout("/customer/find-rescue", title="Yêu Cầu Cứu Hộ"):
            
            with ui.stepper().classes('w-full shadow-none bg-transparent') as stepper:
                # ── STEP 1: CHỌN XE ───────────────────────────────────────────
                with ui.step('Chọn Xe'):
                    ui.label('Chọn phương tiện đang gặp sự cố:').classes('text-lg font-bold mb-4')
                    vehicles_grid = ui.row().classes('w-full gap-4')
                    
                    async def load_vehicles():
                        vehicles_grid.clear()
                        vehicles = await get_customer_vehicles()
                        with vehicles_grid:
                            if not vehicles:
                                ui.label('Bạn chưa có xe nào.').classes('italic text-error')
                                ui.button('THÊM XE', on_click=lambda: ui.navigate.to('/customer/vehicles')).props('flat')
                            else:
                                for v in vehicles:
                                    with ui.card().classes('w-64 cursor-pointer hover:border-primary transition-all') \
                                        .on('click', lambda v=v: select_vehicle(v)):
                                        ui.label(v['license_plate']).classes('font-bold text-lg')
                                        ui.label(f"{v['brand']} {v['model']}")
                                        if state['selected_vehicle'] and state['selected_vehicle']['id'] == v['id']:
                                            ui.icon('check_circle', color='primary').classes('absolute top-2 right-2')

                    def select_vehicle(v):
                        state['selected_vehicle'] = v
                        ui.notify(f"Đã chọn xe: {v['license_plate']}")
                        stepper.next()

                    ui.timer(0.1, load_vehicles, once=True)
                    with ui.stepper_navigation():
                        ui.button('Tiếp theo', on_click=stepper.next).props('unelevated rounded')

                # ── STEP 2: VỊ TRÍ & DỊCH VỤ ──────────────────────────────────
                with ui.step('Vị trí & Sự cố'):
                    with ui.row().classes('w-full gap-8'):
                        with ui.column().classes('flex-1 gap-4'):
                            # Service Select
                            services = await get_services()
                            svc_select = ui.select(options={s: s for s in services}, label='Loại sự cố *').classes('w-full').props('outlined')
                            
                            # Issue description
                            issue_input = ui.textarea('Mô tả tình trạng *').classes('w-full').props('outlined')
                            
                            # Location manual input
                            with ui.row().classes('w-full gap-2'):
                                lat_input = ui.number('Vĩ độ', value=state['lat'], format='%.6f').classes('flex-1').props('outlined dense')
                                lng_input = ui.number('Kinh độ', value=state['lng'], format='%.6f').classes('flex-1').props('outlined dense')
                            
                            ui.button('Lấy vị trí GPS', icon='my_location', on_click=lambda: _get_gps(lat_input, lng_input)) \
                                .classes('w-full').props('outline rounded')

                        with ui.card().classes('flex-1 h-[300px] p-0 overflow-hidden rounded-2xl'):
                            m = ui.leaflet(center=(state['lat'], state['lng']), zoom=13).classes('w-full h-full')
                            m.tile_layer(url_template='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png')
                            marker = m.marker(latlng=(state['lat'], state['lng']))

                    def _update_map():
                        marker.set_latlng((lat_input.value, lng_input.value))
                        m.set_center((lat_input.value, lng_input.value))

                    lat_input.on('update:model-value', _update_map)
                    lng_input.on('update:model-value', _update_map)

                    with ui.stepper_navigation():
                        ui.button('Tìm cứu hộ', on_click=lambda: _search_companies(stepper, svc_select.value, issue_input.value, lat_input.value, lng_input.value)) \
                            .classes('bg-primary text-white px-8 rounded-xl')
                        ui.button('Quay lại', on_click=stepper.previous).props('flat')

                # ── STEP 3: CHỌN ĐƠN VỊ ────────────────────────────────────────
                with ui.step('Chọn Đơn Vị'):
                    ui.label('Danh sách các đơn vị cứu hộ gần bạn:').classes('text-lg font-bold mb-4')
                    companies_container = ui.column().classes('w-full gap-4')
                    
                    with ui.stepper_navigation():
                        ui.button('Quay lại', on_click=stepper.previous).props('flat')

                # ── STEP 4: XÁC NHẬN ──────────────────────────────────────────
                with ui.step('Xác Nhận'):
                    summary_container = ui.column().classes('w-full gap-4 p-6 bg-surface-variant/20 rounded-3xl')
                    
                    with ui.stepper_navigation():
                        submit_btn = ui.button('GỬI YÊU CẦU', on_click=lambda: _do_submit()) \
                            .classes('bg-primary text-white font-bold px-10 py-4 rounded-xl shadow-lg')
                        ui.button('Quay lại', on_click=stepper.previous).props('flat')

        # --- Helper Logic ---
        async def _get_gps(lat_f, lng_f):
            pos = await ui.run_javascript('navigator.geolocation.getCurrentPosition(p => { return {lat: p.coords.latitude, lng: p.coords.longitude} })', timeout=5)
            if pos:
                lat_f.set_value(pos['lat'])
                lng_f.set_value(pos['lng'])

        async def _search_companies(stepper, svc, issue, lat, lng):
            if not svc or not issue:
                ui.notify("Vui lòng điền đủ thông tin", type='warning')
                return
            
            state.update({'service_name': svc, 'issue_detail': issue, 'lat': lat, 'lng': lng})
            stepper.next()
            
            companies_container.clear()
            with companies_container:
                loading = ui.spinner(size='lg').classes('self-center')
                res = await find_nearby_companies(lat, lng, svc)
                loading.delete()
                
                if not res:
                    ui.label('Không tìm thấy đơn vị nào phù hợp.').classes('text-error')
                else:
                    for c in res:
                        with ui.card().classes('w-full p-4 border border-surface-variant/50 hover:bg-primary-container/10 cursor-pointer') \
                            .on('click', lambda c=c: _select_company(stepper, c)):
                            with ui.row().classes('w-full justify-between'):
                                ui.label(c['company_name']).classes('font-bold text-lg')
                                ui.label(f"⭐ {c['rating_avg']}")
                            with ui.row().classes('w-full gap-4 text-sm'):
                                ui.label(f"📍 {c['distance_km']} km")
                                ui.label(f"⏱️ {c['eta_minutes']} phút")
                                ui.label(f"💰 {c['estimated_price']:,.0f} đ").classes('text-green-600 font-bold')

        def _select_company(stepper, c):
            state['selected_company'] = c
            _render_summary()
            stepper.next()

        def _render_summary():
            summary_container.clear()
            with summary_container:
                ui.label("Tóm tắt yêu cầu").classes("text-xl font-bold text-primary mb-2")
                ui.label(f"🚗 Xe: {state['selected_vehicle']['license_plate']} ({state['selected_vehicle']['brand']} {state['selected_vehicle']['model']})")
                ui.label(f"🛠️ Sự cố: {state['service_name']}")
                ui.label(f"📝 Mô tả: {state['issue_detail']}")
                ui.label(f"🏢 Đơn vị: {state['selected_company']['company_name']}")
                ui.label(f"💰 Phí dự kiến: {state['selected_company']['estimated_price']:,.0f} đ").classes("font-bold text-green-600")

        async def _do_submit():
            # Find service_id
            company = state['selected_company']
            svc_name = state['service_name']
            matched_svc = next((s for s in company['services'] if s['service_name'] == svc_name), None)
            
            try:
                res = await create_rescue_request(
                    service_id=matched_svc['id'],
                    vehicle_id=state['selected_vehicle']['id'],
                    latitude=state['lat'],
                    longitude=state['lng'],
                    address_description="Vị trí GPS",
                    incident_type=state['service_name'],
                    description=state['issue_detail'],
                    company_id=company['id']
                )
                ui.notify("Đã gửi yêu cầu thành công!", type='positive')
                ui.navigate.to(f"/customer/track/{res['id']}")
            except Exception as e:
                ui.notify(f"Lỗi: {e}", type='negative')
