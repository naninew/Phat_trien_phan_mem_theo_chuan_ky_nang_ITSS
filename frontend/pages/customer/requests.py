"""
Trang danh sách yêu cầu cứu hộ của khách hàng.
UI redesign - hiện đại, đồng bộ, clean style.
"""

from nicegui import ui
from typing import Dict, Any
from datetime import datetime

from core.auth import require_role
from components.page_layout import page_layout
from services.rescue_api import get_my_requests, cancel_request


def create_requests_page():

    @ui.page('/customer/requests')
    async def requests_page():

        if not require_role("customer"):
            return

        # ============================================================
        # STATUS CONFIG
        # ============================================================

        STATUS_MAP = {
            "PENDING": {
                "label": "Chờ tiếp nhận",
                "badge": "bg-amber-100 text-amber-700",
                "bar": "bg-amber-500",
                "icon": "schedule"
            },
            "ASSIGNED": {
                "label": "Đã phân công",
                "badge": "bg-sky-100 text-sky-700",
                "bar": "bg-sky-500",
                "icon": "assignment"
            },
            "IN_PROGRESS": {
                "label": "Đang xử lý",
                "badge": "bg-indigo-100 text-indigo-700",
                "bar": "bg-indigo-500",
                "icon": "build_circle"
            },
            "COMPLETED": {
                "label": "Hoàn thành",
                "badge": "bg-emerald-100 text-emerald-700",
                "bar": "bg-emerald-500",
                "icon": "check_circle"
            },
            "CANCELLED": {
                "label": "Đã hủy",
                "badge": "bg-gray-100 text-gray-600",
                "bar": "bg-gray-400",
                "icon": "cancel"
            },
        }

        # ============================================================
        # PAGE
        # ============================================================

        with page_layout("/customer/requests", title="Yêu Cầu Của Tôi"):

            # ========================================================
            # HERO HEADER
            # ========================================================

            with ui.card().classes(
    "w-full rounded-[28px] border border-blue-100 bg-blue-50/80 p-8 shadow-sm"
):

                with ui.row().classes(
        "w-full items-center justify-between"
    ):

                    with ui.column().classes("gap-1"):

                        ui.label(
                "Danh Sách Yêu Cầu"
            ).classes(
                "text-4xl font-bold text-slate-800"
            )

                        ui.label(
                "Theo dõi trạng thái cứu hộ và quản lý các yêu cầu của bạn"
            ).classes(
                "text-slate-500 text-base"
            )

                    ui.button(
            "GỬI YÊU CẦU MỚI",
            on_click=lambda: ui.navigate.to(
                "/customer/find-rescue"
            )
        ).classes(
            "bg-blue-600 text-white font-bold px-6 py-3 rounded-xl shadow-sm hover:bg-blue-700 transition-all"
        ).props(
            "unelevated"
        )

            # ========================================================
            # TOOLBAR
            # ========================================================

            with ui.card().classes(
                "w-full rounded-2xl shadow-sm border border-gray-100 p-4"
            ):

                with ui.row().classes(
                    "w-full items-center gap-4"
                ):

                    with ui.row().classes(
                        "items-center gap-2"
                    ):
                        ui.icon(
                            "filter_alt",
                            color="indigo"
                        )

                        ui.label(
                            "Lọc trạng thái"
                        ).classes(
                            "font-semibold text-gray-700"
                        )

                    status_filter = ui.select(
                        options={
                            'all': 'Tất cả',
                            'PENDING': 'Chờ tiếp nhận',
                            'ASSIGNED': 'Đã phân công',
                            'IN_PROGRESS': 'Đang xử lý',
                            'COMPLETED': 'Hoàn thành',
                            'CANCELLED': 'Đã hủy'
                        },
                        value='all',
                        on_change=lambda: _load_data()
                    ).classes(
                        "w-64"
                    ).props(
                        "outlined dense rounded"
                    )

                    ui.space()

                    ui.label(
                        "Tự động cập nhật mỗi 30 giây"
                    ).classes(
                        "text-sm text-gray-400"
                    )

                    refresh_btn = ui.button(
                        icon="refresh",
                        on_click=lambda: _load_data()
                    ).props(
                        "flat round color=indigo"
                    )

            # ========================================================
            # LIST CONTAINER
            # ========================================================

            list_container = ui.column().classes(
                "w-full gap-5"
            )

        # ============================================================
        # LOAD DATA
        # ============================================================

        async def _load_data():

            refresh_btn.props("loading")

            list_container.clear()

            try:

                all_reqs = await get_my_requests()

                current_filter = status_filter.value

                if current_filter != 'all':
                    reqs = [
                        r for r in all_reqs
                        if r['status'] == current_filter
                    ]
                else:
                    reqs = all_reqs

                # ====================================================
                # EMPTY STATE
                # ====================================================

                if not reqs:

                    with list_container:

                        with ui.card().classes(
                            "w-full rounded-3xl shadow-sm border border-dashed border-gray-300 p-20 items-center"
                        ):

                            ui.icon(
                                "inbox",
                                size="5rem"
                            ).classes(
                                "text-gray-200"
                            )

                            ui.label(
                                "Không có yêu cầu nào"
                            ).classes(
                                "text-2xl font-bold text-gray-500 mt-4"
                            )

                            ui.label(
                                "Các yêu cầu cứu hộ của bạn sẽ hiển thị tại đây"
                            ).classes(
                                "text-gray-400"
                            )

                            ui.button(
                                "Tạo yêu cầu mới",
                                icon="add",
                                on_click=lambda: ui.navigate.to(
                                    "/customer/find-rescue"
                                )
                            ).classes(
                                "mt-6 bg-indigo-600 text-white px-6 py-3 rounded-xl font-bold"
                            )

                else:

                    for request in reqs:
                        _render_request_item(
                            list_container,
                            request
                        )

            except Exception as e:

                ui.notify(
                    f"Lỗi tải dữ liệu: {e}",
                    type="negative"
                )

            finally:

                refresh_btn.props(remove="loading")

        # ============================================================
        # REQUEST CARD
        # ============================================================

        def _render_request_item(
            container,
            r: Dict[str, Any]
        ):

            config = STATUS_MAP.get(
                r['status'],
                STATUS_MAP["PENDING"]
            )

            # ========================================================
            # FORMAT TIME
            # ========================================================

            try:

                dt = datetime.fromisoformat(
                    r['created_at'].replace(
                        'Z',
                        '+00:00'
                    )
                )

                time_str = dt.strftime(
                    "%H:%M • %d/%m/%Y"
                )

            except Exception:

                time_str = r['created_at']

            # ========================================================
            # SERVICE NAME
            # ========================================================

            service_name = "Dịch vụ cứu hộ"

            if r.get("services") and len(r["services"]) > 0:

                service_name = r["services"][0].get(
                    "service_name",
                    "Dịch vụ cứu hộ"
                )

            elif r.get("incident_type"):

                service_name = r["incident_type"]

            # ========================================================
            # PRICE
            # ========================================================

            price = r.get("agreed_price")

            with container:

                with ui.card().classes(
                    "w-full rounded-[24px] border border-gray-100 shadow-sm hover:shadow-lg transition-all duration-300 overflow-hidden"
                ):

                    with ui.row().classes(
                        "w-full no-wrap"
                    ):

                        # =================================================
                        # LEFT STATUS BAR
                        # =================================================

                        ui.element("div").classes(
                            f"w-2 {config['bar']}"
                        )

                        # =================================================
                        # MAIN CONTENT
                        # =================================================

                        with ui.column().classes(
                            "flex-1 p-6 gap-5"
                        ):

                            # =============================================
                            # TOP
                            # =============================================

                            with ui.row().classes(
                                "w-full justify-between items-start"
                            ):

                                with ui.column().classes(
                                    "gap-2"
                                ):

                                    with ui.row().classes(
                                        "items-center gap-3"
                                    ):

                                        ui.label(
                                            f"#{r['id']}"
                                        ).classes(
                                            "text-sm font-bold text-gray-400"
                                        )

                                        with ui.row().classes(
                                            f"items-center gap-1 px-3 py-1 rounded-full {config['badge']}"
                                        ):

                                            ui.icon(
                                                config['icon'],
                                                size="0.9rem"
                                            )

                                            ui.label(
                                                config['label']
                                            ).classes(
                                                "text-xs font-bold"
                                            )

                                    ui.label(
                                        service_name
                                    ).classes(
                                        "text-2xl font-bold text-gray-800"
                                    )

                                with ui.column().classes(
                                    "items-end gap-1"
                                ):

                                    ui.label(
                                        time_str
                                    ).classes(
                                        "text-sm text-gray-400"
                                    )

                                    if price:

                                        ui.label(
                                            f"{price:,.0f} đ"
                                        ).classes(
                                            "text-2xl font-bold text-emerald-600"
                                        )

                                        ui.label(
                                            "Tổng chi phí"
                                        ).classes(
                                            "text-xs uppercase text-gray-400"
                                        )

                                        if r.get("invoice_description"):
                                            ui.label(
                                                r["invoice_description"]
                                            ).classes(
                                                "text-xs text-emerald-700 italic max-w-[200px] text-right truncate"
                                            ).tooltip(r["invoice_description"])

                            # =============================================
                            # INFO GRID
                            # =============================================

                            with ui.row().classes(
                                "w-full gap-4"
                            ):

                                # LOCATION
                                with ui.row().classes(
                                    "items-center gap-2 bg-gray-50 px-4 py-3 rounded-xl flex-1"
                                ):

                                    ui.icon(
                                        "place",
                                        color="red"
                                    )

                                    with ui.column().classes(
                                        "gap-0"
                                    ):

                                        ui.label(
                                            "Vị trí"
                                        ).classes(
                                            "text-xs uppercase text-gray-400"
                                        )

                                        ui.label(
                                            r.get(
                                                'address_description',
                                                'N/A'
                                            )
                                        ).classes(
                                            "font-medium text-gray-700"
                                        )

                                # COMPANY
                                if r.get('company_name'):

                                    with ui.row().classes(
                                        "items-center gap-2 bg-indigo-50 px-4 py-3 rounded-xl"
                                    ):

                                        ui.icon(
                                            "business",
                                            color="indigo"
                                        )

                                        with ui.column().classes(
                                            "gap-0"
                                        ):

                                            ui.label(
                                                "Đơn vị cứu hộ"
                                            ).classes(
                                                "text-xs uppercase text-indigo-400"
                                            )

                                            ui.label(
                                                r['company_name']
                                            ).classes(
                                                "font-semibold text-indigo-700"
                                            )

                            # =============================================
                            # ACTIONS
                            # =============================================

                            ui.separator()

                            with ui.row().classes(
                                "w-full justify-end gap-3"
                            ):

                                if r['status'] == 'PENDING':

                                    ui.button(
                                        "Hủy yêu cầu",
                                        icon="close",
                                        on_click=lambda rid=r['id']: _confirm_cancel(rid)
                                    ).classes(
                                        "rounded-xl"
                                    ).props(
                                        "outline color=red"
                                    )

                                ui.button(
                                    "Chi tiết & Theo dõi",
                                    icon="visibility",
                                    on_click=lambda rid=r['id']: ui.navigate.to(
                                        f"/customer/track/{rid}"
                                    )
                                ).classes(
                                    "bg-indigo-600 text-white font-bold px-5 rounded-xl"
                                ).props(
                                    "unelevated"
                                )

        # ============================================================
        # CANCEL DIALOG
        # ============================================================

        async def _confirm_cancel(
            request_id: int
        ):

            with ui.dialog() as dialog, ui.card().classes(
                "rounded-3xl p-7 w-[420px]"
            ):

                ui.icon(
                    "warning",
                    size="3rem"
                ).classes(
                    "text-red-500 mx-auto"
                )

                ui.label(
                    "Xác nhận hủy yêu cầu"
                ).classes(
                    "text-2xl font-bold text-center mt-3"
                )

                ui.label(
                    "Bạn có chắc chắn muốn hủy yêu cầu cứu hộ này không?"
                ).classes(
                    "text-center text-gray-500"
                )

                with ui.row().classes(
                    "w-full justify-end gap-3 mt-6"
                ):

                    ui.button(
                        "Đóng",
                        on_click=dialog.close
                    ).props(
                        "flat"
                    )

                    async def do_cancel():

                        try:

                            await cancel_request(
                                request_id
                            )

                            ui.notify(
                                "Đã hủy yêu cầu",
                                type="info"
                            )

                            dialog.close()

                            await _load_data()

                        except Exception as e:

                            ui.notify(
                                f"Lỗi: {e}",
                                type="negative"
                            )

                    ui.button(
                        "Xác nhận hủy",
                        icon="delete",
                        on_click=do_cancel
                    ).classes(
                        "bg-red-500 text-white font-bold rounded-xl px-5"
                    )

            dialog.open()

        # ============================================================
        # INIT
        # ============================================================

        await _load_data()

        timer = ui.timer(
            30,
            _load_data
        )
        ui.context.client.on_disconnect(timer.deactivate)