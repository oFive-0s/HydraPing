"""
HydraPing - Glassmorphic Hydration Reminder Overlay
A sleek PySide6-based desktop overlay with advanced glassmorphism design
"""

import functools
import re
import sys
import os
import time
from PySide6 import QtCore, QtWidgets, QtGui
from theme_manager import ThemeManager
from confetti_widget import ConfettiWidget
from layouts import LayoutManager


_RGBA_RE = re.compile(r'rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([\d.]+)\s*)?\)')


@functools.lru_cache(maxsize=256)
def _rgba_tuple(value, fallback):
    """Parse 'rgba(r,g,b,a)' to a plain tuple.

    Cached on the token string: theme colours are a fixed, tiny set, but
    paintEvent re-reads them on every frame of the hover animation.  The cache
    holds tuples rather than QColors deliberately -- QColor is mutable, and
    callers do mutate what they get back (setAlpha), which would poison a cache
    of shared instances.
    """
    match = _RGBA_RE.match(value.strip()) if isinstance(value, str) else None
    if not match:
        return fallback
    r, g, b, a = match.groups()
    return (int(r), int(g), int(b), int(float(a)) if a is not None else 255)


@functools.lru_cache(maxsize=64)
def rgb_triplet(value):
    """Parse an 'r,g,b' edge token to a tuple, cached."""
    try:
        parts = [int(p) for p in value.split(',')]
        return tuple(parts[:3]) if len(parts) >= 3 else (255, 255, 255)
    except (ValueError, AttributeError):
        return (255, 255, 255)


def parse_rgba(value, fallback=(255, 255, 255, 255)):
    """Parse an 'rgba(r,g,b,a)' theme token into a fresh QColor (alpha 0-255)."""
    return QtGui.QColor(*_rgba_tuple(value, fallback))


def lerp_color(a, b, t):
    """Blend two QColors; t=0 gives a, t=1 gives b."""
    t = max(0.0, min(1.0, t))
    return QtGui.QColor(
        round(a.red() + (b.red() - a.red()) * t),
        round(a.green() + (b.green() - a.green()) * t),
        round(a.blue() + (b.blue() - a.blue()) * t),
        round(a.alpha() + (b.alpha() - a.alpha()) * t),
    )


class CircularProgress(QtWidgets.QWidget):
    """Circular progress ring widget"""
    
    def __init__(self, parent=None, theme_manager=None):
        super().__init__(parent)
        self.setFixedSize(46, 46)
        self._progress = 0  # 0-100
        self._animated_progress = 0
        self.theme_manager = theme_manager or ThemeManager()
        
        # Animation for smooth progress updates (reused)
        self._progress_anim = QtCore.QPropertyAnimation(self, b"animated_progress", self)
        self._progress_anim.setDuration(600)
        self._progress_anim.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)
        self._anim_running = False
        
    def get_animated_progress(self):
        return self._animated_progress
        
    def set_animated_progress(self, value):
        self._animated_progress = value
        self.update()
        
    animated_progress = QtCore.Property(float, get_animated_progress, set_animated_progress)
    
    def set_progress(self, value):
        """Set progress value (0-100)"""
        self._progress = max(0, min(100, value))
        if not self._anim_running or self._progress_anim.state() == QtCore.QAbstractAnimation.State.Stopped:
            self._progress_anim.stop()
            self._progress_anim.setStartValue(self._animated_progress)
            self._progress_anim.setEndValue(self._progress)
            self._progress_anim.start()
            self._anim_running = True
        
    def paintEvent(self, event):
        """Draw circular progress ring with enhanced visuals"""
        if not self.isVisible():
            return
            
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QtGui.QPainter.RenderHint.TextAntialiasing)
        
        # Calculate dimensions with perfect centering
        width = self.width()
        height = self.height()
        size = min(width, height)
        center = QtCore.QPointF(width / 2.0, height / 2.0)
        
        # Refined pen width for better visual balance
        pen_width = max(2.8, size / 14.0)
        radius = (size - pen_width) / 2.0 - 1.5
        
        # The old black shadow ellipse at radius-0.5 was a second, near-coincident
        # stroke under the track; the two partial-coverage rings beat against each
        # other and grained the circle.  The track alone carries the recess now.

        # Track, tinted from the theme's text colour so it stays visible on the
        # light themes (a hardcoded white track vanished on those).
        track_colour = parse_rgba(self.theme_manager.get_theme()['text_primary'])
        track_colour.setAlpha(38)
        pen = QtGui.QPen(track_colour)
        pen.setWidthF(pen_width)
        pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
        painter.drawEllipse(center, radius, radius)
        
        # Progress arc with glow effect
        if self._animated_progress > 0:
            # Get theme-based colors
            colors = self.theme_manager.get_progress_colors()
            
            if self._animated_progress < 33:
                color_str = colors['low']
            elif self._animated_progress < 66:
                color_str = colors['mid']
            else:
                color_str = colors['high']
            
            color = parse_rgba(color_str, (255, 255, 255, 220))
            rect = QtCore.QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2)
            span_angle = int(self._animated_progress * 360 / 100 * 16)
            
            # Outer glow
            glow_pen = QtGui.QPen(color)
            glow_pen.setWidthF(pen_width + 1.5)
            glow_pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
            glow_color = QtGui.QColor(color)
            glow_color.setAlpha(80)
            glow_pen.setColor(glow_color)
            painter.setPen(glow_pen)
            painter.drawArc(rect, 90 * 16, -span_angle)
            
            # Main progress arc
            pen = QtGui.QPen(color)
            pen.setWidthF(pen_width)
            pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
            painter.setPen(pen)
            painter.drawArc(rect, 90 * 16, -span_angle)
            
        # Percentage text
        font = painter.font()
        font_size = max(9, int(size / 4.2))
        font.setPixelSize(font_size)
        font.setWeight(QtGui.QFont.Weight.Bold)
        font.setFamily("Poppins")
        painter.setFont(font)

        text = f"{int(self._animated_progress)}%"

        # Centre the glyph ink on the ring's centre, not the font's line box.
        # AlignCenter centres ascent+descent, which for digits (no descenders)
        # leaves the visible ink off-centre; the old 1px-offset drop shadow then
        # dragged the composite a further half-pixel down.
        metrics = QtGui.QFontMetricsF(font)
        ink = metrics.tightBoundingRect(text)
        baseline_x = center.x() - ink.width() / 2.0 - ink.x()
        baseline_y = center.y() - ink.height() / 2.0 - ink.y()

        # tightBoundingRect is metric-exact but lands on fractional pixels, which
        # resamples badly at these sizes.  Snap the baseline to the device grid.
        dpr = self.devicePixelRatioF() or 1.0
        baseline_x = round(baseline_x * dpr) / dpr
        baseline_y = round(baseline_y * dpr) / dpr

        # Follow the theme: hardcoded white was invisible on the light themes,
        # whose text_primary is near-black.
        text_colour = parse_rgba(self.theme_manager.get_theme()['text_primary'])
        painter.setPen(text_colour)
        painter.drawText(QtCore.QPointF(baseline_x, baseline_y), text)


    def _parse_rgba(self, rgba_str):
        """Parse rgba string to QColor"""
        # Parse "rgba(r,g,b,a)" format
        import re
        match = re.match(r'rgba\((\d+),\s*(\d+),\s*(\d+),\s*(\d+)\)', rgba_str)
        if match:
            r, g, b, a = map(int, match.groups())
            return QtGui.QColor(r, g, b, a)
        return QtGui.QColor(255, 255, 255, 220)  # Fallback


class OverlayWindow(QtWidgets.QWidget):
    """Glassmorphic always-on-top overlay with animations and hover effects"""
    
    # Signals for controller communication
    drink_now_clicked = QtCore.Signal()
    snooze_clicked = QtCore.Signal()
    position_changed = QtCore.Signal(int, int)
    settings_requested = QtCore.Signal()
    manual_drink_requested = QtCore.Signal(int)
    terminate_requested = QtCore.Signal()
    
    def paintEvent(self, event):
        """Paint the glass surface: fill and rim on a single path.

        Everything the user sees as "the edge" is drawn here and nowhere else.
        The container/hover QFrames are transparent layout hosts (see
        ThemeManager.get_overlay_stylesheet) because a QSS rounded background
        under a painted stroke is two independent rasterisations of nearly the
        same shape, and their antialiased corners disagree by a fraction of a
        pixel.  That mismatch, plus three stacked partial-coverage strokes, is
        what made the old edge look ragged.
        """
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)

        rect = QtCore.QRectF(self.rect())
        radius = 8.0 if self._window_shape == 'circular' else 12.0

        # Quantise the pen to whole device pixels.  Qt paints in logical
        # coordinates, so on a 125%/150% display a 1.1px pen becomes 1.375/1.65
        # device px and resamples into a grainy edge no matter how clean the
        # geometry is.
        dpr = self.devicePixelRatioF() or 1.0
        pen_w = max(1.0, round(1.1 * dpr)) / dpr
        half = pen_w / 2.0

        # Inset by exactly half the pen so the stroke centreline lands on the
        # half-pixel grid instead of straddling a pixel boundary at ~50% coverage.
        body = rect.adjusted(half, half, -half, -half)
        body_radius = max(0.0, radius - half)

        theme = self.theme_manager.get_theme()
        t = self._hover_t

        # ---- fill: rest -> hover, interpolated so the hover fade is continuous
        fill = QtGui.QLinearGradient(rect.topLeft(), rect.bottomRight())
        fill.setColorAt(0.0, lerp_color(parse_rgba(theme['overlay_bg_start']),
                                        parse_rgba(theme['hover_bg_start']), t))
        fill.setColorAt(1.0, lerp_color(parse_rgba(theme['overlay_bg_end']),
                                        parse_rgba(theme['hover_bg_end']), t))

        # ---- rim: one stroke whose alpha varies around the perimeter
        rim = QtGui.QLinearGradient(rect.topLeft(), rect.bottomRight())
        for offset, rgb, alpha in self.theme_manager.get_rim_stops(t):
            # Direct construction: the alpha changes every hover frame, so a
            # formatted 'rgba(...)' string would miss the parse cache every time.
            rim.setColorAt(offset, QtGui.QColor(*rgb_triplet(rgb), int(alpha)))

        path = QtGui.QPainterPath()
        path.addRoundedRect(body, body_radius, body_radius)

        pen = QtGui.QPen(QtGui.QBrush(rim), pen_w)
        pen.setJoinStyle(QtCore.Qt.PenJoinStyle.RoundJoin)
        pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(QtGui.QBrush(fill))
        # Single drawPath: fill and stroke share one rasterisation, so there is
        # no seam between them.
        painter.drawPath(path)

        edge_hi, _ = self.theme_manager.get_edge_colors()

        # ---- glass thickness: concentric inner feather, lit on its top 45% only
        feather_inset = pen_w + 0.35
        feather = rect.adjusted(feather_inset, feather_inset,
                                -feather_inset, -feather_inset)
        if feather.width() > 0 and feather.height() > 0:
            inner = QtGui.QLinearGradient(feather.topLeft(), feather.bottomLeft())
            hi = rgb_triplet(edge_hi)
            inner.setColorAt(0.0, QtGui.QColor(*hi, round(34 * (1 + 0.45 * t))))
            inner.setColorAt(0.45, QtGui.QColor(*hi, 0))
            inner_pen = QtGui.QPen(QtGui.QBrush(inner), 0.9)
            inner_pen.setJoinStyle(QtCore.Qt.PenJoinStyle.RoundJoin)
            painter.setPen(inner_pen)
            painter.setBrush(QtCore.Qt.BrushStyle.NoBrush)
            inner_radius = max(0.0, radius - feather_inset)
            inner_path = QtGui.QPainterPath()
            inner_path.addRoundedRect(feather, inner_radius, inner_radius)
            painter.drawPath(inner_path)

        # ---- sheen hairline just inside the top edge, fading out before the corners
        if rect.width() > radius * 2:
            y = feather_inset + 0.6
            sheen = QtGui.QLinearGradient(radius, y, rect.width() - radius, y)
            hi = rgb_triplet(edge_hi)
            sheen.setColorAt(0.0, QtGui.QColor(*hi, 0))
            sheen.setColorAt(0.35, QtGui.QColor(*hi, round(60 * (1 + 0.45 * t))))
            sheen.setColorAt(0.82, QtGui.QColor(*hi, 0))
            sheen_pen = QtGui.QPen(QtGui.QBrush(sheen), 1.0)
            sheen_pen.setCapStyle(QtCore.Qt.PenCapStyle.FlatCap)
            painter.setPen(sheen_pen)
            painter.drawLine(QtCore.QPointF(radius, y),
                             QtCore.QPointF(rect.width() - radius, y))

        painter.end()

    def __init__(self, parent=None, theme_name='Dark Glassmorphic'):
        super().__init__(parent)
        
        # Theme manager
        self.theme_manager = ThemeManager(theme_name)
        
        # Window shape setting and layout manager
        self._window_shape = 'rectangular'  # 'rectangular' or 'circular'
        self._saved_shape = 'rectangular'  # User's preferred shape (for auto-revert)
        self._layout_manager = LayoutManager(self)
        
        # State management
        self._drag_active = False
        self._drag_offset = QtCore.QPoint()
        self._is_hovered = False
        # Hover is a continuous 0..1 value read by paintEvent, not a second
        # translucent QFrame faded in over the first.  Two stacked glass panels
        # meant two rims and two rounded-rect rasterisations.
        self._hover_t = 0.0
        self._alert_mode = False
        self._current_message_index = 0
        self._current_consumed = 0
        self._current_goal = 2000
        self._show_consumed = True  # Toggle between consumed and countdown
        
        # Sound loop timer (reused)
        self._sound_loop_timer = QtCore.QTimer(self)
        self._sound_loop_timer.timeout.connect(self._replay_sound_internal)
        self._current_sound_path = None
        
        # Motivational messages
        self._motivational_messages = [
            "Stay Hydrated, Stay Healthy",
            "Water is Life's Elixir",
            "Hydration is Key to Wellness",
            "Drink Water, Feel Better",
            "Your Body Needs Water",
            "Keep Sipping, Keep Shining",
            "Water: Nature's Medicine",
            "Hydrate for Better Focus",
            "Every Sip Counts",
            "Refresh Your Body",
            "Water Fuels Your Energy",
            "Stay Fresh, Stay Hydrated",
            "Your Health Starts Here",
            "Drink Up, Live Well",
            "Hydration = Happiness",
            "Water is Vital",
            "Nourish Your Body",
            "Small Sips, Big Impact",
            "Keep Your Body Happy",
            "Water: Your Best Friend",
            "Stay Balanced, Stay Hydrated",
            "Hydrate to Elevate",
            "Drink More, Worry Less",
            "Wellness Begins with Water",
            "Your Daily Dose of Health",
            "Sip by Sip, Feel the Difference",
            "Hydrate Your Mind & Body",
            "Water: The Ultimate Reset",
            "Quench Your Thirst for Life",
            "Pure Hydration, Pure Joy",
            "Drink Water, Embrace Vitality",
            "Your Cells Thank You",
            "Stay Hydrated, Stay Sharp",
            "Water: Liquid Wellness",
            "Every Drop Matters",
            "Hydrate to Celebrate Life",
            "Water is Your Superpower",
            "Refresh, Recharge, Repeat",
            "Hydration is Self-Care",
            "Drink Up, Glow Up",
            "Water: Nature's Perfect Drink",
            "Stay Healthy, Stay Hydrated",
            "Your Body is 60% Water",
            "Hydrate Like a Champion",
            "Sip Smart, Live Better",
            "Water: Simple Yet Essential",
            "Hydration Fuels Everything",
            "Make Water Your Priority",
            "Drink More, Thrive More",
            "Water is Your Daily Ritual",
            "Stay Hydrated, Stay Amazing",
            "Pure Water, Pure Energy",
            "Hydration Never Goes Out of Style",
            "Your Best Health Starts with H2O",
            "Sip Your Way to Wellness"
        ]
        
        self._setup_window()
        self._create_ui()
        self._setup_animations()
        self._setup_timers()
        self._setup_background_detection()
        
        # Confetti widget
        self._confetti = ConfettiWidget()
        
    def _setup_window(self):
        """Configure window properties for glassmorphic overlay"""
        # Set window icon
        import os
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QtGui.QIcon(icon_path))
        
        # Frameless, always-on-top, translucent
        self.setWindowFlags(
            QtCore.Qt.WindowType.FramelessWindowHint |
            QtCore.Qt.WindowType.Tool |
            QtCore.Qt.WindowType.WindowStaysOnTopHint |
            QtCore.Qt.WindowType.NoDropShadowWindowHint
        )
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_NoSystemBackground)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_OpaquePaintEvent, False)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        
        # Fixed size for overlay (will be updated based on shape)
        self._apply_window_shape()
        
        # Position at top center of screen
        self._position_window()
    
    def _setup_background_detection(self):
        """Setup timer for background brightness detection"""
        self._bg_check_timer = QtCore.QTimer(self)
        self._bg_check_timer.timeout.connect(self._check_background_and_switch_theme)
        # Disabled by default - user's manual theme choice should persist
        # self._bg_check_timer.start(2000)  # Check every 2 seconds
        
    def _check_background_and_switch_theme(self):
        """Detect background brightness and switch theme dynamically"""
        if not self.theme_manager.auto_switch_enabled:
            return
            
        try:
            # Get screenshot of area behind overlay
            screen = QtWidgets.QApplication.primaryScreen()
            if screen is None:
                return
                
            # Capture area behind overlay
            x = self.x()
            y = self.y()
            w = self.width()
            h = self.height()
            
            pixmap = screen.grabWindow(0, x, y, w, h)
            image = pixmap.toImage()
            
            # Sample pixels to determine average brightness
            total_brightness = 0
            sample_count = 0
            step = 10  # Sample every 10 pixels
            
            for py in range(0, h, step):
                for px in range(0, w, step):
                    if px < image.width() and py < image.height():
                        color = image.pixelColor(px, py)
                        # Calculate perceived brightness
                        brightness = (0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue())
                        total_brightness += brightness
                        sample_count += 1
            
            if sample_count == 0:
                return
                
            avg_brightness = total_brightness / sample_count
            
            # Switch theme based on brightness
            # If background is dark (< 128), use light theme
            # If background is light (>= 128), use dark theme
            if avg_brightness < 128:
                new_theme = 'Dark Glassmorphic'  # Light overlay on dark background
            else:
                new_theme = 'Light Glassmorphic'  # Dark overlay on light background
            
            # Only update if theme changed
            if self.theme_manager.current_theme != new_theme:
                self.theme_manager.set_theme(new_theme)
                self._update_theme_colors()
                
        except Exception as e:
            print(f"[Overlay] Background detection error: {e}")
    
    def _update_theme_colors(self):
        """Re-colour every themed widget from the current theme.

        Called from __init__ as well as set_theme: the widgets are built with
        placeholder colours, and until this runs they are all white, which is
        invisible on the light themes.
        """
        # Update stylesheets
        self._bg_box.setStyleSheet(self.theme_manager.get_overlay_stylesheet())
        self._container.setStyleSheet(self.theme_manager.get_overlay_stylesheet())

        # Update text colors
        theme = self.theme_manager.get_theme()
        edge_hi, _ = self.theme_manager.get_edge_colors()

        # NB: this used to guard on '_consumed_label', an attribute that is never
        # assigned anywhere, so the ml counter was never re-themed at all.
        if hasattr(self, '_info_label'):
            self._info_label.setStyleSheet(f"""
                QLabel {{
                    color: {theme['text_secondary']};
                    font-size: 10.5px;
                    font-weight: 600;
                    font-family: 'Poppins', 'Segoe UI', sans-serif;
                    background: transparent;
                    border: none;
                    padding: 2px 4px;
                    letter-spacing: 0.1px;
                }}
            """)

        # Drink / snooze were previously never re-themed on any code path.
        for button, tint in ((getattr(self, '_drink_button', None), edge_hi),
                             (getattr(self, '_snooze_button', None), '255,200,100')):
            if button is None:
                continue
            button.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(
                        x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba({tint},55),
                        stop:0.06 rgba({tint},34),
                        stop:1 rgba({tint},16)
                    );
                    color: {theme['text_primary']};
                    border: none;
                    border-radius: 8px;
                    padding: 5px 14px;
                    font-size: 11px;
                    font-weight: 600;
                    font-family: 'Poppins', 'Segoe UI', sans-serif;
                }}
                QPushButton:hover {{
                    background: qlineargradient(
                        x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba({tint},78),
                        stop:0.06 rgba({tint},50),
                        stop:1 rgba({tint},26)
                    );
                }}
                QPushButton:pressed {{
                    background: qlineargradient(
                        x1:0, y1:0, x2:0, y2:1,
                        stop:0 rgba({tint},40),
                        stop:1 rgba({tint},22)
                    );
                }}
            """)

        if hasattr(self, '_progress_widget'):
            self._progress_widget.theme_manager = self.theme_manager

        if hasattr(self, '_message_label'):
            self._message_label.setStyleSheet(f"""
                QLabel {{
                    color: {theme['text_secondary']};
                    font-size: 10px;
                    font-weight: 500;
                    background: transparent;
                    letter-spacing: 0.5px;
                }}
            """)
        
        if hasattr(self, '_menu_button'):
            # Deliberately far more transparent than theme['button_bg'] (alpha
            # ~25-30): this button sits *on* the glass, and at that weight it
            # reads as an opaque chip competing with the surface rather than an
            # affordance resting on it.  Matches the original alpha-6 intent.
            self._menu_button.setStyleSheet(f"""
                QToolButton {{
                    background: rgba({edge_hi},8);
                    color: {theme['text_secondary']};
                    border: none;
                    border-radius: 8px;
                    padding: 1px;
                    font-size: 15px;
                    font-weight: 600;
                }}
                QToolButton:hover {{
                    background: rgba({edge_hi},20);
                    color: {theme['text_primary']};
                }}
                QToolButton:pressed {{
                    background: rgba({edge_hi},12);
                }}
            """)
            try:
                import icons
                dpr = self.devicePixelRatioF() or 1.0
                self._menu_button.setIcon(
                    icons.icon('kebab', parse_rgba(theme['text_secondary']), 16, dpr))
                self._menu_button.setIconSize(QtCore.QSize(16, 16))
            except Exception:
                # Icon rendering unavailable: fall back to the text glyph.
                self._menu_button.setText("⋮")
        
        # Update progress widget
        if hasattr(self, '_progress_widget'):
            self._progress_widget.update()
        
    def _create_ui(self):
        """Create glassmorphic UI components"""
        # Main layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Background hover effect (initially hidden)
        self._bg_box = QtWidgets.QFrame(self)
        self._bg_box.setObjectName("hoverBackground")
        self._bg_box.setStyleSheet(self.theme_manager.get_overlay_stylesheet())
        
        # Opacity effect for background
        self._bg_opacity_effect = QtWidgets.QGraphicsOpacityEffect(self._bg_box)
        self._bg_opacity_effect.setOpacity(0.0)
        self._bg_box.setGraphicsEffect(self._bg_opacity_effect)
        
        # Main container
        container = QtWidgets.QFrame(self)
        container.setObjectName("overlayContainer")
        container.setStyleSheet(self.theme_manager.get_overlay_stylesheet())
        container.installEventFilter(self)
        main_layout.addWidget(container)
        self._container = container
        
        # Create widgets first
        self._create_all_widgets(container)
        
        # Apply initial layout using LayoutManager
        self._layout_manager.set_preferred_layout(self._window_shape)
        self._layout_manager.apply_layout(self._window_shape)

        # Widgets are built with placeholder colours; bind them to the theme now.
        # main.py constructs OverlayWindow(theme_name=...) and only calls
        # set_theme() later when settings change, so without this a launch with a
        # light theme saved showed white-on-white until the user re-picked it.
        self._update_theme_colors()

        # Use window opacity instead of graphics effect to avoid painting conflicts
        self.setWindowOpacity(0.65)  # Rest state
    
    def _create_all_widgets(self, container):
        """Create all UI widgets"""
        # Circular progress widget
        self._progress_widget = CircularProgress(container, self.theme_manager)
        
        # Menu button (⋮)
        self._menu_button = QtWidgets.QToolButton(container)
        # Icon set in _update_theme_colors so it can follow the theme colour.
        self._menu_button.setText("")
        self._menu_button.setFixedSize(30, 30)
        self._menu_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self._menu_button.setStyleSheet("""
            QToolButton {
                background: rgba(255,255,255,6);
                color: rgba(255,255,255,160);
                font-size: 15px;
                font-weight: 600;
                border-radius: 8px;
                padding: 1px;
                border: 1px solid transparent;
            }
            QToolButton:hover {
                background: rgba(255,255,255,18);
                color: rgba(255,255,255,240);
                border-color: rgba(255,255,255,12);
            }
            QToolButton:pressed {
                background: rgba(255,255,255,10);
            }
        """)
        self._menu_button.clicked.connect(self._show_menu)
        
        # Message label (rotating motivational messages)
        self._message_label = QtWidgets.QLabel(self._motivational_messages[0])
        self._message_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self._message_label.setStyleSheet("""
            QLabel {
                color: rgba(255,255,255,230);
                font-size: 11.5px;
                font-weight: 600;
                font-family: 'Poppins', 'Segoe UI', sans-serif;
                letter-spacing: -0.15px;
                background: transparent;
            }
        """)
        
        # Drink Now button (hidden initially)
        self._drink_button = QtWidgets.QPushButton("Drink Now")
        self._drink_button.setFixedSize(87, 32)
        self._drink_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self._drink_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,255,255,30),
                    stop:1 rgba(255,255,255,20)
                );
                color: rgba(255,255,255,240);
                border-radius: 8px;
                border: 1px solid rgba(255,255,255,40);
                padding: 5px 14px;
                font-size: 11px;
                font-weight: 600;
                font-family: 'Poppins', 'Segoe UI', sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,255,255,42),
                    stop:1 rgba(255,255,255,32)
                );
                border-color: rgba(255,255,255,55);
            }
            QPushButton:pressed {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,255,255,50),
                    stop:1 rgba(255,255,255,40)
                );
            }
        """)
        self._drink_button.clicked.connect(self.drink_now_clicked.emit)
        self._drink_button.setVisible(False)
        
        # Snooze button (hidden initially)
        self._snooze_button = QtWidgets.QPushButton("Snooze")
        self._snooze_button.setFixedSize(69, 32)
        self._snooze_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self._snooze_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,200,100,30),
                    stop:1 rgba(255,200,100,20)
                );
                color: rgba(255,255,255,240);
                border-radius: 8px;
                border: 1px solid rgba(255,200,100,40);
                padding: 5px 14px;
                font-size: 11px;
                font-weight: 600;
                font-family: 'Poppins', 'Segoe UI', sans-serif;
            }
            QPushButton:hover {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,200,100,42),
                    stop:1 rgba(255,200,100,32)
                );
                border-color: rgba(255,200,100,55);
            }
            QPushButton:pressed {
                background: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255,200,100,50),
                    stop:1 rgba(255,200,100,40)
                );
            }
        """)
        self._snooze_button.clicked.connect(self.snooze_clicked.emit)
        self._snooze_button.setVisible(False)
        
        # Info label (alternates between consumed and countdown on hover)
        self._info_label = QtWidgets.QLabel("0ml / 2000ml")
        self._info_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
        # 110px clipped the leading digit at exactly the moment that matters
        # most: "2000ml / 2000ml" measures 103px and the 4px side padding left
        # only 102px, so hitting your goal truncated the number.
        self._info_label.setFixedWidth(128)
        self._info_label.setStyleSheet("""
            QLabel {
                color: rgba(255,255,255,220);
                font-size: 10.5px;
                font-weight: 600;
                font-family: 'Poppins', 'Segoe UI', sans-serif;
                background-color: transparent;
                background: transparent;
                border: none;
                padding: 2px 4px;
                letter-spacing: 0.1px;
            }
        """)
        self._info_label.setAttribute(QtCore.Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._info_label.setVisible(False)
        
        # Store countdown text for alternating display
        self._countdown_text = "Next: --:--"
    
    def _update_bg_box_geometry(self):
        """Update background box geometry based on current window shape"""
        # Now handled by LayoutManager.apply_layout()
        pass
        
    def get_hover_t(self):
        return self._hover_t

    def set_hover_t(self, value):
        self._hover_t = max(0.0, min(1.0, float(value)))
        self.update()

    hover_t = QtCore.Property(float, get_hover_t, set_hover_t)

    def _animate_hover(self, target):
        """Drive the rim/fill blend toward `target` (0 rest, 1 hover)."""
        self._bg_box_anim.stop()
        self._bg_box_anim.setStartValue(self._hover_t)
        self._bg_box_anim.setEndValue(float(target))
        self._bg_box_anim.start()

    def _setup_animations(self):
        """Setup smooth animations for all interactive elements"""
        # Main window fade animation
        self._fade_anim = QtCore.QPropertyAnimation(self, b"windowOpacity", self)
        self._fade_anim.setDuration(380)
        self._fade_anim.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)

        # Hover blend animation (drives paintEvent, not a QFrame's opacity)
        self._bg_box_anim = QtCore.QPropertyAnimation(self, b"hover_t", self)
        self._bg_box_anim.setDuration(350)
        self._bg_box_anim.setEasingCurve(QtCore.QEasingCurve.Type.InOutQuad)
        
        # Drink button fade animation
        self._drink_button_anim = QtCore.QPropertyAnimation(self._drink_button, b"maximumHeight", self)
        self._drink_button_anim.setDuration(300)
        self._drink_button_anim.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)
        
        # Info label - no animations, just show/hide
        
    def _setup_timers(self):
        """Setup timers for message rotation and topmost enforcement"""
        # Message rotation timer (15 seconds)
        self._message_timer = QtCore.QTimer(self)
        self._message_timer.timeout.connect(self._rotate_message)
        self._message_timer.start(15000)
        
        # Info alternation timer (2 seconds) - switches between consumed and countdown
        self._info_alternation_timer = QtCore.QTimer(self)
        self._info_alternation_timer.timeout.connect(self._alternate_info_display)
        
        # Always-on-top enforcement timer (4 seconds)
        if sys.platform == "win32":
            self._topmost_timer = QtCore.QTimer(self)
            self._topmost_timer.timeout.connect(self._ensure_topmost)
            self._topmost_timer.start(4000)
            
    def _rotate_message(self):
        """Rotate to next motivational message"""
        if not self._alert_mode:
            self._current_message_index = (self._current_message_index + 1) % len(self._motivational_messages)
            self._message_label.setText(self._motivational_messages[self._current_message_index])
    
    def set_smart_message(self, message: str):
        """Set a smart message (AI prediction or context-aware)"""
        if hasattr(self, '_message_label') and not self._alert_mode:
            self._message_label.setText(message)
    
    def _alternate_info_display(self):
        """Alternate between showing consumed ml and countdown timer"""
        if self._is_hovered and not self._alert_mode:
            self._show_consumed = not self._show_consumed
            
            # Determine new text
            if self._show_consumed:
                new_text = f"{self._current_consumed}ml / {self._current_goal}ml"
            else:
                new_text = self._countdown_text
            
            # Update text and ensure visible
            self._info_label.setText(new_text)
            self._info_label.setVisible(True)
            self._info_label.update()
            
    def _ensure_topmost(self):
        """Ensure window stays on top using Win32 API"""
        if sys.platform == "win32":
            try:
                import ctypes
                hwnd = int(self.winId())
                # HWND_TOPMOST = -1, SWP_NOMOVE | SWP_NOSIZE = 0x0013
                ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0013)
            except:
                pass
                
    def _animate_opacity(self, target_opacity):
        """Smoothly animate window opacity"""
        self._fade_anim.stop()
        self._fade_anim.setStartValue(self.windowOpacity())
        self._fade_anim.setEndValue(target_opacity)
        self._fade_anim.start()
        
    def _show_menu(self):
        """Show context menu with drink presets and settings"""
        menu = QtWidgets.QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: rgba(28,28,36,245);
                color: rgba(255,255,255,230);
                border: 1px solid rgba(255,255,255,60);
                border-radius: 10px;
                padding: 6px 4px;
                font-size: 11px;
                font-family: 'Poppins', 'Segoe UI', sans-serif;
            }
            QMenu::item {
                padding: 7px 20px 7px 12px;
                border-radius: 6px;
                margin: 1px 4px;
            }
            QMenu::item:selected {
                background: rgba(255,255,255,18);
            }
            QMenu::separator {
                height: 1px;
                background: rgba(255,255,255,10);
                margin: 4px 10px;
            }
        """)
        
        # Drink preset actions
        menu.addAction("Drink 100ml", lambda: self.manual_drink_requested.emit(100))
        menu.addAction("Drink 200ml", lambda: self.manual_drink_requested.emit(200))
        menu.addAction("Drink 250ml", lambda: self.manual_drink_requested.emit(250))
        menu.addAction("Drink 500ml", lambda: self.manual_drink_requested.emit(500))
        menu.addSeparator()
        
        # Custom amount action
        custom_action = menu.addAction("Custom Amount...", self._show_custom_dialog)
        menu.addSeparator()
        
        # Settings action
        menu.addAction("Settings", self.settings_requested.emit)
        
        # Show menu below menu button
        pos = self._menu_button.mapToGlobal(QtCore.QPoint(0, self._menu_button.height()))
        menu.exec(pos)
        
    def _show_custom_dialog(self):
        """Show dialog for custom water amount"""
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Custom Amount")
        dialog.setModal(True)
        dialog.setFixedSize(280, 140)
        dialog.setStyleSheet("""
            QDialog {
                background: rgba(28,28,36,250);
                border: 1px solid rgba(255,255,255,60);
                border-radius: 12px;
            }
            QLabel {
                color: rgba(255,255,255,230);
                font-size: 12px;
                font-weight: 600;
                font-family: 'Poppins', 'Segoe UI', sans-serif;
            }
            QSpinBox {
                background: rgba(255,255,255,10);
                color: rgba(255,255,255,230);
                border: 1.5px solid rgba(255,255,255,35);
                border-radius: 7px;
                padding: 7px;
                font-size: 12px;
                font-family: 'Poppins', 'Segoe UI', sans-serif;
            }
            QSpinBox:focus {
                border-color: rgba(138, 180, 248, 180);
            }
            QPushButton {
                background: rgba(255,255,255,18);
                color: rgba(255,255,255,230);
                border: 1px solid rgba(255,255,255,35);
                border-radius: 7px;
                padding: 8px 18px;
                font-size: 11px;
                font-weight: 600;
                font-family: 'Poppins', 'Segoe UI', sans-serif;
            }
            QPushButton:hover {
                background: rgba(255,255,255,28);
                border-color: rgba(255,255,255,50);
            }
            QPushButton:pressed {
                background: rgba(255,255,255,12);
            }
        """)
        
        layout = QtWidgets.QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        
        label = QtWidgets.QLabel("Enter amount (ml):")
        layout.addWidget(label)
        
        spinbox = QtWidgets.QSpinBox()
        spinbox.setRange(50, 2000)
        spinbox.setValue(250)
        spinbox.setSuffix(" ml")
        layout.addWidget(spinbox)
        
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setSpacing(8)
        
        ok_button = QtWidgets.QPushButton("OK")
        ok_button.clicked.connect(dialog.accept)
        cancel_button = QtWidgets.QPushButton("Cancel")
        cancel_button.clicked.connect(dialog.reject)
        
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)
        
        if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
            self.manual_drink_requested.emit(spinbox.value())
            
    def _handle_hover_enter(self):
        """Consolidated hover enter logic"""
        self._is_hovered = True
        self._animate_opacity(0.85)
        
        # Brighten the rim and lift the fill.  This is safe in every shape now:
        # the old code had to skip circular mode because the hover QFrame's
        # square corners poked outside the rounded window.  There is no second
        # frame any more, so the blend just follows the one path.
        self._animate_hover(1.0)


        # Only show info/close in rectangular mode
        if self._layout_manager.should_show_info_label():
            # Show info label and start alternation
            self._show_consumed = True
            self._info_label.setText(f"{self._current_consumed}ml / {self._current_goal}ml")
            self._info_label.setVisible(True)
            self._info_alternation_timer.start(2000)
    
    def enterEvent(self, event):
        """Handle mouse entering the overlay widget"""
        self._handle_hover_enter()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """Handle mouse leaving the overlay widget"""
        QtCore.QTimer.singleShot(100, self._check_and_hide)
        super().leaveEvent(event)
        
    def eventFilter(self, watched, event):
        """Handle hover events for container"""
        if hasattr(self, "_container") and watched == self._container:
            if event.type() == QtCore.QEvent.Type.Enter:
                self._handle_hover_enter()
            elif event.type() == QtCore.QEvent.Type.Leave:
                QtCore.QTimer.singleShot(100, self._check_and_hide)
        return super().eventFilter(watched, event)
        
    def _check_and_hide(self):
        """Check if mouse is truly outside and hide elements"""
        cursor_pos = QtGui.QCursor.pos()
        widget_rect = self.rect()
        local_pos = self.mapFromGlobal(cursor_pos)
        
        if not widget_rect.contains(local_pos):
            self._is_hovered = False
            if not self._alert_mode:
                self._animate_opacity(0.65)
                
            # Settle the rim back to rest
            self._animate_hover(0.0)

            # Hide info label and stop alternation (only if should be shown)
            if self._layout_manager.should_show_info_label():
                self._info_label.setVisible(False)
                self._info_alternation_timer.stop()
            
    def mousePressEvent(self, event):
        """Handle mouse press for drag-to-move"""
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self._drag_active = True
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            
    def mouseMoveEvent(self, event):
        """Handle mouse move for drag-to-move"""
        if self._drag_active and event.buttons() & QtCore.Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_offset)
            
    def mouseReleaseEvent(self, event):
        """Handle mouse release after dragging"""
        if self._drag_active:
            self._drag_active = False
            self.position_changed.emit(self.x(), self.y())
    
    def mouseDoubleClickEvent(self, event):
        """Handle double-click to open settings (especially for circular mode)"""
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.settings_requested.emit()
    
    def play_alert_sound(self, custom_sound_path=None, loop=False):
        """Play alert sound - custom file or default system beep"""
        # Stop any existing loop
        self._sound_loop_timer.stop()
        self._current_sound_path = custom_sound_path
            
        if custom_sound_path and os.path.exists(custom_sound_path):
            try:
                import winsound
                import ctypes
                
                # Use MCI for MP3/other formats, fallback to winsound for WAV
                if custom_sound_path.lower().endswith('.wav'):
                    flags = winsound.SND_FILENAME | winsound.SND_ASYNC
                    if loop:
                        flags |= winsound.SND_LOOP
                    winsound.PlaySound(custom_sound_path, flags)
                else:
                    # Use Windows MCI for MP3/OGG/FLAC
                    winmm = ctypes.windll.winmm
                    winmm.mciSendStringW(f'close alertsound', None, 0, None)  # Close previous
                    winmm.mciSendStringW(f'open "{custom_sound_path}" type mpegvideo alias alertsound', None, 0, None)
                    
                    if loop:
                        # Set up loop timer for non-WAV files
                        winmm.mciSendStringW('play alertsound from 0', None, 0, None)
                        
                        # Get duration
                        buffer = ctypes.create_unicode_buffer(255)
                        winmm.mciSendStringW('status alertsound length', buffer, 254, None)
                        try:
                            duration_ms = int(buffer.value)
                            self._sound_loop_timer.start(duration_ms + 100)  # Add small gap
                        except:
                            pass
                    else:
                        winmm.mciSendStringW('play alertsound from 0', None, 0, None)
            except Exception as e:
                print(f"[Overlay] Failed to play custom sound: {e}")
                try:
                    import winsound
                    winsound.MessageBeep(winsound.MB_ICONASTERISK)
                except:
                    pass
        else:
            try:
                import winsound
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            except:
                pass
    
    def _replay_sound_internal(self):
        """Replay sound for looping (internal method)"""
        try:
            import ctypes
            winmm = ctypes.windll.winmm
            winmm.mciSendStringW('play alertsound from 0', None, 0, None)
        except:
            pass
    
    def stop_alert_sound(self):
        """Stop any playing alert sound"""
        self._sound_loop_timer.stop()
        self._current_sound_path = None
        
        try:
            import winsound
            import ctypes
            
            # Stop WAV playback
            winsound.PlaySound(None, winsound.SND_PURGE)
            
            # Stop MCI playback
            winmm = ctypes.windll.winmm
            winmm.mciSendStringW('stop alertsound', None, 0, None)
            winmm.mciSendStringW('close alertsound', None, 0, None)
        except:
            pass
    
    def set_alert_mode(self, enabled, custom_sound_path=None, loop_sound=False):
        """Toggle alert mode (time to drink)"""
        self._alert_mode = enabled
        
        # Use LayoutManager to handle alert mode transitions
        self._layout_manager.set_alert_mode(enabled)
        
        if enabled:
            # Alert state - hide message but show consumption info
            self._message_label.setVisible(False)
            self._info_label.setText(f"{self._current_consumed}ml / {self._current_goal}ml")
            self._info_label.setVisible(True)
            
            self._animate_opacity(1.0)

            # Glow effect
            self._animate_hover(1.0)

            # Play sound
            self.play_alert_sound(custom_sound_path, loop_sound)
            
        else:
            # Rest state - restore message label
            self.stop_alert_sound()
            
            # Show message label based on layout
            if self._layout_manager.should_show_message_label():
                self._message_label.setVisible(True)
                self._message_label.setText(self._motivational_messages[self._current_message_index])
            
            if not self._is_hovered:
                self._animate_opacity(0.65)
                self._animate_hover(0.0)
                
    def update_countdown(self, text):
        """Update countdown text (only in non-alert mode)"""
        if not self._alert_mode:
            self._countdown_text = text
            # Update display ONLY if currently showing countdown AND hovered AND in rectangular mode
            if self._is_hovered and not self._show_consumed and self._layout_manager.should_show_info_label():
                self._info_label.setText(text)
            
    def update_consumption(self, consumed, goal):
        """Update consumption display"""
        self._current_consumed = consumed
        self._current_goal = goal
        
        # Update display ONLY if currently showing consumed AND hovered
        if self._is_hovered and self._show_consumed:
            self._info_label.setText(f"{consumed}ml / {goal}ml")
        
        # Update progress ring
        percentage = (consumed / goal * 100) if goal > 0 else 0
        self._progress_widget.set_progress(percentage)
        
    def flash_success(self):
        """Brief flash effect when water is logged"""
        # Briefly go to full opacity
        current_opacity = self.windowOpacity()
        self._animate_opacity(1.0)
        
        # Return to previous state after 300ms
        QtCore.QTimer.singleShot(300, lambda: self._animate_opacity(current_opacity))
    
    def celebrate_goal(self):
        """Trigger confetti celebration animation"""
        # Position confetti widget at screen center
        screen = QtWidgets.QApplication.primaryScreen().geometry()
        confetti_width = screen.width()
        confetti_height = screen.height()
        self._confetti.start_celebration(confetti_width, confetti_height)
    
    def set_theme(self, theme_name):
        """Change the overlay theme"""
        self.theme_manager.set_theme(theme_name)
        # Update all theme-dependent colors immediately
        self._update_theme_colors()
        # Update progress widget theme
        self._progress_widget.theme_manager = self.theme_manager
        self._progress_widget.update()
    
    def set_window_shape(self, shape, save_preference=True):
        """Change window shape between rectangular and circular"""
        if shape in ['rectangular', 'circular'] and shape != self._window_shape:
            self._window_shape = shape
            
            # Save user preference (unless it's a temporary switch)
            if save_preference:
                self._saved_shape = shape
                self._layout_manager.set_preferred_layout(shape)
            
            # Apply layout using new manager
            self._layout_manager.apply_layout(shape)
            
            # Position window
            self._position_window()
    
    def _apply_window_shape(self):
        """Apply the current window shape (rectangular or circular)"""
        # Now handled by LayoutManager.apply_layout()
        pass
    
    def _position_window(self):
        """Position window at top center of screen"""
        screen = QtWidgets.QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = 20
        self.move(x, y)
