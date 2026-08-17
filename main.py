"""
HydraPing - Main Controller
MVC Controller + Event-driven architecture (tray removed)
Features: AI predictions, smart scheduling
"""

import sys
import os
import time
from datetime import datetime
from PySide6 import QtCore, QtWidgets, QtGui

from core.data_manager import get_data_manager
from core.auto_launch import is_auto_launch_enabled, enable_auto_launch, disable_auto_launch
from core.pattern_analyzer import PatternAnalyzer
from overlay_window import OverlayWindow
from settings_dialog import SettingsDialog
from font_loader import load_poppins


class HydraPingController(QtCore.QObject):
    """Main controller managing business logic, timers, and state coordination"""
    
    def __init__(self, data_manager):
        super().__init__()
        
        self.data_manager = data_manager
        self.paused = False
        self.overlay_is_visible = False  # Start hidden
        
        # AI system
        self.pattern_analyzer = PatternAnalyzer(data_manager)
        
        # Tray signals removed
        
        # Load settings and state
        self.settings = self.data_manager.get_settings()
        self.today_intake = self.data_manager.get_today_total()
        
        # Create overlay window with theme (but don't show yet)
        theme = self.settings.get('theme', 'Dark Glassmorphic')
        overlay_x = self.settings.get('overlay_x')
        overlay_y = self.settings.get('overlay_y', 20)
        self._overlay = OverlayWindow(theme_name=theme)
        
        # Apply window shape from settings
        window_shape = self.settings.get('window_shape', 'rectangular')
        self._overlay.set_window_shape(window_shape, save_preference=True)
        
        if overlay_x is not None:
            self._overlay.move(overlay_x, overlay_y)
        self._overlay.update_consumption(self.today_intake, self.settings['daily_goal_ml'])
        
        # Connect overlay signals to handlers
        self._overlay.drink_now_clicked.connect(self._handle_drink_now)
        self._overlay.snooze_clicked.connect(self._handle_snooze)
        self._overlay.position_changed.connect(self._persist_overlay_position)
        self._overlay.settings_requested.connect(self.open_settings)
        self._overlay.manual_drink_requested.connect(self._handle_manual_drink)
        self._overlay.terminate_requested.connect(self._terminate_app)
        
        # Fast timer for countdown display (1 second)
        self._countdown_timer = QtCore.QTimer(self)
        self._countdown_timer.setInterval(1000)
        self._countdown_timer.timeout.connect(self._update_countdown)
        
        # Slow timer for system checks (60 seconds)
        self._system_check_timer = QtCore.QTimer(self)
        self._system_check_timer.setInterval(60000)  # 1 minute
        self._system_check_timer.timeout.connect(self._system_checks)
        
        # AI message timer (30 seconds) - update smart messages
        self._ai_message_timer = QtCore.QTimer(self)
        self._ai_message_timer.setInterval(30000)  # 30 seconds
        self._ai_message_timer.timeout.connect(self._update_smart_message)
        
        # Tracking - snap initial reminder to next clock-aligned time
        self.last_reminder_time = time.time()
        self._next_reminder_time = self._calc_next_clock_aligned_time(
            self.settings.get('reminder_interval_minutes', 45)
        )
        self.last_date = datetime.now().date()
        self._in_sleep_hours = False
        self._bedtime_warning_shown = False
        self._is_snoozed = False
        self._snooze_end_time = 0
        
        # Tray removed
        
    def _calc_next_clock_aligned_time(self, interval_minutes):
        """Calculate the next reminder time aligned to a multiple of 5 on the clock.
        
        E.g. if interval is 25 min and current time is 2:03 PM,
        the raw next time would be 2:28 PM, which snaps to 2:30 PM.
        """
        from datetime import timedelta
        now = datetime.now()
        raw_next = now + timedelta(minutes=interval_minutes)
        
        # Snap to nearest multiple of 5 minutes
        minute = raw_next.minute
        snapped_minute = round(minute / 5) * 5
        
        if snapped_minute == 60:
            raw_next = raw_next.replace(minute=0, second=0, microsecond=0)
            raw_next += timedelta(hours=1)
        else:
            raw_next = raw_next.replace(minute=snapped_minute, second=0, microsecond=0)
        
        return raw_next.timestamp()
        
    def start(self):
        """Start the application - show overlay"""
        self._countdown_timer.start()
        self._system_check_timer.start()
        self._ai_message_timer.start()
        self._system_checks()  # Run initial check
        self._update_smart_message()  # Initial smart message
        self._overlay.show()
        self.overlay_is_visible = True
        
    def _update_countdown(self):
        """Fast timer: Update countdown display every second with AI predictions"""
        if not self.paused and not self._in_sleep_hours:
            # Check if snoozed
            if self._is_snoozed:
                snooze_remaining = int(self._snooze_end_time - time.time())
                if snooze_remaining <= 0:
                    # Snooze ended, trigger alert
                    self._is_snoozed = False
                    self._trigger_alert()
                    self.last_reminder_time = time.time()
                    base_interval = self.settings.get('reminder_interval_minutes', 45)
                    self._next_reminder_time = self._calc_next_clock_aligned_time(base_interval)
                else:
                    # Show snooze countdown
                    mins = snooze_remaining // 60
                    secs = snooze_remaining % 60
                    self._overlay.update_countdown(f"Snoozed: {mins:02d}:{secs:02d}")
            else:
                # Calculate remaining seconds until the clock-aligned reminder
                remaining_seconds = int(self._next_reminder_time - time.time())
                
                # Check if time to trigger alert
                if remaining_seconds <= 0:
                    self._trigger_alert()
                    self.last_reminder_time = time.time()
                    # Schedule next reminder aligned to clock
                    base_interval = self.settings.get('reminder_interval_minutes', 45)
                    adjusted_interval = self.pattern_analyzer.get_smart_reminder_delay(base_interval)
                    self._next_reminder_time = self._calc_next_clock_aligned_time(adjusted_interval)
                    remaining_seconds = int(self._next_reminder_time - time.time())
                
                # Update display with AI prediction
                if remaining_seconds > 0:
                    mins = remaining_seconds // 60
                    secs = remaining_seconds % 60
                    
                    # Try to show AI prediction
                    prediction = self.pattern_analyzer.predict_next_drink_time()
                    if prediction and prediction[1] > 0.6:  # High confidence
                        pred_time, confidence, _ = prediction
                        pred_mins = int((pred_time - datetime.now()).total_seconds() / 60)
                        if pred_mins > 0 and pred_mins < adjusted_interval * 1.5:
                            self._overlay.update_countdown(f"AI: ~{pred_mins}m (Next: {mins:02d}:{secs:02d})")
                        else:
                            self._overlay.update_countdown(f"Next: {mins:02d}:{secs:02d}")
                    else:
                        self._overlay.update_countdown(f"Next: {mins:02d}:{secs:02d}")
                else:
                    self._overlay.update_countdown("Next: 00:00")
        elif self._in_sleep_hours:
            self._overlay.update_countdown("Sleep Mode")
    
    def _update_smart_message(self):
        """Update overlay message with AI predictions"""
        try:
            # Get AI prediction
            prediction = self.pattern_analyzer.predict_next_drink_time()
            
            # Decide which message to show
            if prediction and prediction[1] > 0.7:  # High confidence prediction
                pred_time, confidence, reason = prediction
                pred_mins = int((pred_time - datetime.now()).total_seconds() / 60)
                
                if 0 < pred_mins <= 60:
                    # Show prediction message
                    confidence_pct = int(confidence * 100)
                    message = f"AI predicts: ~{pred_mins}min until thirst ({confidence_pct}%)"
                    self._overlay.set_smart_message(message)
                    return
            
            # Check if ahead/behind schedule
            ahead = self.pattern_analyzer.is_ahead_of_schedule()
            if ahead is True:
                self._overlay.set_smart_message("Great pace! You're ahead of schedule")
                return
            elif ahead is False:
                self._overlay.set_smart_message("Behind schedule - drink up!")
                return
            
            # Fallback to default rotation (do nothing, let normal rotation continue)
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Smart message error: {e}")
    
    def _system_checks(self):
        """Slow timer: Check date rollover, sleep hours, bedtime warning every minute"""
        # Check for daily reset (midnight rollover)
        current_date = datetime.now().date()
        if current_date != self.last_date:
            self.last_date = current_date
            self.data_manager.reset_today()
            self.today_intake = 0
            self._overlay.update_consumption(self.today_intake, self.settings['daily_goal_ml'])
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Auto-reset: New day detected, water intake reset to 0 ml")
        
        # Check if in sleep hours
        current_hour = datetime.now().hour
        sleep_start = self.settings.get('sleep_start_hour', 22)
        sleep_end = self.settings.get('sleep_end_hour', 7)
        
        if sleep_start < sleep_end:
            self._in_sleep_hours = sleep_start <= current_hour < sleep_end
        else:  # Sleep hours span midnight
            self._in_sleep_hours = current_hour >= sleep_start or current_hour < sleep_end
        
        # Check for bedtime warning (30 min before sleep)
        if self.settings.get('bedtime_warning_enabled', True):
            warning_hour = (sleep_start - 1) % 24
            warning_min_start = 30
            if current_hour == warning_hour and datetime.now().minute >= warning_min_start:
                if not self._bedtime_warning_shown and self.today_intake < self.settings['daily_goal_ml']:
                    self._show_bedtime_warning()
                    self._bedtime_warning_shown = True
            else:
                self._bedtime_warning_shown = False
                
    def _trigger_alert(self):
        """Trigger hydration alert"""
        custom_sound_path = self.settings.get('custom_sound_path')
        loop_sound = self.settings.get('loop_alert_sound', False)
        self._overlay.set_alert_mode(True, custom_sound_path, loop_sound)
        
        # Sound is now handled by overlay's set_alert_mode method
        
            
    def _handle_drink_now(self):
        """Handle drink now button click"""
        default_amount = self.settings.get('default_sip_ml', 250)
        self._log_water(default_amount)
        self._overlay.set_alert_mode(False)
        self._is_snoozed = False
        self.last_reminder_time = time.time()
        base_interval = self.settings.get('reminder_interval_minutes', 45)
        adjusted_interval = self.pattern_analyzer.get_smart_reminder_delay(base_interval)
        self._next_reminder_time = self._calc_next_clock_aligned_time(adjusted_interval)
        
    def _handle_snooze(self):
        """Handle snooze button click"""
        snooze_minutes = self.settings.get('snooze_duration_minutes', 5)
        self._is_snoozed = True
        self._snooze_end_time = time.time() + (snooze_minutes * 60)
        self._overlay.set_alert_mode(False)
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Snoozed for {snooze_minutes} minutes")
        
    def _handle_manual_drink(self, amount):
        """Handle manual drink logging from menu"""
        self._log_water(amount)
        if self._overlay._alert_mode:
            self._overlay.set_alert_mode(False)
            self._is_snoozed = False
            self.last_reminder_time = time.time()
            base_interval = self.settings.get('reminder_interval_minutes', 45)
            adjusted_interval = self.pattern_analyzer.get_smart_reminder_delay(base_interval)
            self._next_reminder_time = self._calc_next_clock_aligned_time(adjusted_interval)
            
    def _log_water(self, amount):
        """Log water intake and update UI"""
        was_below_goal = self.today_intake < self.settings['daily_goal_ml']
        
        self.data_manager.log_water(amount)
        self.today_intake += amount
        self._overlay.update_consumption(self.today_intake, self.settings['daily_goal_ml'])
        self._overlay.flash_success()
        
        # Check if goal achieved (trigger confetti only on first time reaching goal)
        if was_below_goal and self.today_intake >= self.settings['daily_goal_ml']:
            self._overlay.celebrate_goal()  # Trigger confetti animation only
            
        # Dashboard removed; no additional UI to refresh
    
    def _show_bedtime_warning(self):
        """Show warning to drink before bed"""
        remaining = self.settings['daily_goal_ml'] - self.today_intake
        msg_box = QtWidgets.QMessageBox()
        msg_box.setWindowTitle("Bedtime Reminder")
        msg_box.setText(f"You're {remaining}ml away from your goal!\\nDrink some water before bed?")
        msg_box.setIcon(QtWidgets.QMessageBox.Icon.Information)
        msg_box.setStandardButtons(
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )
        msg_box.setStyleSheet("""
            QMessageBox {
                background: rgba(28,28,36,250);
            }
            QLabel {
                color: rgba(255,255,255,230);
                font-size: 12px;
                font-family: 'Poppins', 'Segoe UI', sans-serif;
            }
            QPushButton {
                background: rgba(255,255,255,18);
                color: rgba(255,255,255,230);
                border: 1px solid rgba(255,255,255,35);
                border-radius: 7px;
                padding: 7px 18px;
                font-weight: 600;
                font-family: 'Poppins', 'Segoe UI', sans-serif;
                min-width: 64px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,28);
                border-color: rgba(255,255,255,50);
            }
            QPushButton:pressed {
                background: rgba(255,255,255,12);
            }
        """)
        
        if msg_box.exec() == QtWidgets.QMessageBox.StandardButton.Yes:
            self._handle_drink_now()
            
    def _show_goal_achieved(self):
        """Show goal achievement notification"""
        msg_box = QtWidgets.QMessageBox()
        msg_box.setWindowTitle("Goal Achieved!")
        msg_box.setText("Congratulations! You've reached your daily hydration goal!")
        msg_box.setIcon(QtWidgets.QMessageBox.Icon.Information)
        msg_box.setStyleSheet("""
            QMessageBox {
                background: rgba(28,28,36,250);
            }
            QLabel {
                color: rgba(255,255,255,230);
                font-size: 12px;
                font-family: 'Poppins', 'Segoe UI', sans-serif;
            }
            QPushButton {
                background: rgba(255,255,255,18);
                color: rgba(255,255,255,230);
                border: 1px solid rgba(255,255,255,35);
                border-radius: 7px;
                padding: 7px 18px;
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
        msg_box.exec()
        
    def _persist_overlay_position(self, x, y):
        """Save overlay position to database"""
        self.data_manager.set_setting('overlay_x', x)
        self.data_manager.set_setting('overlay_y', y)
        
    @QtCore.Slot()
    def open_settings(self):
        """Open settings dialog"""
        try:
            # Refresh settings before opening dialog to ensure latest values
            self.settings = self.data_manager.get_settings()
            
            dialog = SettingsDialog(self.data_manager, parent=self._overlay)
            dialog.settings_updated.connect(self._apply_settings)
            dialog.water_reset.connect(self._handle_water_reset)
            dialog.terminate_requested.connect(self._terminate_app)
            if dialog.exec() == QtWidgets.QDialog.DialogCode.Accepted:
                # Settings were saved - only update if overlay still exists
                if self._overlay is not None:
                    self.settings = self.data_manager.get_settings()
                    self.today_intake = self.data_manager.get_today_total()
                    self._overlay.update_consumption(self.today_intake, self.settings['daily_goal_ml'])
        except Exception as e:
            print(f"Error opening settings: {e}")
            import traceback
            traceback.print_exc()
    
    @QtCore.Slot()
    def launch_overlay(self):
        """Launch overlay mode"""
        if not self.overlay_is_visible:
            self._overlay.show()
            self.overlay_is_visible = True
            
    
    @QtCore.Slot()
    def _handle_water_reset(self):
        """Handle water reset from settings dialog"""
        self.today_intake = 0
        self._overlay.update_consumption(self.today_intake, self.settings['daily_goal_ml'])
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Manual reset: Water intake reset to 0 ml")
    
    @QtCore.Slot(dict)
    def _apply_settings(self, updated_settings):
        """Apply updated settings from dialog"""
        self.settings = updated_settings
        self._overlay.update_consumption(self.today_intake, self.settings['daily_goal_ml'])
        
        # Update theme if changed
        new_theme = updated_settings.get('theme', 'Dark Glassmorphic')
        self._overlay.set_theme(new_theme)
        
        # Update window shape if changed
        new_shape = updated_settings.get('window_shape', 'rectangular')
        self._overlay.set_window_shape(new_shape, save_preference=True)
        
        if not self.paused:
            self.last_reminder_time = time.time()  # Reset reminder timer with new interval
    
    @QtCore.Slot()
    def _handle_intake_reset(self):
        """Handle intake reset from settings"""
        self.today_intake = 0
        self._overlay.update_consumption(self.today_intake, self.settings['daily_goal_ml'])
        
            
    def toggle_overlay_visibility(self):
        """Toggle overlay visibility"""
        if self.overlay_is_visible:
            self._overlay.hide()
            self.overlay_is_visible = False
        else:
            self._overlay.show()
            self.overlay_is_visible = True
        
            
    def toggle_pause(self):
        """Toggle pause state"""
        self.paused = not self.paused
        
            
    def trigger_drink_now(self):
        """Manually trigger drink now (from tray)"""
        self._handle_drink_now()
        
    # Tray integration methods removed
    
    def cleanup(self):
        """Cleanup resources before exit"""
        print("[HydraPing] Starting cleanup...")
        
        # Stop timers
        if hasattr(self, '_countdown_timer') and self._countdown_timer:
            self._countdown_timer.stop()
        if hasattr(self, '_system_check_timer') and self._system_check_timer:
            self._system_check_timer.stop()
            print("[HydraPing] Timers stopped")
        
        # Hide and cleanup overlay
        if hasattr(self, '_overlay') and self._overlay:
            self._overlay.hide()
            self._overlay.deleteLater()
            self._overlay = None
            print("[HydraPing] Overlay closed")
        
        # Tray removed
        
        print("[HydraPing] Cleanup complete - Application will exit")
    
    def _terminate_app(self):
        """Terminate the entire application"""
        QtWidgets.QApplication.instance().quit()
        


class HydraPingApp:
    """Main application entry point"""
    
    def __init__(self):
        self.data_manager = get_data_manager()
        self.current_user = None
        self.app = None
        
        # No user initialization needed for single-user app
        
    def start(self):
        """Start the application"""
        self.app = QtWidgets.QApplication(sys.argv)
        self.app.setApplicationName("HydraPing")
        
        # Load bundled Poppins fonts before any UI is created
        load_poppins()
        
        # Tray removed; quit when last window closes
        self.app.setQuitOnLastWindowClosed(True)
        
        # Create controller
        self.controller = HydraPingController(self.data_manager)
        
        # Connect cleanup on application quit
        self.app.aboutToQuit.connect(self.controller.cleanup)
        
        self.controller.start()
        
        sys.exit(self.app.exec())
    



if __name__ == "__main__":
    app = HydraPingApp()
    app.start()
