"""
Modern Theme Configuration for NiceGUI Application
Defines color palette, typography, and global styles
"""
from nicegui import ui

# Color Palette (Modern, Professional, Accessible)
COLORS = {
    'primary': '#4F46E5',      # Indigo 600 - Main brand color
    'primary-dark': '#4338CA', # Indigo 700 - Hover state
    'secondary': '#0EA5E9',    # Sky 500 - Secondary actions
    'accent': '#F59E0B',       # Amber 500 - Highlights
    'success': '#10B981',      # Emerald 500 - Success states
    'warning': '#F59E0B',      # Amber 500 - Warnings
    'error': '#EF4444',        # Red 500 - Errors
    'info': '#3B82F6',         # Blue 500 - Info
    
    # Neutrals
    'background': '#F9FAFB',   # Gray 50 - Page background
    'surface': '#FFFFFF',      # White - Cards/Surfaces
    'border': '#E5E7EB',       # Gray 200 - Borders
    'text-primary': '#111827', # Gray 900 - Main text
    'text-secondary': '#6B7280', # Gray 500 - Secondary text
    'text-light': '#9CA3AF',   # Gray 400 - Disabled text
}

# Typography Scale
TYPOGRAPHY = {
    'h1': {'size': '2.25rem', 'weight': '700', 'line-height': '2.5rem'},
    'h2': {'size': '1.875rem', 'weight': '600', 'line-height': '2.25rem'},
    'h3': {'size': '1.5rem', 'weight': '600', 'line-height': '2rem'},
    'h4': {'size': '1.25rem', 'weight': '600', 'line-height': '1.75rem'},
    'h5': {'size': '1.125rem', 'weight': '600', 'line-height': '1.75rem'},
    'h6': {'size': '1rem', 'weight': '600', 'line-height': '1.5rem'},
    'body': {'size': '1rem', 'weight': '400', 'line-height': '1.5rem'},
    'caption': {'size': '0.875rem', 'weight': '400', 'line-height': '1.25rem'},
    'small': {'size': '0.75rem', 'weight': '400', 'line-height': '1rem'},
}

# Spacing Scale (Tailwind-inspired)
SPACING = {
    'xs': '0.25rem',   # 4px
    'sm': '0.5rem',    # 8px
    'md': '1rem',      # 16px
    'lg': '1.5rem',    # 24px
    'xl': '2rem',      # 32px
    '2xl': '3rem',     # 48px
}

# Border Radius
RADIUS = {
    'none': '0',
    'sm': '0.25rem',   # 4px
    'md': '0.375rem',  # 6px
    'lg': '0.5rem',    # 8px
    'xl': '0.75rem',   # 12px
    'full': '9999px',  # Circle
}

# Shadows
SHADOWS = {
    'none': 'none',
    'sm': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    'md': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    'lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    'xl': '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
}

def apply_global_theme():
    """Apply global theme styles to the application"""
    
    # Inject custom CSS variables and global styles
    ui.add_head_html(f'''
    <style>
        :root {{
            /* Colors */
            --color-primary: {COLORS['primary']};
            --color-primary-dark: {COLORS['primary-dark']};
            --color-secondary: {COLORS['secondary']};
            --color-accent: {COLORS['accent']};
            --color-success: {COLORS['success']};
            --color-warning: {COLORS['warning']};
            --color-error: {COLORS['error']};
            --color-info: {COLORS['info']};
            
            /* Neutrals */
            --color-bg: {COLORS['background']};
            --color-surface: {COLORS['surface']};
            --color-border: {COLORS['border']};
            --color-text: {COLORS['text-primary']};
            --color-text-secondary: {COLORS['text-secondary']};
            --color-text-light: {COLORS['text-light']};
            
            /* Typography */
            --font-h1: {TYPOGRAPHY['h1']['size']};
            --font-h2: {TYPOGRAPHY['h2']['size']};
            --font-h3: {TYPOGRAPHY['h3']['size']};
            --font-body: {TYPOGRAPHY['body']['size']};
            
            /* Spacing */
            --space-xs: {SPACING['xs']};
            --space-sm: {SPACING['sm']};
            --space-md: {SPACING['md']};
            --space-lg: {SPACING['lg']};
            --space-xl: {SPACING['xl']};
            
            /* Radius */
            --radius-md: {RADIUS['md']};
            --radius-lg: {RADIUS['lg']};
            --radius-xl: {RADIUS['xl']};
            
            /* Shadows */
            --shadow-md: {SHADOWS['md']};
            --shadow-lg: {SHADOWS['lg']};
            --shadow-xl: {SHADOWS['xl']};
        }}
        
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: var(--color-bg);
            color: var(--color-text);
            line-height: 1.5;
        }}
        
        /* Modern Card Styles */
        .modern-card {{
            background: var(--color-surface);
            border-radius: var(--radius-xl);
            box-shadow: var(--shadow-md);
            border: 1px solid var(--color-border);
            transition: all 0.2s ease;
        }}
        
        .modern-card:hover {{
            box-shadow: var(--shadow-lg);
            transform: translateY(-2px);
        }}
        
        /* Button Enhancements */
        .nicegui-button {{
            border-radius: var(--radius-md);
            font-weight: 500;
            transition: all 0.2s ease;
            text-transform: none;
            letter-spacing: 0.025em;
        }}
        
        .nicegui-button:hover {{
            transform: translateY(-1px);
            box-shadow: var(--shadow-md);
        }}
        
        .nicegui-button:active {{
            transform: translateY(0);
        }}
        
        /* Input Fields */
        .nicegui-input, .nicegui-select, .nicegui-textarea {{
            border-radius: var(--radius-md);
            border: 1px solid var(--color-border);
            transition: all 0.2s ease;
        }}
        
        .nicegui-input:focus, .nicegui-select:focus, .nicegui-textarea:focus {{
            border-color: var(--color-primary);
            box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
        }}
        
        /* Table Styles */
        .modern-table {{
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
        }}
        
        .modern-table th {{
            background: var(--color-bg);
            font-weight: 600;
            text-align: left;
            padding: var(--space-md);
            border-bottom: 2px solid var(--color-border);
            color: var(--color-text-secondary);
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}
        
        .modern-table td {{
            padding: var(--space-md);
            border-bottom: 1px solid var(--color-border);
            transition: background 0.15s ease;
        }}
        
        .modern-table tr:last-child td {{
            border-bottom: none;
        }}
        
        .modern-table tr:hover td {{
            background: var(--color-bg);
        }}
        
        /* Responsive Utilities */
        .container {{
            width: 100%;
            max-width: 1280px;
            margin: 0 auto;
            padding: 0 var(--space-md);
        }}
        
        @media (max-width: 640px) {{
            .hide-mobile {{
                display: none !important;
            }}
        }}
        
        @media (min-width: 641px) and (max-width: 1024px) {{
            .hide-tablet {{
                display: none !important;
            }}
        }}
        
        /* Loading Animation */
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.5; }}
        }}
        
        .loading {{
            animation: pulse 1.5s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }}
        
        /* Status Badges */
        .badge {{
            display: inline-flex;
            align-items: center;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 500;
            line-height: 1rem;
        }}
        
        .badge-success {{
            background-color: rgba(16, 185, 129, 0.1);
            color: var(--color-success);
        }}
        
        .badge-warning {{
            background-color: rgba(245, 158, 11, 0.1);
            color: var(--color-warning);
        }}
        
        .badge-error {{
            background-color: rgba(239, 68, 68, 0.1);
            color: var(--color-error);
        }}
        
        .badge-info {{
            background-color: rgba(59, 130, 246, 0.1);
            color: var(--color-info);
        }}
    </style>
    ''')

def get_color(name: str) -> str:
    """Get color by name"""
    return COLORS.get(name, COLORS['text-primary'])

def get_spacing(name: str) -> str:
    """Get spacing value by name"""
    return SPACING.get(name, SPACING['md'])

def get_radius(name: str) -> str:
    """Get radius value by name"""
    return RADIUS.get(name, RADIUS['md'])
