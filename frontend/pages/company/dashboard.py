"""
Company dashboard page for NiceGUI frontend.
"""
from nicegui import ui
from frontend.core.auth import require_auth, get_current_user, get_user_role, COMPANY_DASHBOARD
from frontend.components.navbar import create_navbar


def create_company_dashboard():
    """Create company dashboard page with NiceGUI components."""
    
    @ui.page(COMPANY_DASHBOARD)
    def company_dashboard():
        # Require authentication
        if not require_auth():
            return
        
        # Require company staff role
        user_role = get_user_role()
        if user_role != 'company_staff' and user_role != 'admin':
            ui.notify("Access denied", color="negative")
            ui.navigate.to(COMPANY_DASHBOARD)
            return
        
        create_navbar("Company Dashboard")
        
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
                # Queue Management Card
                with ui.card().classes('flex-1 min-w-[250px]'):
                    ui.icon('queue', size='xl').classes('text-primary')
                    ui.label('Queue Management').classes('text-lg font-bold mt-2')
                    ui.label('View and manage rescue requests').classes('text-gray-600')
                    ui.button('View Queue', on_click=lambda: ui.navigate.to('/company/queue')).classes('mt-4 w-full')
                
                # Fleet Management Card
                with ui.card().classes('flex-1 min-w-[250px]'):
                    ui.icon('directions_car', size='xl').classes('text-secondary')
                    ui.label('Fleet Management').classes('text-lg font-bold mt-2')
                    ui.label('Manage your rescue vehicles').classes('text-gray-600')
                    ui.button('Manage Fleet', on_click=lambda: ui.navigate.to('/company/fleet')).classes('mt-4 w-full')
                
                # Profile Card
                with ui.card().classes('flex-1 min-w-[250px]'):
                    ui.icon('account_circle', size='xl').classes('text-accent')
                    ui.label('Company Profile').classes('text-lg font-bold mt-2')
                    ui.label('Update company information').classes('text-gray-600')
                    ui.button('View Profile', on_click=lambda: ui.navigate.to('/company/profile')).classes('mt-4 w-full')
            
            # Statistics section
            ui.label('Today\'s Statistics').classes('text-xl font-semibold mt-8')
            
            with ui.row().classes('w-full gap-4 mt-4'):
                with ui.card().classes('flex-1 p-4'):
                    ui.label('Pending Requests').classes('text-3xl font-bold text-orange-600')
                    ui.label('0').classes('text-gray-600')
                
                with ui.card().classes('flex-1 p-4'):
                    ui.label('In Progress').classes('text-3xl font-bold text-blue-600')
                    ui.label('0').classes('text-gray-600')
                
                with ui.card().classes('flex-1 p-4'):
                    ui.label('Completed Today').classes('text-3xl font-bold text-green-600')
                    ui.label('0').classes('text-gray-600')
            
            # Recent activity section
            ui.label('Recent Activity').classes('text-xl font-semibold mt-8')
            
            with ui.card().classes('w-full mt-4'):
                ui.label('No recent activity').classes('text-gray-500 p-4')

