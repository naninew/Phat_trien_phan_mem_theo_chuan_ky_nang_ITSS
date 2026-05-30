"""
Community Page - NiceGUI
"""
from nicegui import ui
from core.auth import require_role
from components.page_layout import page_layout
from datetime import datetime
from services.community_api import (
    get_posts,
    get_post_detail,
    create_post,
    create_reply,
    mark_reply_helpful,
    close_post,
)


def create_community_page():
    """Register /customer/community route."""

    @ui.page("/customer/community")
    async def community_page():
        if not require_role("customer"):
            return

        ui.add_head_html("""
        <style>
            .community-title {
                font-size: 30px;
                font-weight: 900;
                color: #0f172a;
                letter-spacing: -0.03em;
            }

            .community-subtitle {
                color: #64748b;
                font-size: 14px;
            }

            .post-card {
                width: 100%;
                padding: 22px;
                border-radius: 24px;
                background: #ffffff;
                border: 1px solid #e2e8f0;
                box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
                transition: all 0.25s ease;
                cursor: pointer;
            }

            .post-card:hover {
                transform: translateY(-3px);
                border-color: #2563eb;
                box-shadow: 0 16px 36px rgba(15, 23, 42, 0.10);
            }

            .topic-badge {
                padding: 5px 12px;
                border-radius: 999px;
                background: #eff6ff;
                color: #2563eb;
                font-size: 12px;
                font-weight: 800;
            }

            .closed-badge {
                padding: 5px 12px;
                border-radius: 999px;
                background: #dcfce7;
                color: #15803d;
                font-size: 12px;
                font-weight: 800;
            }

            .post-title {
                font-size: 20px;
                font-weight: 850;
                color: #0f172a;
                margin-top: 12px;
            }

            .post-content {
                color: #64748b;
                font-size: 14px;
                line-height: 1.6;
                margin-top: 8px;
            }

            .author-avatar {
                width: 32px;
                height: 32px;
                border-radius: 999px;
                background: #eff6ff;
                color: #2563eb;
            }

            .sidebar-card {
                width: 100%;
                padding: 22px;
                border-radius: 24px;
                background: #ffffff;
                border: 1px solid #e2e8f0;
                box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
            }

            .sidebar-title {
                font-size: 17px;
                font-weight: 850;
                color: #0f172a;
                margin-bottom: 14px;
            }

            .topic-item {
                display: flex;
                align-items: center;
                gap: 10px;
                padding: 10px 12px;
                border-radius: 14px;
                color: #475569;
                font-size: 14px;
                font-weight: 600;
                transition: all 0.2s ease;
            }

            .topic-item:hover {
                background: #eff6ff;
                color: #2563eb;
            }

            .topic-item .q-icon {
                font-size: 20px;
                color: #2563eb;
            }

            .dialog-card {
                border-radius: 28px;
                box-shadow: 0 25px 70px rgba(15, 23, 42, 0.20);
            }

            .post-detail-scroll {
                overflow-y: auto;
                min-height: 0;
            }

            .post-detail-scroll::-webkit-scrollbar {
                width: 6px;
            }

            .post-detail-scroll::-webkit-scrollbar-thumb {
                background: #cbd5e1;
                border-radius: 999px;
            }

            .reply-card {
                width: 100%;
                padding: 14px;
                border-radius: 18px;
                background: #f8fafc;
                border: 1px solid #e2e8f0;
            }

            .helpful-btn {
                color: #2563eb;
                font-weight: 700;
                border-radius: 10px;
            }

            .helpful-done {
                display: inline-flex;
                align-items: center;
                gap: 6px;
                padding: 6px 12px;
                border-radius: 999px;
                background: #dcfce7;
                color: #166534;
                font-size: 12px;
                font-weight: 800;
            }

            .comment-box {
                border-top: 1px solid #e2e8f0;
                background: #ffffff;
                box-shadow: 0 -8px 24px rgba(15, 23, 42, 0.04);
            }
        </style>
        """)

        with page_layout("/customer/community", title="Cộng Đồng Rescue"):

            with ui.row().classes("w-full items-center justify-between mb-8"):
                with ui.column().classes("gap-1"):
                    with ui.row().classes("items-center gap-3"):
                        ui.icon("groups", size="2rem").classes("text-primary")
                        ui.label("Cộng đồng cứu hộ").classes("community-title")

                    ui.label(
                        "Chia sẻ kinh nghiệm, hỏi đáp sự cố và hỗ trợ lẫn nhau"
                    ).classes("community-subtitle")

                ui.button(
                    "ĐĂNG BÀI MỚI",
                    icon="edit_square",
                    on_click=lambda: _open_create_dialog(),
                ).classes(
                    "bg-primary text-white px-6 py-3 rounded-2xl font-bold shadow-md hover:shadow-lg"
                )

            with ui.row().classes("w-full gap-8 items-start"):
                posts_container = ui.column().classes("flex-1 gap-4")

                with ui.column().classes("w-80 gap-5"):
                    with ui.element("div").classes("sidebar-card"):
                        ui.label("Chủ đề nổi bật").classes("sidebar-title")

                        with ui.element("div").classes("topic-item"):
                            ui.icon("build_circle")
                            ui.label("Kinh nghiệm sửa xe")

                        with ui.element("div").classes("topic-item"):
                            ui.icon("verified")
                            ui.label("Review đơn vị cứu hộ")

                        with ui.element("div").classes("topic-item"):
                            ui.icon("crisis_alert")
                            ui.label("Cảnh báo đoạn đường xấu")

                        with ui.element("div").classes("topic-item"):
                            ui.icon("local_gas_station")
                            ui.label("Hết xăng / thủng lốp")

                    with ui.element("div").classes("sidebar-card"):
                        ui.label("Gợi ý đăng bài").classes("sidebar-title")
                        with ui.row().classes("items-start gap-3"):
                            ui.icon("tips_and_updates").classes("text-primary mt-1")
                            ui.label(
                                "Hãy mô tả rõ vấn đề, vị trí, loại xe và tình trạng hiện tại để mọi người hỗ trợ nhanh hơn."
                            ).classes("text-sm text-gray-500 leading-relaxed")

            async def refresh_posts():
                posts_container.clear()
                posts = await get_posts()

                with posts_container:
                    if not posts:
                        with ui.column().classes(
                            "w-full items-center justify-center py-24 bg-white rounded-3xl border border-dashed border-slate-300"
                        ):
                            ui.icon("forum", size="4rem").classes("text-blue-200")
                            ui.label("Chưa có bài đăng nào").classes(
                                "text-lg font-bold text-gray-700"
                            )
                            ui.label(
                                "Hãy là người đầu tiên chia sẻ vấn đề của bạn"
                            ).classes("text-sm text-gray-500")
                        return

                    for p in posts:
                        _render_post_card(p)

            def _render_post_card(p):
                with ui.element("div").classes("post-card").on(
                    "click", lambda: _open_post_detail(p["id"])
                ):
                    with ui.row().classes("w-full justify-between items-center"):
                        with ui.row().classes("items-center gap-2"):
                            ui.label(
                                p.get("incident_type", "Thảo luận")
                            ).classes("topic-badge")

                            if p.get("is_closed"):
                                ui.label("ĐÃ GIẢI QUYẾT").classes("closed-badge")

                        with ui.row().classes("items-center gap-1"):
                            ui.icon("calendar_month", size="xs").classes("text-gray-400")
                            formatted_time = datetime.fromisoformat(
                                p["created_at"]).strftime("%d/%m/%Y %H:%M")

                            ui.label(formatted_time).classes("text-xs text-gray-400")

                    ui.label(p["title"]).classes("post-title")
                    ui.label(p["content"]).classes("post-content line-clamp-2")

                    with ui.row().classes("w-full mt-5 items-center justify-between"):
                        with ui.row().classes("items-center gap-2"):
                            ui.avatar(icon="account_circle").classes("author-avatar")
                            ui.label(p["user_name"]).classes(
                                "text-sm font-bold text-gray-700"
                            )

                        with ui.row().classes("items-center gap-2 text-gray-400"):
                            ui.icon("mode_comment", size="sm")
                            ui.label(str(p.get("reply_count", 0))).classes(
                                "text-sm font-semibold"
                            )

            def _open_create_dialog():
                with ui.dialog() as d, ui.card().classes("dialog-card w-[520px] p-8"):
                    with ui.row().classes("items-center gap-3 mb-2"):
                        ui.icon("edit_square", size="2rem").classes("text-primary")
                        ui.label("Tạo bài đăng mới").classes(
                            "text-2xl font-black text-gray-900"
                        )

                    ui.label("Chia sẻ vấn đề hoặc kinh nghiệm của bạn").classes(
                        "text-sm text-gray-500 mb-6"
                    )

                    title = ui.input("Tiêu đề").classes("w-full mb-4").props(
                        "outlined rounded"
                    )

                    incident = ui.select(
                        ["Hỏng máy", "Thủng lốp", "Hết xăng", "Tai nạn", "Khác"],
                        label="Chủ đề",
                        value="Khác",
                    ).classes("w-full mb-4").props("outlined rounded")

                    content = ui.textarea("Nội dung").classes("w-full mb-6").props(
                        "outlined rounded"
                    )

                    with ui.row().classes("w-full justify-end gap-3"):
                        ui.button("ĐÓNG", on_click=d.close).props("flat").classes(
                            "rounded-xl font-bold"
                        )

                        async def submit():
                            if not title.value or not content.value:
                                ui.notify(
                                    "Vui lòng nhập tiêu đề và nội dung",
                                    type="warning",
                                )
                                return

                            if await create_post(title.value, content.value, incident.value):
                                ui.notify("Đã đăng bài thành công!", type="positive")
                                d.close()
                                await refresh_posts()
                            else:
                                ui.notify("Không thể đăng bài", type="negative")

                        ui.button("ĐĂNG BÀI", on_click=submit).classes(
                            "bg-primary text-white px-8 rounded-xl font-bold"
                        )

                d.open()

            async def _open_post_detail(post_id):
                p = await get_post_detail(post_id)

                if not p:
                    ui.notify("Không tìm thấy bài đăng", type="negative")
                    return

                with ui.dialog() as d, ui.card().classes(
                    "dialog-card w-[820px] max-w-[95vw] h-[88vh] p-0 overflow-hidden"
                ):
                    with ui.column().classes("w-full h-full"):

                        with ui.column().classes(
                            "w-full flex-1 post-detail-scroll px-8 pt-8 pb-6"
                        ):
                            with ui.row().classes(
                                "w-full justify-between items-center mb-5"
                            ):
                                with ui.row().classes("items-center gap-2"):
                                    ui.button(
                                        icon="arrow_back",
                                        on_click=d.close,
                                    ).props("flat round color=primary")

                                    ui.label(
                                        p.get("incident_type", "Thảo luận")
                                    ).classes("topic-badge")

                                    closed_badge_area = ui.row().classes(
                                        "items-center gap-2"
                                    )

                                    with closed_badge_area:
                                        if p.get("is_closed"):
                                            ui.label("ĐÃ GIẢI QUYẾT").classes(
                                                "closed-badge"
                                            )

                                with ui.row().classes("items-center gap-2"):
                                    if not p.get("is_closed"):
                                        closed_btn = ui.button(
                                            "ĐÁNH DẤU ĐÃ GIẢI QUYẾT",
                                            icon="check_circle",
                                        ).classes(
                                            "bg-green-600 text-white rounded-xl px-4 font-bold"
                                        )

                                        async def mark_post_closed(btn=closed_btn):
                                            btn.props("loading")

                                            if await close_post(post_id):
                                                ui.notify(
                                                    "Đã đánh dấu bài viết là đã giải quyết",
                                                    type="positive",
                                                )

                                                btn.delete()

                                                with closed_badge_area:
                                                    ui.label(
                                                        "ĐÃ GIẢI QUYẾT"
                                                    ).classes("closed-badge")

                                                await refresh_posts()
                                            else:
                                                ui.notify(
                                                    "Không thể đánh dấu bài viết",
                                                    type="negative",
                                                )
                                                btn.props(remove="loading")

                                        closed_btn.on("click", mark_post_closed)

                            ui.label(p["title"]).classes(
                                "text-3xl font-black text-gray-900 mb-4"
                            )

                            with ui.row().classes("items-center gap-3 mb-6"):
                                ui.avatar(icon="account_circle").classes(
                                    "author-avatar"
                                )

                                with ui.column().classes("gap-0"):
                                    ui.label(p["user_name"]).classes(
                                        "font-bold text-gray-800"
                                    )
                                    formatted_time = datetime.fromisoformat(
                                        p["created_at"]).strftime("%d/%m/%Y %H:%M")
                                    ui.label(formatted_time).classes("text-xs text-gray-400")

                            ui.label(p["content"]).classes(
                                "text-base text-gray-700 leading-relaxed mb-8 whitespace-pre-wrap"
                            )

                            ui.separator().classes("mb-6")

                            with ui.row().classes("items-center gap-2 mb-4"):
                                ui.icon("mode_comment").classes("text-primary")
                                comment_count_label = ui.label(
                                    f"Bình luận ({len(p['replies'])})"
                                ).classes("text-xl font-black text-gray-900")

                            replies_container = ui.column().classes("w-full gap-3")

                            with replies_container:
                                empty_reply_label = None

                                if not p["replies"]:
                                    empty_reply_label = ui.label(
                                        "Chưa có bình luận nào."
                                    ).classes("text-sm text-gray-400 italic")

                                for r in p["replies"]:
                                    with ui.element("div").classes("reply-card"):
                                        with ui.row().classes(
                                            "w-full justify-between"
                                        ):
                                            with ui.row().classes(
                                                "items-center gap-2"
                                            ):
                                                ui.icon("account_circle").classes(
                                                    "text-primary"
                                                )
                                                ui.label(r["user_name"]).classes(
                                                    "font-bold text-sm text-primary"
                                                )

                                            formatted_time = datetime.fromisoformat(
                                                r["created_at"]
                                            ).strftime("%d/%m/%Y %H:%M")
                                            ui.label(formatted_time).classes(
                                                "text-xs text-gray-400"
                                            )

                                        ui.label(r["content"]).classes(
                                            "mt-2 text-sm text-gray-700"
                                        )

                                        action_row = ui.row().classes(
                                            "w-full justify-between items-center mt-3"
                                        )

                                        with action_row:
                                            if r.get("is_helpful"):
                                                with ui.element("div").classes(
                                                    "helpful-done"
                                                ):
                                                    ui.icon("verified", size="xs")
                                                    ui.label("Hữu ích")
                                            else:
                                                helpful_btn = ui.button(
                                                    "Đánh dấu hữu ích",
                                                    icon="thumb_up",
                                                ).props("flat dense").classes("helpful-btn")

                                                async def mark_helpful_action(
                                                    reply_id=r["id"],
                                                    btn=helpful_btn,
                                                    row=action_row,
                                                ):
                                                    btn.props("loading")

                                                    if await mark_reply_helpful(
                                                        reply_id
                                                    ):
                                                        ui.notify(
                                                            "Đã đánh dấu phản hồi hữu ích",
                                                            type="positive",
                                                        )

                                                        btn.delete()

                                                        with row:
                                                            with ui.element(
                                                                "div"
                                                            ).classes("helpful-done"):
                                                                ui.icon(
                                                                    "verified",
                                                                    size="xs",
                                                                )
                                                                ui.label("Hữu ích")
                                                    else:
                                                        ui.notify(
                                                            "Không thể đánh dấu phản hồi",
                                                            type="negative",
                                                        )
                                                        btn.props(remove="loading")

                                                helpful_btn.on(
                                                    "click", mark_helpful_action
                                                )

                        with ui.row().classes(
                            "w-full gap-3 items-center px-8 py-5 comment-box"
                        ):
                            reply_input = ui.input(
                                placeholder="Viết bình luận..."
                            ).classes("flex-1").props("outlined rounded dense")

                            async def send_r():
                                content = (reply_input.value or "").strip()

                                if not content:
                                    ui.notify(
                                        "Vui lòng nhập bình luận",
                                        type="warning",
                                    )
                                    return

                                send_btn.props("loading")
                                res = await create_reply(post_id, content)

                                if res:
                                    ui.notify("Đã gửi bình luận", type="positive")
                                    reply_input.value = ""
                                    reply_input.update()

                                    if empty_reply_label:
                                        empty_reply_label.delete()

                                    current_count = len(p["replies"]) + 1
                                    p["replies"].append({"content": content})
                                    comment_count_label.set_text(
                                        f"Bình luận ({current_count})"
                                    )

                                    with replies_container:
                                        with ui.element("div").classes("reply-card"):
                                            with ui.row().classes(
                                                "w-full justify-between"
                                            ):
                                                with ui.row().classes(
                                                    "items-center gap-2"
                                                ):
                                                    ui.icon(
                                                        "account_circle"
                                                    ).classes("text-primary")
                                                    ui.label("Bạn").classes(
                                                        "font-bold text-sm text-primary"
                                                    )

                                                ui.label("Vừa xong").classes(
                                                    "text-xs text-gray-400"
                                                )

                                            ui.label(content).classes(
                                                "mt-2 text-sm text-gray-700"
                                            )

                                    send_btn.props(remove="loading")
                                else:
                                    ui.notify(
                                        "Không thể gửi bình luận",
                                        type="negative",
                                    )
                                    send_btn.props(remove="loading")

                            send_btn = ui.button(
                                icon="send",
                                on_click=send_r,
                            ).props("round unelevated color=primary")

                d.open()

            await refresh_posts()