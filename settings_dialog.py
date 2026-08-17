"""
Settings Dialog - Modal window for overlay settings
Accessible from overlay context menu
"""

import os
from PySide6 import QtWidgets, QtCore, QtGui
from core.auto_launch import is_auto_launch_enabled, enable_auto_launch, disable_auto_launch
from theme_manager import ThemeManager
import ui_kit
import icons
import window_chrome


class SettingsDialog(QtWidgets.QDialog):
    """Settings dialog accessible from overlay"""
    
    settings_updated = QtCore.Signal(dict)
    water_reset = QtCore.Signal()
    terminate_requested = QtCore.Signal()
    
    def __init__(self, data_manager, parent=None):
        super().__init__(parent)
        self.data_manager = data_manager
        self.settings = self.data_manager.get_settings()
        
        self.setWindowTitle("HydraPing Settings")
        self.setModal(True)
        self.setFixedSize(525, 650)  # Increased height for new settings

        # The dialog follows the same theme as the overlay it configures, rather
        # than the fixed Material palette it used to hardcode.
        self._theme_name = self.settings.get('theme', 'Dark Glassmorphic')

        # Set window icon
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'icon.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QtGui.QIcon(icon_path))

        self._setup_ui()
        self._load_settings()
        self._apply_theme()

    # ---- small builders -------------------------------------------------

    def _group(self, title):
        """A titled group: sticky-ish header + rounded card. Returns (card_layout)."""
        header = QtWidgets.QLabel(title.upper())
        header.setObjectName("groupHeader")
        self._content_layout.addWidget(header)
        self._content_layout.addSpacing(4)

        card = QtWidgets.QFrame()
        card.setObjectName("groupCard")
        inner = QtWidgets.QVBoxLayout(card)
        inner.setContentsMargins(12, 2, 12, 2)
        inner.setSpacing(0)
        self._content_layout.addWidget(card)
        self._content_layout.addSpacing(12)
        return inner

    def _row(self, card, label, widget, hint=None, first=False):
        """One label/control row inside a group card."""
        if not first:
            card.addWidget(ui_kit.divider())

        row = QtWidgets.QWidget()
        row.setAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground, False)
        h = QtWidgets.QHBoxLayout(row)
        h.setContentsMargins(0, 7, 0, 7)
        h.setSpacing(14)

        text_col = QtWidgets.QVBoxLayout()
        text_col.setContentsMargins(0, 0, 0, 0)
        text_col.setSpacing(1)
        name = QtWidgets.QLabel(label)
        name.setObjectName("rowLabel")
        text_col.addWidget(name)
        row.hint_label = None
        if hint:
            sub = QtWidgets.QLabel(hint)
            sub.setObjectName("rowHint")
            text_col.addWidget(sub)
            # Exposed so callers can update it later (the sound row shows the
            # chosen filename here) without hunting through findChildren().
            row.hint_label = sub
        h.addLayout(text_col, 1)
        h.addWidget(widget, 0, QtCore.Qt.AlignmentFlag.AlignRight)

        card.addWidget(row)
        return row

    def _icon_button(self, name, tooltip, checkable=False):
        btn = QtWidgets.QPushButton()
        btn.setObjectName("iconButton")
        btn.setFixedSize(30, 30)
        btn.setToolTip(tooltip)
        btn.setCheckable(checkable)
        btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self._icon_buttons.append((btn, name))
        return btn

    def _setup_ui(self):
        """Build the dialog: header, scrollable groups, sticky footer."""
        self._icon_buttons = []

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---- header ------------------------------------------------------
        head = QtWidgets.QWidget()
        head_layout = QtWidgets.QVBoxLayout(head)
        head_layout.setContentsMargins(22, 16, 22, 10)
        head_layout.setSpacing(1)
        title = QtWidgets.QLabel("Settings")
        title.setObjectName("dialogTitle")
        self._subtitle = QtWidgets.QLabel("")
        self._subtitle.setObjectName("dialogSubtitle")
        head_layout.addWidget(title)
        head_layout.addWidget(self._subtitle)
        root.addWidget(head)

        # ---- scrollable body ---------------------------------------------
        self._scroll = ui_kit.SmoothScrollArea()
        content = QtWidgets.QWidget()
        content.setObjectName("scrollContent")
        self._content_layout = QtWidgets.QVBoxLayout(content)
        self._content_layout.setContentsMargins(22, 6, 22, 10)
        self._content_layout.setSpacing(0)

        # ── Hydration ──
        card = self._group("Hydration")

        self.goal_spin = QtWidgets.QSpinBox()
        self.goal_spin.setRange(250, 10000)
        self.goal_spin.setSingleStep(50)
        self.goal_spin.setSuffix(" ml")
        self.goal_spin.setMinimumWidth(112)
        self.goal_spin.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight |
                                    QtCore.Qt.AlignmentFlag.AlignVCenter)
        self._row(card, "Daily goal", self.goal_spin, first=True)

        self.sip_spin = QtWidgets.QSpinBox()
        self.sip_spin.setRange(50, 1000)
        self.sip_spin.setSingleStep(50)
        self.sip_spin.setSuffix(" ml")
        self.sip_spin.setMinimumWidth(112)
        self.sip_spin.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight |
                                   QtCore.Qt.AlignmentFlag.AlignVCenter)
        self._row(card, "Default sip size", self.sip_spin, "Logged per tap")

        presets = QtWidgets.QWidget()
        pl = QtWidgets.QHBoxLayout(presets)
        pl.setContentsMargins(0, 0, 0, 0)
        pl.setSpacing(6)
        self._preset_buttons = []
        for label, ml in (("Light", 2000), ("Moderate", 2500), ("High", 3000)):
            b = QtWidgets.QPushButton(f"{label}\n{ml}ml")
            b.setObjectName("presetChip")
            b.setCheckable(True)
            # Sizing lives in the stylesheet (min-width/min-height on
            # #presetChip), NOT setFixedSize: applying a stylesheet re-polishes
            # the widget and QSS min-height overrides the fixed size set here,
            # which silently squashed these to 26px and clipped both text lines.
            b.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(lambda _=False, v=ml: self.goal_spin.setValue(v))
            pl.addWidget(b)
            self._preset_buttons.append((b, ml))
        self._row(card, "Quick presets", presets)
        self.goal_spin.valueChanged.connect(self._sync_preset_chips)

        # ── Reminders ──
        card = self._group("Reminders")

        self.interval_spin = QtWidgets.QSpinBox()
        self.interval_spin.setRange(5, 240)
        self.interval_spin.setSuffix(" min")
        self.interval_spin.setMinimumWidth(112)
        self.interval_spin.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight |
                                        QtCore.Qt.AlignmentFlag.AlignVCenter)
        self._row(card, "Interval", self.interval_spin, first=True)

        self.snooze_spin = QtWidgets.QSpinBox()
        self.snooze_spin.setRange(5, 30)
        self.snooze_spin.setSuffix(" min")
        self.snooze_spin.setMinimumWidth(112)
        self.snooze_spin.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight |
                                      QtCore.Qt.AlignmentFlag.AlignVCenter)
        self._row(card, "Snooze duration", self.snooze_spin)

        sleep_widget = QtWidgets.QWidget()
        sl = QtWidgets.QHBoxLayout(sleep_widget)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.setSpacing(6)
        self.sleep_start_spin = QtWidgets.QSpinBox()
        self.sleep_start_spin.setRange(0, 23)
        self.sleep_start_spin.setSuffix(":00")
        self.sleep_start_spin.setMinimumWidth(78)
        self.sleep_end_spin = QtWidgets.QSpinBox()
        self.sleep_end_spin.setRange(0, 23)
        self.sleep_end_spin.setSuffix(":00")
        self.sleep_end_spin.setMinimumWidth(78)
        sleep_to = QtWidgets.QLabel("to")
        sleep_to.setObjectName("rowHint")
        sl.addWidget(self.sleep_start_spin)
        sl.addWidget(sleep_to)
        sl.addWidget(self.sleep_end_spin)
        self._row(card, "Sleep hours", sleep_widget, "No reminders in this window")

        self.bedtime_warning_check = ui_kit.ToggleSwitch()
        self._row(card, "Bedtime warning", self.bedtime_warning_check,
                  "Nudge before sleep hours")

        # ── Sound ──
        card = self._group("Sound")

        self.sound_check = ui_kit.ToggleSwitch()
        self._row(card, "Alert sound", self.sound_check, first=True)

        sound_widget = QtWidgets.QWidget()
        sw = QtWidgets.QHBoxLayout(sound_widget)
        sw.setContentsMargins(0, 0, 0, 0)
        sw.setSpacing(6)
        browse_btn = QtWidgets.QPushButton("Browse")
        browse_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self._icon_buttons.append((browse_btn, 'folder'))
        browse_btn.clicked.connect(self._browse_sound_file)
        test_btn = self._icon_button('play', "Test sound")
        test_btn.clicked.connect(self._test_sound)
        self.loop_btn = self._icon_button('loop', "Loop alert sound", checkable=True)
        clear_btn = self._icon_button('clear', "Clear custom sound")
        clear_btn.clicked.connect(self._clear_sound_file)
        for b in (browse_btn, test_btn, self.loop_btn, clear_btn):
            sw.addWidget(b)

        # The row's hint line doubles as the chosen-filename display, which is
        # what _load_settings / _browse_sound_file / _save_settings read and write.
        self._sound_row = self._row(card, "Custom file", sound_widget, "Default")
        self.sound_path_label = self._sound_row.hint_label
        self.sound_path_label.setTextFormat(QtCore.Qt.TextFormat.PlainText)

        # ── Appearance ──
        card = self._group("Appearance")

        self.theme_combo = QtWidgets.QComboBox()
        self.theme_combo.addItems(ThemeManager().get_theme_names())
        self.theme_combo.setMinimumWidth(168)
        self.theme_combo.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.theme_combo.currentTextChanged.connect(self._preview_theme)
        self._row(card, "Theme", self.theme_combo, first=True)

        mode_widget = QtWidgets.QWidget()
        ml = QtWidgets.QHBoxLayout(mode_widget)
        ml.setContentsMargins(0, 0, 0, 0)
        ml.setSpacing(12)
        self.normal_mode_radio = QtWidgets.QRadioButton("Normal")
        self.minimal_mode_radio = QtWidgets.QRadioButton("Minimal")
        self.normal_mode_radio.setChecked(True)
        for r in (self.normal_mode_radio, self.minimal_mode_radio):
            r.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
            ml.addWidget(r)
        self._row(card, "Display mode", mode_widget, "Bar or compact chip")

        self.auto_launch_check = ui_kit.ToggleSwitch()
        self._row(card, "Launch at startup", self.auto_launch_check,
                  "Start with Windows")

        # ── Danger zone ──
        header = QtWidgets.QLabel("DANGER ZONE")
        header.setObjectName("groupHeader")
        self._content_layout.addWidget(header)
        self._content_layout.addSpacing(4)

        danger = QtWidgets.QFrame()
        danger.setObjectName("dangerCard")
        dl = QtWidgets.QHBoxLayout(danger)
        dl.setContentsMargins(12, 10, 12, 10)
        dl.setSpacing(8)
        reset_btn = QtWidgets.QPushButton("Reset to Defaults")
        reset_btn.clicked.connect(self._reset_to_defaults)
        reset_water_btn = QtWidgets.QPushButton("Reset Water")
        reset_water_btn.clicked.connect(self._reset_water)
        close_app_btn = QtWidgets.QPushButton("Close HydraPing")
        close_app_btn.clicked.connect(self._terminate_app)
        for b, ic in ((reset_btn, 'reset'), (reset_water_btn, 'drop'),
                      (close_app_btn, 'power')):
            b.setObjectName("dangerButton")
            b.setMinimumHeight(34)
            b.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
            # Expanding + equal stretch: the three actions share the full width
            # instead of sitting at their label widths with dead space after.
            b.setSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding,
                            QtWidgets.QSizePolicy.Policy.Fixed)
            self._icon_buttons.append((b, ic))
            dl.addWidget(b, 1)
        self._content_layout.addWidget(danger)

        self._content_layout.addStretch(1)
        self._scroll.setWidget(content)
        root.addWidget(self._scroll, 1)

        # ---- sticky footer -----------------------------------------------
        self._footer = QtWidgets.QWidget()
        # Named so the stylesheet can target it. An unscoped setStyleSheet() on
        # this widget cascades its background onto the child buttons and wipes
        # out their own fills.
        self._footer.setObjectName("dialogFooter")
        fl = QtWidgets.QHBoxLayout(self._footer)
        fl.setContentsMargins(22, 12, 22, 12)
        fl.setSpacing(8)
        fl.addStretch(1)
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.setObjectName("ghostButton")
        cancel_btn.setMinimumHeight(32)
        cancel_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        save_btn = QtWidgets.QPushButton("Save Changes")
        save_btn.setObjectName("primaryButton")
        save_btn.setMinimumHeight(32)
        save_btn.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._save_settings)
        fl.addWidget(cancel_btn)
        fl.addWidget(save_btn)
        root.addWidget(self._footer)

    def _sync_preset_chips(self, value=None):
        """Light up whichever preset matches the current goal."""
        value = self.goal_spin.value() if value is None else value
        for button, ml in getattr(self, '_preset_buttons', []):
            button.setChecked(ml == value)

    def _preview_theme(self, name):
        """Restyle the dialog live when the theme dropdown changes."""
        self._theme_name = name
        self._apply_theme()

    def _apply_theme(self):
        """Apply the theme to the stylesheet, icons, scroll area and title bar."""
        theme_manager = ThemeManager(self._theme_name)
        palette = theme_manager.get_dialog_palette()

        self.setStyleSheet(theme_manager.get_dialog_stylesheet())

        self._subtitle.setText(f"{self._theme_name} \u00b7 "
                               f"{self.goal_spin.value()} ml daily goal")

        # (footer is styled via QWidget#dialogFooter in the dialog stylesheet)

        self._scroll.set_colours(palette['surface'], palette['scroll_thumb'])

        # ToggleSwitch paints itself, so it takes colours directly rather than QSS.
        for toggle in (self.sound_check, self.bedtime_warning_check,
                       self.auto_launch_check):
            toggle.set_colours(palette['field'], palette['accent'],
                               palette['text_faint'], palette['accent_ink'])

        # Icons are rasterised per tint, so re-render them on every theme change.
        icons.clear_cache()
        dpr = self.devicePixelRatioF() or 1.0
        for button, name in getattr(self, '_icon_buttons', []):
            colour = QtGui.QColor(palette['danger_text']
                                  if button.objectName() == "dangerButton"
                                  else palette['text'])
            button.setIcon(icons.icon(name, colour, 16, dpr))
            button.setIconSize(QtCore.QSize(16, 16))

        # Native title bar: QSS cannot reach the non-client area, so tint it
        # through DWM instead. No-op below Windows 11 / off Windows.
        window_chrome.apply_window_chrome(
            self,
            QtGui.QColor(palette['surface']),
            QtGui.QColor(palette['text']))

    def showEvent(self, event):
        """Re-apply chrome: Qt can recreate the native handle, resetting it."""
        super().showEvent(event)
        palette = ThemeManager(self._theme_name).get_dialog_palette()
        window_chrome.apply_window_chrome(
            self,
            QtGui.QColor(palette['surface']),
            QtGui.QColor(palette['text']))


    def _browse_sound_file(self):
        """Open file dialog to select custom sound file"""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Select Sound File",
            "",
            "Sound Files (*.wav *.mp3 *.ogg *.flac);;All Files (*.*)"
        )
        
        if file_path:
            import os
            self.sound_path_label.setText(os.path.basename(file_path))
            self.sound_path_label.setToolTip(file_path)
    
    def _clear_sound_file(self):
        """Clear custom sound file selection"""
        self.sound_path_label.setText("Default")
        self.sound_path_label.setToolTip("")
    
    def _test_sound(self):
        """Test the selected sound file"""
        custom_sound_path = None
        if self.sound_path_label.text() != "Default" and self.sound_path_label.toolTip():
            custom_sound_path = self.sound_path_label.toolTip()
        
        if custom_sound_path and os.path.exists(custom_sound_path):
            try:
                import winsound
                import ctypes
                
                # Use MCI for MP3/other formats, fallback to winsound for WAV
                if custom_sound_path.lower().endswith('.wav'):
                    winsound.PlaySound(custom_sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
                else:
                    # Use Windows MCI for MP3/OGG/FLAC
                    winmm = ctypes.windll.winmm
                    winmm.mciSendStringW(f'open "{custom_sound_path}" type mpegvideo alias mp3', None, 0, None)
                    winmm.mciSendStringW('play mp3 from 0', None, 0, None)
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, 'Sound Test', 
                    f'Could not play sound: {str(e)}')
        else:
            try:
                import winsound
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            except:
                QtWidgets.QMessageBox.information(self, 'Sound Test', 
                    'Playing default system beep')
    
    def _load_settings(self):
        """Load current settings into form"""
        self.goal_spin.setValue(self.settings.get('daily_goal_ml', 2000))
        self.interval_spin.setValue(self.settings.get('reminder_interval_minutes', 60))
        self.sip_spin.setValue(self.settings.get('default_sip_ml', 250))
        self.snooze_spin.setValue(self.settings.get('snooze_duration_minutes', 5))
        self.theme_combo.setCurrentText(self.settings.get('theme', 'Dark Glassmorphic'))
        self.auto_launch_check.setChecked(is_auto_launch_enabled())
        self.sound_check.setChecked(self.settings.get('chime_enabled', True))
        
        custom_sound = self.settings.get('custom_sound_path', None)
        if custom_sound:
            import os
            self.sound_path_label.setText(os.path.basename(custom_sound))
            self.sound_path_label.setToolTip(custom_sound)
        else:
            self.sound_path_label.setText("Default")
            self.sound_path_label.setToolTip("")
        
        self.loop_btn.setChecked(self.settings.get('loop_alert_sound', False))
        self.sleep_start_spin.setValue(self.settings.get('sleep_start_hour', 22))
        self.sleep_end_spin.setValue(self.settings.get('sleep_end_hour', 7))
        self.bedtime_warning_check.setChecked(self.settings.get('bedtime_warning_enabled', True))
        
        # Load window shape setting
        window_shape = self.settings.get('window_shape', 'rectangular')
        if window_shape == 'rectangular':
            self.normal_mode_radio.setChecked(True)
        else:
            self.minimal_mode_radio.setChecked(True)
    
    def _save_settings(self):
        """Save settings and close dialog"""
        # Get values
        new_goal = self.goal_spin.value()
        new_interval = self.interval_spin.value()
        new_sip = self.sip_spin.value()
        new_snooze = self.snooze_spin.value()
        new_theme = self.theme_combo.currentText()
        sound_enabled = self.sound_check.isChecked()
        
        # Get custom sound path
        custom_sound_path = None
        if self.sound_path_label.text() != "Default" and self.sound_path_label.toolTip():
            custom_sound_path = self.sound_path_label.toolTip()
        
        loop_enabled = self.loop_btn.isChecked()
        sleep_start = self.sleep_start_spin.value()
        sleep_end = self.sleep_end_spin.value()
        bedtime_warning = self.bedtime_warning_check.isChecked()
        window_shape = 'rectangular' if self.normal_mode_radio.isChecked() else 'circular'
        
        # Update via data_manager
        self.data_manager.update_settings(
            daily_goal_ml=new_goal,
            reminder_interval_minutes=new_interval,
            default_sip_ml=new_sip,
            snooze_duration_minutes=new_snooze,
            theme=new_theme,
            chime_enabled=sound_enabled,
            custom_sound_path=custom_sound_path,
            loop_alert_sound=loop_enabled,
            sleep_start_hour=sleep_start,
            sleep_end_hour=sleep_end,
            bedtime_warning_enabled=bedtime_warning,
            window_shape=window_shape
        )
        
        # Handle auto-launch
        if self.auto_launch_check.isChecked():
            success, message = enable_auto_launch()
            if not success:
                QtWidgets.QMessageBox.warning(self, 'Auto-Launch', 
                    f'Could not enable auto-launch: {message}')
        else:
            success, message = disable_auto_launch()
            if not success:
                QtWidgets.QMessageBox.warning(self, 'Auto-Launch', 
                    f'Could not disable auto-launch: {message}')
        
        # Emit signal with new settings
        updated_settings = {
            'daily_goal_ml': new_goal,
            'reminder_interval_minutes': new_interval,
            'default_sip_ml': new_sip,
            'snooze_duration_minutes': new_snooze,
            'theme': new_theme,
            'chime_enabled': sound_enabled,
            'custom_sound_path': custom_sound_path,
            'loop_alert_sound': loop_enabled,
            'sleep_start_hour': sleep_start,
            'sleep_end_hour': sleep_end,
            'bedtime_warning_enabled': bedtime_warning,
            'window_shape': window_shape
        }
        self.settings_updated.emit(updated_settings)
        
        self.accept()
    
    def _reset_to_defaults(self):
        """Reset all settings to default values"""
        reply = QtWidgets.QMessageBox.question(
            self,
            'Reset Settings',
            'Are you sure you want to reset all settings to defaults?',
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )
        
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            self.goal_spin.setValue(2000)
            self.interval_spin.setValue(60)
            self.sip_spin.setValue(250)
            self.snooze_spin.setValue(5)
            self.theme_combo.setCurrentText('Dark Glassmorphic')
            self.sound_check.setChecked(True)
            self.sound_path_label.setText("Default")
            self.sound_path_label.setToolTip("")
            self.loop_btn.setChecked(False)
            self.sleep_start_spin.setValue(22)
            self.sleep_end_spin.setValue(7)
            self.bedtime_warning_check.setChecked(True)
            self.normal_mode_radio.setChecked(True)
    
    def _reset_water(self):
        """Reset today's water consumption to zero"""
        reply = QtWidgets.QMessageBox.question(
            self,
            'Reset Water Intake',
            'Are you sure you want to reset today\'s water consumption to zero?',
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )
        
        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            # Clear today's hydration logs
            self.data_manager.reset_today()
            self.water_reset.emit()  # Notify controller to update overlay
            QtWidgets.QMessageBox.information(
                self,
                'Water Reset',
                'Today\'s water intake has been reset to zero.'
            )
    
    def _terminate_app(self):
        """Terminate HydraPing completely"""
        self.terminate_requested.emit()
        self.accept()
