"""
Customer Dashboard – Bản đồ tương tác & danh sách công ty đối tác.
"""
from nicegui import ui
import httpx
from core.auth import get_access_token, require_role
from core.config import BACKEND_URL
from components.page_layout import page_layout
from components.company_detail_dialog import open_company_detail

def create_customer_dashboard():

    @ui.page("/customer/dashboard")
    async def customer_dashboard():
        if not require_role("customer"):
            return

        all_companies = []
        sort_by = "distance"

        # --- UI Logic ---
        def _render_companies():
            companies_container.clear()
            
            # Sorting logic
            sorted_list = all_companies
            if sort_by == "rating":
                sorted_list = sorted(all_companies, key=lambda x: x['rating_avg'], reverse=True)
            elif sort_by == "distance":
                sorted_list = all_companies # In real app, calculate actual distance
            
            with companies_container:
                if not sorted_list:
                    ui.label("Không tìm thấy đơn vị cứu hộ nào.").classes("text-on-surface-variant italic opacity-50 py-4 w-full text-center")
                else:
                    for c in sorted_list:
                        _company_row(c)

        def _company_row(c):
            with ui.row().classes("w-full p-4 items-center gap-4 hover:bg-surface-variant/30 cursor-pointer rounded-xl transition-all border-b border-surface-variant/20").on("click", lambda: open_company_detail(c['id'])):
                with ui.element('div').classes('p-3 bg-primary-container rounded-lg'):
                    ui.icon('local_taxi', color='primary', size='1.5rem')
                
                with ui.column().classes("flex-1 gap-0"):
                    ui.label(c['company_name']).classes("font-bold text-on-surface text-base")
                    with ui.row().classes("items-center gap-2"):
                        ui.label(f"⭐ {c['rating_avg']:.1f}").classes("text-amber-600 font-bold text-sm")
                        ui.label(f"({c['rating_count']} đánh giá)").classes("text-on-surface-variant text-xs")
                
                with ui.column().classes("items-end"):
                    ui.label(f"~ {c.get('distance_km', '??')} km").classes("text-primary font-bold text-sm")
                    ui.label("Chi tiết").classes("text-xs text-primary underline")

        async def load_data():
            loading_spinner.set_visibility(True)
            try:
                token = get_access_token()
                async with httpx.AsyncClient() as client:
                    r_comp = await client.get(f"{BACKEND_URL}/rescue/companies", headers={"Authorization": f"Bearer {token}"}, timeout=10)
                    if r_comp.status_code == 200:
                        nonlocal all_companies
                        all_companies = r_comp.json()["data"]
                        _render_companies()
                        _update_map()
                    else:
                        ui.notify(f"Lỗi tải dữ liệu: {r_comp.status_code}", type="negative")
            except Exception as e:
                ui.notify(f"Lỗi kết nối: {e}", type="negative")
            finally:
                loading_spinner.set_visibility(False)

        def _update_map():
            # Update leaflet markers
            m.clear_layers()
            for c in all_companies:
                c_lat, c_lng = c.get('latitude'), c.get('longitude')
                if c_lat and c_lng:
                    # Circle for radius
                    m.generic_layer(name='circle', args=[[c_lat, c_lng], {
                        'radius': c['service_radius_km'] * 1000,
                        'color': '#4caf50',
                        'fillOpacity': 0.1,
                        'weight': 1
                    }])
                    
                    # Custom marker
                    m.marker(latlng=(c_lat, c_lng))

        # --- UI Layout ---
        with page_layout("/customer/dashboard", title="Dashboard"):
            with ui.row().classes("w-full h-[calc(100vh-200px)] gap-6"):
                
                # Left: Map
                with ui.card().classes("flex-[2] h-full m3-card p-0 overflow-hidden relative shadow-xl"):
                    m = ui.leaflet(center=(21.0285, 105.8542), zoom=12).classes("w-full h-full")
                    m.tile_layer(url_template='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png')
                    
                    # User position marker (Red)
                    m.generic_layer(name='marker', args=[[21.0285, 105.8542], {
                        'icon': {
                            'iconUrl': 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
                            'shadowUrl': 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/0.7.7/images/marker-shadow.png',
                            'iconSize': [25, 41],
                            'iconAnchor': [12, 41],
                            'popupAnchor': [1, -34],
                            'shadowSize': [41, 41]
                        }
                    }])
                    
                    with ui.row().classes("absolute top-4 right-4 z-[1000] gap-2"):
                        ui.button(icon="my_location", on_click=lambda: (m.set_center((21.0285, 105.8542)), m.set_zoom(13))).props("round unelevated color=primary-container text-color=primary shadow-lg").classes("bg-[#f0f4f8]")
                    
                # Right: Companies List
                with ui.column().classes("flex-1 h-full gap-4"):
                    with ui.card().classes("w-full h-full m3-card p-6 gap-4 shadow-lg"):
                        with ui.row().classes("w-full justify-between items-center"):
                            ui.label("Đơn vị cứu hộ đối tác").classes("text-xl font-bold font-outfit text-on-surface")
                            with ui.row().classes("gap-2"):
                                loading_spinner = ui.spinner(size='sm').classes('hidden')
                                ui.button(icon='refresh', on_click=load_data).props('flat round').tooltip('Cập nhật dữ liệu')
                        
                        # Sorting
                        with ui.row().classes("w-full gap-2"):
                            ui.button("Gần nhất", icon="near_me", on_click=lambda: set_sort("distance")).props("rounded flat dense").classes("text-[10px] text-primary")
                            ui.button("Đánh giá", icon="star", on_click=lambda: set_sort("rating")).props("rounded flat dense").classes("text-[10px] text-primary")

                        ui.separator()
                        
                        # List Container
                        companies_container = ui.column().classes("w-full overflow-y-auto gap-0 flex-1")

        def set_sort(val):
            nonlocal sort_by
            sort_by = val
            _render_companies()

        await load_data()
