"""Screen / Display Configuration Page — Full Feature Parity with original PnCConf."""
from __future__ import annotations

try:
    from PyQt6.QtWidgets import (
        QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
        QComboBox, QDoubleSpinBox, QGroupBox, QSpinBox, QCheckBox,
        QScrollArea, QFrame, QWidget,
        QPushButton, QDialog, QDialogButtonBox, QFileDialog, QMessageBox,
    )
    from PyQt6.QtCore import Qt
except ImportError:
    from PySide6.QtWidgets import (
        QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit,
        QComboBox, QDoubleSpinBox, QGroupBox, QSpinBox, QCheckBox,
        QScrollArea, QFrame, QWidget,
        QPushButton, QDialog, QDialogButtonBox, QFileDialog, QMessageBox,
    )
    from PySide6.QtCore import Qt

from pages.base_page import BasePage
from config.machine_config import MachineConfig, ControlPanelConfig

_HINT = "color: #4C566A; font-size: 8.5pt;"


# ─────────────────────────────────────────────────────────────────────────────
# Minimal dialog: collect panel name + path from the user
# ─────────────────────────────────────────────────────────────────────────────

class _AddPanelDialog(QDialog):
    """Collects a panel name and a file/directory path.

    All data stays in memory — no files are written.
    Returns a populated ControlPanelConfig on accept().
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Control Panel")
        self.setMinimumWidth(420)

        lay = QVBoxLayout(self)
        lay.setSpacing(10)

        form = QGridLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)
        form.setColumnStretch(1, 1)

        # Panel Name
        self._name = QLineEdit()
        self._name.setPlaceholderText("e.g. my_panel")
        form.addWidget(QLabel("Panel Name:"), 0, 0)
        form.addWidget(self._name, 0, 1)

        # Panel Path + browse button
        self._path = QLineEdit()
        self._path.setPlaceholderText("/path/to/panel.ui  or  /path/to/panel/dir")
        browse_btn = QPushButton("Browse…")
        browse_btn.setFixedWidth(72)
        browse_btn.clicked.connect(self._browse)
        path_row = QHBoxLayout()
        path_row.setSpacing(6)
        path_row.addWidget(self._path)
        path_row.addWidget(browse_btn)
        form.addWidget(QLabel("Panel Path:"), 1, 0)
        form.addLayout(path_row, 1, 1)

        hint = QLabel("Point to a .ui file, a .py handler, or the panel directory.")
        hint.setStyleSheet(_HINT)
        form.addWidget(hint, 2, 0, 1, 2)

        lay.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        lay.addWidget(buttons)

    def _browse(self):
        """Let the user pick a file or directory."""
        path = QFileDialog.getExistingDirectory(self, "Select Panel Directory")
        if not path:
            path, _ = QFileDialog.getOpenFileName(
                self, "Select Panel File", "",
                "Panel Files (*.ui *.py);;All Files (*)"
            )
        if path:
            self._path.setText(path)

    def _on_accept(self):
        name = self._name.text().strip()
        path = self._path.text().strip()
        if not name or not path:
            QMessageBox.warning(self, "Incomplete", "Both Panel Name and Panel Path are required.")
            return
        self.accept()

    def result_config(self) -> ControlPanelConfig:
        """Call after exec() returns Accepted."""
        return ControlPanelConfig(
            panel_name=self._name.text().strip(),
            panel_path=self._path.text().strip(),
        )


# ─────────────────────────────────────────────────────────────────────────────
# Main page
# ─────────────────────────────────────────────────────────────────────────────

class ScreenConfigPage(BasePage):
    PAGE_TITLE    = "Screen Configuration"
    PAGE_SUBTITLE = "Configure the LinuxCNC GUI type and display parameters"

    GUI_TYPES = [
        "axis",
        "gmoccapy",
        "touchy",
        "qtplasmac",
        "gscreen",
        "ngcgui",
        "qtvcp my_panel",    # meukron custom QtVCP panel
    ]
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
        root.addWidget(self._build_panel_group())      # ← control panel selection
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
            "touchy: minimal touch  |  qtplasmac: plasma cutting  |  "
            "qtvcp my_panel: meukron custom panel"
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

    # ── Control Panel Selection ───────────────────────────────────────────────
    def _build_panel_group(self) -> QGroupBox:
        """Minimal group: dropdown of user-added panels + 'Add New Panel' button.

        The panel list is EMPTY at startup and lives only in memory for the
        duration of the wizard session.  Each entry is a ControlPanelConfig
        stored in self._panel_registry (list).
        """
        self._panel_registry: list[ControlPanelConfig] = []   # in-memory store

        grp = QGroupBox("Control Panel")
        g = QGridLayout(grp)
        g.setHorizontalSpacing(16)
        g.setVerticalSpacing(10)
        g.setColumnStretch(1, 1)

        self._panel_combo = QComboBox()
        self._panel_combo.addItem("(none)")          # default — no panel selected
        g.addWidget(QLabel("Selected Panel:"), 0, 0)
        g.addWidget(self._panel_combo, 0, 1)

        add_btn = QPushButton("Add New Panel…")
        add_btn.setFixedWidth(130)
        add_btn.clicked.connect(self._on_add_panel)
        g.addWidget(add_btn, 0, 2)

        hint = QLabel(
            "Add a custom QtVCP panel.  Leave as '(none)' to use the default GUI."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet(_HINT)
        g.addWidget(hint, 1, 0, 1, 3)

        return grp

    def _on_add_panel(self):
        dlg = _AddPanelDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            panel = dlg.result_config()
            self._panel_registry.append(panel)
            self._panel_combo.addItem(panel.panel_name)
            # Auto-select the panel just added
            self._panel_combo.setCurrentIndex(self._panel_combo.count() - 1)

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

        # Restore panel selection if a panel was already configured on this cfg
        # (e.g. wizard navigated back to this page during the same session)
        cp = cfg.control_panel
        if cp.is_configured:
            # Add to registry if not already present (back-navigation scenario)
            known = [p.panel_name for p in self._panel_registry]
            if cp.panel_name not in known:
                self._panel_registry.append(ControlPanelConfig(cp.panel_name, cp.panel_path))
                self._panel_combo.addItem(cp.panel_name)
            idx = self._panel_combo.findText(cp.panel_name)
            if idx >= 0:
                self._panel_combo.setCurrentIndex(idx)

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

        # ── Control panel ────────────────────────────────────────────────────
        selected_name = self._panel_combo.currentText()
        matched = next(
            (p for p in self._panel_registry if p.panel_name == selected_name),
            None,
        )
        if matched:
            cfg.control_panel.panel_name = matched.panel_name
            cfg.control_panel.panel_path = matched.panel_path
        else:
            # "(none)" or nothing selected — clear any previously stored value
            cfg.control_panel.panel_name = ""
            cfg.control_panel.panel_path = ""
