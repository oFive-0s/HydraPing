"""
Theme utilities for HydraPing.
Provides helpers for applying themes dynamically.
"""

from PySide6 import QtWidgets, QtGui
from theme_config import ThemeConfig
from theme_manager import ThemeManager


def apply_dashboard_theme(window, theme_name='dark'):
    """
    Apply theme to dashboard window and all child widgets.
    
    Args:
        window: QWidget or QMainWindow instance
        theme_name: Theme name ('dark' or 'light')
    """
    theme_config = ThemeConfig(theme_name)
    
    palette = QtGui.QPalette()
    
    bg_color = _parse_color(theme_config.get('bg'))
    text_color = _parse_color(theme_config.get('text_primary'))
    
    palette.setColor(QtGui.QPalette.ColorRole.Window, bg_color)
    palette.setColor(QtGui.QPalette.ColorRole.WindowText, text_color)
    palette.setColor(QtGui.QPalette.ColorRole.Base, bg_color)
    palette.setColor(QtGui.QPalette.ColorRole.Text, text_color)
    
    window.setPalette(palette)
    
    qss = get_dashboard_qss(theme_config)
    window.setStyleSheet(qss)
    
    return theme_config


def apply_overlay_theme(overlay, theme_name='Dark Glassmorphic'):
    """
    Apply theme to overlay window.
    
    Args:
        overlay: OverlayWindow instance
        theme_name: Theme name from ThemeManager.THEMES
    """
    overlay.set_theme(theme_name)


def get_dashboard_qss(theme_config):
    """
    Generate QSS stylesheet for dashboard based on theme config.
    
    Args:
        theme_config: ThemeConfig instance
    
    Returns:
        str: QSS stylesheet
    """
    return f"""
    QMainWindow {{
        background-color: {theme_config.get('bg')};
        color: {theme_config.get('text_primary')};
    }}
    
    QWidget {{
        background-color: {theme_config.get('bg')};
        color: {theme_config.get('text_primary')};
        font-family: 'Poppins', 'Segoe UI', sans-serif;
    }}
    
    QScrollBar:vertical {{
        background: {theme_config.get('card')};
        width: 8px;
        border-radius: 4px;
    }}
    
    QScrollBar::handle:vertical {{
        background: {theme_config.get('accent')};
        border-radius: 4px;
        min-height: 20px;
    }}
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    
    QPushButton {{
        background-color: {theme_config.get('button_bg')};
        color: {theme_config.get('button_text')};
        border: 1px solid {theme_config.get('border')};
        border-radius: 8px;
        padding: 8px 16px;
        font-size: 13px;
        font-weight: 600;
    }}
    
    QPushButton:hover {{
        background-color: {theme_config.get('button_hover')};
    }}
    
    QPushButton:pressed {{
        background-color: {theme_config.get('accent')};
    }}
    
    QLineEdit, QSpinBox, QComboBox {{
        background-color: {theme_config.get('input_bg')};
        color: {theme_config.get('text_primary')};
        border: 1px solid {theme_config.get('input_border')};
        border-radius: 6px;
        padding: 6px 10px;
        font-size: 13px;
    }}
    
    QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
        border: 1px solid {theme_config.get('accent')};
    }}
    
    QTabWidget::pane {{
        border: none;
        background-color: {theme_config.get('bg')};
    }}
    
    QTabBar::tab {{
        background-color: {theme_config.get('tab_inactive_bg')};
        color: {theme_config.get('text_secondary')};
        border: none;
        padding: 10px 20px;
        margin-right: 4px;
        border-radius: 8px 8px 0 0;
    }}
    
    QTabBar::tab:selected {{
        background-color: {theme_config.get('tab_active_bg')};
        color: {theme_config.get('accent')};
    }}
    
    QTabBar::tab:hover:!selected {{
        background-color: {theme_config.get('card')};
    }}
    """


def _parse_color(color_str):
    """
    Parse color string to QColor.
    
    Args:
        color_str: Color in format '#RRGGBB' or 'rgba(r,g,b,a)'
    
    Returns:
        QtGui.QColor instance
    """
    if color_str.startswith('#'):
        return QtGui.QColor(color_str)
    elif color_str.startswith('rgba'):
        import re
        match = re.match(r'rgba\((\d+),\s*(\d+),\s*(\d+),\s*(\d+|\d+\.\d+)\)', color_str)
        if match:
            r, g, b, a = match.groups()
            return QtGui.QColor(int(r), int(g), int(b), int(float(a) * 255))
    
    return QtGui.QColor(color_str)


def get_available_themes():
    """
    Get list of available theme names.
    
    Returns:
        dict: {'dashboard': [...], 'overlay': [...]}
    """
    from core.config import AVAILABLE_THEMES
    
    return {
        'dashboard': ['dark', 'light'],
        'overlay': AVAILABLE_THEMES
    }
