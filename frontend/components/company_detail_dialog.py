"""
Reusable Dialog for Company Details & Reviews.
UI đẹp hơn + bo góc + debug lỗi đầy đủ.
"""

from nicegui import ui
import httpx
import traceback

from core.auth import get_access_token
from core.config import BACKEND_URL


def open_company_detail(company_id: int):

    token = get_access_token()

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # =========================================================
    # STATE
    # =========================================================
    data = {
        "info": {},
        "reviews": [],
        "history": []
    }

    # =========================================================
    # LOAD DATA
    # =========================================================
    async def _load_details():

        try:

            loading_bar.visible = True

            print(f"[DETAIL] Loading company id = {company_id}")

            async with httpx.AsyncClient() as client:

                r = await client.get(
                    f"{BACKEND_URL}/rescue/companies/{company_id}/full-details",
                    headers=headers,
                    timeout=10
                )

                print("[STATUS]", r.status_code)
                print("[RAW RESPONSE]", r.text)

                if r.status_code != 200:
                    raise Exception(f"API ERROR: {r.status_code}")

                response_json = r.json()

                res = response_json.get("data", {})

                print("[PARSED DATA]", res)

                # save state
                data["info"] = res
                data["reviews"] = res.get("reviews", [])
                data["history"] = res.get("my_history", [])

                # render
                _render_ui()

        except Exception as e:

            print("\n========== DETAIL ERROR ==========")
            traceback.print_exc()
            print("==================================\n")

            ui.notify(
                f"Lỗi tải chi tiết: {str(e)}",
                type="negative"
            )

            dialog.close()

        finally:
            loading_bar.visible = False

    # =========================================================
    # RENDER UI
    # =========================================================
    def _render_ui():

        try:

            info_container.clear()

            info = data["info"]

            print("[RENDER INFO]", info)

            with info_container:

                with ui.scroll_area().classes(
                    'w-full h-[85vh]'
                ):

                    # =================================================
                    # HEADER
                    # =================================================
                    with ui.column().classes(
                        '''
                        w-full
                        relative
                        overflow-hidden
                        '''
                    ):

                        with ui.element('div').classes(
                            '''
                            w-full
                            h-56
                            bg-gradient-to-r
                            from-blue-500
                            via-indigo-500
                            to-purple-500
                            relative
                            flex
                            items-center
                            justify-center
                            '''
                        ):

                            # background icon
                            ui.icon(
                                'local_taxi',
                                size='7rem',
                                color='white'
                            ).classes('opacity-10')

                            # close button
                            ui.button(
                                icon='close',
                                on_click=dialog.close
                            ).props(
                                'round flat color=white'
                            ).classes(
                                '''
                                absolute
                                top-4
                                right-4
                                bg-white/20
                                backdrop-blur-md
                                '''
                            )

                            # company info overlay
                            with ui.column().classes(
                                '''
                                absolute
                                bottom-6
                                left-6
                                text-white
                                gap-1
                                '''
                            ):

                                ui.label(
                                    info.get("company_name", "Không có tên")
                                ).classes(
                                    '''
                                    text-3xl
                                    font-bold
                                    '''
                                )

                                ui.label(
                                    info.get("address", "Không có địa chỉ")
                                ).classes(
                                    '''
                                    text-sm
                                    opacity-90
                                    '''
                                )

                    # =================================================
                    # BODY
                    # =================================================
                    with ui.column().classes(
                        '''
                        w-full
                        p-6
                        gap-6
                        bg-white
                        '''
                    ):

                        # =============================================
                        # TOP STATS
                        # =============================================
                        with ui.row().classes(
                            '''
                            w-full
                            gap-4
                            '''
                        ):

                            # rating card
                            with ui.card().classes(
                                '''
                                flex-1
                                rounded-2xl
                                shadow-sm
                                border-none
                                bg-amber-50
                                p-5
                                '''
                            ):

                                ui.label("Đánh giá").classes(
                                    'text-sm text-gray-500'
                                )

                                ui.label(
                                    f"⭐ {info.get('rating_avg', 0):.1f}"
                                ).classes(
                                    '''
                                    text-3xl
                                    font-bold
                                    text-amber-600
                                    '''
                                )

                                ui.label(
                                    f"{info.get('rating_count', 0)} lượt đánh giá"
                                ).classes(
                                    'text-xs text-gray-500'
                                )

                            # hotline card
                            with ui.card().classes(
                                '''
                                flex-1
                                rounded-2xl
                                shadow-sm
                                border-none
                                bg-blue-50
                                p-5
                                '''
                            ):

                                ui.label("Hotline").classes(
                                    'text-sm text-gray-500'
                                )

                                ui.label(
                                    info.get("hotline", "N/A")
                                ).classes(
                                    '''
                                    text-2xl
                                    font-bold
                                    text-blue-600
                                    '''
                                )

                        # =============================================
                        # DESCRIPTION
                        # =============================================
                        if info.get("description"):

                            with ui.card().classes(
                                '''
                                w-full
                                rounded-2xl
                                shadow-sm
                                border-none
                                p-5
                                '''
                            ):

                                ui.label(
                                    "Giới thiệu"
                                ).classes(
                                    '''
                                    text-lg
                                    font-bold
                                    mb-2
                                    '''
                                )

                                ui.label(
                                    info["description"]
                                ).classes(
                                    '''
                                    text-sm
                                    leading-relaxed
                                    text-gray-600
                                    '''
                                )

                        # =============================================
                        # REVIEWS
                        # =============================================
                        ui.label(
                            f"Đánh giá gần đây ({len(data['reviews'])})"
                        ).classes(
                            '''
                            text-xl
                            font-bold
                            '''
                        )

                        if not data["reviews"]:

                            with ui.card().classes(
                                '''
                                w-full
                                rounded-2xl
                                shadow-none
                                bg-gray-50
                                p-6
                                items-center
                                '''
                            ):

                                ui.icon(
                                    'reviews',
                                    size='2rem'
                                ).classes('text-gray-400')

                                ui.label(
                                    "Chưa có đánh giá nào"
                                ).classes(
                                    'text-gray-500'
                                )

                        else:

                            with ui.column().classes(
                                '''
                                w-full
                                gap-4
                                '''
                            ):

                                for rev in data["reviews"][:10]:

                                    with ui.card().classes(
                                        '''
                                        w-full
                                        rounded-2xl
                                        shadow-sm
                                        border-none
                                        bg-gray-50
                                        p-5
                                        '''
                                    ):

                                        with ui.row().classes(
                                            '''
                                            w-full
                                            justify-between
                                            items-center
                                            '''
                                        ):

                                            ui.label(
                                                rev.get(
                                                    "customer_name",
                                                    "Ẩn danh"
                                                )
                                            ).classes(
                                                'font-bold'
                                            )

                                            ui.label(
                                                f"⭐ {rev.get('rating', 0)}"
                                            ).classes(
                                                '''
                                                text-amber-600
                                                font-bold
                                                '''
                                            )

                                        ui.label(
                                            rev.get(
                                                "comment",
                                                "Không có bình luận"
                                            )
                                        ).classes(
                                            '''
                                            text-sm
                                            italic
                                            text-gray-600
                                            mt-2
                                            '''
                                        )

                                        ui.label(
                                            rev.get(
                                                "created_at",
                                                ""
                                            )[:10]
                                        ).classes(
                                            '''
                                            text-xs
                                            text-gray-400
                                            mt-3
                                            '''
                                        )

                        # =============================================
                        # HISTORY
                        # =============================================
                        ui.label(
                            f"Lịch sử cứu hộ ({len(data['history'])})"
                        ).classes(
                            '''
                            text-xl
                            font-bold
                            mt-4
                            '''
                        )

                        with ui.column().classes(
                            'w-full gap-3'
                        ):

                            for h in data["history"][:5]:

                                services = ", ".join(
                                    h.get("services", [])
                                )

                                with ui.card().classes(
                                    '''
                                    w-full
                                    rounded-2xl
                                    shadow-none
                                    border
                                    border-gray-200
                                    p-4
                                    '''
                                ):

                                    with ui.row().classes(
                                        '''
                                        w-full
                                        justify-between
                                        '''
                                    ):

                                        ui.label(
                                            services or "Không có dịch vụ"
                                        ).classes(
                                            'font-semibold'
                                        )

                                        ui.label(
                                            h.get("status", "")
                                        ).classes(
                                            '''
                                            text-xs
                                            font-bold
                                            text-blue-600
                                            '''
                                        )

                                    ui.label(
                                        f"{h.get('created_at', '')[:10]}"
                                    ).classes(
                                        '''
                                        text-xs
                                        text-gray-500
                                        mt-1
                                        '''
                                    )

                        # =============================================
                        # ACTIONS
                        # =============================================
                        with ui.row().classes(
                            '''
                            w-full
                            gap-4
                            mt-6
                            '''
                        ):

                            ui.button(
                                'GỌI HOTLINE',
                                icon='phone',
                                on_click=lambda:
                                ui.navigate.to(
                                    f"tel:{info.get('hotline', '')}"
                                )
                            ).classes(
                                '''
                                flex-1
                                py-4
                                rounded-2xl
                                bg-blue-600
                                text-white
                                font-bold
                                shadow-lg
                                '''
                            )

                            ui.button(
                                'ĐÓNG',
                                icon='close',
                                on_click=dialog.close
                            ).props(
                                'outline'
                            ).classes(
                                '''
                                flex-1
                                py-4
                                rounded-2xl
                                font-bold
                                '''
                            )

        except Exception as e:

            print("\n========== RENDER ERROR ==========")
            traceback.print_exc()
            print("==================================\n")

            ui.notify(
                f"Lỗi render UI: {str(e)}",
                type="negative"
            )

    # =========================================================
    # DIALOG
    # =========================================================
    with ui.dialog() as dialog:

        with ui.card().classes(
            '''
            w-full
            max-w-4xl
            p-0
            overflow-hidden
            rounded-[32px]
            shadow-2xl
            border-none
            '''
        ):

            loading_bar = ui.linear_progress(
                value=0,
                show_value=False
            ).classes(
                '''
                w-full
                absolute
                top-0
                z-50
                '''
            )

            loading_bar.visible = False

            info_container = ui.column().classes(
                'w-full'
            )

    # =========================================================
    # START
    # =========================================================
    async def start():

        dialog.open()

        await _load_details()
    ui.timer(
        0.1,
        start,
        once=True
    )