"""
Community Page - NiceGUI
"""
from nicegui import ui
from typing import Dict, Any, List, Optional
from datetime import datetime
from core.auth import require_role
from components.page_layout import page_layout
from services.community_api import get_posts, get_post_detail, create_post, create_reply, mark_reply_helpful

def create_community_page():
    """Register /customer/community route."""

    @ui.page('/customer/community')
    async def community_page():
        if not require_role("customer"):
            return

        with page_layout("/customer/community", title="Cộng Đồng Rescue"):
            
            with ui.row().classes("w-full items-center justify-between mb-6"):
                with ui.column().classes("gap-0"):
                    ui.label("💬 Cộng Đồng Cứu Hộ").classes("text-3xl font-bold font-outfit")
                    ui.label("Chia sẻ kinh nghiệm và hỗ trợ lẫn nhau").classes("opacity-60")
                
                ui.button("ĐĂNG BÀI MỚI", icon="add", on_click=lambda: _open_create_dialog()) \
                    .classes("bg-primary text-white px-6 py-3 rounded-2xl shadow-lg shadow-primary/30 font-bold")

            # Main content
            with ui.row().classes("w-full gap-8 items-start"):
                # Left: Posts List
                posts_container = ui.column().classes("flex-1 gap-4")
                
                # Right: Sidebar/Info
                with ui.column().classes("w-80 gap-6"):
                    with ui.card().classes("w-full rounded-3xl p-6 border border-primary/20 bg-primary/5"):
                        ui.label("Top Chủ Đề").classes("text-lg font-bold mb-4 font-outfit text-primary")
                        ui.label("• Kinh nghiệm sửa xe").classes("text-sm mb-2 cursor-pointer hover:text-primary")
                        ui.label("• Review đơn vị cứu hộ").classes("text-sm mb-2 cursor-pointer hover:text-primary")
                        ui.label("• Cảnh báo đoạn đường xấu").classes("text-sm cursor-pointer hover:text-primary")

            # --- Logic ---
            async def refresh_posts():
                posts_container.clear()
                posts = await get_posts()
                with posts_container:
                    if not posts:
                        ui.label("Chưa có bài đăng nào.").classes("italic opacity-50 py-20 self-center")
                    for p in posts:
                        _render_post_card(p)

            def _render_post_card(p):
                with ui.card().classes("w-full rounded-3xl p-6 border border-surface-variant/30 hover:border-primary/50 transition-all cursor-pointer") \
                    .on('click', lambda: _open_post_detail(p['id'])):
                    with ui.row().classes("w-full justify-between items-start"):
                        ui.badge(p.get('incident_type', 'Thảo luận')).classes("rounded-full px-3")
                        ui.label(p['created_at'][:10]).classes("text-xs opacity-50")
                    
                    ui.label(p['title']).classes("text-xl font-bold mt-2 font-outfit")
                    ui.label(p['content']).classes("text-sm opacity-70 line-clamp-2 mt-2")
                    
                    with ui.row().classes("w-full mt-4 items-center justify-between"):
                        with ui.row().classes("items-center gap-2"):
                            ui.avatar(icon="person").classes("w-6 h-6 bg-primary/10 text-primary")
                            ui.label(p['user_name']).classes("text-xs font-bold")
                        
                        with ui.row().classes("items-center gap-4"):
                            with ui.row().classes("items-center gap-1"):
                                ui.icon("chat_bubble_outline", size="xs").classes("opacity-50")
                                ui.label(str(p.get('reply_count', 0))).classes("text-xs opacity-50")

            def _open_create_dialog():
                with ui.dialog() as d, ui.card().classes("p-8 rounded-3xl w-[500px]"):
                    ui.label("Tạo bài đăng mới").classes("text-2xl font-bold mb-6 font-outfit text-primary")
                    title = ui.input("Tiêu đề").classes("w-full mb-4").props("outlined rounded")
                    incident = ui.select(["Hỏng máy", "Thủng lốp", "Hết xăng", "Tai nạn", "Khác"], label="Chủ đề") \
                        .classes("w-full mb-4").props("outlined rounded")
                    content = ui.textarea("Nội dung").classes("w-full mb-6").props("outlined rounded")
                    
                    with ui.row().classes("w-full justify-end gap-3"):
                        ui.button("ĐÓNG", on_click=d.close).props("flat")
                        async def submit():
                            if await create_post(title.value, content.value, incident.value):
                                ui.notify("Đã đăng bài thành công!", type='positive')
                                d.close()
                                await refresh_posts()
                        ui.button("ĐĂNG BÀI", on_click=submit).classes("bg-primary text-white px-8 rounded-xl")
                d.open()

            async def _open_post_detail(post_id):
                p = await get_post_detail(post_id)
                if not p: return
                
                with ui.dialog() as d, ui.card().classes("p-0 rounded-3xl w-[800px] overflow-hidden"):
                    with ui.column().classes("w-full p-8"):
                        # Header
                        with ui.row().classes("w-full justify-between items-center mb-4"):
                            ui.button(icon="arrow_back", on_click=d.close).props("flat round color=primary")
                            ui.badge(p['incident_type']).classes("rounded-full px-4")
                        
                        ui.label(p['title']).classes("text-3xl font-bold font-outfit mb-4")
                        with ui.row().classes("items-center gap-3 mb-6"):
                            ui.avatar(icon="person").classes("bg-primary/10 text-primary")
                            with ui.column().classes("gap-0"):
                                ui.label(p['user_name']).classes("font-bold")
                                ui.label(p['created_at']).classes("text-xs opacity-50")
                        
                        ui.label(p['content']).classes("text-lg opacity-80 mb-8 whitespace-pre-wrap")
                        
                        ui.separator().classes("mb-6")
                        
                        # Replies
                        ui.label(f"Bình luận ({len(p['replies'])})").classes("text-xl font-bold mb-4 font-outfit")
                        with ui.column().classes("w-full gap-4 mb-8"):
                            for r in p['replies']:
                                with ui.card().classes("w-full rounded-2xl p-4 bg-surface-variant/10 border-none"):
                                    with ui.row().classes("w-full justify-between"):
                                        ui.label(r['user_name']).classes("font-bold text-sm text-primary")
                                        ui.label(r['created_at'][:16]).classes("text-[10px] opacity-40")
                                    ui.label(r['content']).classes("mt-1 text-sm")
                                    if r.get('is_helpful'):
                                        ui.badge("HỮU ÍCH").classes("bg-green-100 text-green-700 mt-2 px-2 text-[10px]")

                        # Reply input
                        with ui.row().classes("w-full gap-2 items-center"):
                            reply_input = ui.input(placeholder="Viết bình luận...").classes("flex-1").props("outlined rounded dense")
                            async def send_r():
                                if await create_reply(post_id, reply_input.value):
                                    ui.notify("Đã gửi bình luận")
                                    d.close()
                                    await _open_post_detail(post_id)
                            ui.button(icon="send", on_click=send_r).props("round unelevated color=primary")
                d.open()

            await refresh_posts()
