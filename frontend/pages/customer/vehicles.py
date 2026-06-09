"""
Customer Vehicles Management Page - NiceGUI
"""
from typing import Any, Dict, List

from nicegui import ui

from core.auth import require_role
from components.page_layout import page_layout
from services.rescue_api import (
    add_customer_vehicle,
    delete_customer_vehicle,
    get_customer_vehicles,
    update_customer_vehicle,
)


FUEL_CONFIG = {
    "Xăng": {"label": "Xăng", "icon": "local_gas_station", "classes": "bg-blue-50 text-blue-700"},
    "Dầu": {"label": "Dầu", "icon": "local_gas_station", "classes": "bg-slate-100 text-slate-700"},
    "Điện": {"label": "Điện", "icon": "electric_car", "classes": "bg-emerald-50 text-emerald-700"},
    "Hybrid": {"label": "Hybrid", "icon": "energy_savings_leaf", "classes": "bg-amber-50 text-amber-700"},
}


def create_vehicles_page():
    """Register /customer/vehicles route."""

    @ui.page("/customer/vehicles")
    async def vehicles_page():
        if not require_role("customer"):
            return

        state = {
            "vehicles": [],
            "search": "",
            "brand": "all",
            "fuel": "all",
            "year": "all",
        }

        def fuel_config(fuel: str) -> Dict[str, str]:
            return FUEL_CONFIG.get(fuel, {"label": fuel or "--", "icon": "local_gas_station", "classes": "bg-slate-100 text-slate-700"})

        def vehicle_image(v: Dict[str, Any]):
            return v.get("image_url") or v.get("photo_url") or v.get("avatar_url") or v.get("image")

        def is_default_vehicle(v: Dict[str, Any]) -> bool:
            return bool(v.get("is_default") or v.get("default") or v.get("is_primary"))

        def brand_initials(brand: str) -> str:
            words = [w for w in (brand or "XE").split() if w]
            return "".join(w[0].upper() for w in words[:2]) or "XE"

        def filtered_vehicles() -> List[Dict[str, Any]]:
            query = state["search"].strip().lower()
            result = []
            for v in state["vehicles"]:
                if query and query not in (v.get("license_plate") or "").lower():
                    continue
                if state["brand"] != "all" and v.get("brand") != state["brand"]:
                    continue
                if state["fuel"] != "all" and v.get("fuel_type") != state["fuel"]:
                    continue
                if state["year"] != "all" and str(v.get("year")) != str(state["year"]):
                    continue
                result.append(v)
            return result

        def update_filter_options():
            brands = sorted({v.get("brand") for v in state["vehicles"] if v.get("brand")})
            fuels = sorted({v.get("fuel_type") for v in state["vehicles"] if v.get("fuel_type")})
            years = sorted({str(v.get("year")) for v in state["vehicles"] if v.get("year")}, reverse=True)

            brand_filter.options = {"all": "Tất cả hãng", **{b: b for b in brands}}
            fuel_filter.options = {"all": "Tất cả nhiên liệu", **{f: f for f in fuels}}
            year_filter.options = {"all": "Tất cả năm", **{y: y for y in years}}
            brand_filter.update()
            fuel_filter.update()
            year_filter.update()

        with page_layout("/customer/vehicles", title="Quản Lý Xe Cá Nhân"):
            with ui.column().classes("w-full gap-5"):
                with ui.row().classes("w-full items-center justify-between gap-4"):
                    with ui.column().classes("gap-1"):
                        ui.label("Danh sách phương tiện").classes(
                            "text-3xl font-bold text-slate-900 font-outfit"
                        )
                        ui.label("Quản lý xe cá nhân để đặt cứu hộ nhanh và chính xác hơn.").classes(
                            "text-sm text-slate-500"
                        )

                    ui.button(
                        "Thêm xe mới",
                        icon="add",
                        on_click=lambda: open_vehicle_dialog(),
                    ).classes(
                        "rounded-xl bg-blue-600 px-5 py-3 font-bold text-white shadow-sm hover:bg-blue-700"
                    ).props("unelevated")

                stats_container = ui.row().classes("w-full gap-3 flex-wrap")

                with ui.card().classes(
                    "w-full rounded-2xl border border-slate-100 bg-white p-4 shadow-sm "
                    "transition-all hover:-translate-y-0.5 hover:border-blue-100 hover:shadow-md"
                ):
                    with ui.row().classes("w-full items-center gap-3 flex-wrap"):
                        search_input = ui.input(
                            placeholder="Tìm theo biển số xe..."
                        ).classes("min-w-[260px] flex-1").props("outlined dense rounded clearable")
                        search_input.on("update:model-value", lambda: set_filter("search", search_input.value or ""))

                        brand_filter = ui.select(
                            options={"all": "Tất cả hãng"},
                            value="all",
                            label="Hãng xe",
                            on_change=lambda: set_filter("brand", brand_filter.value),
                        ).classes("w-48").props("outlined dense rounded")

                        fuel_filter = ui.select(
                            options={"all": "Tất cả nhiên liệu"},
                            value="all",
                            label="Nhiên liệu",
                            on_change=lambda: set_filter("fuel", fuel_filter.value),
                        ).classes("w-48").props("outlined dense rounded")

                        year_filter = ui.select(
                            options={"all": "Tất cả năm"},
                            value="all",
                            label="Năm sản xuất",
                            on_change=lambda: set_filter("year", year_filter.value),
                        ).classes("w-44").props("outlined dense rounded")

                        refresh_btn = ui.button(
                            icon="refresh",
                            on_click=lambda: refresh_vehicles(),
                        ).props("flat round color=primary")

                vehicles_container = ui.row().classes("w-full gap-4 items-stretch")

        def set_filter(key: str, value):
            state[key] = value or "all"
            render()

        def render_stats():
            stats_container.clear()
            vehicles = state["vehicles"]
            stat_items = [
                (
                    "Tổng số xe",
                    len(vehicles),
                    "directions_car",
                    "text-blue-600",
                    "bg-blue-50",
                    "border-blue-100",
                    "bg-blue-100",
                ),
                (
                    "Xe xăng",
                    sum(1 for v in vehicles if v.get("fuel_type") == "Xăng"),
                    "local_gas_station",
                    "text-blue-600",
                    "bg-sky-50",
                    "border-sky-100",
                    "bg-sky-100",
                ),
                (
                    "Xe điện",
                    sum(1 for v in vehicles if v.get("fuel_type") == "Điện"),
                    "electric_car",
                    "text-emerald-600",
                    "bg-emerald-50",
                    "border-emerald-100",
                    "bg-emerald-100",
                ),
                (
                    "Xe hybrid",
                    sum(1 for v in vehicles if v.get("fuel_type") == "Hybrid"),
                    "bolt",
                    "text-amber-600",
                    "bg-amber-50",
                    "border-amber-100",
                    "bg-amber-100",
                ),
            ]
            with stats_container:
                for label, value, icon, color, card_bg, border, icon_bg in stat_items:
                    with ui.card().classes(
                        f"flex-1 min-w-[180px] rounded-2xl border {border} {card_bg} p-4 shadow-sm "
                        "transition-all hover:-translate-y-0.5 hover:shadow-md"
                    ):
                        with ui.row().classes("w-full items-center justify-between gap-4"):
                            with ui.column().classes("gap-3"):
                                ui.label(label).classes("text-xs font-bold uppercase text-slate-400")
                                with ui.element("div").classes(
                                    f"h-11 w-11 rounded-2xl {icon_bg} flex items-center justify-center"
                                ):
                                    ui.icon(icon, size="1.35rem").classes(color)
                            ui.label(str(value)).classes("text-3xl font-black text-slate-900")

        def render_empty(filtered: bool = False):
            with vehicles_container:
                with ui.column().classes(
                    "w-full items-center justify-center rounded-3xl border border-dashed "
                    "border-slate-300 bg-white py-16 shadow-sm"
                ):
                    ui.icon("directions_car", size="4rem").classes("text-slate-200")
                    ui.label(
                        "Không tìm thấy phương tiện phù hợp" if filtered else "Bạn chưa đăng ký phương tiện nào"
                    ).classes("text-xl font-bold text-slate-700")
                    ui.label(
                        "Thử đổi bộ lọc hoặc thêm xe mới." if filtered else "Thêm xe để sử dụng dịch vụ cứu hộ nhanh hơn."
                    ).classes("text-sm text-slate-500")
                    ui.button(
                        "Thêm xe ngay",
                        icon="add",
                        on_click=lambda: open_vehicle_dialog(),
                    ).classes("mt-4 rounded-xl bg-blue-600 px-5 py-2.5 font-bold text-white")

        def render():
            render_stats()
            vehicles_container.clear()
            vehicles = filtered_vehicles()
            if not vehicles:
                render_empty(filtered=bool(state["vehicles"]))
                return

            with vehicles_container:
                for index, v in enumerate(vehicles):
                    render_vehicle_card(v, index)

        def render_vehicle_media(v: Dict[str, Any]):
            image = vehicle_image(v)
            if image:
                ui.image(image).classes("h-16 w-16 rounded-2xl object-cover border border-slate-100")
                return

            with ui.element("div").classes(
                "h-16 w-16 rounded-2xl bg-blue-50 flex items-center justify-center border border-blue-100"
            ):
                ui.label(brand_initials(v.get("brand", ""))).classes("text-lg font-black text-blue-700")

        def render_vehicle_card(v: Dict[str, Any], index: int):
            fuel = fuel_config(v.get("fuel_type"))
            is_default = is_default_vehicle(v)

            with ui.card().classes(
                "w-full md:w-[calc(50%-0.5rem)] xl:w-[calc(33.333%-0.75rem)] "
                "rounded-2xl border border-slate-100 bg-white p-4 shadow-sm "
                "transition-all hover:-translate-y-0.5 hover:border-blue-100 hover:shadow-lg"
            ):
                with ui.column().classes("w-full gap-4"):
                    with ui.row().classes("w-full items-start justify-between gap-3"):
                        with ui.row().classes("items-center gap-3 min-w-0"):
                            render_vehicle_media(v)
                            with ui.column().classes("gap-1 min-w-0"):
                                with ui.row().classes("items-center gap-2 flex-wrap"):
                                    ui.label(v.get("license_plate", "--")).classes(
                                        "text-xl font-black tracking-wide text-slate-900"
                                    )
                                    if is_default:
                                        ui.badge("Xe mặc định").classes(
                                            "rounded-full bg-emerald-50 px-2 py-1 text-emerald-700"
                                        )
                                ui.label(f"{v.get('brand', '--')} {v.get('model', '')}".strip()).classes(
                                    "text-sm font-semibold text-slate-500"
                                )

                        with ui.button(icon="more_horiz").props("flat round dense"):
                            with ui.menu().classes("rounded-xl shadow-lg"):
                                ui.menu_item("Sửa thông tin", lambda v=v: open_vehicle_dialog(v))
                                ui.menu_item("Xóa xe", lambda v=v: confirm_delete(v))

                    with ui.row().classes("w-full gap-2 flex-wrap"):
                        with ui.row().classes(f"items-center gap-1 rounded-full px-3 py-1 {fuel['classes']}"):
                            ui.icon(fuel["icon"], size="0.9rem")
                            ui.label(fuel["label"]).classes("text-xs font-bold")
                        with ui.row().classes("items-center gap-1 rounded-full bg-slate-100 px-3 py-1 text-slate-600"):
                            ui.icon("calendar_month", size="0.9rem")
                            ui.label(f"Năm {v.get('year', '--')}").classes("text-xs font-bold")

                    ui.separator()

                    with ui.row().classes("w-full gap-3"):
                        info_chip("badge", "Biển số", v.get("license_plate"))
                        info_chip("factory", "Hãng", v.get("brand"))
                        info_chip("commute", "Dòng", v.get("model"))

                    with ui.row().classes("w-full justify-end gap-2"):
                        ui.button(
                            "Sửa",
                            icon="edit",
                            on_click=lambda v=v: open_vehicle_dialog(v),
                        ).classes("rounded-xl px-3 font-semibold text-blue-700 hover:bg-blue-50").props("flat")
                        ui.button(
                            "Xóa",
                            icon="delete",
                            on_click=lambda v=v: confirm_delete(v),
                        ).classes("rounded-xl px-3 font-semibold text-red-600 hover:bg-red-50").props("flat")

        def info_chip(icon: str, label: str, value):
            with ui.column().classes("flex-1 min-w-[90px] gap-0 rounded-xl bg-slate-50 px-3 py-2"):
                with ui.row().classes("items-center gap-1"):
                    ui.icon(icon, size="0.9rem").classes("text-slate-400")
                    ui.label(label).classes("text-[11px] font-bold uppercase text-slate-400")
                ui.label(str(value or "--")).classes("text-sm font-bold text-slate-700 truncate")

        async def refresh_vehicles():
            refresh_btn.props("loading")
            try:
                state["vehicles"] = await get_customer_vehicles()
                update_filter_options()
                render()
            except Exception as e:
                ui.notify(f"Lỗi tải danh sách xe: {e}", type="negative")
            finally:
                refresh_btn.props(remove="loading")

        def confirm_delete(v):
            with ui.dialog() as d, ui.card().classes("w-[440px] max-w-full rounded-3xl p-7 shadow-xl"):
                with ui.column().classes("w-full gap-3"):
                    with ui.row().classes("items-center gap-3"):
                        with ui.element("div").classes(
                            "h-12 w-12 rounded-2xl bg-red-50 flex items-center justify-center"
                        ):
                            ui.icon("warning", size="1.8rem").classes("text-red-600")

                        ui.label("Xác nhận xóa xe").classes("text-xl font-black text-slate-900")

                    ui.label(
                        f"Bạn có chắc chắn muốn xóa xe {v['license_plate']} không?"
                    ).classes("text-slate-500")

                    with ui.row().classes("w-full justify-end gap-3 mt-5"):
                        ui.button("Hủy", on_click=d.close).props("flat").classes("rounded-xl px-5 font-bold")

                        async def do_delete():
                            if await delete_customer_vehicle(v["id"]):
                                ui.notify("Đã xóa xe", type="positive")
                                d.close()
                                await refresh_vehicles()

                        ui.button("Xóa", on_click=do_delete).classes(
                            "rounded-xl bg-red-600 px-6 font-bold text-white"
                        )

            d.open()

        def open_vehicle_dialog(v=None):
            is_edit = v is not None

            with ui.dialog() as d, ui.card().classes("w-[460px] max-w-full rounded-3xl p-7 shadow-xl"):
                with ui.column().classes("w-full gap-4"):
                    with ui.row().classes("items-center gap-3 mb-2"):
                        with ui.element("div").classes(
                            "h-14 w-14 rounded-2xl bg-blue-50 flex items-center justify-center"
                        ):
                            ui.icon("edit" if is_edit else "add_circle", size="2rem").classes("text-blue-600")

                        with ui.column().classes("gap-0"):
                            ui.label("Sửa thông tin xe" if is_edit else "Thêm xe mới").classes(
                                "text-2xl font-black text-slate-900"
                            )
                            ui.label("Cập nhật thông tin phương tiện của bạn").classes(
                                "text-sm text-slate-500"
                            )

                    plate = ui.input("Biển số *", value=v["license_plate"] if is_edit else "").classes("w-full").props(
                        "outlined rounded stack-label"
                    )
                    brand = ui.input("Hãng xe *", value=v["brand"] if is_edit else "").classes("w-full").props(
                        "outlined rounded stack-label"
                    )
                    model = ui.input("Dòng xe *", value=v["model"] if is_edit else "").classes("w-full").props(
                        "outlined rounded stack-label"
                    )
                    year = ui.number("Năm sản xuất *", value=v["year"] if is_edit else 2024).classes("w-full").props(
                        "outlined rounded stack-label"
                    )
                    fuel = ui.select(
                        ["Xăng", "Dầu", "Điện", "Hybrid"],
                        label="Loại nhiên liệu",
                        value=v["fuel_type"] if is_edit else "Xăng",
                    ).classes("w-full").props("outlined rounded stack-label")

                    with ui.row().classes("w-full justify-end gap-3 mt-4"):
                        ui.button("Hủy", on_click=d.close).props("flat").classes("rounded-xl px-5 font-bold")

                        async def save():
                            if not plate.value or not brand.value or not model.value or not year.value:
                                ui.notify("Vui lòng điền đầy đủ thông tin", type="warning")
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

                        ui.button("Lưu", on_click=save).classes(
                            "rounded-xl bg-blue-600 px-8 font-bold text-white"
                        )

            d.open()

        await refresh_vehicles()
