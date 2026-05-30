"""
Customer Dashboard – Professional UI Version
"""
from nicegui import ui
import httpx
from core.auth import get_access_token, require_role
from core.config import BACKEND_URL
from components.page_layout import page_layout
from components.company_detail_dialog import open_company_detail
# Hàm lấy tên địa điểm từ tọa độ GPS
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
# Hàm yêu cầu quyền truy cập vị trí 
async def get_user_location():
    try:
        result = await ui.run_javascript("""
            return new Promise((resolve, reject) => {
                if (!navigator.geolocation) {
                    reject("No geolocation support");
                }

                navigator.geolocation.getCurrentPosition(
                    (pos) => {
                        resolve({
                            lat: pos.coords.latitude,
                            lng: pos.coords.longitude
                        });
                    },
                    (err) => reject(err.message),
                    {
                        enableHighAccuracy: true
                    }
                );
            });
        """)
        return result
    except Exception:
        return None
def create_customer_dashboard():

    @ui.page('/customer/dashboard')
    async def customer_dashboard():
        user_lat = 21.0285
        user_lng = 105.8542
        user_location_text = "Đang lấy vị trí..."
        location_label = None
        async def _update_user_location():
            nonlocal user_lat, user_lng, user_location_text

            try:
                gps = await get_user_location()

                if gps and isinstance(gps, dict):
                    user_lat = gps.get('lat', user_lat)
                    user_lng = gps.get('lng', user_lng)
                    print(f"[GPS] lat={user_lat}, lng={user_lng}")

                    # 1. reverse geocode phải dùng tọa độ MỚI
                    user_location_text = await get_location_text(user_lat, user_lng)

                #    2. update UI an toàn
                if location_label:
                    location_label.text = user_location_text
                    location_label.update()

                # 3. update map marker
                m.marker(latlng=(user_lat, user_lng))

                return user_lat, user_lng

            except Exception as e:
                ui.notify(f'Không lấy được GPS: {e}', type='warning')
                return user_lat, user_lng

        all_companies = []
        sort_by = 'distance'

        # =====================================================
        # COMPANY CARD
        # =====================================================
        def _company_row(c):

            with ui.card().classes("""
                w-full
                rounded-2xl
                border-none
                shadow-md
                hover:shadow-2xl
                hover:-translate-y-1
                hover:bg-blue-50
                transition-all duration-300
                cursor-pointer
                p-4
                bg-white
            """).on(
                'click',
                 lambda: open_company_detail(c['id'])
            ):

                with ui.row().classes("""
                    w-full
                    items-center
                    gap-4
                """):

                    # Icon
                    with ui.element('div').classes("""
                        w-14 h-14
                        rounded-2xl
                        bg-primary/10
                        flex items-center justify-center
                    """):

                        ui.icon(
                            'local_taxi',
                            color='primary',
                            size='1.7rem'
                        )

                    # Info
                    with ui.column().classes("""
                        flex-1
                        gap-1
                    """):

                        ui.label(
                            c['company_name']
                        ).classes("""
                            text-base
                            font-bold
                            text-on-surface
                        """)

                        with ui.row().classes("""
                            items-center
                            gap-2
                        """):

                            ui.label(
                                f"⭐ {c['rating_avg']:.1f}"
                            ).classes("""
                                text-amber-600
                                text-sm
                                font-bold
                            """)

                            ui.label(
                                f"{c['rating_count']} đánh giá"
                            ).classes("""
                                text-xs
                                text-on-surface-variant
                            """)

                    # Right side
                    with ui.column().classes("""
                        items-end
                        gap-1
                    """):

                        ui.label(
                            f"{c.get('distance_km', '??')} km"
                        ).classes("""
                            text-primary
                            font-bold
                        """)

                        ui.button(
                            'Chi tiết',
                            icon='arrow_forward'
                        ).props(
                            'flat dense'
                        ).classes("""
                            text-primary
                            text-xs
                        """)

        # =====================================================
        # RENDER COMPANIES
        # =====================================================
        def _render_companies():

            companies_container.clear()

            sorted_list = all_companies

            if sort_by == 'rating':

                sorted_list = sorted(
                    all_companies,
                    key=lambda x: x['rating_avg'],
                    reverse=True
                )

            with companies_container:

                if not sorted_list:

                    with ui.column().classes("""
                        w-full
                        items-center
                        justify-center
                        py-12
                        gap-3
                    """):

                        ui.icon(
                            'location_off',
                            size='3rem'
                        ).classes('text-gray-400')

                        ui.label(
                            'Không tìm thấy đơn vị cứu hộ'
                        ).classes(
                            'text-on-surface-variant'
                        )

                else:

                    for c in sorted_list:
                        _company_row(c)

        # =====================================================
        # UPDATE MAP
        # =====================================================
        async def _update_map():
            nonlocal user_lat, user_lng,user_location_text
            m.clear_layers()
            m.tile_layer(
                url_template='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
            )
            user_lat, user_lng = await _update_user_location()
            user_location_text = await get_location_text(user_lat, user_lng)
             # User marker
            user_marker = m.marker(
                latlng=(user_lat, user_lng)
            )

            user_marker.run_method(
                'bindPopup',
                'Vị trí của bạn'
            )

    # Company markers
            for c in all_companies:

                c_lat = c.get('latitude')
                c_lng = c.get('longitude')

                if c_lat is not None and c_lng is not None:

                    # Service radius
                    m.generic_layer(
                        name='circle',
                        args=[[
                            c_lat,
                            c_lng
                            ], {
                                'radius': c['service_radius_km'] * 1000,
                                'color': '#2563eb',
                                'fillOpacity': 0.08,
                                'weight': 1
                             }]
                        )

                    # Marker
                    marker = m.marker(
                        latlng=(c_lat, c_lng)
                    )

                    marker.run_method(
                        'bindPopup',
                        f"""
                <div style="
                    min-width:200px;
                    padding:8px;
                    font-family:Inter,sans-serif;
                ">
                    <h3 style="
                        margin:0;
                        font-size:16px;
                        font-weight:700;
                    ">
                        {c['company_name']}
                    </h3>

                    <p style="
                        margin-top:6px;
                        color:#666;
                    ">
                        ⭐ {c['rating_avg']:.1f}
                        ({c['rating_count']} đánh giá)
                    </p>
                </div>
                """
            )

        # =====================================================
        # LOAD DATA
        # =====================================================
        async def load_data():

            loading_spinner.visible = True

            try:

                token = get_access_token()

                async with httpx.AsyncClient() as client:

                    response = await client.get(
                        f'{BACKEND_URL}/rescue/companies',
                        headers={
                            'Authorization': f'Bearer {token}'
                        },
                        timeout=10
                    )

                    if response.status_code == 200:

                        nonlocal all_companies

                        all_companies = response.json()['data']

                        _render_companies()
                        await _update_map()

                    else:

                        ui.notify(
                            f'Lỗi tải dữ liệu: {response.status_code}',
                            type='negative'
                        )

            except Exception as e:

                ui.notify(
                    f'Lỗi kết nối: {e}',
                    type='negative'
                )

            finally:

                loading_spinner.visible = False

        # =====================================================
        # SORT
        # =====================================================
        def set_sort(value):

            nonlocal sort_by

            sort_by = value

            _render_companies()

        # =====================================================
        # PAGE
        # =====================================================
        with page_layout(
            '/customer/dashboard',
            title='Dashboard'
        ):

            with ui.column().classes("""
                w-full
                gap-6
            """):

                # =================================================
                # HEADER
                # =================================================
                with ui.row().classes("""
                    w-full
                    justify-between
                    items-center
                """):

                    with ui.column().classes("gap-1"):

                        ui.label(
                            'Trung tâm cứu hộ'
                        ).classes("""
                            text-3xl
                            font-bold
                            font-outfit
                        """)

                        ui.label(
                            'Theo dõi đơn vị cứu hộ gần bạn theo thời gian thực'
                        ).classes("""
                            text-on-surface-variant
                        """)

                    ui.button(
                        'Làm mới dữ liệu',
                        icon='refresh',
                        on_click=load_data
                    ).props(
                        'unelevated'
                    ).classes("""
                        bg-primary
                        text-white
                        rounded-xl
                        px-6 py-3
                        shadow-lg
                        hover:shadow-xl
                        transition-all
                    """)

                # =================================================
                # CONTENT
                # =================================================
                with ui.row().classes("""
                    w-full
                    h-[calc(100vh-220px)]
                    gap-6
                """):

                    # =============================================
                    # MAP
                    # =============================================
                    with ui.card().classes("""
                        flex-[2]
                        h-full
                        overflow-hidden
                        rounded-[28px]
                        border-none
                        shadow-2xl
                        relative
                        bg-white
                    """):

                        m = ui.leaflet(
                            center=(21.0285, 105.8542),
                            zoom=12
                        ).classes('w-full h-full')

                        m.tile_layer(
                            url_template='https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'
                        )

                        # Floating panel
                        with ui.row().classes("""
                            absolute
                            top-4 left-4
                            z-[1000]
                            bg-white/90
                            backdrop-blur-md
                            rounded-2xl
                            shadow-xl
                            px-5 py-3
                            gap-4
                            items-center
                        """):

                            ui.icon(
                                'location_on',
                                color='primary'
                            )

                            with ui.column().classes('gap-0'):

                                ui.label(
                                    'Vị trí hiện tại'
                                ).classes("""
                                    font-bold
                                    text-sm
                                """)

                                location_label = ui.label(user_location_text).classes("""
                                text-xs
                                text-on-surface-variant
                                """)

                        # Floating button
                        with ui.column().classes("""
                            absolute
                            bottom-4 right-4
                            z-[1000]
                            gap-3
                        """):

                            ui.button(
                                icon='my_location',
                                on_click=lambda: (
                                    m.set_center(
                                        (21.0285, 105.8542)
                                    ),
                                    m.set_zoom(13)
                                )
                            ).props(
                                'round unelevated'
                            ).classes("""
                                bg-white
                                shadow-xl
                                hover:scale-110
                                transition-all
                            """)

                    # =============================================
                    # SIDEBAR
                    # =============================================
                    with ui.card().classes("""
                        flex-1
                        h-full
                        rounded-[28px]
                        border-none
                        shadow-xl
                        bg-white
                        p-6
                        gap-5
                    """):

                        # Header
                        with ui.row().classes("""
                            w-full
                            justify-between
                            items-center
                        """):

                            with ui.column().classes('gap-0'):

                                ui.label(
                                    'Đơn vị đối tác'
                                ).classes("""
                                    text-xl
                                    font-bold
                                    font-outfit
                                """)

                                ui.label(
                                    'Các đơn vị đang hoạt động'
                                ).classes("""
                                    text-xs
                                    text-on-surface-variant
                                """)

                            loading_spinner = ui.spinner(
                                size='sm'
                            )

                            loading_spinner.visible = False

                        # Sort
                        with ui.row().classes("""
                            w-full
                            gap-2
                        """):

                            ui.button(
                                'Gần nhất',
                                icon='near_me',
                                on_click=lambda: set_sort('distance')
                            ).props(
                                'unelevated'
                            ).classes("""
                                rounded-xl
                                bg-primary/10
                                text-primary
                                font-bold
                            """)

                            ui.button(
                                'Đánh giá cao',
                                icon='star',
                                on_click=lambda: set_sort('rating')
                            ).props(
                                'unelevated'
                            ).classes("""
                                rounded-xl
                                bg-amber-100
                                text-amber-700
                                font-bold
                            """)

                        ui.separator()

                        # List
                        companies_container = ui.column().classes("""
                            w-full
                            flex-1
                            overflow-y-auto
                            gap-4
                            pr-2
                        """)

        # =====================================================
        # INITIAL LOAD
        # =====================================================
        await load_data()