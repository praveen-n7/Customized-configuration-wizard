"""Screen / Display Configuration Page"""
from __future__ import annotations

try:
    from PyQt6.QtWidgets import (
        QVBoxLayout, QGridLayout, QLabel, QLineEdit,
        QComboBox, QDoubleSpinBox, QGroupBox,
    )
except ImportError:
    from PySide6.QtWidgets import (
        QVBoxLayout, QGridLayout, QLabel, QLineEdit,
        QComboBox, QDoubleSpinBox, QGroupBox,
    )

from pages.base_page import BasePage
from config.machine_config import MachineConfig


class ScreenConfigPage(BasePage):
    PAGE_TITLE = "Screen Configuration"
    PAGE_SUBTITLE = "Configure the LinuxCNC GUI type and display parameters"

    GUI_TYPES = ["axis", "gmoccapy", "touchy", "qtplasmac", "gscreen", "ngcgui"]
    EDITORS = ["gedit", "nano", "mousepad", "xed", "kate", "vi"]
    OFFSETS = ["relative", "machine"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(16)

        # ── GUI Type ──────────────────────────────────────────────────────────
        gui_group = QGroupBox("GUI Type")
        gui_grid = QGridLayout(gui_group)
        gui_grid.setHorizontalSpacing(16)
        gui_grid.setVerticalSpacing(10)

        self._gui_type = QComboBox()
        self._gui_type.addItems(self.GUI_TYPES)
        gui_grid.addWidget(QLabel("GUI Frontend:"), 0, 0)
        gui_grid.addWidget(self._gui_type, 0, 1)

        hint = QLabel(
            "axis: classic, full-featured  |  gmoccapy: touch-screen  |  "
            "touchy: minimal touch  |  qtplasmac: plasma cutting"
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #4C566A; font-size: 8.5pt;")
        gui_grid.addWidget(hint, 1, 0, 1, 2)

        self._position_offset = QComboBox()
        self._position_offset.addItems(self.OFFSETS)
        gui_grid.addWidget(QLabel("Position Offset:"), 2, 0)
        gui_grid.addWidget(self._position_offset, 2, 1)

        self._geometry = QLineEdit()
        self._geometry.setPlaceholderText("800x600+0+0")
        gui_grid.addWidget(QLabel("Display Geometry:"), 3, 0)
        gui_grid.addWidget(self._geometry, 3, 1)

        root.addWidget(gui_group)

        # ── Override Limits ───────────────────────────────────────────────────
        override_group = QGroupBox("Override Limits")
        override_grid = QGridLayout(override_group)
        override_grid.setHorizontalSpacing(16)
        override_grid.setVerticalSpacing(10)

        self._max_feed_override = QDoubleSpinBox()
        self._max_feed_override.setRange(0.1, 5.0)
        self._max_feed_override.setSingleStep(0.1)
        self._max_feed_override.setValue(1.5)
        self._max_feed_override.setDecimals(2)
        self._max_feed_override.setSuffix("  ×")
        override_grid.addWidget(QLabel("Max Feed Override:"), 0, 0)
        override_grid.addWidget(self._max_feed_override, 0, 1)

        self._max_spindle_override = QDoubleSpinBox()
        self._max_spindle_override.setRange(0.1, 5.0)
        self._max_spindle_override.setSingleStep(0.1)
        self._max_spindle_override.setValue(1.5)
        self._max_spindle_override.setDecimals(2)
        self._max_spindle_override.setSuffix("  ×")
        override_grid.addWidget(QLabel("Max Spindle Override:"), 1, 0)
        override_grid.addWidget(self._max_spindle_override, 1, 1)

        root.addWidget(override_group)

        # ── Editor & Increments ───────────────────────────────────────────────
        editor_group = QGroupBox("Editor & Jog Increments")
        editor_grid = QGridLayout(editor_group)
        editor_grid.setHorizontalSpacing(16)
        editor_grid.setVerticalSpacing(10)

        self._editor = QComboBox()
        self._editor.addItems(self.EDITORS)
        self._editor.setEditable(True)
        editor_grid.addWidget(QLabel("G-Code Editor:"), 0, 0)
        editor_grid.addWidget(self._editor, 0, 1)

        self._increments = QLineEdit()
        self._increments.setPlaceholderText("1mm .1mm .01mm .001mm")
        editor_grid.addWidget(QLabel("Jog Increments:"), 1, 0)
        editor_grid.addWidget(self._increments, 1, 1)

        hint2 = QLabel("Space-separated list of jog increments shown in the GUI.")
        hint2.setStyleSheet("color: #4C566A; font-size: 8.5pt;")
        editor_grid.addWidget(hint2, 2, 0, 1, 2)

        root.addWidget(editor_group)
        root.addStretch()

    def populate(self, cfg: MachineConfig):
        sc = cfg.screen
        idx = self._gui_type.findText(sc.gui_type)
        if idx >= 0: self._gui_type.setCurrentIndex(idx)
        idx = self._position_offset.findText(sc.position_offset)
        if idx >= 0: self._position_offset.setCurrentIndex(idx)
        self._geometry.setText(sc.geometry)
        self._max_feed_override.setValue(sc.max_feed_override)
        self._max_spindle_override.setValue(sc.max_spindle_override)
        self._editor.setCurrentText(sc.editor)
        self._increments.setText(sc.increments)

    def save(self, cfg: MachineConfig):
        sc = cfg.screen
        sc.gui_type = self._gui_type.currentText()
        sc.position_offset = self._position_offset.currentText()
        sc.geometry = self._geometry.text().strip() or "800x600+0+0"
        sc.max_feed_override = self._max_feed_override.value()
        sc.max_spindle_override = self._max_spindle_override.value()
        sc.editor = self._editor.currentText()
        sc.increments = self._increments.text().strip() or "1mm .1mm .01mm"
