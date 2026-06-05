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
    get_customer_vehicles
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
            'companies': []
        }

        with page_layout("/customer/find-rescue", title="Yêu Cầu Cứu Hộ"):
            
            with ui.stepper().classes(
                'w-full rounded-3xl bg-white/70 p-4 shadow-sm border border-gray-100'
            ).props('flat animated') as stepper:
                # ── STEP 1: CHỌN XE ───────────────────────────────────────────
                with ui.step('Chọn Xe'):
                    with ui.column().classes('w-full gap-6'):
                        # Header
                        ui.label('Chọn phương tiện đang gặp sự cố').classes('text-2xl font-bold text-primary')
                        ui.label('Bạn có thể chọn xe từ danh sách phương tiện của mình').classes('text-sm text-gray-600 mb-2')
                        
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
                                                ui.label(f"🔧 {v.get('vehicle_type', 'N/A')}")
                                                ui.label(f"📅 {v.get('year', 'N/A')}")

                        def select_vehicle(v):
                            state['selected_vehicle'] = v
                            ui.notify(f"✓ Đã chọn xe: {v['license_plate']}", type='positive')
                            stepper.next()

                        ui.timer(0.1, load_vehicles, once=True)
                        
                    with ui.stepper_navigation():
                        ui.button('Tiếp theo', on_click=stepper.next).classes(
                            'bg-primary text-white px-8 py-3 rounded-lg font-bold hover:shadow-lg transition-all'
                        )

                # ── STEP 2: VỊ TRÍ & DỊCH VỤ ──────────────────────────────────
                with ui.step('Vị trí & Sự cố'):
                    services = await get_services()
                    service_mapping = {s['id']: s['service_name'] for s in services}

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
                                                m.id,
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
                                            ui.label(
                                                selected_vehicle.get('license_plate', 'Chưa chọn xe')
                                            ).classes('text-sm font-bold text-slate-800')
                                            if selected_vehicle:
                                                ui.label(
                                                    f"{selected_vehicle.get('brand', '')} {selected_vehicle.get('model', '')}".strip()
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
                    with ui.column().classes('w-full gap-6'):
                        # Header
                        ui.label('Danh sách các đơn vị cứu hộ gần bạn').classes('text-2xl font-bold text-primary')
                        ui.label('Chọn đơn vị phù hợp nhất dựa trên khoảng cách, thời gian, và giá cước').classes('text-sm text-gray-600 mb-2')
                        
                        # Companies Container
                        companies_container = ui.column().classes('w-full gap-4')
                    
                    with ui.stepper_navigation():
                        ui.button('Tìm lại', on_click=stepper.previous).classes(
                            'px-8 py-3 rounded-lg font-bold border border-primary text-primary'
                        )

                # ── STEP 4: XÁC NHẬN ──────────────────────────────────────────
                with ui.step('Xác Nhận'):
                    with ui.column().classes('w-full gap-6'):
                        # Header
                        ui.label('Xác nhận yêu cầu cứu hộ').classes('text-2xl font-bold text-primary')
                        ui.label('Kiểm tra thông tin trước khi gửi yêu cầu').classes('text-sm text-gray-600 mb-2')
                        
                        # Summary Container
                        summary_container = ui.column().classes('w-full gap-4 p-6 bg-gradient-to-br from-blue-50 to-blue-100 rounded-2xl border-2 border-blue-200')
                    
                    with ui.stepper_navigation():
                        ui.button('GỬI YÊU CẦU', on_click=lambda: _do_submit()).classes(
                            'bg-green-600 text-white font-bold px-10 py-4 rounded-lg shadow-lg hover:bg-green-700 transition-all'
                        )
                        ui.button('Quay lại', on_click=stepper.previous).classes(
                            'px-8 py-3 rounded-lg font-bold border border-gray-300 text-gray-700'
                        )

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

        async def _sync_user_marker(map_id, lat, lng):
            await ui.run_javascript(f"""
                (function() {{
                    var el = getElement({map_id});
                    if (!el) return;
                    var map = el._leaflet_map ?? el.leaflet ?? el._map;
                    if (!map) return;

                    var latlng = [{lat}, {lng}];
                    var markerKey = '__rescueUserMarker_{map_id}';
                    var blueIcon = L.icon({{
                        iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
                        shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
                        iconSize: [25, 41],
                        iconAnchor: [12, 41],
                        popupAnchor: [1, -34],
                        shadowSize: [41, 41]
                    }});

                    if (window[markerKey]) {{
                        window[markerKey].setLatLng(latlng);
                    }} else {{
                        window[markerKey] = L.marker(latlng, {{ icon: blueIcon }}).addTo(map);
                    }}

                    window[markerKey]
                        .setIcon(blueIcon)
                        .bindPopup('<div style="font-weight:600;color:#2563eb;">Vị trí hiện tại của bạn</div>')
                        .openPopup();

                    map.invalidateSize();
                    map.flyTo(latlng, 16, {{ animate: true, duration: 0.8 }});
                    setTimeout(function() {{ map.invalidateSize(); }}, 250);
                }})();
            """, timeout=5.0)

        async def _get_gps(address_label, gps_status_label, gps_status_icon, gps_button, map_id, summary_address):
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

                    await _sync_user_marker(map_id, pos['lat'], pos['lng'])

                    address = await get_location_text(pos['lat'], pos['lng'])
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
        # Tìm kiếm công ty 
        async def _search_companies(stepper, svc_id, issue, lat, lng):
            if not svc_id or not issue:
                ui.notify("Vui lòng điền đủ thông tin", type='warning')
                return
            if not state.get('address'):
                ui.notify("Vui lòng lấy vị trí GPS trước khi tìm cứu hộ", type='warning')
                return
            
            # Get service name from mapping
            svc_name = service_mapping.get(svc_id, 'Không xác định')
            state.update({'service_id': svc_id, 'service_name': svc_name, 'issue_detail': issue, 'lat': lat, 'lng': lng})
            
            service_ids = [svc_id]  # Convert to list for API
            companies_container.clear()
            with companies_container:
                loading = ui.spinner(size='lg').classes('self-center')
                loading.delete()
            res= None
            try:
                res = await find_nearby_companies(lat, lng, service_ids)
            except Exception as e:
                companies_container.clear()
                ui.notify(f"Lỗi API: {e}", type='negative')
                return
            if not res:
                    with companies_container:
                        with ui.card().classes('w-full p-8 rounded-2xl bg-yellow-50 border-2 border-yellow-200'):
                            with ui.column().classes('items-center gap-4'):
                                ui.icon('info', size='lg').classes('text-yellow-600')
                                ui.label('Không tìm thấy đơn vị nào phù hợp').classes('font-bold text-gray-700')
                                ui.label('Vui lòng thử thay đổi vị trí hoặc loại sự cố').classes('text-sm text-gray-600')
                        return
            stepper.next()
            with companies_container:
                for c in res:
                    with ui.card().classes(
                        'w-full p-6 rounded-2xl border-2 border-gray-200 hover:border-primary hover:shadow-lg '
                        'cursor-pointer transition-all bg-white'
                    ).on('click', lambda c=c: _select_company(stepper, c)):
                        with ui.row().classes('w-full justify-between items-start mb-4'):
                            with ui.column().classes('gap-2'):
                                ui.label(c['company_name']).classes('font-bold text-lg text-primary')
                                with ui.row().classes('gap-2 text-sm text-gray-600'):
                                    ui.icon('location_on', size='sm').classes('text-red-500')
                                    ui.label(f"{c['distance_km']} km")
                                    ui.label('•')
                                    ui.icon('schedule', size='sm').classes('text-blue-500')
                                    ui.label(f"{c['eta_minutes']} phút")
                            with ui.column().classes('items-end gap-1'):
                                with ui.row().classes('items-center gap-1'):
                                    ui.icon('star', size='md').classes('text-yellow-500')
                                    ui.label(f"{c['rating_avg']:.1f}").classes('font-bold')
                        with ui.row().classes('w-full justify-between items-center pt-4 border-t border-gray-200'):
                            ui.label('Giá dự kiến').classes('text-sm text-gray-600')
                            ui.label(f"{c['estimated_price']:,.0f} đ").classes('font-bold text-lg text-green-600')

        def _select_company(stepper, c):
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
                
                # Vehicle Info
                with ui.card().classes('w-full p-4 rounded-xl bg-white border border-gray-200'):
                    with ui.row().classes('w-full items-center gap-4'):
                        ui.icon('directions_car', size='lg').classes('text-primary')
                        with ui.column().classes('gap-1'):
                            ui.label('Phương tiện').classes('text-sm text-gray-600 font-bold')
                            ui.label(f"{state['selected_vehicle']['license_plate']} - {state['selected_vehicle']['brand']} {state['selected_vehicle']['model']}").classes('font-bold')
                
                # Service & Issue Info
                with ui.card().classes('w-full p-4 rounded-xl bg-white border border-gray-200'):
                    with ui.row().classes('w-full items-start gap-4'):
                        ui.icon('build', size='lg').classes('text-warning')
                        with ui.column().classes('gap-1 flex-1'):
                            ui.label('Loại sự cố').classes('text-sm text-gray-600 font-bold')
                            ui.label(state['service_name']).classes('font-bold')
                            ui.label(f"Mô tả: {state['issue_detail']}").classes('text-sm text-gray-700 mt-2')
                
                # Company & Price Info
                with ui.card().classes('w-full p-4 rounded-xl bg-white border border-gray-200'):
                    with ui.row().classes('w-full items-center gap-4'):
                        ui.icon('business', size='lg').classes('text-info')
                        with ui.column().classes('gap-1 flex-1'):
                            ui.label('Đơn vị cứu hộ').classes('text-sm text-gray-600 font-bold')
                            ui.label(state['selected_company']['company_name']).classes('font-bold')
                        # with ui.column().classes('items-end gap-1'):
                        #     ui.label('Phí dự kiến').classes('text-sm text-gray-600 font-bold')
                        #     ui.label(f"{state['selected_company']['estimated_price']:,.0f} đ").classes('font-bold text-lg text-green-600')
                
                # Total Price Summary
                with ui.card().classes('w-full p-6 rounded-xl bg-gradient-to-r from-green-50 to-green-100 border-2 border-green-300'):
                    with ui.row().classes('w-full items-center justify-between'):
                        with ui.column().classes('gap-1'):
                            ui.label('Tổng phí dự kiến').classes('text-sm text-gray-600 font-bold')
                            ui.label('Bao gồm phí cứu hộ').classes('text-xs text-gray-500')
                        ui.label(f"{state['selected_company']['estimated_price']:,.0f} đ").classes(
                            'font-bold text-4xl text-green-600'
                        )

        async def _do_submit():
            # Find service_id
            company = state['selected_company']
            service_id = state['service_id']  # Get the actual service ID
            matched_svc = next(
                (s for s in company['services'] if s['id'] == service_id),
                    None
                )
            incident_type = matched_svc['service_name']
            if not matched_svc:
                ui.notify("Không tìm thấy dịch vụ", type='negative')
                return
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
