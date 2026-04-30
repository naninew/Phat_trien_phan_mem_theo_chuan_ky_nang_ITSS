"""
Customer dashboard page for NiceGUI frontend.
"""
from nicegui import ui
from frontend.core.auth import require_auth, get_current_user, get_user_role, logout_user, CUSTOMER_DASHBOARD
from frontend.components.navbar import create_navbar


def create_customer_dashboard():
    """Create customer dashboard page with NiceGUI components."""
    
    @ui.page(CUSTOMER_DASHBOARD)
    def customer_dashboard():
        # Require authentication
        if not require_auth():
            return
        
        # Require customer role
        user_role = get_user_role()
        if user_role != 'customer' and user_role != 'admin':
            ui.notify("Access denied", color="negative")
            ui.navigate.to(CUSTOMER_DASHBOARD)
            return
        
        create_navbar("Customer Dashboard")
        
        user = get_current_user()
        
        with ui.column().classes('w-full p-8'):
            # Welcome header
            with ui.row().classes('w-full items-center justify-between'):
                ui.label(f"Welcome, {user.get('full_name', 'User')}!").classes('text-2xl font-bold')
                
                with ui.row().classes('gap-2'):
                    ui.button(icon='refresh', on_click=lambda: ui.navigate.reload()).props('round dense flat')
            
            # Quick actions cards
            ui.label('Quick Actions').classes('text-xl font-semibold mt-8')
            
            with ui.row().classes('w-full gap-4 mt-4'):
                # Request Rescue Card
                with ui.card().classes('flex-1 min-w-[250px]'):
                    ui.icon('emergency', size='xl').classes('text-primary')
                    ui.label('Request Rescue').classes('text-lg font-bold mt-2')
                    ui.label('Get immediate help for your vehicle').classes('text-gray-600')
                    ui.button('Request Now', on_click=lambda: ui.navigate.to('/customer/find-rescue')).classes('mt-4 w-full')
                
                # My Requests Card
                with ui.card().classes('flex-1 min-w-[250px]'):
                    ui.icon('list_alt', size='xl').classes('text-secondary')
                    ui.label('My Requests').classes('text-lg font-bold mt-2')
                    ui.label('View and track your rescue requests').classes('text-gray-600')
                    ui.button('View Requests', on_click=lambda: ui.navigate.to('/customer/requests')).classes('mt-4 w-full')
                
                # Community Card
                with ui.card().classes('flex-1 min-w-[250px]'):
                    ui.icon('people', size='xl').classes('text-accent')
                    ui.label('Community').classes('text-lg font-bold mt-2')
                    ui.label('Get advice from other drivers').classes('text-gray-600')
                    ui.button('Join Community', on_click=lambda: ui.navigate.to('/customer/community')).classes('mt-4 w-full')
            
            # Recent activity section
            ui.label('Recent Activity').classes('text-xl font-semibold mt-8')
            
            with ui.card().classes('w-full mt-4'):
                ui.label('No recent activity').classes('text-gray-500 p-4')
            
            # Profile summary
            with ui.card().classes('w-full mt-4'):
                ui.label('Profile Summary').classes('text-lg font-bold')
                with ui.grid(columns=2).classes('w-full mt-2'):
                    ui.label('Name:')
                    ui.label(user.get('full_name', 'N/A'))
                    ui.label('Phone:')
                    ui.label(user.get('phone', 'N/A'))
                    ui.label('Email:')
                    ui.label(user.get('email', 'N/A'))

