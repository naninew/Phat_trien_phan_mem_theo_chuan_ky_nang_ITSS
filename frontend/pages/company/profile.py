"""
Trang thông tin công ty – dành cho quản lý công ty.
"""
from nicegui import ui
from core.auth import require_role
from components.page_layout import page_layout
from services.api_client import api_client


def create_profile_page():

    @ui.page('/company/profile')
    async def profile_page():
        if not require_role("company_staff"):
            return

        # Fetch current company info
        try:
            # We use a custom endpoint or just get from the current user session if it had it
            # For now, let's assume we have a GET /rescue/profile or similar
            res = await api_client.get("/profile/company")
            c = res.get("data", {})
        except:
            c = {}
            ui.notify("Không thể tải thông tin hồ sơ", type="negative")

        with page_layout("/company/profile", title="Hồ Sơ Công Ty"):
            
            with ui.column().classes("w-full max-w-3xl mx-auto gap-6"):
                ui.label("🏢 Hồ Sơ Công Ty").classes("text-3xl font-bold text-gray-800")
                
                with ui.card().classes("w-full rounded-2xl p-8 shadow-sm border border-gray-100"):
                    ui.label("Thông tin cơ bản").classes("text-lg font-bold text-gray-700 mb-4")
                    
                    name = ui.input(label="Tên công ty", value=c.get('company_name', '')).classes("w-full").props("outlined")
                    hotline = ui.input(label="Hotline cứu hộ", value=c.get('hotline', '')).classes("w-full mt-2").props("outlined")
                    license = ui.input(label="Số giấy phép kinh doanh", value=c.get('license_number', '')).classes("w-full mt-2").props("outlined disabled")
                    
                    ui.label("Vị trí & Địa chỉ").classes("text-lg font-bold text-gray-700 mt-8 mb-4")
                    addr = ui.textarea(label="Địa chỉ trụ sở", value=c.get('address', '')).classes("w-full").props("outlined")
                    
                    with ui.row().classes("w-full gap-4 mt-2"):
                        lat = ui.number(label="Vĩ độ (Latitude)", value=c.get('latitude', 0.0), format="%.6f").classes("flex-1").props("outlined")
                        lng = ui.number(label="Kinh độ (Longitude)", value=c.get('longitude', 0.0), format="%.6f").classes("flex-1").props("outlined")
                    
                    ui.button("Lấy vị trí hiện tại của tôi", icon="my_location", on_click=lambda: _get_geo(lat, lng)).classes("mt-2").props("flat color=indigo")

                    ui.label("Dịch vụ").classes("text-lg font-bold text-gray-700 mt-8 mb-4")
                    radius = ui.number(label="Bán kính phục vụ (km)", value=c.get('service_radius_km', 20)).classes("w-full").props("outlined")

                    ui.separator().classes("my-8")
                    
                    save_btn = ui.button("LƯU THAY ĐỔI", icon="save", on_click=lambda: _save_profile()).classes("w-full py-4 rounded-xl bg-indigo-600 text-white font-bold shadow-lg shadow-indigo-100")

        # ── Logic ────────────────────────────────────────────────────────
        
        async def _get_geo(lat_f, lng_f):
            pos = await ui.run_javascript('navigator.geolocation.getCurrentPosition(p => p.coords, e => null)')
            if pos:
                lat_f.set_value(pos.latitude)
                lng_f.set_value(pos.longitude)
            else:
                ui.notify("Không thể lấy vị trí")

        async def _save_profile():
            save_btn.props("loading")
            payload = {
                "company_name": name.value,
                "hotline": hotline.value,
                "address": addr.value,
                "latitude": lat.value,
                "longitude": lng.value,
                "service_radius_km": radius.value
            }
            try:
                await api_client.put("/profile/company", data=payload)
                ui.notify("Đã cập nhật hồ sơ thành công", type="positive")
            except Exception as e:
                ui.notify(f"Lỗi: {e}", type="negative")
            finally:
                save_btn.props(remove="loading")
