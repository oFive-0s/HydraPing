"""
Native window chrome tinting for HydraPing.

Windows draws the title bar in the non-client area, so no amount of QSS reaches
it -- by default it follows the OS light/dark setting, which means a dark
HydraPing dialog can end up wearing a white title bar.  Windows 11 (build 22000+)
exposes the caption, caption-text and border colours through DWM, so the real
title bar can be tinted to match the app instead of being replaced by a
frameless imitation.  Keeping the native bar preserves Snap Layouts, drag,
double-click-to-maximise, the system menu and the window animations.

Degrades quietly: on Windows 10 only the dark-mode flag is honoured, and on
non-Windows platforms every call is a no-op.
"""

import sys

# DWMWINDOWATTRIBUTE values (dwmapi.h)
DWMWA_USE_IMMERSIVE_DARK_MODE_OLD = 19   # Windows 10 pre-20H1
DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_BORDER_COLOR = 34                  # Windows 11 22000+
DWMWA_CAPTION_COLOR = 35                 # Windows 11 22000+
DWMWA_TEXT_COLOR = 36                    # Windows 11 22000+

_IS_WINDOWS = sys.platform == "win32"


def _build():
    if not _IS_WINDOWS:
        return 0
    try:
        return sys.getwindowsversion().build
    except Exception:
        return 0


def supports_caption_colour():
    """True if this OS can tint the caption to an arbitrary colour."""
    return _IS_WINDOWS and _build() >= 22000


def _colorref(colour):
    """QColor -> Win32 COLORREF.

    COLORREF is 0x00BBGGRR: the byte order is BGR, not RGB.  Passing an RGB
    value here silently swaps red and blue, which is the classic way this ends
    up looking almost-right but wrong.
    """
    return (colour.blue() << 16) | (colour.green() << 8) | colour.red()


def _set_attr(hwnd, attr, value):
    import ctypes
    from ctypes import wintypes
    try:
        v = ctypes.c_int(value)
        hr = ctypes.windll.dwmapi.DwmSetWindowAttribute(
            wintypes.HWND(hwnd), ctypes.c_uint(attr),
            ctypes.byref(v), ctypes.c_uint(ctypes.sizeof(v)))
        return hr == 0
    except Exception:
        return False


def is_dark(colour):
    """Perceived-brightness test, used to pick a readable caption text colour."""
    return (0.299 * colour.red() + 0.587 * colour.green()
            + 0.114 * colour.blue()) < 128


def apply_window_chrome(widget, caption, text=None, border=None):
    """Tint `widget`'s native title bar.

    caption / text / border are QColors; text and border default to sensible
    values derived from `caption`.  Returns True if the caption colour itself
    was applied.

    Call this *after* the window has a handle -- widget.winId() forces creation,
    so it is safe to call before show().  Re-apply from showEvent(), because Qt
    can recreate the native handle (a window flag change does it), and a
    recreated handle comes back with default chrome.
    """
    if not _IS_WINDOWS:
        return False

    try:
        hwnd = int(widget.winId())
    except Exception:
        return False
    if not hwnd:
        return False

    dark = is_dark(caption)

    # Always set the immersive flag: on Windows 10 it is the only lever we have,
    # and on 11 it still drives the system-menu and control glyph rendering.
    _set_attr(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, 1 if dark else 0)
    if _build() < 19041:
        _set_attr(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE_OLD, 1 if dark else 0)

    if not supports_caption_colour():
        return False

    from PySide6 import QtGui

    if text is None:
        text = QtGui.QColor(255, 255, 255) if dark else QtGui.QColor(24, 24, 24)
    if border is None:
        # A hair lighter than the caption on dark, a hair darker on light, so the
        # window still separates from whatever is behind it.
        delta = 18 if dark else -18
        border = QtGui.QColor(
            max(0, min(255, caption.red() + delta)),
            max(0, min(255, caption.green() + delta)),
            max(0, min(255, caption.blue() + delta)))

    ok = _set_attr(hwnd, DWMWA_CAPTION_COLOR, _colorref(caption))
    _set_attr(hwnd, DWMWA_TEXT_COLOR, _colorref(text))
    _set_attr(hwnd, DWMWA_BORDER_COLOR, _colorref(border))
    return ok


def apply_theme_chrome(widget, theme_manager, theme_name=None):
    """Tint `widget`'s title bar from a ThemeManager theme."""
    from overlay_window import parse_rgba

    theme = theme_manager.get_theme(theme_name)
    caption = parse_rgba(theme['dialog_bg'])
    caption.setAlpha(255)                      # the caption cannot be translucent
    text = parse_rgba(theme['text_primary'])
    text.setAlpha(255)
    return apply_window_chrome(widget, caption, text)
