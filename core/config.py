"""
Configuration and constants for HydraPing application.
Centralizes default settings, paths, and application metadata.
"""

import os
import sys
from pathlib import Path

# Application metadata
APP_NAME = "HydraPing"
APP_VERSION = "1.2.0"
APP_AUTHOR = "HydraPing Team"
ORG_NAME = "HydraPing"
ORG_DOMAIN = "hydra-ping.app"

DEFAULT_DAILY_GOAL = 2000
DEFAULT_REMINDER_INTERVAL = 45
DEFAULT_DRINK_AMOUNT = 250
DEFAULT_THEME = "Dark Glassmorphic"

AVAILABLE_THEMES = [
    "Dark Glassmorphic",
    "Wine Red",
    "Forest Green",
    "Ocean Blue",
    "Light Glassmorphic",
    "Sunset Orange",
    "Light Overlay"
]

LOG_RETENTION_DAYS = 90

DB_SCHEMA_VERSION = 1
DB_SCHEMA_VERSION = 1

DEFAULT_OVERLAY_X = None
DEFAULT_OVERLAY_Y = 20
OVERLAY_VISIBLE_ON_START = True

DEFAULT_WINDOW_SHAPE = "rectangular"  # Options: "rectangular", "circular"

ENABLE_SOUND_NOTIFICATIONS = True
ENABLE_VISUAL_NOTIFICATIONS = True

AUTO_LAUNCH_ENABLED = False


def get_user_data_dir():
    """
    Get OS-appropriate user data directory for HydraPing.
    
    Returns:
        Path: User data directory path
        
    Locations:
        Windows: %APPDATA%/HydraPing
        Linux: ~/.config/HydraPing
        macOS: ~/Library/Application Support/HydraPing
    """
    if sys.platform == "win32":
        base_path = os.getenv('APPDATA')
        if not base_path:
            base_path = Path.home() / "AppData" / "Roaming"
        else:
            base_path = Path(base_path)
    elif sys.platform == "darwin":
        base_path = Path.home() / "Library" / "Application Support"
    else:
        base_path = Path(os.getenv('XDG_CONFIG_HOME', Path.home() / ".config"))
    
    data_dir = base_path / APP_NAME
    data_dir.mkdir(parents=True, exist_ok=True)
    
    return data_dir


def get_database_path():
    """
    Get full path to the SQLite database file.
    
    Returns:
        Path: Database file path
    """
    return get_user_data_dir() / "hydration.db"


def get_config_file_path():
    """
    Get path to the optional JSON config file.
    
    Returns:
        Path: Config file path
    """
    return get_user_data_dir() / "config.json"


def get_logs_dir():
    """
    Get directory for application logs (if needed).
    
    Returns:
        Path: Logs directory path
    """
    logs_dir = get_user_data_dir() / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir


WINDOWS_REGISTRY_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
WINDOWS_REGISTRY_VALUE_NAME = APP_NAME


def is_frozen():
    """
    Check if running as compiled executable (PyInstaller).
    
    Returns:
        bool: True if frozen, False if running from source
    """
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')


def get_app_root():
    """
    Get application root directory.
    
    Returns:
        Path: Root directory (executable dir if frozen, script dir if source)
    """
    if is_frozen():
        return Path(sys.executable).parent
    else:
        return Path(__file__).parent.parent


ACHIEVEMENT_THRESHOLDS = {
    'first_drink': 1,
    'daily_goal': 1,
    'weekly_streak': 7,
    'monthly_streak': 30,
    'hydration_hero': 100,
    'early_bird': 50,
    'night_owl': 50,
    'consistent': 30,
    'champion': 365,
}
