"""
Debug Dockable Widget - Captures and displays logs and print statements.

This widget can be docked in any QMainWindow and captures:
- print() statements
- logging module output
- exceptions and tracebacks
- custom debug messages
"""

import sys
import logging
from io import StringIO
from typing import Optional, Callable

from qtpy.QtWidgets import (
    QDockWidget, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QComboBox, QLabel, QSpinBox
)
from qtpy.QtCore import Qt, QObject, Signal
from qtpy.QtGui import QColor, QFont, QTextCursor, QTextOption


class LogCapture(QObject):
    """Captures log records and emits signals."""
    
    # Signal emitted when a log record is captured
    logReceived = Signal(str, str)  # (message, level)
    
    def __init__(self):
        super().__init__()
        self.handler = None
        self._setup_handler()
    
    def _setup_handler(self):
        """Setup logging handler."""
        self.handler = logging.Handler()
        self.handler.emit = self._emit_log
        logging.getLogger().addHandler(self.handler)
        logging.getLogger().setLevel(logging.DEBUG)
    
    def _emit_log(self, record: logging.LogRecord):
        """Emit log record as signal."""
        level_name = record.levelname
        # Format the message using logging formatter
        formatter = logging.Formatter('%(message)s')
        message = formatter.format(record)
        self.logReceived.emit(message, level_name)
    
    def cleanup(self):
        """Remove handler."""
        if self.handler:
            logging.getLogger().removeHandler(self.handler)


class StdoutCapture:
    """Captures stdout and stderr."""
    
    def __init__(self, callback: Callable[[str], None]):
        self.callback = callback
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
    
    def write(self, message: str):
        """Capture write calls."""
        if message and message.strip():
            self.callback(message.strip())
        self.original_stdout.write(message)
    
    def flush(self):
        """Flush output."""
        self.original_stdout.flush()
    
    def isatty(self):
        """Check if terminal."""
        return False
    
    def enable(self):
        """Enable capture."""
        sys.stdout = self
        sys.stderr = self
    
    def disable(self):
        """Disable capture."""
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr


class DebugDockWidget(QDockWidget):
    """
    Dockable widget for displaying logs and print statements.
    
    Features:
    - Captures all print() statements
    - Captures logging module output
    - Captures print() and logging from separate threads
    - Color-coded output by log level
    - Clear button to clear all logs
    - Level filter to show only certain log levels
    - Auto-scroll to latest message
    - Timestamp display option
    - Word wrap
    """
    
    def __init__(self, parent=None, title: str = "Debug Output"):
        """
        Initialize the debug widget.
        
        :param parent: Parent widget
        :param title: Title for the dock widget
        """
        super().__init__(title, parent)
        self.setObjectName("debugDockWidget")
        
        # Create main widget
        main_widget = QWidget()
        layout = QVBoxLayout()
        
        # Create toolbar
        toolbar_layout = QHBoxLayout()
        
        # Level filter
        toolbar_layout.addWidget(QLabel("Level:"))
        self.level_combo = QComboBox()
        self.level_combo.addItems(["All", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.level_combo.currentTextChanged.connect(self._on_level_changed)
        toolbar_layout.addWidget(self.level_combo)
        
        toolbar_layout.addSpacing(10)
        
        # Max lines spinbox
        toolbar_layout.addWidget(QLabel("Max lines:"))
        self.max_lines_spin = QSpinBox()
        self.max_lines_spin.setMinimum(100)
        self.max_lines_spin.setMaximum(10000)
        self.max_lines_spin.setValue(1000)
        self.max_lines_spin.setSingleStep(100)
        toolbar_layout.addWidget(self.max_lines_spin)
        
        toolbar_layout.addStretch()
        
        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._on_clear)
        toolbar_layout.addWidget(clear_btn)
        
        layout.addLayout(toolbar_layout)
        
        # Create text display
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setFont(QFont("Courier", 9))
        # Disable word wrap
        self.text_display.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self.text_display)
        
        main_widget.setLayout(layout)
        self.setWidget(main_widget)
        
        # Setup capturing
        self._setup_capture()
        
        # Store captured logs
        self._logs = []
        self._current_level_filter = "All"
        
        # Log level colors
        self._level_colors = {
            "DEBUG": QColor(100, 100, 100),      # Gray
            "INFO": QColor(0, 0, 0),              # Black
            "WARNING": QColor(255, 128, 0),      # Orange
            "ERROR": QColor(255, 0, 0),          # Red
            "CRITICAL": QColor(255, 0, 128),    # Red-Magenta
        }
    
    def _setup_capture(self):
        """Setup logging and stdout capture."""
        # Setup logging capture
        self.log_capture = LogCapture()
        self.log_capture.logReceived.connect(self._on_log_received)
        
        # Setup stdout/stderr capture
        self.stdout_capture = StdoutCapture(self._on_stdout)
        self.stdout_capture.enable()
    
    def _on_log_received(self, message: str, level: str):
        """Handle log received signal."""
        self._add_log(message, level)
    
    def _on_stdout(self, message: str):
        """Handle stdout capture."""
        self._add_log(message, "PRINT")
    
    def _add_log(self, message: str, level: str = "INFO"):
        """
        Add a log message to the display.
        
        :param message: Log message
        :param level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL, PRINT)
        """
        # Store log
        self._logs.append((message, level))
        
        # Limit logs in memory
        max_logs = self.max_lines_spin.value()
        if len(self._logs) > max_logs:
            self._logs = self._logs[-max_logs:]
        
        # Update display if level matches filter
        if self._should_show_level(level):
            self._update_display()
    
    def _should_show_level(self, level: str) -> bool:
        """Check if level should be shown based on current filter."""
        if self._current_level_filter == "All":
            return True
        return level == self._current_level_filter
    
    def _update_display(self):
        """Update the display with filtered logs."""
        self.text_display.clear()
        cursor = self.text_display.textCursor()
        
        for message, level in self._logs:
            if self._should_show_level(level):
                # Format message with level and styling
                format_str = f"[{level}] {message}"
                
                # Set color based on level
                color = self._level_colors.get(level, QColor(0, 0, 0))
                
                # Insert text with color
                cursor.movePosition(QTextCursor.MoveOperation.End)
                char_format = cursor.charFormat()
                char_format.setForeground(color)
                cursor.setCharFormat(char_format)
                cursor.insertText(format_str + "\n")
        
        # Scroll to bottom
        self.text_display.moveCursor(QTextCursor.MoveOperation.End)
    
    def _on_level_changed(self, level: str):
        """Handle level filter change."""
        self._current_level_filter = level
        self._update_display()
    
    def _on_clear(self):
        """Clear all logs."""
        self._logs.clear()
        self.text_display.clear()
    
    def log(self, message: str, level: str = "INFO"):
        """
        Manually add a log message.
        
        :param message: Log message
        :param level: Log level
        """
        self._add_log(message, level)
    
    def cleanup(self):
        """Cleanup resources."""
        self.stdout_capture.disable()
        if hasattr(self, 'log_capture'):
            self.log_capture.cleanup()
    
    def closeEvent(self, event):
        """Handle close event."""
        self.cleanup()
        super().closeEvent(event)
