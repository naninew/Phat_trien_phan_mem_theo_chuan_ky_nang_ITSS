"""
Reusable Dialog for Company Details & Reviews.
"""
from nicegui import ui
import httpx
from core.auth import get_access_token
from core.config import BACKEND_URL

def open_company_detail(company_id: int):
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # State
    data = {"info": {}, "reviews": [], "history": []}

    async def _load_details():
        loading_bar.set_visibility(True)
        try:
            async with httpx.AsyncClient() as client:
                r = await client.get(f"{BACKEND_URL}/rescue/companies/{company_id}/full-details", headers=headers, timeout=10)
                if r.status_code == 200:
                    res = r.json()["data"]
                    data["info"] = res
                    data["reviews"] = res.get("reviews", [])
                    data["history"] = res.get("my_history", [])
                    _render_ui()
                else:
                    ui.notify(f"Không thể tải chi tiết: {r.status_code}", type="negative")
                    dialog.close()
        except Exception as e:
            ui.notify(f"Lỗi kết nối chi tiết: {e}", type="negative")
            dialog.close()
        finally:
            loading_bar.set_visibility(False)

    def _render_ui():
        info_container.clear()
        info = data["info"]
        
        with info_container:
            with ui.scroll_area().classes('w-full max-h-[85vh]'):
                # Header with Image (Mock)
                with ui.row().classes('w-full h-48 bg-gradient-to-r from-primary/20 to-indigo-100 items-center justify-center relative'):
                    ui.icon('business', size='4rem', color='primary').classes('opacity-30')
                    ui.button(icon='close', on_click=dialog.close).props('round flat color=white').classes('absolute top-4 right-4 bg-black/10')

                # Body
                with ui.column().classes('w-full p-8 gap-6'):
                    # Basic Info
                    with ui.row().classes('w-full justify-between items-start'):
                        with ui.column().classes('gap-1'):
                            ui.label(info['company_name']).classes('text-3xl font-bold text-on-surface font-outfit')
                            ui.label(info['address']).classes('text-on-surface-variant flex items-center gap-2')
                        
                        with ui.column().classes('items-end'):
                            ui.label(f"⭐ {info['rating_avg']:.1f}").classes('text-2xl font-bold text-amber-600')
                            ui.label(f"{info['rating_count']} lượt đánh giá").classes('text-xs text-on-surface-variant')

                    ui.separator()

                    # Description
                    if info.get('description'):
                        with ui.column().classes('w-full gap-2'):
                            ui.label('Giới thiệu').classes('font-bold text-lg')
                            ui.label(info['description']).classes('text-on-surface-variant text-sm leading-relaxed')

                    # Reviews Section
                    ui.label(f"Đánh giá gần đây ({len(data['reviews'])})").classes('font-bold text-lg mt-4')
                    if not data['reviews']:
                        ui.label("Chưa có đánh giá nào.").classes("text-on-surface-variant italic opacity-50")
                    else:
                        with ui.column().classes('w-full gap-4'):
                            for rev in data['reviews'][:10]: # Show up to 10
                                with ui.card().classes('w-full m3-card p-4 bg-surface-variant/10 shadow-none border border-surface-variant/20'):
                                    with ui.row().classes('w-full justify-between items-center'):
                                        ui.label(rev['customer_name']).classes('font-bold text-sm')
                                        ui.label(f"⭐ {rev['rating']}").classes('text-amber-600 font-bold')
                                    ui.label(rev['comment']).classes('text-sm text-on-surface-variant italic mt-1')
                                    ui.label(f"Dịch vụ: {rev.get('service_name', 'N/A')} • {rev['created_at'][:10]}").classes('text-[10px] text-on-surface-variant/60 mt-2')

                    # Actions
                    with ui.row().classes('w-full gap-4 mt-8'):
                        ui.button('GỌI HOTLINE', icon='phone', on_click=lambda: ui.navigate.to(f"tel:{info['hotline']}")).classes('flex-1 py-4 btn-primary')
                        ui.button('TÌM CỨU HỘ', icon='near_me', on_click=lambda: (dialog.close(), ui.navigate.to('/customer/find-rescue'))).props('outline').classes('flex-1 py-4')

    # --- Dialog Structure ---
    with ui.dialog() as dialog, ui.card().classes('w-full max-w-3xl p-0 overflow-hidden rounded-3xl shadow-2xl'):
        loading_bar = ui.linear_progress(value=0, show_value=False).classes('w-full absolute top-0 z-10')
        info_container = ui.column().classes('w-full h-full')
        
    ui.timer(0.1, _load_details, once=True)
    dialog.open()
