"""
BasePage
========
Abstract base class for all wizard pages.
Each page knows how to populate itself from config and save back.
"""

from __future__ import annotations

try:
    from PyQt6.QtWidgets import QWidget
    from PyQt6.QtCore import pyqtSignal as Signal
except ImportError:
    from PySide6.QtWidgets import QWidget
    from PySide6.QtCore import Signal

from config.machine_config import MachineConfig


class BasePage(QWidget):
    """
    Abstract wizard page.

    Subclasses must implement:
        populate(cfg)   - load values from MachineConfig into widgets
        save(cfg)       - write widget values back into MachineConfig
        validate()      - return (bool, str) — valid?, message
    """

    # Emitted when the page wants to move to a specific step index
    navigate_to = Signal(int)

    PAGE_TITLE = "Page"
    PAGE_SUBTITLE = ""

    def __init__(self, parent=None):
        super().__init__(parent)

    def populate(self, cfg: MachineConfig):
        """Load config values into widgets."""
        pass

    def save(self, cfg: MachineConfig):
        """Save widget values back to config."""
        pass

    def validate(self) -> tuple[bool, str]:
        """Validate the page. Returns (is_valid, error_message)."""
        return True, ""
