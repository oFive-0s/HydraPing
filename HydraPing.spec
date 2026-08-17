# -*- mode: python ; coding: utf-8 -*-


import sys
from pathlib import Path

# Get Python DLL path dynamically from current environment
python_dlls = list(Path(sys.base_prefix).glob('python3*.dll'))
binaries_list = [(str(p), '.') for p in python_dlls if p.name != 'python3.dll']

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries_list,
    datas=[('icon.png', '.'), ('core', 'core'), ('layouts', 'layouts'), ('theme_manager.py', '.'), ('settings_dialog.py', '.'), ('overlay_window.py', '.'), ('confetti_widget.py', '.'), ('db_schema.py', '.'), ('font_loader.py', '.'), ('fonts', 'fonts'), ('icons.py', '.'), ('ui_kit.py', '.'), ('window_chrome.py', '.')],
    # PySide6.QtSvg is imported lazily inside icons.py, and the PySide6 hook
    # prunes Qt modules it does not see referenced at import time.  Without it
    # the frozen build silently loses every settings icon and check mark.
    hiddenimports=['PySide6.QtCore', 'PySide6.QtWidgets', 'PySide6.QtGui', 'PySide6.QtSvg', 'sqlite3', 'hashlib', 'ctypes', 'winsound', 'statistics', 'logging', 'base64', 'tempfile'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='HydraPing',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['icon.png'],
)
