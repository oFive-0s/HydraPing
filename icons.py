"""
Vector icon set for HydraPing.

The settings dialog previously used text glyphs for its controls -- "▶", "↻",
"×" -- which is fragile: rendering depends on the active font actually carrying
those codepoints, they cannot be weight-matched to the surrounding UI, and they
sit on the text baseline rather than being optically centred in their button.

These are stroked SVG paths rendered to QIcon at the widget's device pixel
ratio, so they stay crisp on scaled displays and can be recoloured per theme.
"""

import os

from PySide6 import QtCore, QtGui

# 16x16 viewBox, stroke-based so a single colour drives the whole glyph.
_PATHS = {
    'play':   ('<path d="M6 4.2 12.2 8 6 11.8Z" fill="CLR" stroke="none"/>'),
    'loop':   ('<path d="M4 7.2V6.6A2.1 2.1 0 0 1 6.1 4.5h5.2"/>'
               '<path d="m9.6 2.9 1.8 1.6-1.8 1.6"/>'
               '<path d="M12 8.8v.6a2.1 2.1 0 0 1-2.1 2.1H4.7"/>'
               '<path d="m6.4 13.1-1.8-1.6 1.8-1.6"/>'),
    'clear':  ('<path d="m5.2 5.2 5.6 5.6M10.8 5.2l-5.6 5.6"/>'),
    'folder': ('<path d="M2.2 5.6a1 1 0 0 1 1-1h2.4l1.2 1.5h5.9a1 1 0 0 1 1 1v4.7'
               'a1 1 0 0 1-1 1H3.2a1 1 0 0 1-1-1Z"/>'),
    'reset':  ('<path d="M3.4 8a4.6 4.6 0 1 0 1.5-3.4"/><path d="M3.1 3.2v2.6h2.6"/>'),
    'drop':   ('<path d="M8 2.4c0 0-3.7 4.2-3.7 6.6a3.7 3.7 0 0 0 7.4 0C11.7 6.6 8 2.4 8 2.4Z"/>'),
    'power':  ('<path d="M8 2.6v4.8"/><path d="M5.1 4.7a4.4 4.4 0 1 0 5.8 0"/>'),
    'chevron': ('<path d="m4.5 6.5 3.5 3.5 3.5-3.5"/>'),
}

_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" '
        'viewBox="0 0 16 16" fill="none" stroke="CLR" stroke-width="1.5" '
        'stroke-linecap="round" stroke-linejoin="round">{body}</svg>')

_cache = {}


def _render(name, colour, size, dpr):
    """Rasterise one icon at the target device pixel ratio."""
    from PySide6.QtSvg import QSvgRenderer

    body = _PATHS[name].replace('CLR', colour.name())
    svg = _SVG.replace('CLR', colour.name()).format(body=body)

    px = QtGui.QPixmap(int(size * dpr), int(size * dpr))
    px.fill(QtCore.Qt.GlobalColor.transparent)
    renderer = QSvgRenderer(QtCore.QByteArray(svg.encode('utf-8')))
    painter = QtGui.QPainter(px)
    painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
    renderer.render(painter)
    painter.end()
    px.setDevicePixelRatio(dpr)
    return px


def icon(name, colour, size=16, dpr=1.0):
    """QIcon for `name` tinted `colour` (a QColor).  Cached per variant."""
    if name not in _PATHS:
        return QtGui.QIcon()
    key = (name, colour.name(), size, round(dpr, 2))
    if key not in _cache:
        try:
            _cache[key] = QtGui.QIcon(_render(name, colour, size, dpr))
        except Exception:
            # QtSvg missing or render failure: an empty icon degrades to a
            # text-free button rather than taking the dialog down.
            _cache[key] = QtGui.QIcon()
    return _cache[key]


def qss_image(key, svg_body, size=16):
    """Rasterise an SVG to PNG on disk; return a path usable in QSS url(...).

    Two separate traps here, both of which render nothing and report no error:

    1. Qt resolves stylesheet url() through QPixmap, which loads *files* and does
       not understand data: URIs.  (The dialog's old combobox arrow was an inline
       base64 SVG, so its arrow never drew.)
    2. QPixmap can only read .svg when the qsvg *imageformat plugin* is
       installed -- which is separate from the QtSvg module, and is absent here.
       So the file has to be a PNG, rasterised via QSvgRenderer ourselves.

    A @2x companion is written alongside, which Qt picks up automatically on
    high-DPI displays.
    """
    import hashlib
    import tempfile

    digest = hashlib.md5(f"{key}|{svg_body}|{size}".encode('utf-8')).hexdigest()[:12]
    cache_dir = os.path.join(tempfile.gettempdir(), 'hydraping_icons')
    try:
        from PySide6.QtSvg import QSvgRenderer

        os.makedirs(cache_dir, exist_ok=True)
        base = os.path.join(cache_dir, f"{key}-{digest}")
        path = base + '.png'

        if not os.path.exists(path):
            svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" '
                   'viewBox="0 0 16 16">%s</svg>' % svg_body)
            renderer = QSvgRenderer(QtCore.QByteArray(svg.encode('utf-8')))
            for scale, target in ((1, path), (2, base + '@2x.png')):
                px = QtGui.QPixmap(size * scale, size * scale)
                px.fill(QtCore.Qt.GlobalColor.transparent)
                painter = QtGui.QPainter(px)
                painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
                renderer.render(painter)
                painter.end()
                px.save(target, 'PNG')

        # QSS wants forward slashes even on Windows.
        return path.replace('\\', '/')
    except Exception:
        return ''


def available():
    """True if QtSvg is importable, so callers can fall back to text."""
    try:
        from PySide6.QtSvg import QSvgRenderer  # noqa: F401
        return True
    except Exception:
        return False


def clear_cache():
    """Drop cached pixmaps (call on theme change so tints are re-rendered)."""
    _cache.clear()
