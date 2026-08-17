"""
Shared UI pieces for HydraPing's settings window.

SmoothScrollArea replaces four QScrollArea defaults that make a long settings
pane feel cheap:

  * the wheel jumps ~3 lines instantly, with no easing
  * content is cut dead at the top and bottom edges, giving no sense that it
    continues
  * the scrollbar is a permanent strip taking horizontal space
  * nothing tells you which section you are currently looking at
"""

from PySide6 import QtCore, QtGui, QtWidgets


class SmoothScrollArea(QtWidgets.QScrollArea):
    """Scroll area with eased wheel scrolling, edge fades and an overlay bar."""

    FADE_HEIGHT = 20
    BAR_WIDTH = 4
    BAR_MARGIN = 5
    IDLE_MS = 700
    ANIM_MS = 180

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        # The native bar still drives geometry; it is simply never painted, so
        # the overlay bar can sit above the content instead of beside it.
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self._surface = QtGui.QColor(32, 33, 36)
        self._thumb = QtGui.QColor(255, 255, 255, 70)
        self._bar_opacity = 0.0
        self._hovered = False

        self._anim = QtCore.QPropertyAnimation(self.verticalScrollBar(), b"value", self)
        self._anim.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)
        self._anim.setDuration(self.ANIM_MS)

        self._bar_anim = QtCore.QPropertyAnimation(self, b"bar_opacity", self)
        self._bar_anim.setDuration(220)

        self._idle = QtCore.QTimer(self)
        self._idle.setSingleShot(True)
        self._idle.setInterval(self.IDLE_MS)
        self._idle.timeout.connect(self._fade_bar_out)

        self.verticalScrollBar().valueChanged.connect(self._on_scrolled)
        self.viewport().installEventFilter(self)
        self.setMouseTracking(True)

    # ---- theming -------------------------------------------------------
    def set_colours(self, surface, thumb):
        """surface drives the edge fades; thumb is the overlay scrollbar."""
        self._surface = QtGui.QColor(surface)
        self._thumb = QtGui.QColor(thumb)
        self.viewport().update()

    # ---- overlay bar opacity (animatable) ------------------------------
    def get_bar_opacity(self):
        return self._bar_opacity

    def set_bar_opacity(self, value):
        self._bar_opacity = max(0.0, min(1.0, float(value)))
        self.viewport().update()

    bar_opacity = QtCore.Property(float, get_bar_opacity, set_bar_opacity)

    def _fade_bar(self, target):
        self._bar_anim.stop()
        self._bar_anim.setStartValue(self._bar_opacity)
        self._bar_anim.setEndValue(float(target))
        self._bar_anim.start()

    def _fade_bar_out(self):
        if not self._hovered:
            self._fade_bar(0.0)

    def _on_scrolled(self):
        self._fade_bar(1.0)
        self._idle.start()
        self.viewport().update()

    # ---- eased wheel ---------------------------------------------------
    def wheelEvent(self, event):
        bar = self.verticalScrollBar()
        if bar.maximum() == 0:
            event.ignore()
            return

        # Accumulate onto the animation's *target*, not the current value, so a
        # fast flick keeps building distance instead of restarting each notch.
        running = self._anim.state() == QtCore.QAbstractAnimation.State.Running
        current = self._anim.endValue() if running else bar.value()

        steps = event.angleDelta().y() / 120.0
        target = int(current - steps * bar.singleStep() * 3)
        target = max(bar.minimum(), min(bar.maximum(), target))

        self._anim.stop()
        self._anim.setStartValue(bar.value())
        self._anim.setEndValue(target)
        self._anim.start()
        event.accept()

    def eventFilter(self, watched, event):
        if watched is self.viewport():
            if event.type() == QtCore.QEvent.Type.Paint:
                # Let the viewport paint itself first, then draw over it.
                result = super().eventFilter(watched, event)
                self._paint_overlay()
                return result
            if event.type() == QtCore.QEvent.Type.Enter:
                self._hovered = True
                self._fade_bar(1.0)
            elif event.type() == QtCore.QEvent.Type.Leave:
                self._hovered = False
                self._idle.start()
        return super().eventFilter(watched, event)

    # ---- fades + overlay bar -------------------------------------------
    def _paint_overlay(self):
        bar = self.verticalScrollBar()
        maximum = bar.maximum()
        if maximum <= 0:
            return

        vp = self.viewport()
        painter = QtGui.QPainter(vp)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        w, h = vp.width(), vp.height()
        value = bar.value()

        # Edge fades, each shown only when content actually continues past it.
        top = QtGui.QColor(self._surface)
        clear = QtGui.QColor(self._surface)
        clear.setAlpha(0)

        if value > 2:
            grad = QtGui.QLinearGradient(0, 0, 0, self.FADE_HEIGHT)
            grad.setColorAt(0.0, top)
            grad.setColorAt(1.0, clear)
            painter.fillRect(QtCore.QRectF(0, 0, w, self.FADE_HEIGHT), QtGui.QBrush(grad))

        if value < maximum - 2:
            grad = QtGui.QLinearGradient(0, h - self.FADE_HEIGHT, 0, h)
            grad.setColorAt(0.0, clear)
            grad.setColorAt(1.0, top)
            painter.fillRect(QtCore.QRectF(0, h - self.FADE_HEIGHT, w, self.FADE_HEIGHT),
                             QtGui.QBrush(grad))

        # Overlay scrollbar: thumb sized to the viewport/content ratio.
        if self._bar_opacity > 0.01:
            track = h - 8
            content = maximum + bar.pageStep()
            ratio = bar.pageStep() / content if content else 1.0
            thumb_h = max(28.0, track * ratio)
            y = 4 + (track - thumb_h) * (value / maximum)

            colour = QtGui.QColor(self._thumb)
            colour.setAlphaF(colour.alphaF() * self._bar_opacity)
            painter.setPen(QtCore.Qt.PenStyle.NoPen)
            painter.setBrush(colour)
            painter.drawRoundedRect(
                QtCore.QRectF(w - self.BAR_MARGIN - self.BAR_WIDTH, y,
                              self.BAR_WIDTH, thumb_h),
                self.BAR_WIDTH / 2.0, self.BAR_WIDTH / 2.0)
        painter.end()


class ToggleSwitch(QtWidgets.QAbstractButton):
    """A pill toggle for boolean settings.

    QSS cannot express a sliding knob, so a checkbox indicator can only ever be
    a square that fills in.  For settings that are plainly on/off -- alert
    sound, bedtime warning, launch at startup -- a switch states that far more
    directly, and animates between the two.

    Exposes the QAbstractButton API (isChecked / setChecked / toggled), so it is
    a drop-in for the QCheckBox it replaces.
    """

    WIDTH = 38
    HEIGHT = 21
    KNOB = 15

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setFixedSize(self.WIDTH, self.HEIGHT)
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)

        self._pos = 0.0            # 0 = off, 1 = on
        self._track_off = QtGui.QColor(60, 64, 72)
        self._track_on = QtGui.QColor(138, 180, 248)
        self._knob_off = QtGui.QColor(160, 165, 175)
        self._knob_on = QtGui.QColor(16, 35, 63)

        self._anim = QtCore.QPropertyAnimation(self, b"knob_pos", self)
        self._anim.setDuration(160)
        self._anim.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)
        self.toggled.connect(self._animate)

    def set_colours(self, track_off, track_on, knob_off, knob_on):
        self._track_off = QtGui.QColor(track_off)
        self._track_on = QtGui.QColor(track_on)
        self._knob_off = QtGui.QColor(knob_off)
        self._knob_on = QtGui.QColor(knob_on)
        self.update()

    def get_knob_pos(self):
        return self._pos

    def set_knob_pos(self, value):
        self._pos = max(0.0, min(1.0, float(value)))
        self.update()

    knob_pos = QtCore.Property(float, get_knob_pos, set_knob_pos)

    def _animate(self, checked):
        self._anim.stop()
        self._anim.setStartValue(self._pos)
        self._anim.setEndValue(1.0 if checked else 0.0)
        self._anim.start()

    def setChecked(self, checked):
        """Keep the knob in sync when set programmatically (e.g. _load_settings).

        toggled only fires on a *change*, so loading a value equal to the
        current one would otherwise leave the knob at the wrong end.
        """
        super().setChecked(checked)
        self._anim.stop()
        self._pos = 1.0 if checked else 0.0
        self.update()

    def sizeHint(self):
        return QtCore.QSize(self.WIDTH, self.HEIGHT)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        painter.setPen(QtCore.Qt.PenStyle.NoPen)

        rect = QtCore.QRectF(0, 0, self.width(), self.height())
        radius = rect.height() / 2.0

        track = QtGui.QColor(
            round(self._track_off.red() + (self._track_on.red() - self._track_off.red()) * self._pos),
            round(self._track_off.green() + (self._track_on.green() - self._track_off.green()) * self._pos),
            round(self._track_off.blue() + (self._track_on.blue() - self._track_off.blue()) * self._pos),
        )
        painter.setBrush(track)
        painter.drawRoundedRect(rect, radius, radius)

        margin = (self.height() - self.KNOB) / 2.0
        travel = self.width() - self.KNOB - margin * 2
        x = margin + travel * self._pos
        painter.setBrush(self._knob_on if self._pos > 0.5 else self._knob_off)
        painter.drawEllipse(QtCore.QRectF(x, margin, self.KNOB, self.KNOB))
        painter.end()


def divider(parent=None):
    """One-pixel row separator styled by QFrame#rowDivider."""
    line = QtWidgets.QFrame(parent)
    line.setObjectName("rowDivider")
    line.setFixedHeight(1)
    line.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
    return line
