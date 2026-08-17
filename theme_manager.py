"""
Theme Manager for HydraPing
Handles color schemes and styling for the application
"""

class ThemeManager:
    """Manage application themes and color schemes"""

    # Rim gradient stops shared by every theme: (offset, which_edge, alpha 0-255).
    # Alpha varies along a 135 deg axis so the top-left catches light, the long
    # edges nearly vanish and the bottom-right picks up bounce.  A constant-alpha
    # stroke is what reads as a drawn outline; this reads as glass.
    RIM_STOPS = (
        (0.00, 'edge_hi', 105),
        (0.28, 'edge_hi', 38),
        (0.52, 'edge_lo', 16),
        (0.78, 'edge_lo', 30),
        (1.00, 'edge_hi', 62),
    )
    RIM_HOVER_GAIN = 1.45

    THEMES = {
        'Light Glassmorphic': {
            'name': 'Light Glassmorphic',
            'edge_hi': '255,255,255',
            'edge_lo': '0,0,0',
            'overlay_bg_start': 'rgba(30,30,30,40)',
            'overlay_bg_end': 'rgba(20,20,20,30)',
            'overlay_border': 'rgba(0,0,0,90)',
            'hover_bg_start': 'rgba(30,30,30,60)',
            'hover_bg_end': 'rgba(20,20,20,50)',
            'hover_border': 'rgba(0,0,0,120)',
            'text_primary': 'rgba(0,0,0,250)',
            'text_secondary': 'rgba(0,0,0,200)',
            'text_tertiary': 'rgba(0,0,0,180)',
            'button_bg': 'rgba(0,0,0,25)',
            'button_hover': 'rgba(0,0,0,35)',
            'dialog_bg': 'rgba(240,240,240,250)',
            'progress_low': 'rgba(232,71,71,220)',
            'progress_mid': 'rgba(255,193,7,220)',
            'progress_high': 'rgba(76,175,80,220)',
        },
        'Dark Glassmorphic': {
            'name': 'Dark Glassmorphic',
            'edge_hi': '255,255,255',
            'edge_lo': '255,255,255',
            'overlay_bg_start': 'rgba(255,255,255,40)',
            'overlay_bg_end': 'rgba(255,255,255,30)',
            'overlay_border': 'rgba(255,255,255,90)',
            'hover_bg_start': 'rgba(255,255,255,60)',
            'hover_bg_end': 'rgba(255,255,255,50)',
            'hover_border': 'rgba(255,255,255,120)',
            'text_primary': 'rgba(255,255,255,250)',
            'text_secondary': 'rgba(255,255,255,200)',
            'text_tertiary': 'rgba(255,255,255,180)',
            'button_bg': 'rgba(255,255,255,25)',
            'button_hover': 'rgba(255,255,255,35)',
            'dialog_bg': 'rgba(30,30,40,250)',
            'progress_low': 'rgba(232,71,71,220)',
            'progress_mid': 'rgba(255,193,7,220)',
            'progress_high': 'rgba(76,175,80,220)',
        },
        'Wine Red': {
            'name': 'Wine Red',
            'edge_hi': '255,205,205',
            'edge_lo': '120,0,0',
            'overlay_bg_start': 'rgba(139,0,0,45)',
            'overlay_bg_end': 'rgba(115,0,0,35)',
            'overlay_border': 'rgba(178,34,34,100)',
            'hover_bg_start': 'rgba(139,0,0,65)',
            'hover_bg_end': 'rgba(115,0,0,55)',
            'hover_border': 'rgba(178,34,34,130)',
            'text_primary': 'rgba(255,255,255,250)',
            'text_secondary': 'rgba(255,255,255,220)',
            'text_tertiary': 'rgba(255,255,255,200)',
            'button_bg': 'rgba(139,0,0,30)',
            'button_hover': 'rgba(139,0,0,45)',
            'dialog_bg': 'rgba(80,0,0,250)',
            'progress_low': 'rgba(255,138,101,220)',
            'progress_mid': 'rgba(255,193,7,220)',
            'progress_high': 'rgba(255,182,193,220)',
        },
        'Forest Green': {
            'name': 'Forest Green',
            'edge_hi': '220,255,225',
            'edge_lo': '20,70,25',
            'overlay_bg_start': 'rgba(129,199,132,45)',
            'overlay_bg_end': 'rgba(102,187,106,35)',
            'overlay_border': 'rgba(165,214,167,100)',
            'hover_bg_start': 'rgba(129,199,132,65)',
            'hover_bg_end': 'rgba(102,187,106,55)',
            'hover_border': 'rgba(165,214,167,130)',
            'text_primary': 'rgba(255,255,255,250)',
            'text_secondary': 'rgba(255,255,255,220)',
            'text_tertiary': 'rgba(255,255,255,200)',
            'button_bg': 'rgba(129,199,132,30)',
            'button_hover': 'rgba(129,199,132,45)',
            'dialog_bg': 'rgba(27,94,32,250)',
            'progress_low': 'rgba(255,138,101,220)',
            'progress_mid': 'rgba(255,213,79,220)',
            'progress_high': 'rgba(165,214,167,220)',
        },
        'Ocean Blue': {
            'name': 'Ocean Blue',
            'edge_hi': '215,240,255',
            'edge_lo': '10,50,100',
            'overlay_bg_start': 'rgba(100,181,246,45)',
            'overlay_bg_end': 'rgba(66,165,245,35)',
            'overlay_border': 'rgba(129,212,250,100)',
            'hover_bg_start': 'rgba(100,181,246,65)',
            'hover_bg_end': 'rgba(66,165,245,55)',
            'hover_border': 'rgba(129,212,250,130)',
            'text_primary': 'rgba(255,255,255,250)',
            'text_secondary': 'rgba(255,255,255,220)',
            'text_tertiary': 'rgba(255,255,255,200)',
            'button_bg': 'rgba(100,181,246,30)',
            'button_hover': 'rgba(100,181,246,45)',
            'dialog_bg': 'rgba(13,71,161,250)',
            'progress_low': 'rgba(244,143,177,220)',
            'progress_mid': 'rgba(255,213,79,220)',
            'progress_high': 'rgba(129,212,250,220)',
        },
        'Sunset Orange': {
            'name': 'Sunset Orange',
            'edge_hi': '255,235,205',
            'edge_lo': '150,60,10',
            'overlay_bg_start': 'rgba(255,183,77,45)',
            'overlay_bg_end': 'rgba(255,167,38,35)',
            'overlay_border': 'rgba(255,204,128,100)',
            'hover_bg_start': 'rgba(255,183,77,65)',
            'hover_bg_end': 'rgba(255,167,38,55)',
            'hover_border': 'rgba(255,204,128,130)',
            'text_primary': 'rgba(255,255,255,250)',
            'text_secondary': 'rgba(255,255,255,220)',
            'text_tertiary': 'rgba(255,255,255,200)',
            'button_bg': 'rgba(255,183,77,30)',
            'button_hover': 'rgba(255,183,77,45)',
            'dialog_bg': 'rgba(191,54,12,250)',
            'progress_low': 'rgba(239,83,80,220)',
            'progress_mid': 'rgba(255,213,79,220)',
            'progress_high': 'rgba(255,183,77,220)',
        },
        'Light Overlay': {
            'name': 'Light Overlay',
            'edge_hi': '255,255,255',
            'edge_lo': '120,120,120',
            'overlay_bg_start': 'rgba(255,255,255,20)',
            'overlay_bg_end': 'rgba(250,250,250,15)',
            'overlay_border': 'rgba(200,200,200,80)',
            'hover_bg_start': 'rgba(255,255,255,40)',
            'hover_bg_end': 'rgba(250,250,250,30)',
            'hover_border': 'rgba(180,180,180,110)',
            'text_primary': 'rgba(33,33,33,250)',
            'text_secondary': 'rgba(66,66,66,220)',
            'text_tertiary': 'rgba(100,100,100,200)',
            'button_bg': 'rgba(220,220,220,30)',
            'button_hover': 'rgba(200,200,200,45)',
            'dialog_bg': 'rgba(255,255,255,250)',
            'progress_low': 'rgba(244,67,54,220)',
            'progress_mid': 'rgba(255,193,7,220)',
            'progress_high': 'rgba(76,175,80,220)',
        },
        'Midnight Blue': {
            'name': 'Midnight Blue',
            'edge_hi': '200,220,255',
            'edge_lo': '10,20,45',
            'overlay_bg_start': 'rgba(13,27,42,50)',
            'overlay_bg_end': 'rgba(27,38,59,40)',
            'overlay_border': 'rgba(65,105,225,100)',
            'hover_bg_start': 'rgba(13,27,42,70)',
            'hover_bg_end': 'rgba(27,38,59,60)',
            'hover_border': 'rgba(65,105,225,130)',
            'text_primary': 'rgba(255,255,255,250)',
            'text_secondary': 'rgba(220,230,255,220)',
            'text_tertiary': 'rgba(200,210,235,200)',
            'button_bg': 'rgba(65,105,225,30)',
            'button_hover': 'rgba(65,105,225,45)',
            'dialog_bg': 'rgba(13,27,42,250)',
            'progress_low': 'rgba(220,20,60,220)',
            'progress_mid': 'rgba(255,215,0,220)',
            'progress_high': 'rgba(100,149,237,220)',
        },
    }
    
    # Solid, opaque palette for the settings window.  The overlay is translucent
    # glass; this window is not, so it needs real surface colours rather than
    # alpha tints -- and it needs them per theme, because the dialog used to
    # hardcode one fixed Material palette regardless of the theme chosen.
    # (surface, text, text_dim, text_faint, accent, accent_dim, accent_ink,
    #  button, button_hover, danger_bg, danger_text)
    DIALOG_PALETTES = {
        'Light Glassmorphic': ('#f2f3f5', '#17181a', '#5c6066', '#83888f',
                               '#3b6fd4', '#2f5cb8', '#ffffff',
                               '#e4e7eb', '#d8dce1', '#f4d9d9', '#b3261e'),
        'Dark Glassmorphic':  ('#23262b', '#e8eaed', '#a8adb5', '#7d838b',
                               '#8ab4f8', '#6f9de6', '#10233f',
                               '#2f333a', '#3a3f47', '#3d2a2c', '#f0a6a6'),
        'Wine Red':           ('#33191b', '#f6e7e7', '#c9a5a5', '#a37f7f',
                               '#e4737a', '#c85a62', '#2a0d10',
                               '#422427', '#4f2d31', '#4d2529', '#f2b0b0'),
        'Forest Green':       ('#1b2a1d', '#e6f5e8', '#a6c4aa', '#7f9c84',
                               '#81c784', '#66ab6a', '#0d1f10',
                               '#253627', '#2e4130', '#3b2726', '#f0b3b0'),
        'Ocean Blue':         ('#17293a', '#e4f1fb', '#a2bdd2', '#7b95aa',
                               '#64b5f6', '#4b9ad9', '#08243c',
                               '#203548', '#294056', '#3a262c', '#f2b0b0'),
        'Sunset Orange':      ('#342414', '#faeede', '#ccb096', '#a48a72',
                               '#ffb74d', '#e09b34', '#301c05',
                               '#43301c', '#503a23', '#452725', '#f5b6ad'),
        'Light Overlay':      ('#fafbfc', '#212121', '#5f6368', '#8a8f95',
                               '#1a73e8', '#1560c8', '#ffffff',
                               '#eaedf0', '#dee2e7', '#f7dada', '#b3261e'),
        'Midnight Blue':      ('#182236', '#e7edfa', '#a3b0c8', '#7c8aa3',
                               '#6c8fe8', '#5375cc', '#0a1226',
                               '#222e45', '#2b3952', '#382636', '#f0adba'),
    }

    _PALETTE_KEYS = ('surface', 'text', 'text_dim', 'text_faint', 'accent',
                     'accent_dim', 'accent_ink', 'button', 'button_hover',
                     'danger_bg', 'danger_text')

    @staticmethod
    def _svg_uri(body):
        """Path to an on-disk SVG for use in QSS url(...).

        Qt's stylesheet url() goes through QPixmap and cannot read data: URIs,
        so the icon must be a real file on disk.
        """
        import icons
        import hashlib
        key = 'qss-' + hashlib.md5(body.encode('utf-8')).hexdigest()[:8]
        return icons.qss_image(key, body)

    @staticmethod
    def _hex_to_rgb(value):
        value = value.lstrip('#')
        return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))

    @staticmethod
    def _mix(a, b, t):
        """Blend two hex colours; t=0 gives a, t=1 gives b."""
        ar, ag, ab = ThemeManager._hex_to_rgb(a)
        br, bg, bb = ThemeManager._hex_to_rgb(b)
        return '#%02x%02x%02x' % (
            round(ar + (br - ar) * t),
            round(ag + (bg - ag) * t),
            round(ab + (bb - ab) * t),
        )

    def get_dialog_palette(self, theme_name=None):
        """Concrete opaque colours for the settings window.

        Derived tints (card, field, divider) are mixed against the surface so
        they stay correct on both light and dark themes, instead of assuming a
        white overlay that would disappear on a light surface.
        """
        name = theme_name or self.current_theme
        values = self.DIALOG_PALETTES.get(
            name, self.DIALOG_PALETTES['Dark Glassmorphic'])
        p = dict(zip(self._PALETTE_KEYS, values))

        surface, text = p['surface'], p['text']
        light = sum(self._hex_to_rgb(surface)) > 382   # light surface?

        p['card'] = self._mix(surface, text, 0.05)
        p['field'] = self._mix(surface, '#000000' if not light else '#8a8f95', 0.16)
        p['divider'] = self._mix(surface, text, 0.10)
        p['footer'] = self._mix(surface, '#000000' if not light else '#8a8f95', 0.09)
        p['scroll_thumb'] = self._mix(surface, text, 0.28)
        return p

    def __init__(self, theme_name='Dark Glassmorphic'):
        # Ensure attribute exists even if provided theme is invalid
        self.current_theme = 'Dark Glassmorphic'
        self.auto_switch_enabled = False  # Disable auto-switching to preserve user choice
        
        # Cache for generated stylesheets
        self._overlay_stylesheet_cache = {}
        self._dialog_stylesheet_cache = {}
        
        self.set_theme(theme_name)
        
    def get_theme(self, theme_name=None):
        """Get theme colors"""
        if theme_name is None:
            theme_name = self.current_theme
        return self.THEMES.get(theme_name, self.THEMES['Dark Glassmorphic'])
        
    def set_theme(self, theme_name):
        """Set current theme"""
        if theme_name in self.THEMES:
            self.current_theme = theme_name
            # Clear caches when theme changes
            self._overlay_stylesheet_cache.clear()
            self._dialog_stylesheet_cache.clear()
            return True
        return False
        
    def get_theme_names(self):
        """Get list of available theme names"""
        return list(self.THEMES.keys())
        
    def get_overlay_stylesheet(self, theme_name=None):
        """Get overlay window stylesheet for the current theme"""
        cache_key = theme_name or self.current_theme
        
        # Return cached if available
        if cache_key in self._overlay_stylesheet_cache:
            return self._overlay_stylesheet_cache[cache_key]
        
        # Both surfaces are now painted entirely by OverlayWindow.paintEvent as a
        # single QPainterPath carrying fill *and* rim.  Two separately rasterised
        # rounded rects (a QSS background-with-radius under a painted stroke)
        # disagree by a fraction of a pixel at the corners, and that mismatch is
        # what produced the ragged edge.  These frames are kept purely as layout
        # hosts, so they must contribute no paint of their own.
        stylesheet = """
            #overlayContainer {
                background: transparent;
                border: none;
            }
            #hoverBackground {
                background: transparent;
                border: none;
            }
        """

        # Cache and return
        self._overlay_stylesheet_cache[cache_key] = stylesheet
        return stylesheet

    def get_edge_colors(self, theme_name=None):
        """Return (edge_hi, edge_lo) as 'r,g,b' strings for the rim gradient."""
        theme = self.get_theme(theme_name)
        return theme.get('edge_hi', '255,255,255'), theme.get('edge_lo', '255,255,255')

    def get_rim_stops(self, hovered=0.0):
        """Rim gradient stops as (offset, 'r,g,b', alpha) for the current theme.

        `hovered` is 0..1 so the rim can brighten continuously as the hover
        animation runs, rather than switching between two fixed styles.
        """
        hi, lo = self.get_edge_colors()
        gain = 1.0 + (self.RIM_HOVER_GAIN - 1.0) * max(0.0, min(1.0, hovered))
        return [
            (off, hi if which == 'edge_hi' else lo, min(255, alpha * gain))
            for off, which, alpha in self.RIM_STOPS
        ]
        
    def get_dialog_stylesheet(self, theme_name=None):
        """Stylesheet for the settings window, driven by the theme.

        The dialog previously hardcoded a fixed Material palette across ~40
        inline stylesheets and ignored the selected theme entirely.  Everything
        here derives from get_dialog_palette(), so the window matches the
        overlay it configures.

        Fields are borderless: a recessed fill plus an accent ring on focus,
        rather than a permanent 1.5px outline on all thirteen of them.
        """
        cache_key = theme_name or self.current_theme
        if cache_key in self._dialog_stylesheet_cache:
            return self._dialog_stylesheet_cache[cache_key]

        p = self.get_dialog_palette(theme_name)
        tick = self._svg_uri(
            '<path d="m3.5 8.2 3 3 6-6.4" fill="none" stroke="%s" stroke-width="2.1"'
            ' stroke-linecap="round" stroke-linejoin="round"/>' % p['accent_ink'])
        dot = self._svg_uri(
            '<circle cx="8" cy="8" r="3.4" fill="%s"/>' % p['accent_ink'])

        stylesheet = f"""
            QDialog {{
                background: {p['surface']};
            }}
            QWidget#dialogFooter {{
                background: {p['footer']};
                border-top: 1px solid {p['divider']};
            }}
            QWidget#settingsRoot, QWidget#scrollContent {{
                background: {p['surface']};
            }}
            QLabel {{
                color: {p['text']};
                font-family: 'Poppins', 'Segoe UI', sans-serif;
                font-size: 12px;
                background: transparent;
            }}
            QLabel#dialogTitle {{
                font-size: 17px;
                font-weight: 700;
                letter-spacing: -0.3px;
            }}
            QLabel#dialogSubtitle {{
                font-size: 11px;
                font-weight: 500;
                color: {p['text_dim']};
            }}
            QLabel#groupHeader {{
                font-size: 10px;
                font-weight: 600;
                color: {p['text_faint']};
                letter-spacing: 1.3px;
                background: {p['surface']};
            }}
            QLabel#rowLabel {{
                font-size: 12px;
                font-weight: 500;
                color: {p['text']};
            }}
            QLabel#rowHint {{
                font-size: 10px;
                font-weight: 400;
                color: {p['text_faint']};
            }}
            QFrame#groupCard {{
                background: {p['card']};
                border: none;
                border-radius: 10px;
            }}
            QFrame#rowDivider {{
                background: {p['divider']};
                border: none;
                max-height: 1px;
            }}
            QFrame#dangerCard {{
                background: {p['danger_bg']};
                border: none;
                border-radius: 10px;
            }}

            /* Borderless fields: recessed fill, accent ring only on focus. */
            QSpinBox, QComboBox {{
                background: {p['field']};
                color: {p['text']};
                border: none;
                border-radius: 7px;
                padding: 6px 10px;
                font-size: 12px;
                font-weight: 600;
                font-family: 'Poppins', 'Segoe UI', sans-serif;
                min-height: 22px;
                selection-background-color: {p['accent']};
                selection-color: {p['accent_ink']};
            }}
            QSpinBox:hover, QComboBox:hover {{
                background: {p['button']};
            }}
            QSpinBox:focus, QComboBox:focus {{
                border: 2px solid {p['accent']};
                padding: 4px 8px;
            }}
            QSpinBox QLineEdit, QComboBox QLineEdit {{
                background: transparent;
                color: {p['text']};
                border: none;
                selection-background-color: {p['accent']};
                selection-color: {p['accent_ink']};
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                border: none;
                background: transparent;
                width: 14px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 22px;
            }}
            QComboBox QAbstractItemView {{
                background: {p['card']};
                color: {p['text']};
                selection-background-color: {p['accent']};
                selection-color: {p['accent_ink']};
                border: none;
                border-radius: 8px;
                padding: 4px;
                outline: 0;
            }}

            /* Buttons are flat solid fills - no gradients, no borders. */
            QPushButton {{
                background: {p['button']};
                color: {p['text']};
                border: none;
                border-radius: 8px;
                padding: 7px 13px;
                font-size: 11px;
                font-weight: 600;
                font-family: 'Poppins', 'Segoe UI', sans-serif;
                min-height: 18px;
            }}
            QPushButton:hover {{
                background: {p['button_hover']};
            }}
            QPushButton:pressed {{
                background: {p['field']};
            }}
            QPushButton#primaryButton {{
                background: {p['accent']};
                color: {p['accent_ink']};
                padding: 7px 20px;
            }}
            QPushButton#primaryButton:hover {{
                background: {p['accent_dim']};
            }}
            QPushButton#ghostButton {{
                background: transparent;
                color: {p['text_dim']};
            }}
            QPushButton#ghostButton:hover {{
                background: {p['button']};
                color: {p['text']};
            }}
            QPushButton#dangerButton {{
                background: {p['danger_bg']};
                color: {p['danger_text']};
                padding: 8px 6px;
            }}
            QPushButton#dangerButton:hover {{
                background: {p['button_hover']};
            }}
            QPushButton#iconButton {{
                padding: 0px;
            }}
            QPushButton#iconButton:checked {{
                background: {p['accent']};
            }}
            QPushButton#presetChip {{
                background: {p['card']};
                color: {p['text_dim']};
                padding: 5px 6px;
                font-size: 10px;
                text-align: center;
                min-width: 66px;
                min-height: 32px;
            }}
            QPushButton#presetChip:hover {{
                background: {p['button']};
                color: {p['text']};
            }}
            QPushButton#presetChip:checked {{
                background: {p['accent']};
                color: {p['accent_ink']};
            }}

            QCheckBox, QRadioButton {{
                color: {p['text']};
                font-size: 12px;
                font-weight: 500;
                font-family: 'Poppins', 'Segoe UI', sans-serif;
                spacing: 8px;
                background: transparent;
            }}
            QCheckBox::indicator, QRadioButton::indicator {{
                width: 17px;
                height: 17px;
                border: none;
                background: {p['field']};
            }}
            QCheckBox::indicator {{ border-radius: 5px; }}
            QRadioButton::indicator {{ border-radius: 9px; }}
            QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
                background: {p['button_hover']};
            }}
            QCheckBox::indicator:checked {{
                background: {p['accent']};
                image: url({tick});
            }}
            QRadioButton::indicator:checked {{
                background: {p['accent']};
                image: url({dot});
            }}

            QToolTip {{
                background: {p['card']};
                color: {p['text']};
                border: none;
                padding: 5px 8px;
                font-size: 11px;
                font-family: 'Poppins', 'Segoe UI', sans-serif;
            }}
        """

        self._dialog_stylesheet_cache[cache_key] = stylesheet
        return stylesheet


    def get_progress_colors(self, theme_name=None):
        """Get progress bar colors"""
        theme = self.get_theme(theme_name)
        return {
            'low': theme['progress_low'],
            'mid': theme['progress_mid'],
            'high': theme['progress_high'],
        }
