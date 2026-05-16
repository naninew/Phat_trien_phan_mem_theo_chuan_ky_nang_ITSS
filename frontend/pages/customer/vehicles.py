"""
Customer Vehicles Management Page - NiceGUI
"""
from nicegui import ui
from core.auth import require_role
from components.page_layout import page_layout
from services.rescue_api import (
    get_customer_vehicles,
    add_customer_vehicle,
    update_customer_vehicle,
    delete_customer_vehicle
)

def create_vehicles_page():
    """Register /customer/vehicles route."""

    @ui.page('/customer/vehicles')
    async def vehicles_page():
        if not require_role("customer"):
            return

        with page_layout("/customer/vehicles", title="Quản Lý Xe Cá Nhân"):
            
            with ui.row().classes("w-full items-center justify-between mb-4"):
                ui.label("Danh sách phương tiện của bạn").classes("text-on-surface-variant")
                ui.button("THÊM XE MỚI", icon="add", on_click=lambda: open_vehicle_dialog()) \
                    .classes("rounded-xl bg-primary text-white font-bold px-6")

            # Vehicles container
            vehicles_container = ui.row().classes("w-full gap-6")
            
            async def refresh_vehicles():
                vehicles_container.clear()
                vehicles = await get_customer_vehicles()
                
                with vehicles_container:
                    if not vehicles:
                        with ui.column().classes("w-full items-center py-20 bg-surface-variant/20 rounded-3xl border-2 border-dashed border-surface-variant"):
                            ui.icon("directions_car", size="5rem").classes("opacity-20")
                            ui.label("Bạn chưa đăng ký phương tiện nào").classes("text-on-surface-variant italic")
                    else:
                        for v in vehicles:
                            with ui.card().classes("w-80 rounded-2xl p-6 shadow-sm border border-surface-variant/30 hover:shadow-md transition-all"):
                                with ui.row().classes("w-full justify-between items-start"):
                                    ui.label(v['license_plate']).classes("text-2xl font-black text-primary font-outfit")
                                    ui.badge(v['fuel_type'].upper()).props("color=primary-container text-color=primary")
                                
                                ui.label(f"{v['brand']} {v['model']}").classes("text-lg font-bold text-on-surface mt-2")
                                ui.label(f"Năm sản xuất: {v['year']}").classes("text-sm text-on-surface-variant")
                                
                                ui.separator().classes("my-4")
                                
                                with ui.row().classes("w-full justify-end gap-2"):
                                    ui.button(icon="edit", on_click=lambda v=v: open_vehicle_dialog(v)).props("flat round color=primary")
                                    ui.button(icon="delete", on_click=lambda v=v: confirm_delete(v)).props("flat round color=error")

            def confirm_delete(v):
                with ui.dialog() as d, ui.card().classes("p-6 rounded-2xl"):
                    ui.label("Xác nhận xóa?").classes("text-xl font-bold")
                    ui.label(f"Bạn có chắc chắn muốn xóa xe {v['license_plate']}?").classes("text-on-surface-variant mb-6")
                    with ui.row().classes("w-full justify-end gap-3"):
                        ui.button("HỦY", on_click=d.close).props("flat")
                        async def do_delete():
                            if await delete_customer_vehicle(v['id']):
                                ui.notify("Đã xóa xe", type="positive")
                                d.close()
                                await refresh_vehicles()
                        ui.button("XÓA", on_click=do_delete).classes("bg-error text-white")
                d.open()

            def open_vehicle_dialog(v=None):
                is_edit = v is not None
                with ui.dialog() as d, ui.card().classes("w-[400px] p-8 rounded-3xl"):
                    ui.label("Sửa thông tin xe" if is_edit else "Thêm xe mới").classes("text-2xl font-bold mb-6 font-outfit text-primary")
                    
                    plate = ui.input("Biển số *", value=v['license_plate'] if is_edit else "").classes("w-full mb-2").props("outlined rounded")
                    brand = ui.input("Hãng xe *", value=v['brand'] if is_edit else "").classes("w-full mb-2").props("outlined rounded")
                    model = ui.input("Dòng xe *", value=v['model'] if is_edit else "").classes("w-full mb-2").props("outlined rounded")
                    year = ui.number("Năm sản xuất *", value=v['year'] if is_edit else 2024).classes("w-full mb-2").props("outlined rounded")
                    fuel = ui.select(["Xăng", "Dầu", "Điện"], label="Loại nhiên liệu", value=v['fuel_type'] if is_edit else "Xăng").classes("w-full mb-6").props("outlined rounded")
                    
                    with ui.row().classes("w-full justify-end gap-4"):
                        ui.button("HỦY", on_click=d.close).props("flat")
                        async def save():
                            data = {
                                "license_plate": plate.value,
                                "brand": brand.value,
                                "model": model.value,
                                "year": int(year.value),
                                "fuel_type": fuel.value
                            }
                            if is_edit:
                                res = await update_customer_vehicle(v['id'], data)
                            else:
                                res = await add_customer_vehicle(data)
                            
                            if res:
                                ui.notify("Lưu thành công", type="positive")
                                d.close()
                                await refresh_vehicles()
                        ui.button("LƯU", on_click=save).classes("bg-primary text-white px-8 rounded-xl")
                d.open()

            await refresh_vehicles()
