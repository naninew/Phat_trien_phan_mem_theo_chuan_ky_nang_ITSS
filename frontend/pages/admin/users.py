"""
Admin users management page for NiceGUI frontend.
"""
from nicegui import ui
from typing import Optional, Dict, Any, List
from frontend.core.auth import require_auth, get_current_user, get_access_token, ADMIN_DASHBOARD
from frontend.components.navbar import create_navbar


def create_users_page():
    """Create admin users management page with NiceGUI components."""
    
    @ui.page('/admin/users')
    def users_page():
        # Require authentication and admin role
        if not require_auth():
            return
        
        user_role = get_user_role()
        if user_role != 'admin':
            ui.notify("Access denied - Admin only", color="negative")
            ui.navigate.to(ADMIN_DASHBOARD)
            return
        
        create_navbar("User Management")
        
        with ui.column().classes('w-full p-8'):
            with ui.row().classes('w-full items-center justify-between'):
                ui.label('System Users').classes('text-2xl font-bold')
                
                # Role filter
                role_filter = ui.select(
                    options=['all', 'customer', 'company_staff', 'admin'],
                    label='Filter by Role',
                    value='all'
                ).classes('w-full max-w-xs')
            
            # Refresh button
            ui.button(icon='refresh', on_click=lambda: load_users()).props('round dense flat')
            
            # Users container
            users_container = ui.column().classes('w-full mt-4')
            
            # Role colors
            role_colors = {
                'customer': 'blue',
                'company_staff': 'green',
                'admin': 'red',
            }
            
            async def load_users():
                """Load and display all users."""
                token = get_access_token()
                
                with users_container:
                    users_container.clear()
                    
                    # Mock data for demonstration
                    mock_users = [
                        {
                            'id': 1,
                            'username': 'admin',
                            'full_name': 'System Administrator',
                            'email': 'admin@system.com',
                            'phone': '0901111111',
                            'role': 'admin',
                            'is_active': True,
                        },
                        {
                            'id': 2,
                            'username': 'customer1',
                            'full_name': 'Nguyen Van A',
                            'email': 'customer@example.com',
                            'phone': '0902222222',
                            'role': 'customer',
                            'is_active': True,
                        },
                        {
                            'id': 3,
                            'username': 'company1',
                            'full_name': 'Rescue Company Staff',
                            'email': 'staff@rescue.com',
                            'phone': '0903333333',
                            'role': 'company_staff',
                            'is_active': True,
                        },
                    ]
                    
                    # Filter by role
                    filter_val = role_filter.value
                    if filter_val != 'all':
                        mock_users = [u for u in mock_users if u.get('role') == filter_val]
                    
                    if not mock_users:
                        ui.label('No users found').classes('text-gray-500 p-4')
                        return
                    
                    for user in mock_users:
                        user_id = user.get('id')
                        role = user.get('role', 'unknown')
                        is_active = user.get('is_active', False)
                        
                        with ui.card().classes('w-full p-4 mb-4'):
                            with ui.row().classes('w-full items-center justify-between'):
                                ui.label(f'{user.get("full_name")} (@{user.get("username")})').classes('text-lg font-bold')
                                with ui.row().classes('gap-2'):
                                    ui.badge(role, color=role_colors.get(role, 'gray'))
                                    ui.badge('Active' if is_active else 'Inactive', color='green' if is_active else 'red')
                            
                            ui.label(f'Email: {user.get("email")}').classes('text-gray-600')
                            ui.label(f'Phone: {user.get("phone")}').classes('text-gray-600')
                            
                            # Action buttons
                            with ui.row().classes('w-full gap-2 mt-2'):
                                async def edit_user(u=user):
                                    """Edit user details."""
                                    ui.notify(f'Edit user {u.get("username")}', color='info')
                                
                                async def toggle_status(u=user):
                                    """Toggle user active status."""
                                    new_status = 'inactive' if u.get('is_active') else 'active'
                                    ui.notify(f'User {u.get("username")} marked as {new_status}', color='info')
                                    await load_users()
                                
                                async def delete_user(u=user):
                                    """Delete a user."""
                                    confirmed = await ui.dialog(
                                        title='Confirm Delete',
                                        message=f'Are you sure you want to delete user {u.get("username")}?',
                                        persistent=True
                                    ).wait()
                                    
                                    if confirmed:
                                        ui.notify(f'User {u.get("username")} deleted', color='positive')
                                        await load_users()
                                
                                ui.button('Edit', on_click=edit_user).props('outline')
                                ui.button('Toggle Status', on_click=toggle_status).props('outline')
                                ui.button('Delete', on_click=delete_user).props('color=negative outline')
            
            # Initial load
            ui.timer(1.0, load_users, once=True)

