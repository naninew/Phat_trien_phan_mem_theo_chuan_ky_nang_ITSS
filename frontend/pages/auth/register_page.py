"""
Register page for NiceGUI frontend.
"""
from nicegui import ui
from ..services.auth_api import register
from ..core.auth import login_user, get_redirect_url_for_role, is_authenticated
from ..core.config import CUSTOMER_DASHBOARD, LOGIN_PAGE
from ..components.navbar import create_navbar


def create_register_page():
    """Create registration page with NiceGUI components."""
    
    @ui.page('/register')
    def register_page():
        # Check if already logged in
        if is_authenticated():
            ui.navigate.to(CUSTOMER_DASHBOARD)
            return
        
        create_navbar("Register")
        
        with ui.column().classes('w-full items-center justify-center min-h-screen p-8'):
            with ui.card().classes('w-full max-w-md p-8'):
                ui.label('Create Account').classes('text-2xl font-bold mb-4')
                
                username = ui.input(label='Username').classes('w-full')
                password = ui.input(label='Password', password=True, password_toggle_button=True).classes('w-full')
                confirm_password = ui.input(label='Confirm Password', password=True, password_toggle_button=True).classes('w-full')
                full_name = ui.input(label='Full Name').classes('w-full')
                phone = ui.input(label='Phone Number').classes('w-full')
                email = ui.input(label='Email').classes('w-full')
                
                error_label = ui.label('').classes('text-red-500 mt-2')
                
                async def do_register():
                    """Handle registration action."""
                    # Validation
                    if not all([username.value, password.value, full_name.value, phone.value, email.value]):
                        error_label.set_text('Please fill in all fields')
                        return
                    
                    if password.value != confirm_password.value:
                        error_label.set_text('Passwords do not match')
                        return
                    
                    if len(password.value) < 6:
                        error_label.set_text('Password must be at least 6 characters')
                        return
                    
                    try:
                        result = await register(
                            username=username.value,
                            password=password.value,
                            full_name=full_name.value,
                            phone=phone.value,
                            email=email.value,
                        )
                        
                        if result:
                            ui.notify('Registration successful! Please login.', color='positive')
                            ui.navigate.to(LOGIN_PAGE)
                        else:
                            error_label.set_text('Registration failed')
                    except Exception as e:
                        error_label.set_text(f'Registration failed: {str(e)}')
                
                ui.button('Register', on_click=do_register).classes('w-full mt-4')
                
                with ui.row().classes('w-full justify-center mt-4'):
                    ui.label("Already have an account?")
                    ui.link('Login', LOGIN_PAGE).classes('text-primary')

