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
    # Only real runtime assets. The application's own .py files used to be
    # listed here as well, but they are already frozen into the PYZ as modules,
    # so shipping them again duplicated ~229 KB and risked the loose copies in
    # _MEIPASS shadowing the frozen ones.
    datas=[('icon.png', '.'), ('core', 'core'), ('layouts', 'layouts'), ('fonts', 'fonts')],
    # PySide6.QtSvg is imported lazily inside icons.py, and the PySide6 hook
    # prunes Qt modules it does not see referenced at import time.  Without it
    # the frozen build silently loses every settings icon and check mark.
    hiddenimports=['PySide6.QtCore', 'PySide6.QtWidgets', 'PySide6.QtGui', 'PySide6.QtSvg', 'sqlite3', 'hashlib', 'ctypes', 'winsound', 'statistics', 'logging', 'base64', 'tempfile'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # HydraPing is a pure QtWidgets app: no QML/Quick scenes, no networking, no
    # PDF, no GL widgets. The PySide6 hook bundles those subsystems anyway.
    excludes=[
        'PySide6.QtQml', 'PySide6.QtQuick', 'PySide6.QtQuickWidgets',
        'PySide6.QtQuickControls2', 'PySide6.QtNetwork', 'PySide6.QtPdf',
        'PySide6.QtPdfWidgets', 'PySide6.QtOpenGL', 'PySide6.QtOpenGLWidgets',
        'PySide6.QtVirtualKeyboard', 'PySide6.QtDBus', 'PySide6.QtTest',
        'tkinter', 'unittest', 'pydoc_data',
    ],
    noarchive=False,
    optimize=0,
)

# The Analysis excludes above drop the Python bindings, but the PySide6 hook
# collects the Qt DLLs separately, so they survive unless filtered here too.
# Everything listed is verified unreferenced by the application:
#   opengl32sw.dll  Mesa software GL fallback; QtWidgets renders via raster
#   Qt6Quick/Qml*   QML runtime - the UI is entirely QtWidgets
#   Qt6Pdf          no PDF anywhere in the app
#   Qt6Network+TLS  no sockets; libcrypto/libssl come along only for QtNetwork
#   Qt6VirtualKeyboard, Qt6OpenGL
# Qt6Svg is deliberately NOT excluded: icons.py renders through QSvgRenderer.
_UNUSED = (
    'opengl32sw.dll',
    'Qt6Quick.dll', 'Qt6Qml.dll', 'Qt6QmlModels.dll', 'Qt6QmlMeta.dll',
    'Qt6QmlWorkerScript.dll', 'Qt6QuickControls2.dll',
    'Qt6Pdf.dll', 'Qt6OpenGL.dll', 'Qt6VirtualKeyboard.dll',
    'Qt6Network.dll', 'QtNetwork.pyd',
    'libcrypto-3.dll', 'libssl-3.dll',
    'qopensslbackend.dll', 'qcertonlybackend.dll', 'qschannelbackend.dll',
)


def _keep(entry):
    name = entry[0].replace('\\', '/').split('/')[-1]
    return name not in _UNUSED


_before = len(a.binaries)
a.binaries = TOC([b for b in a.binaries if _keep(b)])
print('[HydraPing] pruned %d unused binaries' % (_before - len(a.binaries)))

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
