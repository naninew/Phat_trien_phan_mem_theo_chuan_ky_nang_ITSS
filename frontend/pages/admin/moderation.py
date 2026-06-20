"""
Trang kiểm duyệt nội dung (Đánh giá & Bài đăng cộng đồng).
"""
from nicegui import ui

from core.auth import require_admin_auth
from components.page_layout import page_layout
from services.admin_api import (
    get_reviews,
    delete_review,
    get_community_posts,
    delete_community_post,
    get_companies,
)

STAR_OPTIONS = {
    "all": "Tất cả",
    "1": "1★",
    "2": "2★",
    "3": "3★",
    "4": "4★",
    "5": "5★",
}

COMMUNITY_STATUS_OPTIONS = {
    "all": "Tất cả",
    "OPEN": "Đang mở",
    "CLOSED": "Đã đóng",
}

INCIDENT_TYPE_OPTIONS = {
    "all": "Tất cả loại sự cố",
    "Hỏng máy": "Hỏng máy",
    "Thủng lốp": "Thủng lốp",
    "Hết xăng": "Hết xăng",
    "Tai nạn": "Tai nạn",
    "Chết máy": "Chết máy",
    "Khác": "Khác",
}


def create_moderation_page():

    @ui.page('/admin/moderation')
    async def moderation_page():
        if not require_admin_auth():
            return

        with page_layout("/admin/moderation", title="Kiểm Duyệt Nội Dung"):

            with ui.tabs().classes('w-full') as tabs:
                review_tab = ui.tab('Đánh giá (Reviews)')
                community_tab = ui.tab('Diễn đàn (Community)')

            with ui.tab_panels(tabs, value=review_tab).classes('w-full bg-transparent'):
                with ui.tab_panel(review_tab):
                    await _render_reviews_panel()

                with ui.tab_panel(community_tab):
                    await _render_community_panel()


async def _render_reviews_panel():
    ui.label("Quản lý đánh giá từ khách hàng").classes("text-xl font-bold mb-4")

    companies = await get_companies()
    company_options = {"all": "Tất cả công ty"}
    for c in companies:
        company_options[str(c["id"])] = c.get("company_name", f"Công ty #{c['id']}")

    with ui.row().classes("w-full items-center gap-4 bg-white p-4 rounded-2xl shadow-sm border border-gray-100 mb-4 flex-wrap"):
        search_input = ui.input(
            placeholder="Tìm theo nội dung nhận xét...",
            on_change=lambda: _load_reviews(),
        ).classes("flex-1 min-w-[200px]").props("outlined dense clearable icon=search")

        ui.label("Số sao:").classes("text-gray-600 font-medium")
        star_filter = ui.select(
            options=STAR_OPTIONS,
            value="all",
            on_change=lambda: _load_reviews(),
        ).classes("w-32").props("outlined dense")

        ui.label("Công ty:").classes("text-gray-600 font-medium")
        company_filter = ui.select(
            options=company_options,
            value="all",
            on_change=lambda: _load_reviews(),
        ).classes("w-56").props("outlined dense")

        ui.label("Từ ngày:").classes("text-gray-600 font-medium")
        from_date_input = ui.input(on_change=lambda: _load_reviews()).classes("w-40").props(
            "outlined dense type=date"
        )

        ui.label("Đến ngày:").classes("text-gray-600 font-medium")
        to_date_input = ui.input(on_change=lambda: _load_reviews()).classes("w-40").props(
            "outlined dense type=date"
        )

    columns = [
        {'name': 'id', 'label': 'ID', 'field': 'id', 'align': 'left'},
        {'name': 'customer', 'label': 'Khách hàng', 'field': 'customer_name', 'align': 'left'},
        {'name': 'company', 'label': 'Công ty', 'field': 'company_name', 'align': 'left'},
        {'name': 'rating', 'label': 'Sao', 'field': 'rating', 'align': 'center'},
        {'name': 'comment', 'label': 'Nội dung', 'field': 'comment', 'align': 'left'},
        {'name': 'created_at', 'label': 'Ngày tạo', 'field': 'created_at', 'align': 'left'},
        {'name': 'actions', 'label': 'Thao tác', 'field': 'id', 'align': 'center'},
    ]

    table = ui.table(columns=columns, rows=[]).classes('w-full m3-card')
    table.add_slot('body-cell-actions', '''
        <q-td :props="props">
            <q-btn flat round color="red" icon="delete" @click="$parent.$emit('delete', props.value)" />
        </q-td>
    ''')

    async def _load_reviews():
        company_id = None
        if company_filter.value and company_filter.value != "all":
            company_id = int(company_filter.value)
        rows = await get_reviews(
            star_filter=star_filter.value,
            company_id=company_id,
            from_date=from_date_input.value or None,
            to_date=to_date_input.value or None,
            search=search_input.value or None,
        )
        table.rows = [
            {**r, "created_at": r.get("created_at", "")[:10]}
            for r in rows
        ]

    async def _show_delete_dialog(review_id):
        with ui.dialog() as dialog, ui.card().classes("p-6 w-[480px]"):
            ui.label(f"Xóa đánh giá ID {review_id}").classes("text-xl font-bold mb-2")
            ui.label("Vui lòng nhập lý do xóa đánh giá vi phạm.").classes("text-gray-500 mb-4")
            reason_input = ui.textarea("Lý do xóa (Bắt buộc)").classes("w-full").props("outlined autofocus")

            with ui.row().classes("w-full justify-end gap-2 mt-4"):
                ui.button("Hủy", on_click=dialog.close).props("flat")

                async def confirm():
                    reason = reason_input.value.strip() if reason_input.value else ""
                    if len(reason) < 5:
                        ui.notify("Lý do phải có ít nhất 5 ký tự", type="warning")
                        return
                    result = await delete_review(review_id, reason)
                    if result.get("success"):
                        ui.notify("Đã xóa đánh giá thành công", type="positive")
                        dialog.close()
                        await _load_reviews()
                    else:
                        ui.notify(result.get("message", "Lỗi khi xóa đánh giá"), type="negative")

                ui.button("Xác nhận xóa", on_click=confirm).classes("bg-red-500 text-white")
        dialog.open()

    table.on('delete', lambda msg: _show_delete_dialog(msg.args))
    await _load_reviews()


async def _render_community_panel():
    ui.label("Kiểm duyệt bài đăng cộng đồng").classes("text-xl font-bold mb-4")

    with ui.row().classes("w-full items-center gap-4 bg-white p-4 rounded-2xl shadow-sm border border-gray-100 mb-4 flex-wrap"):
        ui.label("Trạng thái:").classes("text-gray-600 font-medium")
        status_filter = ui.select(
            options=COMMUNITY_STATUS_OPTIONS,
            value="all",
            on_change=lambda: _load_posts(),
        ).classes("w-40").props("outlined dense")

        ui.label("Loại sự cố:").classes("text-gray-600 font-medium")
        incident_filter = ui.select(
            options=INCIDENT_TYPE_OPTIONS,
            value="all",
            on_change=lambda: _load_posts(),
        ).classes("w-48").props("outlined dense")

    columns = [
        {'name': 'id', 'label': 'ID', 'field': 'id', 'align': 'left'},
        {'name': 'user', 'label': 'Người đăng', 'field': 'user_name', 'align': 'left'},
        {'name': 'title', 'label': 'Tiêu đề', 'field': 'title', 'align': 'left'},
        {'name': 'type', 'label': 'Loại sự cố', 'field': 'incident_type', 'align': 'center'},
        {'name': 'status', 'label': 'Trạng thái', 'field': 'status', 'align': 'center'},
        {'name': 'replies_count', 'label': 'Số phản hồi', 'field': 'replies_count', 'align': 'center'},
        {'name': 'actions', 'label': 'Thao tác', 'field': 'id', 'align': 'center'},
    ]

    table = ui.table(columns=columns, rows=[]).classes('w-full m3-card')
    table.add_slot('body-cell-actions', '''
        <q-td :props="props">
            <q-btn flat round color="red" icon="delete" @click="$parent.$emit('delete', props.value)" />
        </q-td>
    ''')

    async def _load_posts():
        table.rows = await get_community_posts(
            status_filter=status_filter.value,
            incident_type=incident_filter.value,
        )

    async def _show_delete_dialog(post_id):
        with ui.dialog() as dialog, ui.card().classes("p-6 w-[480px]"):
            ui.label(f"Xóa bài đăng ID {post_id}").classes("text-xl font-bold mb-2")
            ui.label("Bài đăng và tất cả phản hồi liên quan sẽ bị xóa vĩnh viễn.").classes("text-gray-500 mb-4")
            reason_input = ui.textarea("Lý do xóa (Bắt buộc)").classes("w-full").props("outlined autofocus")

            with ui.row().classes("w-full justify-end gap-2 mt-4"):
                ui.button("Hủy", on_click=dialog.close).props("flat")

                async def confirm():
                    reason = reason_input.value.strip() if reason_input.value else ""
                    if len(reason) < 5:
                        ui.notify("Lý do phải có ít nhất 5 ký tự", type="warning")
                        return
                    result = await delete_community_post(post_id, reason)
                    if result.get("success"):
                        ui.notify("Đã xóa bài đăng", type="positive")
                        dialog.close()
                        await _load_posts()
                    else:
                        ui.notify(result.get("message", "Lỗi khi xóa bài đăng"), type="negative")

                ui.button("Xác nhận xóa", on_click=confirm).classes("bg-red-500 text-white")
        dialog.open()

    table.on('delete', lambda msg: _show_delete_dialog(msg.args))
    await _load_posts()
