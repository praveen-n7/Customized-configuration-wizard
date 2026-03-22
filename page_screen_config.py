"""Screen / Display Configuration Page — Full Feature Parity with original PnCConf."""
from __future__ import annotations

try:
    from PyQt6.QtWidgets import (
        QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
        QComboBox, QDoubleSpinBox, QGroupBox, QSpinBox, QCheckBox,
        QScrollArea, QFrame, QWidget,
    )
    from PyQt6.QtCore import Qt
except ImportError:
    from PySide6.QtWidgets import (
        QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
        QComboBox, QDoubleSpinBox, QGroupBox, QSpinBox, QCheckBox,
        QScrollArea, QFrame, QWidget,
    )
    from PySide6.QtCore import Qt

from pages.base_page import BasePage
from config.machine_config import MachineConfig

_HINT = "color: #4C566A; font-size: 8.5pt;"


class ScreenConfigPage(BasePage):
    PAGE_TITLE    = "Screen Configuration"
    PAGE_SUBTITLE = "Configure the LinuxCNC GUI type and display parameters"

    GUI_TYPES = ["axis", "gmoccapy", "touchy", "qtplasmac", "gscreen", "ngcgui"]
    EDITORS   = ["gedit", "nano", "mousepad", "xed", "kate", "vi"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        inner = QWidget()
        root = QVBoxLayout(inner)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(16)

        root.addWidget(self._build_gui_group())
        root.addWidget(self._build_overrides_group())
        root.addWidget(self._build_velocity_group())
        root.addWidget(self._build_editor_group())
        root.addWidget(self._build_window_group())
        root.addStretch()

        scroll.setWidget(inner)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    # ── GUI Settings ──────────────────────────────────────────────────────────
    def _build_gui_group(self) -> QGroupBox:
        grp = QGroupBox("GUI Settings")
        g = QGridLayout(grp)
        g.setHorizontalSpacing(16)
        g.setVerticalSpacing(10)
        g.setColumnStretch(1, 1)

        self._gui_type = QComboBox()
        self._gui_type.addItems(self.GUI_TYPES)
        g.addWidget(QLabel("GUI Frontend:"), 0, 0)
        g.addWidget(self._gui_type, 0, 1)

        hint = QLabel(
            "axis: classic full-featured  |  gmoccapy: touch-screen  |  "
            "touchy: minimal touch  |  qtplasmac: plasma cutting"
        )
        hint.setWordWrap(True)
        hint.setStyleSheet(_HINT)
        g.addWidget(hint, 1, 0, 1, 2)

        self._position_offset = QComboBox()
        self._position_offset.addItems(["relative", "machine"])
        g.addWidget(QLabel("Position Offset:"), 2, 0)
        g.addWidget(self._position_offset, 2, 1)

        self._position_feedback = QComboBox()
        self._position_feedback.addItems(["actual", "commanded"])
        g.addWidget(QLabel("Position Feedback:"), 3, 0)
        g.addWidget(self._position_feedback, 3, 1)

        self._display_geometry = QLineEdit()
        self._display_geometry.setPlaceholderText("xyz")
        self._display_geometry.setToolTip(
            "Axes shown in DRO, e.g. 'xyz' or 'xz' for a lathe."
        )
        g.addWidget(QLabel("Display Geometry:"), 4, 0)
        g.addWidget(self._display_geometry, 4, 1)

        return grp

    # ── Override Limits ───────────────────────────────────────────────────────
    def _build_overrides_group(self) -> QGroupBox:
        grp = QGroupBox("Overrides")
        g = QGridLayout(grp)
        g.setHorizontalSpacing(16)
        g.setVerticalSpacing(10)

        def pct_spin(lo, hi, val):
            s = QSpinBox()
            s.setRange(lo, hi)
            s.setValue(val)
            s.setSuffix(" %")
            return s

        self._max_spindle_override = pct_spin(10, 500, 100)
        g.addWidget(QLabel("Max Spindle Override:"), 0, 0)
        g.addWidget(self._max_spindle_override, 0, 1)

        self._min_spindle_override = pct_spin(1, 100, 50)
        g.addWidget(QLabel("Min Spindle Override:"), 1, 0)
        g.addWidget(self._min_spindle_override, 1, 1)

        self._max_feed_override = pct_spin(10, 500, 150)
        g.addWidget(QLabel("Max Feed Override:"), 2, 0)
        g.addWidget(self._max_feed_override, 2, 1)

        return grp

    # ── Velocity Settings ─────────────────────────────────────────────────────
    def _build_velocity_group(self) -> QGroupBox:
        grp = QGroupBox("Velocity Settings")
        g = QGridLayout(grp)
        g.setHorizontalSpacing(16)
        g.setVerticalSpacing(10)

        def dbl(lo, hi, val, suffix=""):
            s = QDoubleSpinBox()
            s.setRange(lo, hi)
            s.setValue(val)
            s.setDecimals(3)
            if suffix:
                s.setSuffix(suffix)
            return s

        velocities = [
            ("Default Linear Velocity:",  "_default_linear_vel",  0, 10000, 25.0),
            ("Min Linear Velocity:",       "_min_linear_vel",      0, 10000,  0.0),
            ("Max Linear Velocity:",       "_max_linear_vel",      0, 10000, 50.0),
            ("Default Angular Velocity:", "_default_angular_vel", 0, 36000, 25.0),
            ("Min Angular Velocity:",      "_min_angular_vel",     0, 36000,  0.0),
            ("Max Angular Velocity:",      "_max_angular_vel",     0, 36000, 360.0),
        ]

        for row, (label, attr, lo, hi, val) in enumerate(velocities):
            spin = dbl(lo, hi, val)
            setattr(self, attr, spin)
            g.addWidget(QLabel(label), row, 0)
            g.addWidget(spin, row, 1)

        units_hint = QLabel("Units: machine units / min (mm/min or inch/min)")
        units_hint.setStyleSheet(_HINT)
        g.addWidget(units_hint, len(velocities), 0, 1, 2)

        return grp

    # ── Editor & Jog Increments ───────────────────────────────────────────────
    def _build_editor_group(self) -> QGroupBox:
        grp = QGroupBox("Editor & Jog Increments")
        g = QGridLayout(grp)
        g.setHorizontalSpacing(16)
        g.setVerticalSpacing(10)
        g.setColumnStretch(1, 1)

        self._editor = QComboBox()
        self._editor.addItems(self.EDITORS)
        self._editor.setEditable(True)
        g.addWidget(QLabel("G-Code Editor:"), 0, 0)
        g.addWidget(self._editor, 0, 1)

        self._increments = QLineEdit()
        self._increments.setPlaceholderText("1mm .1mm .01mm .001mm")
        self._increments.setToolTip(
            "Space-separated list. Shown in GUI jog increment selector."
        )
        g.addWidget(QLabel("Jog Increments:"), 1, 0)
        g.addWidget(self._increments, 1, 1)

        hint = QLabel("Space-separated increments shown in the GUI (e.g. 1mm .1mm .01mm .001mm).")
        hint.setStyleSheet(_HINT)
        g.addWidget(hint, 2, 0, 1, 2)

        return grp

    # ── Window / Size ─────────────────────────────────────────────────────────
    def _build_window_group(self) -> QGroupBox:
        grp = QGroupBox("Window Size & Position")
        g = QGridLayout(grp)
        g.setHorizontalSpacing(16)
        g.setVerticalSpacing(10)

        def ispin(lo, hi, val):
            s = QSpinBox()
            s.setRange(lo, hi)
            s.setValue(val)
            return s

        self._win_w = ispin(200, 7680, 800)
        self._win_h = ispin(150, 4320, 600)
        self._win_x = ispin(0,   7680,   0)
        self._win_y = ispin(0,   4320,   0)

        g.addWidget(QLabel("Width:"),  0, 0)
        g.addWidget(self._win_w,       0, 1)
        g.addWidget(QLabel("Height:"), 0, 2)
        g.addWidget(self._win_h,       0, 3)

        g.addWidget(QLabel("X Pos:"),  1, 0)
        g.addWidget(self._win_x,       1, 1)
        g.addWidget(QLabel("Y Pos:"),  1, 2)
        g.addWidget(self._win_y,       1, 3)

        self._force_maximize = QCheckBox("Force maximize window on startup")
        g.addWidget(self._force_maximize, 2, 0, 1, 4)

        return grp

    # ── populate / save ───────────────────────────────────────────────────────
    def populate(self, cfg: MachineConfig):
        sc = cfg.screen

        idx = self._gui_type.findText(sc.gui_type)
        if idx >= 0: self._gui_type.setCurrentIndex(idx)

        idx = self._position_offset.findText(sc.position_offset)
        if idx >= 0: self._position_offset.setCurrentIndex(idx)

        idx = self._position_feedback.findText(sc.position_feedback)
        if idx >= 0: self._position_feedback.setCurrentIndex(idx)

        self._display_geometry.setText(sc.display_geometry)

        self._max_spindle_override.setValue(sc.max_spindle_override)
        self._min_spindle_override.setValue(sc.min_spindle_override)
        self._max_feed_override.setValue(sc.max_feed_override)

        self._default_linear_vel.setValue(sc.default_linear_velocity)
        self._min_linear_vel.setValue(sc.min_linear_velocity)
        self._max_linear_vel.setValue(sc.max_linear_velocity)
        self._default_angular_vel.setValue(sc.default_angular_velocity)
        self._min_angular_vel.setValue(sc.min_angular_velocity)
        self._max_angular_vel.setValue(sc.max_angular_velocity)

        self._editor.setCurrentText(sc.editor)
        self._increments.setText(sc.increments)

        self._win_w.setValue(sc.window_width)
        self._win_h.setValue(sc.window_height)
        self._win_x.setValue(sc.window_x)
        self._win_y.setValue(sc.window_y)
        self._force_maximize.setChecked(sc.force_maximize)

    def save(self, cfg: MachineConfig):
        sc = cfg.screen

        sc.gui_type           = self._gui_type.currentText()
        sc.position_offset    = self._position_offset.currentText()
        sc.position_feedback  = self._position_feedback.currentText()
        sc.display_geometry   = self._display_geometry.text().strip() or "xyz"

        sc.max_spindle_override = self._max_spindle_override.value()
        sc.min_spindle_override = self._min_spindle_override.value()
        sc.max_feed_override    = self._max_feed_override.value()

        sc.default_linear_velocity  = self._default_linear_vel.value()
        sc.min_linear_velocity      = self._min_linear_vel.value()
        sc.max_linear_velocity      = self._max_linear_vel.value()
        sc.default_angular_velocity = self._default_angular_vel.value()
        sc.min_angular_velocity     = self._min_angular_vel.value()
        sc.max_angular_velocity     = self._max_angular_vel.value()

        sc.editor     = self._editor.currentText()
        sc.increments = self._increments.text().strip() or "1mm .1mm .01mm"

        sc.window_width   = self._win_w.value()
        sc.window_height  = self._win_h.value()
        sc.window_x       = self._win_x.value()
        sc.window_y       = self._win_y.value()
        sc.force_maximize = self._force_maximize.isChecked()

        # Keep legacy geometry string in sync
        sc.geometry = f"{sc.window_width}x{sc.window_height}+{sc.window_x}+{sc.window_y}"
