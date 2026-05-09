"""
Trang tìm kiếm cứu hộ – dành cho khách hàng.
"""
from nicegui import ui, app
from typing import Optional, Dict, Any, List

from core.auth import require_role
from components.page_layout import page_layout
from services.rescue_api import get_services, find_nearby_companies, create_rescue_request
from core.config import BACKEND_URL
from components.company_detail_dialog import open_company_detail


def create_find_rescue_page():

    @ui.page('/customer/find-rescue')
    async def find_rescue_page():
        if not require_role("customer"):
            return

        # State management
        state = {
            'lat': 21.0285, 
            'lng': 105.8542,
            'service_id': None,
            'companies': [],
            'loading': False
        }

        with page_layout("/customer/find-rescue", title="Tìm Cứu Hộ"):
            
            # Header section
            with ui.column().classes("w-full mb-4"):
                ui.label("🆘 Gửi Yêu Cầu Cứu Hộ").classes("text-3xl font-bold text-gray-800")
                ui.label("Vui lòng cung cấp vị trí và sự cố để nhận hỗ trợ nhanh nhất").classes("text-gray-500")

            with ui.row().classes("w-full gap-6 items-start"):
                
                # ── Cột Trái: Thông tin yêu cầu ────────────────────────────────
                with ui.column().classes("w-[400px] gap-6"):
                    
                    # 1. Vị trí
                    with ui.card().classes("w-full rounded-2xl p-6 shadow-sm border border-gray-100"):
                        with ui.row().classes("items-center gap-2 mb-4"):
                            ui.icon("location_on", color="primary").classes("text-xl")
                            ui.label("Vị trí của bạn").classes("text-lg font-bold text-gray-700")
                        
                        with ui.row().classes("w-full gap-4"):
                            lat_input = ui.number(label="Vĩ độ", value=state['lat'], format="%.6f").classes("flex-1").props("outlined dense")
                            lng_input = ui.number(label="Kinh độ", value=state['lng'], format="%.6f").classes("flex-1").props("outlined dense")
                            
                            def _update_user_marker():
                                if lat_input.value is not None and lng_input.value is not None:
                                    search_map.set_center((lat_input.value, lng_input.value))
                                    # Update marker directly via JS or re-render map center
                                    # Since we re-render layers in _render_results, we'll just set center here
                                    # But to show the red marker live, we can clear and add
                                    search_map.clear_layers()
                                    search_map.generic_layer(name='user_marker', args=[[lat_input.value, lng_input.value], {
                                        'icon': {
                                            'iconUrl': 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
                                            'shadowUrl': 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
                                            'iconSize': [25, 41],
                                            'iconAnchor': [12, 41],
                                            'popupAnchor': [1, -34],
                                            'shadowSize': [41, 41]
                                        }
                                    }])

                            lat_input.on('update:model-value', _update_user_marker)
                            lng_input.on('update:model-value', _update_user_marker)
                        
                        ui.button("Lấy vị trí hiện tại", icon="my_location", on_click=lambda: _get_geolocation(lat_input, lng_input)).classes("w-full mt-2").props("outline dense")
                        
                        addr_desc = ui.textarea(label="Địa chỉ chi tiết / Điểm ghi nhớ", placeholder="Ví dụ: Cạnh cây xăng, số nhà 123...").classes("w-full mt-4").props("outlined")

                    # 2. Loại dịch vụ & Sự cố
                    with ui.card().classes("w-full rounded-2xl p-6 shadow-sm border border-gray-100"):
                        with ui.row().classes("items-center gap-2 mb-4"):
                            ui.icon("build", color="primary").classes("text-xl")
                            ui.label("Thông tin sự cố").classes("text-lg font-bold text-gray-700")
                        
                        # Load services from API
                        try:
                            available_services = await get_services() # returns list of strings
                            service_options = {s: s for s in available_services}
                        except:
                            service_options = {}
                            ui.notify("Không thể tải danh sách dịch vụ", type="negative")

                        svc_select = ui.select(
                            options=service_options,
                            label="Chọn loại sự cố *",
                        ).classes("w-full").props("outlined")
                        
                        issue_detail = ui.textarea(
                            label="Chi tiết tình trạng xe *",
                            placeholder="Mô tả sơ qua tình trạng (Ví dụ: Xe không đề được, nổ lốp sau...)"
                        ).classes("w-full mt-2").props("outlined")

                        payment_method = ui.select(
                            options={'cash': 'Tiền mặt', 'banking': 'Chuyển khoản', 'momo': 'Ví Momo'},
                            value='cash',
                            label="Phương thức thanh toán"
                        ).classes("w-full mt-2").props("outlined")

                    # Search Button
                    search_btn = ui.button(
                        "TÌM KIẾM ĐƠN VỊ CỨU HỘ GẦN ĐÂY", 
                        icon="search",
                        on_click=lambda: _handle_search()
                    ).classes("w-full py-4 rounded-xl bg-indigo-600 text-[#f0f4f8] font-bold text-lg shadow-lg hover:bg-indigo-700")

                # ── Cột Phải: Kết quả tìm kiếm & Bản đồ ────────────────────────
                with ui.column().classes("flex-1 gap-4"):
                    # Map section
                    with ui.card().classes("w-full h-[400px] rounded-2xl p-0 overflow-hidden shadow-sm"):
                        search_map = ui.leaflet(center=(state['lat'], state['lng']), zoom=13).classes("w-full h-full")
                        search_map.tile_layer(url_template='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png')
                        # Red marker for user
                        search_map.generic_layer(name='user_marker', args=[[state['lat'], state['lng']], {
                            'icon': {
                                'iconUrl': 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
                                'shadowUrl': 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
                                'iconSize': [25, 41],
                                'iconAnchor': [12, 41],
                                'popupAnchor': [1, -34],
                                'shadowSize': [41, 41]
                            }
                        }])

                    with ui.row().classes("w-full items-center justify-between mt-2"):
                        ui.label("Đơn vị cứu hộ").classes("text-xl font-bold text-gray-700")
                        sort_select = ui.select(
                            options={'priority': 'Ưu tiên', 'rating': 'Đánh giá', 'dist': 'Khoảng cách'},
                            value='priority',
                            on_change=lambda: _render_results()
                        ).props("outlined dense").classes("w-32")
                    
                    with ui.scroll_area().classes("w-full max-h-[800px]"):
                        results_container = ui.column().classes("w-full gap-4")
                        with results_container:
                            ui.label("Nhập thông tin bên trái để tìm kiếm...").classes("text-gray-400 italic mt-4")

        # ── Helper Functions ──────────────────────────────────────────────
        async def _get_geolocation(lat_field, lng_field):
            # Inject JS to get location
            try:
                pos = await ui.run_javascript('''
                    new Promise((resolve, reject) => {
                        navigator.geolocation.getCurrentPosition(
                            (p) => resolve({lat: p.coords.latitude, lng: p.coords.longitude}),
                            (e) => resolve(null),
                            {enableHighAccuracy: true}
                        );
                    });
                ''', timeout=15.0)
                if pos:
                    lat_field.set_value(pos['lat'])
                    lng_field.set_value(pos['lng'])
                    ui.notify("Đã cập nhật vị trí từ GPS", type="positive")
                else:
                    ui.notify("Không thể lấy vị trí từ trình duyệt", type="warning")
            except TimeoutError:
                ui.notify("Hết thời gian chờ cấp quyền vị trí. Vui lòng cho phép trình duyệt truy cập vị trí.", type="warning")

        all_found_companies = []

        def _render_results():
            results_container.clear()
            search_map.clear_layers()
            
            # Re-add user marker
            user_lat = lat_input.value
            user_lng = lng_input.value
            search_map.generic_layer(name='user_marker', args=[[user_lat, user_lng], {
                'icon': {
                    'iconUrl': 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
                    'shadowUrl': 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
                    'iconSize': [25, 41],
                    'iconAnchor': [12, 41],
                    'popupAnchor': [1, -34],
                    'shadowSize': [41, 41]
                }
            }])
            search_map.set_center((user_lat, user_lng))
            
            # Filter companies: nearby or slightly over radius (+30km margin)
            filtered_companies = [c for c in all_found_companies if c['distance_km'] <= c['service_radius_km'] + 30]
            
            if not filtered_companies:
                with results_container:
                    ui.label("Không tìm thấy đơn vị nào quanh khu vực của bạn 😢").classes("text-red-500 mt-4")
                return
            
            # Sort logic
            crit = sort_select.value
            if crit == 'rating':
                sorted_list = sorted(filtered_companies, key=lambda x: x['rating_avg'], reverse=True)
            elif crit == 'dist':
                sorted_list = sorted(filtered_companies, key=lambda x: x['distance_km'])
            else: # priority: score = rating_avg / (1 + distance_km/10)
                sorted_list = sorted(filtered_companies, key=lambda x: x['rating_avg'] / (1 + x['distance_km']/10.0), reverse=True)

            with results_container:
                for c in sorted_list:
                    _company_card(c)
                    
                    # Add blue marker for company
                    c_lat = c.get('latitude')
                    c_lng = c.get('longitude')
                    if c_lat and c_lng:
                        search_map.marker(latlng=(c_lat, c_lng))
                        
            # Optionally set zoom based on bounds or just keep a reasonable zoom
            search_map.set_zoom(11)

        async def _handle_search():
            if not svc_select.value:
                ui.notify("Vui lòng chọn loại dịch vụ", type="warning")
                return
            
            search_btn.props("loading")
            try:
                nonlocal all_found_companies
                all_found_companies = await find_nearby_companies(
                    latitude=lat_input.value,
                    longitude=lng_input.value,
                    service_name=svc_select.value,
                    radius_km=9999.0
                )
                _render_results()
            except Exception as e:
                ui.notify(f"Lỗi tìm kiếm: {e}", type="negative")
            finally:
                search_btn.props(remove="loading")

        def _company_card(c):
            # Radius check
            is_outside = c['distance_km'] > c['service_radius_km']
            extra_dist = c['distance_km'] - c['service_radius_km']

            with ui.card().classes("w-full rounded-2xl p-4 shadow-sm border border-gray-100 hover:border-indigo-300 transition-all"):
                with ui.row().classes("w-full justify-between items-start"):
                    with ui.column().classes("gap-0 cursor-pointer").on('click', lambda: open_company_detail(c['id'])):
                        with ui.row().classes('items-center gap-2'):
                            ui.label(c['company_name']).classes("font-bold text-lg text-gray-800 hover:text-primary")
                            ui.icon('info', color='primary', size='1rem')
                        with ui.row().classes("items-center gap-2"):
                            ui.label(f"📍 {c['distance_km']} km").classes("text-sm text-gray-500")
                            if is_outside:
                                ui.label(f"(Vượt {extra_dist:.1f}km)").classes("text-[10px] text-red-500 font-bold")
                    
                    with ui.column().classes("items-end"):
                        ui.label(f"⭐ {c['rating_avg']}").classes("text-amber-500 font-bold")
                        ui.label(f"({c.get('rating_count', 0)} đánh giá)").classes("text-xs text-gray-400")

                ui.separator().classes("my-2")
                
                with ui.row().classes("w-full items-center justify-between mt-1"):
                    with ui.column().classes("gap-0"):
                        ui.label("Dự kiến").classes("text-[10px] uppercase text-gray-400")
                        ui.label(f"{c['eta_minutes']} phút").classes("font-semibold text-indigo-600")
                    
                    with ui.column().classes("gap-0"):
                        ui.label("Giá ước tính").classes("text-[10px] uppercase text-gray-400")
                        ui.label(f"{c['estimated_price']:,.0f} đ").classes("font-semibold text-green-600")
                
                ui.button("CHỌN ĐƠN VỊ NÀY", on_click=lambda c=c: _submit_req(c)).classes("w-full mt-3 rounded-xl").props("unelevated color=indigo")

        async def _submit_req(company: Dict[str, Any]):
            if not issue_detail.value:
                ui.notify("Vui lòng mô tả chi tiết sự cố", type="warning")
                return
            
            # Tìm service_id cụ thể của công ty này khớp với tên dịch vụ đã chọn
            selected_service_name = svc_select.value
            matched_service = next((s for s in company.get('services', []) if s['service_name'].lower() == selected_service_name.lower()), None)
            if not matched_service:
                ui.notify("Công ty không hỗ trợ dịch vụ này", type="negative")
                return
            
            try:
                res = await create_rescue_request(
                    service_id=matched_service['id'],
                    latitude=lat_input.value,
                    longitude=lng_input.value,
                    address_description=addr_desc.value or "Vị trí GPS",
                    car_issue_detail=issue_detail.value,
                    company_id=company['id'],
                    payment_method=payment_method.value
                )
                ui.notify("Đã gửi yêu cầu thành công!", type="positive")
                ui.navigate.to(f"/customer/track/{res['id']}")
            except Exception as e:
                ui.notify(f"Lỗi gửi yêu cầu: {e}", type="negative")
