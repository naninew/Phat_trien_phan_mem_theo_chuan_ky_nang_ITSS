"""
Trang thông tin công ty – dành cho quản lý công ty.
"""
from nicegui import ui
from core.auth import require_role
from components.page_layout import page_layout
from components.company_ui import inject_company_styles, page_header, section_heading, status_badge
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

        inject_company_styles()

        with page_layout("/company/profile", title=""):
            with ui.column().classes("company-page gap-6"):
                page_header(
                    "Hồ sơ công ty",
                    "Quản lý thông tin doanh nghiệp, liên hệ, vị trí và trạng thái hoạt động.",
                    "business",
                )

                with ui.element("div").classes("company-card p-6 w-full"):
                    section_heading("Thông tin cơ bản", "Thông tin nhận diện và giấy phép hoạt động")
                    
                    with ui.row().classes("w-full gap-4 mt-4"):
                        name = ui.input(label="Tên công ty (*)", value=c.get('company_name', '')).classes("flex-1 company-field").props("outlined")
                        license_input = ui.input(label="Số giấy phép kinh doanh (*)", value=c.get('business_license', '')).classes("flex-1 company-field").props("outlined")
                    
                    ui.separator().classes("my-6")
                    section_heading("Liên hệ", "Kênh khách hàng dùng để kết nối cứu hộ")
                    hotline = ui.input(label="Hotline cứu hộ (*)", value=c.get('hotline', '')).classes("w-full mt-4 company-field").props("outlined")

                    ui.separator().classes("my-6")
                    section_heading("Vị trí & hoạt động", "Địa chỉ trụ sở, khu vực phục vụ và tọa độ vận hành")
                    addr = ui.textarea(label="Địa chỉ trụ sở (*)", value=c.get('address', '')).classes("w-full mt-4 company-field").props("outlined rounded rows=3")
                    operating_area = ui.input(label="Khu vực hoạt động", value=c.get('operating_area', '')).classes("w-full mt-3 company-field").props("outlined")
                    
                    with ui.row().classes("w-full gap-4 mt-3"):
                        lat = ui.number(label="Vĩ độ (Latitude)", value=c.get('latitude', 0.0), format="%.6f").classes("flex-1 company-field").props("outlined")
                        lng = ui.number(label="Kinh độ (Longitude)", value=c.get('longitude', 0.0), format="%.6f").classes("flex-1 company-field").props("outlined")
                    
                    ui.button("Lấy vị trí hiện tại", icon="my_location", on_click=lambda: _get_geo(lat, lng)).classes("company-muted-btn mt-2").props("flat no-caps")

                    ui.separator().classes("my-6")
                    section_heading("Cài đặt dịch vụ", "Mô tả ngắn hiển thị cho khách hàng khi chọn đơn vị")
                    description = ui.textarea(label="Mô tả công ty", value=c.get('description', '')).classes("w-full mt-4 company-field").props("outlined rounded rows=4")
                    
                    if not is_new:
                        ui.separator().classes("my-6")
                        section_heading("Trạng thái hệ thống", "Thông tin chỉ đọc từ hệ thống kiểm duyệt")
                        with ui.row().classes("w-full gap-3 mt-4 flex-wrap"):
                            status_badge(f"Đánh giá {c.get('rating_avg', 0.0)}", "amber")
                            status_badge("Đã xác minh" if c.get('is_verified') else "Chưa xác minh", "emerald" if c.get('is_verified') else "amber")
                            status_badge(c.get('status', 'pending'), "blue")

                    ui.separator().classes("my-8")
                    
                    with ui.row().classes("w-full gap-4 justify-end"):
                        if is_new:
                            save_btn = ui.button("Tạo hồ sơ", icon="add_circle", on_click=lambda: _save_profile(True)).classes("company-primary-btn px-6").props("unelevated no-caps")
                        else:
                            ui.button("Xóa hồ sơ", icon="delete", color="red", on_click=lambda: _confirm_delete()).classes("rounded-xl px-5 font-bold").props("flat no-caps")
                            save_btn = ui.button("Lưu thay đổi", icon="save", on_click=lambda: _save_profile(False)).classes("company-primary-btn px-6").props("unelevated no-caps")

        # ── Logic ────────────────────────────────────────────────────────
        
        async def _get_geo(lat_f, lng_f):
            pos = await ui.run_javascript("""
                await new Promise((resolve) => {
                    if (!navigator.geolocation) {
                        resolve(null);
                        return;
                    }
                    navigator.geolocation.getCurrentPosition(
                        (p) => resolve({
                            latitude: p.coords.latitude,
                            longitude: p.coords.longitude,
                        }),
                        () => resolve(null),
                        { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 },
                    );
                })
            """, timeout=12)
            if pos and pos.get("latitude") is not None and pos.get("longitude") is not None:
                lat_f.set_value(pos["latitude"])
                lng_f.set_value(pos["longitude"])
                ui.notify("Đã lấy vị trí hiện tại", type="positive")
            else:
                ui.notify("Không thể lấy vị trí. Hãy cấp quyền vị trí cho trình duyệt.", type="warning")

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
