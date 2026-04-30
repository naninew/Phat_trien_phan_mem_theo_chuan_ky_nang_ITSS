"""
Responsive Layout Components for NiceGUI Application
Provides mobile-first responsive containers, grids, and layout utilities
"""
from nicegui import ui
from typing import Optional, List, Any
from .theme import SPACING, RADIUS

class ResponsiveContainer:
    """Responsive container with max-width and auto margins"""
    
    def __init__(self, max_width: str = '1280px', padding: str = 'md'):
        self.max_width = max_width
        self.padding = SPACING.get(padding, padding)
        
    def create(self, content_callback=None):
        """Create the responsive container"""
        with ui.element('div').classes(
            f'w-full mx-auto px-{self.padding}'
        ).style(f'max-width: {self.max_width}') as container:
            if content_callback:
                content_callback()
        return container

class Grid:
    """Responsive grid system (mobile-first)"""
    
    def __init__(self, 
                 cols_mobile: int = 1, 
                 cols_tablet: int = 2, 
                 cols_desktop: int = 4,
                 gap: str = 'md'):
        self.cols_mobile = cols_mobile
        self.cols_tablet = cols_tablet
        self.cols_desktop = cols_desktop
        self.gap = SPACING.get(gap, gap)
        
    def create(self, content_callback=None):
        """Create responsive grid"""
        # Using CSS Grid with responsive columns
        grid_style = f'''
            display: grid;
            grid-template-columns: repeat({self.cols_mobile}, 1fr);
            gap: {self.gap};
        '''
        
        with ui.element('div').style(grid_style) as grid:
            # Add media queries via style tag
            ui.add_head_html(f'''
            <style>
                @media (min-width: 640px) {{
                    .grid-{id(grid)} {{
                        grid-template-columns: repeat({self.cols_tablet}, 1fr) !important;
                    }}
                }}
                @media (min-width: 1024px) {{
                    .grid-{id(grid)} {{
                        grid-template-columns: repeat({self.cols_desktop}, 1fr) !important;
                    }}
                }}
            </style>
            ''')
            grid.classes(f'grid-{id(grid)}')
            
            if content_callback:
                content_callback()
                
        return grid

class Card:
    """Modern card component with consistent styling"""
    
    def __init__(self, 
                 title: Optional[str] = None,
                 subtitle: Optional[str] = None,
                 padding: str = 'lg',
                 hover: bool = True,
                 clickable: bool = False):
        self.title = title
        self.subtitle = subtitle
        self.padding = SPACING.get(padding, padding)
        self.hover = hover
        self.clickable = clickable
        
    def create(self, content_callback=None, on_click=None):
        """Create modern card"""
        classes = 'modern-card'
        if self.hover:
            classes += ' cursor-pointer' if self.clickable else ''
            
        with ui.element('div').classes(classes) as card:
            if on_click:
                card.on('click', on_click)
            
            # Header section
            if self.title or self.subtitle:
                with ui.element('div').classes(f'mb-{self.padding}'):
                    if self.title:
                        ui.label(self.title).classes('text-xl font-semibold text-gray-900')
                    if self.subtitle:
                        ui.label(self.subtitle).classes('text-sm text-gray-500 mt-1')
            
            # Content section
            if content_callback:
                content_callback()
                
        return card

class StatCard:
    """Statistics card for dashboards"""
    
    def __init__(self, 
                 title: str,
                 value: str,
                 icon: Optional[str] = None,
                 trend: Optional[str] = None,
                 trend_up: bool = True,
                 color: str = 'primary'):
        self.title = title
        self.value = value
        self.icon = icon
        self.trend = trend
        self.trend_up = trend_up
        self.color = color
        
    def create(self):
        """Create stat card"""
        with Card(padding='lg', hover=False) as card:
            with ui.element('div').classes('flex items-start justify-between'):
                # Left side - Title and Value
                with ui.element('div'):
                    ui.label(self.title).classes('text-sm font-medium text-gray-500')
                    ui.label(self.value).classes('text-3xl font-bold text-gray-900 mt-2')
                    
                    # Trend indicator
                    if self.trend:
                        trend_color = 'text-green-600' if self.trend_up else 'text-red-600'
                        trend_icon = '↑' if self.trend_up else '↓'
                        with ui.element('div').classes(f'flex items-center mt-2 {trend_color}'):
                            ui.label(f'{trend_icon} {self.trend}').classes('text-sm font-medium')
                
                # Right side - Icon
                if self.icon:
                    with ui.element('div').classes(
                        'flex items-center justify-center w-12 h-12 rounded-lg bg-indigo-50'
                    ):
                        ui.html(f'<span class="text-2xl">{self.icon}</span>')
                        
        return card

class ActionButton:
    """Modern action button with icon and label"""
    
    def __init__(self, 
                 label: str,
                 icon: Optional[str] = None,
                 on_click=None,
                 color: str = 'primary',
                 full_width: bool = False,
                 size: str = 'md'):
        self.label = label
        self.icon = icon
        self.on_click_handler = on_click
        self.color = color
        self.full_width = full_width
        self.size = size
        
    def create(self):
        """Create action button"""
        size_classes = {
            'sm': 'px-3 py-2 text-sm',
            'md': 'px-4 py-2 text-base',
            'lg': 'px-6 py-3 text-lg',
        }
        
        color_classes = {
            'primary': 'bg-indigo-600 hover:bg-indigo-700 text-white',
            'secondary': 'bg-gray-100 hover:bg-gray-200 text-gray-900',
            'success': 'bg-green-600 hover:bg-green-700 text-white',
            'error': 'bg-red-600 hover:bg-red-700 text-white',
            'warning': 'bg-yellow-500 hover:bg-yellow-600 text-white',
        }
        
        btn_classes = f'''
            nicegui-button 
            font-medium rounded-lg 
            transition-all duration-200 
            flex items-center justify-center gap-2
            {size_classes.get(self.size, size_classes['md'])}
            {color_classes.get(self.color, color_classes['primary'])}
            {'w-full' if self.full_width else ''}
        '''
        
        with ui.button(on_click=self.on_click_handler).classes(btn_classes) as btn:
            if self.icon:
                ui.html(f'<span>{self.icon}</span>')
            ui.label(self.label)
            
        return btn

class StatusBadge:
    """Status badge component"""
    
    def __init__(self, status: str):
        self.status = status.lower()
        
    def create(self):
        """Create status badge"""
        status_config = {
            'pending': ('badge-warning', '⏳ Pending'),
            'active': ('badge-info', '🔄 Active'),
            'completed': ('badge-success', '✅ Completed'),
            'cancelled': ('badge-error', '❌ Cancelled'),
            'approved': ('badge-success', '✓ Approved'),
            'rejected': ('badge-error', '✗ Rejected'),
        }
        
        badge_class, label = status_config.get(self.status, ('badge-info', self.status.capitalize()))
        
        with ui.element('span').classes(f'badge {badge_class}'):
            ui.label(label)
            
        return ui.element('span').classes(f'badge {badge_class}').props(f'text="{label}"')

def create_section(title: str, description: Optional[str] = None, content_callback=None):
    """Create a section with title and optional description"""
    with ui.element('div').classes('mb-8'):
        ui.label(title).classes('text-2xl font-bold text-gray-900 mb-2')
        if description:
            ui.label(description).classes('text-gray-500 mb-4')
        
        if content_callback:
            content_callback()

def create_empty_state(icon: str, title: str, description: str, action_label: Optional[str] = None, on_action=None):
    """Create an empty state component"""
    with ui.element('div').classes('flex flex-col items-center justify-center py-12 px-4 text-center'):
        ui.html(f'<span class="text-6xl mb-4">{icon}</span>')
        ui.label(title).classes('text-lg font-semibold text-gray-900 mb-2')
        ui.label(description).classes('text-gray-500 mb-6 max-w-md')
        
        if action_label and on_action:
            ActionButton(label=action_label, on_click=on_action, icon='➕').create()

def create_loading_state(text: str = 'Loading...'):
    """Create a loading state component"""
    with ui.element('div').classes('flex flex-col items-center justify-center py-12'):
        with ui.element('div').classes('animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600'):
            pass
        ui.label(text).classes('text-gray-500 mt-4')

# Helper function to create responsive navigation
def create_responsive_navbar(title: str, menu_items: List[dict], on_menu_click=None):
    """Create responsive navbar with hamburger menu for mobile"""
    with ui.header().classes('bg-white border-b border-gray-200 sticky top-0 z-50'):
        with ui.element('div').classes('container mx-auto px-4'):
            with ui.element('div').classes('flex items-center justify-between h-16'):
                # Logo/Title
                ui.label(title).classes('text-xl font-bold text-indigo-600')
                
                # Desktop Navigation
                with ui.element('div').classes('hidden md:flex items-center space-x-4'):
                    for item in menu_items:
                        with ui.button(on_click=lambda i=item: on_menu_click(i) if on_menu_click else None) \
                            .classes('nicegui-button text-gray-600 hover:text-indigo-600'):
                            ui.label(item.get('label', ''))
                
                # Mobile Hamburger Menu
                with ui.element('div').classes('md:hidden'):
                    with ui.button(icon='menu').classes('nicegui-button'):
                        pass
                    # Note: Full mobile menu implementation would use a drawer
                    
    return ui.header()
