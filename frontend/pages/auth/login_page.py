"""
Login page for NiceGUI frontend.
"""
from nicegui import ui
from ..services.auth_api import login
from ..core.auth import login_user, get_redirect_url_for_role, is_authenticated, LOGIN_PAGE
from ..core.config import CUSTOMER_DASHBOARD
from ..components.navbar import create_navbar


def create_login_page():
    """Create login page with NiceGUI components."""
    
    @ui.page(LOGIN_PAGE)
    def login_page():
        # Check if already logged in
        if is_authenticated():
            ui.navigate.to(CUSTOMER_DASHBOARD)
            return
        
        create_navbar("Login")
        
        with ui.column().classes('w-full items-center justify-center min-h-screen p-8'):
            with ui.card().classes('w-full max-w-md p-8'):
                ui.label('Login').classes('text-2xl font-bold mb-4')
                
                username = ui.input(label='Username').classes('w-full')
                password = ui.input(label='Password', password=True, password_toggle_button=True).classes('w-full')
                
                error_label = ui.label('').classes('text-red-500 mt-2')
                
                async def do_login():
                    """Handle login action."""
                    if not username.value or not password.value:
                        error_label.set_text('Please enter username and password')
                        return
                    
                    try:
                        result = await login(username.value, password.value)
                        
                        if result and 'access_token' in result:
                            user_info = result.get('user', {})
                            role = user_info.get('role', 'customer')
                            
                            # Store in session
                            login_user(result['access_token'], user_info, role)
                            
                            # Redirect to appropriate dashboard
                            redirect_url = get_redirect_url_for_role(role)
                            ui.notify('Login successful!', color='positive')
                            ui.navigate.to(redirect_url)
                        else:
                            error_label.set_text('Invalid credentials')
                    except Exception as e:
                        error_label.set_text(f'Login failed: {str(e)}')
                
                ui.button('Login', on_click=do_login).classes('w-full mt-4')
                
                with ui.row().classes('w-full justify-center mt-4'):
                    ui.label("Don't have an account?")
                    ui.link('Register', '/register').classes('text-primary')

