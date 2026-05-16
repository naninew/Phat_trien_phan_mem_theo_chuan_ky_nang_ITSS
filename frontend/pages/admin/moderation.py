"""
Trang kiểm duyệt nội dung (Đánh giá & Bài đăng cộng đồng).
"""
from nicegui import ui
from core.auth import require_role
from components.page_layout import page_layout
from services.admin_api import get_reviews, delete_review, get_community_posts, delete_community_post

def create_moderation_page():

    @ui.page('/admin/moderation')
    async def moderation_page():
        if not require_role("admin"):
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
    
    columns = [
        {'name': 'id', 'label': 'ID', 'field': 'id', 'align': 'left'},
        {'name': 'customer', 'label': 'Khách hàng', 'field': 'customer_name', 'align': 'left'},
        {'name': 'company', 'label': 'Công ty', 'field': 'company_name', 'align': 'left'},
        {'name': 'rating', 'label': 'Sao', 'field': 'rating', 'align': 'center'},
        {'name': 'comment', 'label': 'Nội dung', 'field': 'comment', 'align': 'left'},
        {'name': 'actions', 'label': 'Thao tác', 'field': 'id', 'align': 'center'},
    ]
    
    table = ui.table(columns=columns, rows=[]).classes('w-full m3-card')
    table.add_slot('body-cell-actions', '''
        <q-td :props="props">
            <q-btn flat round color="red" icon="delete" @click="$parent.$emit('delete', props.value)" />
        </q-td>
    ''')

    async def _load_reviews():
        table.rows = await get_reviews()

    async def _handle_delete(review_id):
        if await ui.confirm(f"Bạn có chắc chắn muốn xóa đánh giá ID {review_id}?"):
            if await delete_review(review_id):
                ui.notify("Đã xóa đánh giá thành công")
                await _load_reviews()
            else:
                ui.notify("Lỗi khi xóa đánh giá", type="negative")

    table.on('delete', lambda msg: _handle_delete(msg.args))
    await _load_reviews()

async def _render_community_panel():
    ui.label("Kiểm duyệt bài đăng cộng đồng").classes("text-xl font-bold mb-4")
    
    columns = [
        {'name': 'id', 'label': 'ID', 'field': 'id', 'align': 'left'},
        {'name': 'user', 'label': 'Người đăng', 'field': 'user_name', 'align': 'left'},
        {'name': 'title', 'label': 'Tiêu đề', 'field': 'title', 'align': 'left'},
        {'name': 'type', 'label': 'Loại sự cố', 'field': 'incident_type', 'align': 'center'},
        {'name': 'actions', 'label': 'Thao tác', 'field': 'id', 'align': 'center'},
    ]
    
    table = ui.table(columns=columns, rows=[]).classes('w-full m3-card')
    table.add_slot('body-cell-actions', '''
        <q-td :props="props">
            <q-btn flat round color="red" icon="delete" @click="$parent.$emit('delete', props.value)" />
        </q-td>
    ''')

    async def _load_posts():
        table.rows = await get_community_posts()

    async def _handle_delete(post_id):
        if await ui.confirm(f"Xóa bài đăng ID {post_id} và tất cả bình luận liên quan?"):
            if await delete_community_post(post_id):
                ui.notify("Đã xóa bài đăng")
                await _load_posts()
            else:
                ui.notify("Lỗi khi xóa bài đăng", type="negative")

    table.on('delete', lambda msg: _handle_delete(msg.args))
    await _load_posts()
