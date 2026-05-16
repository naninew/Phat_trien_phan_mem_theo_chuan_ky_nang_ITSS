"""
Standard Page Layout – consistent wrapper for all pages.
"""
from nicegui import ui
from contextlib import contextmanager
from components.navbar import create_navbar
from components.sidebar import create_sidebar
from core.auth import is_authenticated

@contextmanager
def page_layout(current_route: str = "", title: str = "Rescue24"):
    """
    Context manager to wrap page content with standard navbar, sidebar, and styling.
    """
    # 1. Navbar
    create_navbar()
    
    # 2. Sidebar (only for authenticated users)
    if is_authenticated():
        create_sidebar()

    # 3. Main content container
    # If authenticated, we need to account for sidebar width (drawer usually handles this in NiceGUI)
    with ui.column().classes("w-full min-h-screen bg-surface"):
        # Spacer for fixed navbar
        ui.element('div').classes('h-16 w-full')
        
        with ui.column().classes("w-full p-4 md:p-8 max-w-7xl mx-auto gap-6"):
            # Page Title Area
            if title:
                with ui.row().classes("items-center justify-between w-full mb-4"):
                    ui.label(title).classes("text-3xl font-bold text-on-surface font-outfit tracking-tight")
            
            # This is where the page content will go
            yield
            
    # 4. Footer
    with ui.footer().classes("bg-surface border-t border-surface-variant py-6 mt-auto"):
        with ui.row().classes("w-full max-w-7xl mx-auto px-6 justify-between items-center"):
            ui.label("© 2026 Roadside Assistance System").classes("text-sm text-on-surface-variant")
            with ui.row().classes("gap-6"):
                ui.label("Hotline: 1900 2424").classes("text-sm font-bold text-primary")
