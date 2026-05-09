"""
Shared profile editing page for customers and company staff.
"""
from nicegui import ui
import httpx
from core.auth import get_access_token, get_user_role
from core.config import BACKEND_URL
from components.page_layout import page_layout

def create_profile_page():

    @ui.page('/profile')
    async def profile_page():
        token = get_access_token()
        if not token:
            ui.navigate.to('/login')
            return

        headers = {"Authorization": f"Bearer {token}"}
        role = get_user_role()
        
        # Stores basic state
        profile_data = {'avatar_url': None}

        async def _load_profile():
            try:
                async with httpx.AsyncClient() as client:
                    r = await client.get(f"{BACKEND_URL}/profile/me", headers=headers)
                    if r.status_code == 200:
                        data = r.json()["data"]
                        name_input.value = data["full_name"]
                        phone_input.value = data["phone"]
                        email_input.value = data["email"]
                        profile_data['avatar_url'] = data.get("avatar_url")
                        
                        if profile_data['avatar_url']:
                            avatar_img.set_source(f"{BACKEND_URL.replace('/api/v1', '')}{profile_data['avatar_url']}")
                        
                        if role == "company_staff" and data.get("company"):
                            comp = data["company"]
                            comp_name_input.value = comp["company_name"]
                            comp_addr_input.value = comp["address"]
                            comp_hotline_input.value = comp["hotline"]
                            comp_radius_input.value = float(comp["service_radius_km"])
                    else:
                        ui.notify("Không thể tải thông tin cá nhân", type="negative")
            except Exception as e:
                ui.notify(f"Lỗi tải thông tin: {e}", type="negative")

        async def _handle_upload(e):
            try:
                content = await e.file.read()
                async with httpx.AsyncClient() as client:
                    files = {'file': (e.file.name, content, e.file.content_type)}
                    r = await client.post(f"{BACKEND_URL}/profile/me/avatar", files=files, headers={"Authorization": f"Bearer {token}"})
                    if r.status_code == 200:
                        new_url = r.json()["data"]["avatar_url"]
                        profile_data['avatar_url'] = new_url
                        avatar_img.set_source(f"{BACKEND_URL.replace('/api/v1', '')}{new_url}")
                        ui.notify("Cập nhật ảnh đại diện thành công", type="positive")
                    else:
                        ui.notify(f"Lỗi upload ảnh: {r.text}", type="negative")
            except Exception as ex:
                ui.notify(f"Lỗi kết nối: {ex}", type="negative")

        async def _update_profile():
            try:
                async with httpx.AsyncClient() as client:
                    # 1. Update user info
                    user_data = {
                        "full_name": name_input.value,
                        "phone": phone_input.value,
                        "email": email_input.value
                    }
                    r = await client.put(f"{BACKEND_URL}/profile/me", json=user_data, headers=headers)
                    
                    if r.status_code == 200:
                        ui.notify("Cập nhật thông tin cá nhân thành công", type="positive")
                    else:
                        ui.notify(f"Lỗi: {r.json().get('detail', 'Không xác định')}", type="negative")
                        return

                    # 2. Update company info if applicable
                    if role == "company_staff":
                        comp_data = {
                            "company_name": comp_name_input.value,
                            "address": comp_addr_input.value,
                            "hotline": comp_hotline_input.value,
                            "service_radius_km": float(comp_radius_input.value)
                        }
                        r2 = await client.put(f"{BACKEND_URL}/profile/company", json=comp_data, headers=headers)
                        if r2.status_code == 200:
                            ui.notify("Cập nhật thông tin công ty thành công", type="positive")
                        else:
                            ui.notify(f"Lỗi cập nhật công ty: {r2.json().get('detail')}", type="negative")
            except Exception as e:
                ui.notify(f"Lỗi lưu thông tin: {e}", type="negative")

        with page_layout("/profile", title="Tài Khoản"):
            with ui.column().classes('w-full max-w-4xl mx-auto p-8 gap-8'):
                with ui.row().classes('w-full items-center justify-between'):
                    ui.label('Cài Đặt Tài Khoản').classes('text-3xl font-bold text-on-surface font-outfit')
                    ui.button('QUAY LẠI', icon='arrow_back', on_click=lambda: ui.navigate.back()).props('flat rounded')

                # --- Main Content Grid ---
                with ui.row().classes('w-full gap-8 items-start'):
                    
                    # Left Column: Avatar & Role
                    with ui.column().classes('w-72 gap-6'):
                        with ui.card().classes('w-full m3-card p-6 items-center text-center shadow-lg'):
                            avatar_img = ui.image('').classes('w-40 h-40 rounded-full shadow-md object-cover border-4 border-primary/10 mb-4 bg-gray-100')
                            ui.upload(on_upload=_handle_upload, label="Đổi ảnh đại diện", auto_upload=True).props('flat color=primary').classes('w-full')
                            
                            ui.separator().classes('my-4')
                            ui.label(role.replace('_', ' ').upper()).classes('text-[10px] font-bold tracking-widest text-primary bg-primary/10 px-4 py-2 rounded-full')

                    # Right Column: Detailed Forms
                    with ui.column().classes('flex-1 gap-6'):
                        # Personal Information
                        with ui.card().classes('w-full m3-card p-8 gap-6'):
                            with ui.row().classes('items-center gap-4'):
                                ui.icon('person', size='2rem', color='primary')
                                ui.label('Thông Tin Cá Nhân').classes('text-xl font-bold font-outfit')
                            
                            ui.separator()
                            name_input = ui.input('Họ và Tên').classes('w-full').props('outlined rounded')
                            with ui.row().classes('w-full gap-4'):
                                phone_input = ui.input('Số điện thoại').classes('flex-1').props('outlined rounded')
                                email_input = ui.input('Email').classes('flex-1').props('outlined rounded')

                        # Company Information (Only for staff)
                        if role == "company_staff":
                            with ui.card().classes('w-full m3-card p-8 gap-6'):
                                with ui.row().classes('items-center gap-4'):
                                    ui.icon('business', size='2rem', color='primary')
                                    ui.label('Thông Tin Công Ty').classes('text-xl font-bold font-outfit')
                                
                                ui.separator()
                                comp_name_input = ui.input('Tên Công Ty').classes('w-full').props('outlined rounded')
                                comp_addr_input = ui.input('Địa chỉ trụ sở').classes('w-full').props('outlined rounded')
                                with ui.row().classes('w-full gap-4'):
                                    comp_hotline_input = ui.input('Hotline').classes('flex-1').props('outlined rounded')
                                    comp_radius_input = ui.number('Bán kính phục vụ (km)', step=1).classes('flex-1').props('outlined rounded')

                        # Save Action
                        ui.button('LƯU TẤT CẢ THAY ĐỔI', icon='save', on_click=_update_profile).classes('w-full py-4 btn-primary shadow-xl text-lg')

        await _load_profile()
