"""
Navigation Bar Component – Tối ưu giao diện Material 3 & Trải nghiệm UX chuyên nghiệp.
"""
from nicegui import ui
from typing import List, Dict
from core.auth import get_user_role, get_user_name, logout_user

APP_TITLE = "🚑 Cứu Hộ Xe"

MENU_ITEMS: Dict[str, List[Dict]] = {
    "customer": [
        {"label": "Trang Chủ",       "icon": "home",       "route": "/customer/dashboard"},
        {"label": "Tìm Cứu Hộ",      "icon": "search",     "route": "/customer/find-rescue"},
        {"label": "Yêu Cầu Của Tôi", "icon": "list",       "route": "/customer/requests"},
    ],
    "company_staff": [
        {"label": "Tổng Quan",    "icon": "dashboard",   "route": "/company/dashboard"},
        {"label": "Hàng Đợi",    "icon": "queue",       "route": "/company/queue"},
        {"label": "Đội Xe",      "icon": "directions_car", "route": "/company/fleet"},
        {"label": "Hồ Sơ Cty",  "icon": "business",    "route": "/company/profile"},
    ],
    "admin": [
        {"label": "Tổng Quan",     "icon": "dashboard",   "route": "/admin/dashboard"},
        {"label": "Người Dùng",    "icon": "people",      "route": "/admin/users"},
        {"label": "Công Ty",       "icon": "business",    "route": "/admin/companies"},
    ],
}

def create_navbar(current_route: str = "") -> None:
    """
    Tạo Navigation Bar responsive, chuẩn UX/UI chuyên nghiệp.
    """
    role = get_user_role() or ""
    name = get_user_name() or "Người dùng"
    items = MENU_ITEMS.get(role, [])

    # ── BƯỚC 1: KHỞI TẠO HEADER TRƯỚC ───────────────────────────────────
    with ui.header().classes("shadow-sm sticky top-0 z-50 py-0").style(
        "background: linear-gradient(135deg, #1a73e8 0%, #1557b0 100%); backdrop-filter: blur(8px);"
    ):
        with ui.row().classes("w-full items-center justify-between px-4 md:px-8 max-w-7xl mx-auto h-16"):

            # ── Brand Logo & Name ───────────────────────────────────────────
            home_route = items[0]["route"] if items else "/login"
            with ui.row().classes("items-center gap-3 cursor-pointer group").on("click", lambda: ui.navigate.to(home_route)):
                with ui.element('div').classes(
                    'p-2 bg-white/15 rounded-xl group-hover:bg-white/25 group-hover:scale-105 transition-all shadow-inner'
                ):
                    ui.icon("local_taxi", size="1.6rem").classes("text-white")
                ui.label("Rescue System").classes(
                    "text-white font-extrabold text-xl tracking-tight font-outfit"
                )

            # ── Desktop Navigation Menu ─────────────────────────────────────
            with ui.row().classes("hidden md:flex items-center gap-1 h-full"):
                for item in items:
                    is_active = current_route.startswith(item["route"])
                    btn = ui.button(
                        item["label"], 
                        icon=item["icon"], 
                        on_click=lambda r=item["route"]: ui.navigate.to(r)
                    ).classes("px-4 py-2 rounded-xl text-sm font-medium capitalize transition-all duration-200")
                    
                    if is_active:
                        btn.classes("bg-white text-blue-700 font-bold shadow-sm").props("unelevated")
                    else:
                        btn.classes("text-white/85 hover:text-white hover:bg-white/10").props("flat")

            # ── Right Utilities (User info + Actions) ──────────────────────
            with ui.row().classes("items-center gap-2"):
                
                # User Profile Widget (Desktop)
                with ui.row().classes(
                    "hidden lg:flex items-center gap-3 pl-3 pr-1 py-1 rounded-full bg-white/10 border border-white/10 cursor-pointer hover:bg-white/20 transition-all"
                ).on('click', lambda: ui.navigate.to("/profile")):
                    with ui.column().classes("gap-0 items-end pl-2"):
                        ui.label(name).classes("text-white font-semibold text-xs truncate max-w-[120px]")
                        ui.label(role.replace("_", " ").upper()).classes("text-white/60 text-[9px] font-bold tracking-wider")
                    ui.avatar('person', color='white', text_color='#1a73e8').classes('shadow-sm w-8 h-8 min-w-8')

                # Nút Đăng xuất nhanh (Desktop)
                ui.button(
                    icon="logout", 
                    on_click=logout_user
                ).classes("hidden md:inline-flex text-white/80 hover:text-white hover:bg-white/10 rounded-xl").props("flat round").tooltip("Đăng xuất tài khoản")

                # Định nghĩa nút Hamburger Menu (Lưu vào biến ham_btn để cấu hình ở dưới)
                ham_btn = ui.button(icon="menu").classes("md:hidden text-white hover:bg-white/10 rounded-xl p-2").props("flat round")


    # ── BƯỚC 2: KHỞI TẠO DRAWER SAU HEADER ─────────────────────────────
    with ui.drawer(side="right", elevated=True).classes("bg-surface w-72 p-0").props("bordered") as mobile_drawer:
        with ui.column().classes("w-full h-full justify-between p-6"):
            
            # Top Section inside drawer
            with ui.column().classes("w-full gap-4"):
                # User Profile Card in mobile view
                with ui.row().classes(
                    "items-center gap-3 p-3 rounded-xl bg-slate-50 border border-slate-100 w-full cursor-pointer hover:bg-slate-100 transition-colors"
                ).on('click', lambda: (mobile_drawer.hide(), ui.navigate.to("/profile"))):
                    ui.avatar('person', color='primary', text_color='white').classes('shadow-sm')
                    with ui.column().classes("gap-0 overflow-hidden"):
                        ui.label(name).classes("text-slate-900 font-bold text-sm truncate max-w-[160px]")
                        ui.label(role.replace("_", " ").title()).classes("text-slate-500 text-[11px]")

                ui.separator().classes("my-2")

                # Mobile Nav links
                for item in items:
                    is_active = current_route.startswith(item["route"])
                    btn = ui.button(
                        item["label"],
                        icon=item["icon"],
                        on_click=lambda r=item["route"]: (mobile_drawer.hide(), ui.navigate.to(r)),
                    ).classes("w-full justify-start rounded-xl px-4 py-3 text-sm font-medium transition-all").props("flat")
                    
                    if is_active:
                        btn.classes("bg-blue-50 text-blue-600 font-bold").props("unelevated")
                    else:
                        btn.classes("text-slate-700 hover:bg-slate-100")

            # Bottom Section inside drawer (Logout)
            with ui.column().classes("w-full"):
                ui.separator().classes("mb-4")
                ui.button(
                    "Đăng Xuất",
                    icon="logout",
                    on_click=lambda: (mobile_drawer.hide(), logout_user()),
                ).classes("w-full justify-start text-red-600 hover:bg-red-50 rounded-xl px-4 py-3 text-sm font-semibold").props("flat")

    # ── BƯỚC 3: KẾT NỐI SỰ KIỆN CLICK CHO HAMBURGER MENU ───────────────
    ham_btn.on("click", mobile_drawer.toggle)