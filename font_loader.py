"""
Font Loader for HydraPing
Registers bundled Poppins fonts with Qt's font database so they are
available whether running from source or as a frozen PyInstaller exe.
"""

import os
import sys
from PySide6 import QtGui


def _get_fonts_dir() -> str:
    """Resolve the fonts/ directory regardless of frozen vs. source context."""
    if getattr(sys, 'frozen', False):
        # PyInstaller extracts data files next to the exe (one-file) or in
        # _MEIPASS (one-folder).  We ship fonts/ relative to the exe.
        base = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, 'fonts')


def load_poppins() -> bool:
    """
    Register all bundled Poppins TTF files with QFontDatabase.
    Call this once, right after QApplication is constructed.

    Returns True if at least one font was loaded successfully.
    """
    fonts_dir = _get_fonts_dir()

    font_files = [
        'Poppins-Regular.ttf',
        'Poppins-Medium.ttf',
        'Poppins-SemiBold.ttf',
        'Poppins-Bold.ttf',
    ]

    loaded = 0
    for filename in font_files:
        path = os.path.join(fonts_dir, filename)
        if os.path.isfile(path):
            font_id = QtGui.QFontDatabase.addApplicationFont(path)
            if font_id != -1:
                loaded += 1
            else:
                print(f"[FontLoader] Failed to register: {filename}")
        else:
            print(f"[FontLoader] Not found: {path}")

    if loaded:
        print(f"[FontLoader] Loaded {loaded}/{len(font_files)} Poppins variants")
    else:
        print("[FontLoader] Warning: No Poppins fonts loaded - falling back to system font")

    return loaded > 0