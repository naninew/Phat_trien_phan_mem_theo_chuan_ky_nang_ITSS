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
    delete_customer_vehicle,
)


def create_vehicles_page():
    """Register /customer/vehicles route."""

    @ui.page("/customer/vehicles")
    async def vehicles_page():
        if not require_role("customer"):
            return

        ui.add_head_html("""
        <style>
            .vehicle-card {
                width: 300px;
                height: 300px;
                background: #ffffff;
                border-radius: 26px;
                overflow: hidden;
                border: 1px solid #e2e8f0;
                box-shadow: 0 10px 28px rgba(15, 23, 42, 0.08);
                transition: all 0.25s ease;
            }

            .vehicle-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 18px 42px rgba(15, 23, 42, 0.14);
            }

            .vehicle-card-header {
                height: 120px;
                padding: 20px;
                background: #dbeafe;
                color: #1e3a8a;
            }

            .vehicle-plate {
                font-size: 24px;
                font-weight: 900;
                line-height: 1.1;
                letter-spacing: 0.03em;
            }

            .vehicle-name {
                font-size: 14px;
                font-weight: 600;
                opacity: 0.92;
                margin-top: 5px;
            }

            .vehicle-icon-box {
                width: 60px;
                height: 60px;
                border-radius: 18px;
                display: flex;
                align-items: center;
                justify-content: center;
                background: rgba(255, 255, 255, 0.22);
            }

            .fuel-badge {
                padding: 4px 12px;
                border-radius: 999px;
                background: rgba(255, 255, 255, 0.22);
                color: #1e40af;
                font-size: 11px;
                font-weight: 800;
                         
            }

            .vehicle-year {
                font-size: 13px;
                font-weight: 800;
            }

            .vehicle-body {
                height: 180px;
                padding: 16px 18px;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
            }

            .vehicle-info {
                display: flex;
                flex-direction: column;
                gap: 6px;
            }

            .vehicle-info-row {
                display: flex;
                align-items: center;
                gap: 8px;
                color: #334155;
                font-size: 13px;
                font-weight: 600;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }

            .vehicle-info-row .q-icon {
                color: #2563eb;
                font-size: 18px;
            }

            .vehicle-actions {
                display: flex;
                gap: 10px;
            }

            .vehicle-action-edit,
            .vehicle-action-delete {
                flex: 1;
                height: 36px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 800;
            }

            .vehicle-action-edit {
                background: #eff6ff;
                color: #2563eb;
            }

            .vehicle-action-delete {
                background: #fef2f2;
                color: #dc2626;
            }

            .empty-box {
                width: 100%;
                border-radius: 28px;
                border: 2px dashed #cbd5e1;
                background: linear-gradient(135deg, #f8fafc, #eef6ff);
            }

            .dialog-card {
                width: 440px;
                padding: 32px;
                border-radius: 30px;
                box-shadow: 0 25px 70px rgba(15, 23, 42, 0.18);
            }
        </style>
        """)

        with page_layout("/customer/vehicles", title="Quản Lý Xe Cá Nhân"):

            with ui.row().classes("w-full items-center justify-between mb-8"):
                with ui.column().classes("gap-1"):
                    ui.label("Danh sách phương tiện").classes(
                        "text-2xl font-black text-gray-900"
                    )
                    ui.label("Quản lý các xe đã đăng ký trong hệ thống cứu hộ").classes(
                        "text-sm text-gray-500"
                    )

                ui.button(
                    "THÊM XE MỚI",
                    icon="add",
                    on_click=lambda: open_vehicle_dialog(),
                ).classes(
                    "rounded-2xl bg-primary text-white font-bold px-6 py-3 shadow-md hover:shadow-lg"
                )

            vehicles_container = ui.row().classes(
                "w-full gap-6 justify-center items-start"
            )

            async def refresh_vehicles():
                vehicles_container.clear()
                vehicles = await get_customer_vehicles()

                with vehicles_container:
                    if not vehicles:
                        with ui.column().classes(
                            "empty-box items-center justify-center py-24"
                        ):
                            ui.icon("directions_car", size="3rem").classes(
                                "text-blue-300 mb-2"
                            )
                            ui.label("Bạn chưa đăng ký phương tiện nào").classes(
                                "text-xl font-bold text-gray-700"
                            )
                            ui.label(
                                "Hãy thêm xe để sử dụng dịch vụ cứu hộ nhanh hơn"
                            ).classes("text-sm text-gray-500")

                            ui.button(
                                "THÊM XE NGAY",
                                icon="add",
                                on_click=lambda: open_vehicle_dialog(),
                            ).classes(
                                "mt-5 rounded-2xl bg-primary text-white font-bold px-6 py-3"
                            )

                    else:
                        for v in vehicles:
                            with ui.element("div").classes("vehicle-card"):

                                with ui.element("div").classes("vehicle-card-header"):
                                    with ui.row().classes(
                                        "w-full justify-between items-start"
                                    ):
                                        with ui.column().classes("gap-0"):
                                            ui.label(v["license_plate"]).classes(
                                                "vehicle-plate"
                                            )
                                            ui.label(
                                                f'{v["brand"]} {v["model"]}'
                                            ).classes("vehicle-name")

                                        with ui.element("div").classes("vehicle-icon-box"):
                                            ui.icon(
                                                "directions_car",
                                                size="2rem",
                                            ).classes("text-blue-900")

                                    with ui.row().classes(
                                        "w-full justify-between items-center mt-4"
                                    ):
                                        ui.label(v["fuel_type"].upper()).classes(
                                            "fuel-badge"
                                        )
                                        ui.label(f'Năm {v["year"]}').classes(
                                            "vehicle-year"
                                        )

                                with ui.element("div").classes("vehicle-body"):

                                    with ui.element("div").classes("vehicle-info"):
                                        with ui.element("div").classes("vehicle-info-row"):
                                            ui.icon("badge")
                                            ui.label(f"Biển số: {v['license_plate']}")

                                        with ui.element("div").classes("vehicle-info-row"):
                                            ui.icon("factory")
                                            ui.label(f"Hãng xe: {v['brand']}")

                                        with ui.element("div").classes("vehicle-info-row"):
                                            ui.icon("commute")
                                            ui.label(f"Dòng xe: {v['model']}")

                                        with ui.element("div").classes("vehicle-info-row"):
                                            ui.icon("local_gas_station")
                                            ui.label(f"Nhiên liệu: {v['fuel_type']}")

                                    with ui.element("div").classes("vehicle-actions"):
                                        ui.button(
                                            "Sửa",
                                            icon="edit",
                                            on_click=lambda v=v: open_vehicle_dialog(v),
                                        ).props("flat dense").classes("vehicle-action-edit")

                                        ui.button(
                                            "Xóa",
                                            icon="delete",
                                            on_click=lambda v=v: confirm_delete(v),
                                        ).props("flat dense").classes("vehicle-action-delete")

            def confirm_delete(v):
                with ui.dialog() as d, ui.card().classes("dialog-card"):
                    with ui.column().classes("w-full gap-3"):
                        with ui.row().classes("items-center gap-3"):
                            with ui.element("div").classes(
                                "w-12 h-12 rounded-2xl bg-red-100 flex items-center justify-center"
                            ):
                                ui.icon("warning", size="1.8rem").classes(
                                    "text-red-600"
                                )

                            ui.label("Xác nhận xóa xe").classes(
                                "text-xl font-black text-gray-900"
                            )

                        ui.label(
                            f"Bạn có chắc chắn muốn xóa xe {v['license_plate']} không?"
                        ).classes("text-gray-500")

                        with ui.row().classes("w-full justify-end gap-3 mt-5"):
                            ui.button("HỦY", on_click=d.close).props("flat").classes(
                                "rounded-xl px-5 font-bold"
                            )

                            async def do_delete():
                                if await delete_customer_vehicle(v["id"]):
                                    ui.notify("Đã xóa xe", type="positive")
                                    d.close()
                                    await refresh_vehicles()

                            ui.button("XÓA", on_click=do_delete).classes(
                                "bg-red-600 text-white rounded-xl px-6 font-bold"
                            )

                d.open()

            def open_vehicle_dialog(v=None):
                is_edit = v is not None

                with ui.dialog() as d, ui.card().classes("dialog-card"):
                    with ui.column().classes("w-full gap-4"):
                        with ui.row().classes("items-center gap-3 mb-2"):
                            with ui.element("div").classes(
                                "w-14 h-14 rounded-2xl bg-blue-100 flex items-center justify-center"
                            ):
                                ui.icon(
                                    "edit" if is_edit else "add_circle",
                                    size="2rem",
                                ).classes("text-primary")

                            with ui.column().classes("gap-0"):
                                ui.label(
                                    "Sửa thông tin xe" if is_edit else "Thêm xe mới"
                                ).classes("text-2xl font-black text-gray-900")
                                ui.label(
                                    "Cập nhật thông tin phương tiện của bạn"
                                ).classes("text-sm text-gray-500")

                        plate = ui.input(
                            "Biển số *",
                            value=v["license_plate"] if is_edit else "",
                        ).classes("w-full").props("outlined rounded")

                        brand = ui.input(
                            "Hãng xe *",
                            value=v["brand"] if is_edit else "",
                        ).classes("w-full").props("outlined rounded")

                        model = ui.input(
                            "Dòng xe *",
                            value=v["model"] if is_edit else "",
                        ).classes("w-full").props("outlined rounded")

                        year = ui.number(
                            "Năm sản xuất *",
                            value=v["year"] if is_edit else 2024,
                        ).classes("w-full").props("outlined rounded")

                        fuel = ui.select(
                            ["Xăng", "Dầu", "Điện"],
                            label="Loại nhiên liệu",
                            value=v["fuel_type"] if is_edit else "Xăng",
                        ).classes("w-full").props("outlined rounded")

                        with ui.row().classes("w-full justify-end gap-3 mt-5"):
                            ui.button("HỦY", on_click=d.close).props("flat").classes(
                                "rounded-xl px-5 font-bold"
                            )

                            async def save():
                                if (
                                    not plate.value
                                    or not brand.value
                                    or not model.value
                                    or not year.value
                                ):
                                    ui.notify(
                                        "Vui lòng điền đầy đủ thông tin",
                                        type="warning",
                                    )
                                    return

                                data = {
                                    "license_plate": plate.value,
                                    "brand": brand.value,
                                    "model": model.value,
                                    "year": int(year.value),
                                    "fuel_type": fuel.value,
                                }

                                if is_edit:
                                    res = await update_customer_vehicle(v["id"], data)
                                else:
                                    res = await add_customer_vehicle(data)

                                if res:
                                    ui.notify("Lưu thành công", type="positive")
                                    d.close()
                                    await refresh_vehicles()

                            ui.button("LƯU", on_click=save).classes(
                                "bg-primary text-white px-8 rounded-xl font-bold"
                            )

                d.open()

            await refresh_vehicles()