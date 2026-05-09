"""
Navigation Bar Component – tự lấy role/name từ session NiceGUI.
Không cần truyền user_role hay user_name qua tham số nữa.
"""
from nicegui import ui
from typing import Optional, List, Dict, Callable

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
    Tạo navigation bar responsive với thiết kế Material 3.
    """
    role = get_user_role() or ""
    name = get_user_name()
    items = MENU_ITEMS.get(role, [])

    with ui.header().classes(
        "shadow-md sticky top-0 z-50 py-1"
    ).style("background: #1a73e8; border-bottom: 1px solid rgba(255,255,255,0.1)"):
        with ui.row().classes("w-full items-center justify-between px-6 max-w-7xl mx-auto"):

            # ── Logo + Title ────────────────────────────────────────────────
            with ui.row().classes("items-center gap-3 cursor-pointer group").on(
                "click", lambda: ui.navigate.to(
                    items[0]["route"] if items else "/login"
                )
            ):
                with ui.element('div').classes('p-2 bg-white/20 rounded-xl group-hover:scale-110 transition-transform'):
                    ui.icon("local_taxi", size="1.8rem").classes("text-white")
                ui.label("Rescue System").classes("text-[#f0f4f8] font-bold text-xl font-outfit tracking-tight")

            # ── Desktop menu ────────────────────────────────────────────────
            with ui.row().classes("hidden md:flex items-center gap-2"):
                for item in items:
                    is_active = current_route.startswith(item["route"])
                    if is_active:
                        btn = ui.button(item["label"], icon=item["icon"], 
                                      on_click=lambda r=item["route"]: ui.navigate.to(r))
                        btn.classes("px-4 py-2 rounded-full font-bold bg-primary-container text-primary shadow-none").props("unelevated")
                    else:
                        btn = ui.button(item["label"], icon=item["icon"],
                                      on_click=lambda r=item["route"]: ui.navigate.to(r))
                        btn.classes("px-4 py-2 rounded-full font-medium text-on-surface-variant hover:bg-surface-variant transition-colors").props("flat")

            # ── Right: user info + logout ───────────────────────────────────
            with ui.row().classes("items-center gap-3"):
                # User info (desktop)
                with ui.row().classes("hidden lg:flex items-center gap-3 pr-4 border-r border-white/20 cursor-pointer hover:opacity-80 transition-opacity").on('click', lambda: ui.navigate.to("/profile")):
                    with ui.column().classes("gap-0 items-end"):
                        ui.label(name).classes("text-[#f0f4f8] font-semibold text-sm")
                        ui.label(role.replace("_", " ").title()).classes("text-white/60 text-[10px] opacity-70")
                    ui.avatar('person', color='white', text_color='#1a73e8').classes('shadow-sm')

                # Logout
                ui.button(
                    icon="logout",
                    on_click=logout_user,
                ).classes("text-[#f0f4f8] hover:bg-white/10 rounded-full").props("flat round").tooltip("Đăng xuất")

                # ── Mobile hamburger ────────────────────────────────────────
                with ui.button(icon="menu").classes("md:hidden text-[#f0f4f8]").props("flat round") as ham_btn:
                    pass

    # ── Mobile drawer ───────────────────────────────────────────────────
    with ui.drawer(side="right", elevated=True).classes("bg-surface w-72") as mobile_drawer:
        with ui.column().classes("p-6 gap-4 w-full"):
            # Header in drawer
            with ui.row().classes("items-center gap-3 mb-4 cursor-pointer hover:bg-surface-variant p-2 rounded-xl transition-colors w-full").on('click', lambda: (mobile_drawer.hide(), ui.navigate.to("/profile"))):
                ui.avatar('person', color='primary', text_color='#f0f4f8')
                with ui.column().classes("gap-0"):
                    ui.label(name).classes("text-on-surface font-bold")
                    ui.label(role).classes("text-on-surface-variant text-xs")

            ui.separator().classes("mb-2")

            for item in items:
                is_active = current_route.startswith(item["route"])
                btn = ui.button(
                    item["label"],
                    icon=item["icon"],
                    on_click=lambda r=item["route"]: (mobile_drawer.hide(), ui.navigate.to(r)),
                ).classes(
                    "w-full justify-start rounded-2xl px-4 py-3 " +
                    ("bg-primary-container text-primary font-bold" if is_active else "text-on-surface-variant hover:bg-surface-variant")
                ).props("flat")

            ui.separator().classes("mt-4 mb-2")
            ui.button(
                "Đăng Xuất",
                icon="logout",
                on_click=lambda: (mobile_drawer.hide(), logout_user()),
            ).classes("w-full justify-start text-error hover:bg-red-50 rounded-2xl px-4 py-3").props("flat")

    ham_btn.on("click", lambda: mobile_drawer.toggle())
