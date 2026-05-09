"""
Standard Page Layout – consistent wrapper for all pages.
"""
from nicegui import ui
from contextlib import contextmanager
from components.navbar import create_navbar

@contextmanager
def page_layout(current_route: str = "", title: str = "Hệ thống cứu hộ"):
    """
    Context manager to wrap page content with standard navbar and styling.
    Usage:
    with page_layout("/route", "Page Title"):
        ui.label("Content")
    """
    # 1. Navbar
    create_navbar(current_route)
    
    # 2. Main content container
    with ui.column().classes("w-full min-h-screen bg-[#fdfbff]"):
        # Header / Hero area (optional decoration)
        with ui.column().classes("w-full p-6 md:p-10 max-w-7xl mx-auto gap-6"):
            # Breadcrumbs or simple title
            with ui.row().classes("items-center gap-2"):
                ui.label(title).classes("text-3xl md:text-4xl font-bold text-[#001b3e] font-outfit tracking-tight")
            
            # This is where the page content will go
            yield
            
    # 3. Footer
    with ui.footer().classes("bg-[#fdfbff] border-t border-[#e0e2ec] py-8"):
        with ui.row().classes("w-full max-w-7xl mx-auto px-6 justify-between items-center"):
            with ui.column().classes("gap-1"):
                ui.label("© 2024 Roadside Assistance System").classes("text-sm text-[#44474e] font-medium")
                ui.label("Hỗ trợ kỹ thuật 24/7: 1900 1234").classes("text-xs text-[#74777f]")
            with ui.row().classes("gap-4"):
                ui.link("Điều khoản", "#").classes("text-sm text-[#005fb0]")
                ui.link("Bảo mật", "#").classes("text-sm text-[#005fb0]")
