"""
Admin dashboard page for NiceGUI frontend.
"""
from nicegui import ui
from frontend.core.auth import require_auth, get_current_user, get_user_role, ADMIN_DASHBOARD
from frontend.components.navbar import create_navbar


def create_admin_dashboard():
    """Create admin dashboard page with NiceGUI components."""
    
    @ui.page(ADMIN_DASHBOARD)
    def admin_dashboard():
        # Require authentication
        if not require_auth():
            return
        
        # Require admin role
        user_role = get_user_role()
        if user_role != 'admin':
            ui.notify("Access denied - Admin only", color="negative")
            ui.navigate.to(ADMIN_DASHBOARD)
            return
        
        create_navbar("Admin Dashboard")
        
        user = get_current_user()
        
        with ui.column().classes('w-full p-8'):
            # Welcome header
            with ui.row().classes('w-full items-center justify-between'):
                ui.label(f"Welcome, Administrator {user.get('full_name', 'User')}!").classes('text-2xl font-bold')
                
                with ui.row().classes('gap-2'):
                    ui.button(icon='refresh', on_click=lambda: ui.navigate.reload()).props('round dense flat')
            
            # Quick navigation cards
            ui.label('Administration').classes('text-xl font-semibold mt-8')
            
            with ui.row().classes('w-full gap-4 mt-4'):
                # Users Management Card
                with ui.card().classes('flex-1 min-w-[250px]'):
                    ui.icon('people', size='xl').classes('text-primary')
                    ui.label('User Management').classes('text-lg font-bold mt-2')
                    ui.label('Manage all system users').classes('text-gray-600')
                    ui.button('Manage Users', on_click=lambda: ui.navigate.to('/admin/users')).classes('mt-4 w-full')
                
                # Companies Management Card
                with ui.card().classes('flex-1 min-w-[250px]'):
                    ui.icon('business', size='xl').classes('text-secondary')
                    ui.label('Company Management').classes('text-lg font-bold mt-2')
                    ui.label('Manage rescue companies').classes('text-gray-600')
                    ui.button('Manage Companies', on_click=lambda: ui.navigate.to('/admin/companies')).classes('mt-4 w-full')
                
                # Moderation Card
                with ui.card().classes('flex-1 min-w-[250px]'):
                    ui.icon('fact_check', size='xl').classes('text-accent')
                    ui.label('Content Moderation').classes('text-lg font-bold mt-2')
                    ui.label('Review and moderate content').classes('text-gray-600')
                    ui.button('Moderation', on_click=lambda: ui.navigate.to('/admin/moderation')).classes('mt-4 w-full')
                
                # Reports Card
                with ui.card().classes('flex-1 min-w-[250px]'):
                    ui.icon('analytics', size='xl').classes('text-positive')
                    ui.label('Reports & Analytics').classes('text-lg font-bold mt-2')
                    ui.label('View system reports').classes('text-gray-600')
                    ui.button('View Reports', on_click=lambda: ui.navigate.to('/admin/reports')).classes('mt-4 w-full')
            
            # System statistics
            ui.label('System Statistics').classes('text-xl font-semibold mt-8')
            
            with ui.row().classes('w-full gap-4 mt-4'):
                with ui.card().classes('flex-1 p-4'):
                    ui.label('Total Users').classes('text-3xl font-bold text-blue-600')
                    ui.label('0').classes('text-gray-600')
                
                with ui.card().classes('flex-1 p-4'):
                    ui.label('Active Companies').classes('text-3xl font-bold text-green-600')
                    ui.label('0').classes('text-gray-600')
                
                with ui.card().classes('flex-1 p-4'):
                    ui.label('Total Requests').classes('text-3xl font-bold text-purple-600')
                    ui.label('0').classes('text-gray-600')
                
                with ui.card().classes('flex-1 p-4'):
                    ui.label('Pending Reviews').classes('text-3xl font-bold text-orange-600')
                    ui.label('0').classes('text-gray-600')
            
            # Recent activity section
            ui.label('Recent System Activity').classes('text-xl font-semibold mt-8')
            
            with ui.card().classes('w-full mt-4'):
                ui.label('No recent activity').classes('text-gray-500 p-4')

