"""
Trang thông tin công ty – dành cho quản lý công ty.
"""
from nicegui import ui
from core.auth import require_role
from components.page_layout import page_layout
from services.api_client import api_client
import asyncio


def create_profile_page():

    @ui.page('/company/profile')
    async def profile_page():
        if not require_role("company_staff"):
            return

        is_new = False
        c = {}
        
        # Fetch current company info
        res = await api_client.get("/profile/company")
        if not res.get("success"):
            if "Company profile not found" in res.get("message", ""):
                is_new = True
                ui.notify("Chưa có hồ sơ công ty. Vui lòng tạo mới.", type="info")
            elif "Session expired" in res.get("message", ""):
                return  # Handled by api_client
            else:
                ui.notify(res.get("message", "Lỗi tải thông tin hồ sơ"), type="negative")
        else:
            is_new = False
            c = res.get("data", {})

        with page_layout("/company/profile", title="Hồ Sơ Công Ty"):
            
            with ui.column().classes("w-full max-w-3xl mx-auto gap-6"):
                ui.label("🏢 Hồ Sơ Công Ty").classes("text-3xl font-bold text-gray-800")
                
                with ui.card().classes("w-full rounded-2xl p-8 shadow-sm border border-gray-100"):
                    ui.label("Thông tin cơ bản").classes("text-lg font-bold text-gray-700 mb-4")
                    
                    name = ui.input(label="Tên công ty (*)", value=c.get('company_name', '')).classes("w-full").props("outlined")
                    license_input = ui.input(label="Số giấy phép kinh doanh (*)", value=c.get('business_license', '')).classes("w-full mt-2").props("outlined")
                    hotline = ui.input(label="Hotline cứu hộ (*)", value=c.get('hotline', '')).classes("w-full mt-2").props("outlined")
                    
                    ui.label("Vị trí & Hoạt động").classes("text-lg font-bold text-gray-700 mt-8 mb-4")
                    addr = ui.textarea(label="Địa chỉ trụ sở (*)", value=c.get('address', '')).classes("w-full").props("outlined")
                    operating_area = ui.input(label="Khu vực hoạt động", value=c.get('operating_area', '')).classes("w-full mt-2").props("outlined")
                    
                    with ui.row().classes("w-full gap-4 mt-2"):
                        lat = ui.number(label="Vĩ độ (Latitude)", value=c.get('latitude', 0.0), format="%.6f").classes("flex-1").props("outlined")
                        lng = ui.number(label="Kinh độ (Longitude)", value=c.get('longitude', 0.0), format="%.6f").classes("flex-1").props("outlined")
                    
                    ui.button("Lấy vị trí hiện tại của tôi", icon="my_location", on_click=lambda: _get_geo(lat, lng)).classes("mt-2").props("flat color=indigo")

                    ui.label("Thông tin bổ sung").classes("text-lg font-bold text-gray-700 mt-8 mb-4")
                    description = ui.textarea(label="Mô tả công ty", value=c.get('description', '')).classes("w-full").props("outlined")
                    
                    if not is_new:
                        ui.label("Trạng thái hệ thống (Chỉ xem)").classes("text-lg font-bold text-gray-700 mt-8 mb-4")
                        with ui.row().classes("w-full gap-4"):
                            ui.input(label="Đánh giá trung bình", value=str(c.get('rating_avg', 0.0))).classes("flex-1").props("outlined readonly")
                            v_status = "Đã xác minh" if c.get('is_verified') else "Chưa xác minh"
                            ui.input(label="Tình trạng xác minh", value=v_status).classes("flex-1").props("outlined readonly")
                            ui.input(label="Trạng thái", value=c.get('status', 'pending')).classes("flex-1").props("outlined readonly")

                    ui.separator().classes("my-8")
                    
                    with ui.row().classes("w-full gap-4"):
                        if is_new:
                            save_btn = ui.button("TẠO HỒ SƠ", icon="add_circle", on_click=lambda: _save_profile(True)).classes("flex-1 py-4 rounded-xl bg-indigo-600 text-white font-bold shadow-lg shadow-indigo-100")
                        else:
                            save_btn = ui.button("LƯU THAY ĐỔI", icon="save", on_click=lambda: _save_profile(False)).classes("flex-1 py-4 rounded-xl bg-indigo-600 text-white font-bold shadow-lg shadow-indigo-100")
                            ui.button("XÓA HỒ SƠ", icon="delete", color="red", on_click=lambda: _confirm_delete()).classes("py-4 px-6 rounded-xl font-bold")

        # ── Logic ────────────────────────────────────────────────────────
        
        async def _get_geo(lat_f, lng_f):
            pos = await ui.run_javascript('navigator.geolocation.getCurrentPosition(p => p.coords, e => null)')
            if pos:
                lat_f.set_value(pos.latitude)
                lng_f.set_value(pos.longitude)
            else:
                ui.notify("Không thể lấy vị trí")

        async def _save_profile(creating: bool):
            # Validate required fields
            if not name.value or not license_input.value or not addr.value or not hotline.value:
                ui.notify("Vui lòng điền đủ các trường bắt buộc (*)", type="warning")
                return

            save_btn.props("loading")
            payload = {
                "company_name": name.value,
                "business_license": license_input.value,
                "hotline": hotline.value,
                "address": addr.value,
                "operating_area": operating_area.value,
                "latitude": lat.value,
                "longitude": lng.value,
                "description": description.value,
            }
            try:
                if creating:
                    res = await api_client.post("/profile/company", data=payload)
                    if res.get("success"):
                        ui.notify("Tạo hồ sơ thành công!", type="positive")
                        ui.navigate.reload()
                    else:
                        ui.notify(f"Lỗi: {res.get('message')}", type="negative")
                else:
                    res = await api_client.put("/profile/company", data=payload)
                    if res.get("success"):
                        ui.notify("Đã cập nhật hồ sơ thành công", type="positive")
                    else:
                        ui.notify(f"Lỗi: {res.get('message')}", type="negative")
            except Exception as e:
                ui.notify(f"Lỗi hệ thống: {str(e)}", type="negative")
            finally:
                save_btn.props(remove="loading")

        async def _delete_profile():
            try:
                res = await api_client.delete("/profile/company")
                if res.get("success"):
                    ui.notify("Đã xóa hồ sơ công ty thành công", type="positive")
                    ui.navigate.reload()
                else:
                    ui.notify(f"Lỗi khi xóa hồ sơ: {res.get('message')}", type="negative")
            except Exception as e:
                ui.notify(f"Lỗi hệ thống: {str(e)}", type="negative")

        def _confirm_delete():
            with ui.dialog() as dlg, ui.card().classes('rounded-2xl p-6 shadow-2xl'):
                ui.label('Xóa hồ sơ công ty?').classes('text-xl font-bold text-red-600 mb-4')
                ui.label('Hồ sơ của bạn sẽ bị vô hiệu hóa. Bạn có chắc chắn muốn xóa không?').classes('mb-6')
                with ui.row().classes('w-full justify-end gap-3'):
                    ui.button('Hủy', on_click=dlg.close).props('flat text-gray-600')
                    def on_confirm():
                        dlg.close()
                        asyncio.create_task(_delete_profile())
                    ui.button('Xóa', color='red', on_click=on_confirm).props('unelevated')
            dlg.open()
