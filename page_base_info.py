"""Base Machine Information Page — Full Feature Parity with original PnCConf GTK wizard."""
from __future__ import annotations

try:
    from PyQt6.QtWidgets import (
        QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
        QGroupBox, QFrame, QSizePolicy, QPushButton, QFileDialog,
        QCheckBox, QRadioButton, QButtonGroup, QScrollArea, QWidget,
    )
    from PyQt6.QtCore import Qt
except ImportError:
    from PySide6.QtWidgets import (
        QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox,
        QGroupBox, QFrame, QSizePolicy, QPushButton, QFileDialog,
        QCheckBox, QRadioButton, QButtonGroup, QScrollArea, QWidget,
    )
    from PySide6.QtCore import Qt

from pages.base_page import BasePage
from config.machine_config import MachineConfig

_HINT = "color: #4C566A; font-size: 8.5pt;"
_VAL  = "color: #A3BE8C; font-family: monospace;"


class BaseMachineInfoPage(BasePage):
    PAGE_TITLE    = "Base Machine Information"
    PAGE_SUBTITLE = "Configure core machine parameters, axes, I/O, and machine options"

    AXIS_CONFIGS = ["XZ", "XYZ", "XYZA", "XYZB", "XYZC", "XYZAB", "XYZABC"]
    MESA_BOARDS  = [
        "5i25", "6i25", "7i76e", "7i92", "7i92T",
        "7i96", "7i96S", "5i20", "5i23", "5i24",
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    # ──────────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Scroll area so all groups are reachable on small screens
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        inner = QWidget()
        root = QVBoxLayout(inner)
        root.setContentsMargins(32, 24, 32, 24)
        root.setSpacing(16)

        root.addWidget(self._build_identity_group())
        root.addWidget(self._build_kinematics_group())
        root.addWidget(self._build_timing_group())
        root.addWidget(self._build_io_group())
        root.addWidget(self._build_options_group())
        root.addStretch()

        scroll.setWidget(inner)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    # ── Machine Identity ──────────────────────────────────────────────────────
    def _build_identity_group(self) -> QGroupBox:
        grp = QGroupBox("Machine Identity")
        g = QGridLayout(grp)
        g.setColumnStretch(1, 1)
        g.setHorizontalSpacing(16)
        g.setVerticalSpacing(10)

        self._machine_name = QLineEdit()
        self._machine_name.setPlaceholderText("meukron")
        g.addWidget(QLabel("Machine Name:"), 0, 0)
        g.addWidget(self._machine_name, 0, 1)

        config_row = QHBoxLayout()
        self._config_dir = QLineEdit()
        self._config_dir.setPlaceholderText("/home/user/linuxcnc/configs/my_machine")
        browse_btn = QPushButton("Browse…")
        browse_btn.setFixedWidth(90)
        browse_btn.clicked.connect(self._browse_dir)
        config_row.addWidget(self._config_dir)
        config_row.addWidget(browse_btn)
        g.addWidget(QLabel("Config Directory:"), 1, 0)
        g.addLayout(config_row, 1, 1)

        return grp

    # ── Kinematics & Units ────────────────────────────────────────────────────
    def _build_kinematics_group(self) -> QGroupBox:
        grp = QGroupBox("Kinematics & Units")
        g = QGridLayout(grp)
        g.setHorizontalSpacing(16)
        g.setVerticalSpacing(10)

        self._axis_config = QComboBox()
        self._axis_config.addItems(self.AXIS_CONFIGS)
        g.addWidget(QLabel("Axis Configuration:"), 0, 0)
        g.addWidget(self._axis_config, 0, 1)

        self._include_spindle = QCheckBox("Include Spindle")
        self._include_spindle.setToolTip(
            "Enable when the machine has a spindle (mills, lathes). "
            "Disable for plasma/router-only setups."
        )
        g.addWidget(self._include_spindle, 1, 0, 1, 2)

        self._units = QComboBox()
        self._units.addItems(["Metric (mm)", "Imperial (inch)"])
        g.addWidget(QLabel("Machine Units:"), 2, 0)
        g.addWidget(self._units, 2, 1)

        return grp

    # ── Real-Time Timing ──────────────────────────────────────────────────────
    def _build_timing_group(self) -> QGroupBox:
        grp = QGroupBox("Computer Response / Real-Time Timing")
        g = QGridLayout(grp)
        g.setHorizontalSpacing(16)
        g.setVerticalSpacing(10)

        # Actual servo period (adjustable)
        self._servo_period = QSpinBox()
        self._servo_period.setRange(100_000, 10_000_000)
        self._servo_period.setSingleStep(100_000)
        self._servo_period.setValue(1_000_000)
        self._servo_period.setSuffix(" ns")
        self._servo_period.setToolTip(
            "Actual servo period. Lower = faster but needs a faster RT kernel."
        )

        period_row = QHBoxLayout()
        minus_btn = QPushButton("−")
        minus_btn.setFixedWidth(32)
        minus_btn.clicked.connect(lambda: self._servo_period.stepDown())
        plus_btn = QPushButton("+")
        plus_btn.setFixedWidth(32)
        plus_btn.clicked.connect(lambda: self._servo_period.stepUp())
        period_row.addWidget(minus_btn)
        period_row.addWidget(self._servo_period)
        period_row.addWidget(plus_btn)
        period_row.addStretch()

        g.addWidget(QLabel("Actual Servo Period:"), 0, 0)
        g.addLayout(period_row, 0, 1)

        self._servo_period_display = QLabel("= 1.000 ms  (1000 Hz)")
        self._servo_period_display.setStyleSheet(_VAL)
        g.addWidget(self._servo_period_display, 0, 2)
        self._servo_period.valueChanged.connect(self._update_period_display)

        # Recommended (display-only)
        self._recommended_display = QLabel("1000000 ns  (recommended)")
        self._recommended_display.setStyleSheet(_HINT)
        g.addWidget(QLabel("Recommended Servo Period:"), 1, 0)
        g.addWidget(self._recommended_display, 1, 1, 1, 2)

        # Jitter test button
        jitter_btn = QPushButton("Test Base Period Jitter")
        jitter_btn.setToolTip(
            "Launch latency-test to measure RT jitter. "
            "Set servo period ≥ latency result."
        )
        jitter_btn.clicked.connect(self._launch_jitter_test)
        g.addWidget(jitter_btn, 2, 0, 1, 2)

        return grp

    # ── I/O Control ───────────────────────────────────────────────────────────
    def _build_io_group(self) -> QGroupBox:
        grp = QGroupBox("I/O Control")
        root = QVBoxLayout(grp)
        root.setSpacing(10)

        # Mesa0
        mesa0_box = QGroupBox("Mesa0 Card")
        mesa0_grid = QGridLayout(mesa0_box)
        mesa0_grid.setHorizontalSpacing(12)
        self._mesa0_enabled = QCheckBox("Use Mesa0 Card")
        mesa0_grid.addWidget(self._mesa0_enabled, 0, 0, 1, 3)

        self._mesa0_type = QComboBox()
        self._mesa0_type.addItems(["PCI", "Eth", "Parport"])
        mesa0_grid.addWidget(QLabel("Connection:"), 1, 0)
        mesa0_grid.addWidget(self._mesa0_type, 1, 1)

        self._mesa0_card = QComboBox()
        self._mesa0_card.addItems(self.MESA_BOARDS)
        self._mesa0_card.setCurrentText("7i76e")
        mesa0_grid.addWidget(QLabel("Board:"), 2, 0)
        mesa0_grid.addWidget(self._mesa0_card, 2, 1)

        self._mesa0_enabled.toggled.connect(self._mesa0_type.setEnabled)
        self._mesa0_enabled.toggled.connect(self._mesa0_card.setEnabled)
        self._mesa0_type.setEnabled(False)
        self._mesa0_card.setEnabled(False)
        root.addWidget(mesa0_box)

        # Mesa1
        mesa1_box = QGroupBox("Mesa1 Card")
        mesa1_grid = QGridLayout(mesa1_box)
        mesa1_grid.setHorizontalSpacing(12)
        self._mesa1_enabled = QCheckBox("Use Mesa1 Card")
        mesa1_grid.addWidget(self._mesa1_enabled, 0, 0, 1, 3)

        self._mesa1_type = QComboBox()
        self._mesa1_type.addItems(["PCI", "Eth", "Parport"])
        mesa1_grid.addWidget(QLabel("Connection:"), 1, 0)
        mesa1_grid.addWidget(self._mesa1_type, 1, 1)

        self._mesa1_card = QComboBox()
        self._mesa1_card.addItems(self.MESA_BOARDS)
        self._mesa1_card.setCurrentText("5i25")
        mesa1_grid.addWidget(QLabel("Board:"), 2, 0)
        mesa1_grid.addWidget(self._mesa1_card, 2, 1)

        self._mesa1_enabled.toggled.connect(self._mesa1_type.setEnabled)
        self._mesa1_enabled.toggled.connect(self._mesa1_card.setEnabled)
        self._mesa1_type.setEnabled(False)
        self._mesa1_card.setEnabled(False)
        root.addWidget(mesa1_box)

        # Parallel port radios
        pp_box = QGroupBox("Parallel Port")
        pp_layout = QHBoxLayout(pp_box)
        self._pp_group = QButtonGroup(pp_box)
        self._pp_none = QRadioButton("None")
        self._pp_one  = QRadioButton("One Parport")
        self._pp_two  = QRadioButton("Two Parports")
        self._pp_none.setChecked(True)
        for rb in [self._pp_none, self._pp_one, self._pp_two]:
            self._pp_group.addButton(rb)
            pp_layout.addWidget(rb)
        pp_layout.addStretch()
        root.addWidget(pp_box)

        return grp

    # ── Machine Options ───────────────────────────────────────────────────────
    def _build_options_group(self) -> QGroupBox:
        grp = QGroupBox("Defaults and Options")
        g = QGridLayout(grp)
        g.setHorizontalSpacing(16)
        g.setVerticalSpacing(8)

        options = [
            ("_opt_require_home",       "Require homing before MDI / running"),
            ("_opt_popup_toolchange",   "Popup manual toolchange prompt"),
            ("_opt_spindle_on_tc",      "Leave spindle on during tool change"),
            ("_opt_force_individual",   "Force individual manual homing"),
            ("_opt_spindle_up_before",  "Move spindle up before tool change"),
            ("_opt_restore_joint",      "Restore joint position after shutdown"),
            ("_opt_random_toolchanger", "Random position toolchanger"),
        ]

        for row, (attr, label) in enumerate(options):
            cb = QCheckBox(label)
            setattr(self, attr, cb)
            g.addWidget(cb, row, 0, 1, 2)

        return grp

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _browse_dir(self):
        path = QFileDialog.getExistingDirectory(self, "Select Config Directory", "/home")
        if path:
            self._config_dir.setText(path)

    def _update_period_display(self, ns: int):
        ms  = ns / 1_000_000
        hz  = 1_000_000_000 / ns if ns > 0 else 0
        self._servo_period_display.setText(f"= {ms:.3f} ms  ({hz:.0f} Hz)")

    def _launch_jitter_test(self):
        """Attempt to launch latency-test; silently skip if not found."""
        import subprocess, shutil
        if shutil.which("latency-test"):
            subprocess.Popen(["latency-test"])
        elif shutil.which("latency-histogram"):
            subprocess.Popen(["latency-histogram"])

    # ── populate / save / validate ─────────────────────────────────────────────
    def populate(self, cfg: MachineConfig):
        self._machine_name.setText(cfg.machine_name)
        self._config_dir.setText(cfg.config_directory)

        idx = self._axis_config.findText(cfg.axis_config)
        if idx >= 0: self._axis_config.setCurrentIndex(idx)

        self._include_spindle.setChecked(cfg.include_spindle)
        self._units.setCurrentIndex(0 if cfg.units == "metric" else 1)
        self._servo_period.setValue(cfg.servo_period_ns)

        rec = cfg.recommended_servo_period_ns
        self._recommended_display.setText(f"{rec} ns  (recommended)")

        io = cfg.io_port
        self._mesa0_enabled.setChecked(io.mesa0_enabled)
        self._mesa0_type.setCurrentText(io.mesa0_type)
        self._mesa0_card.setCurrentText(io.mesa0_card)
        self._mesa1_enabled.setChecked(io.mesa1_enabled)
        self._mesa1_type.setCurrentText(io.mesa1_type)
        self._mesa1_card.setCurrentText(io.mesa1_card)

        pp = io.parport_mode
        if pp == "one":   self._pp_one.setChecked(True)
        elif pp == "two": self._pp_two.setChecked(True)
        else:             self._pp_none.setChecked(True)

        mo = cfg.machine_options
        self._opt_require_home.setChecked(mo.require_home_before_mdi)
        self._opt_popup_toolchange.setChecked(mo.popup_toolchange_prompt)
        self._opt_spindle_on_tc.setChecked(mo.leave_spindle_on_toolchange)
        self._opt_force_individual.setChecked(mo.force_individual_homing)
        self._opt_spindle_up_before.setChecked(mo.move_spindle_up_before_toolchange)
        self._opt_restore_joint.setChecked(mo.restore_joint_position_on_shutdown)
        self._opt_random_toolchanger.setChecked(mo.random_position_toolchanger)

    def save(self, cfg: MachineConfig):
        cfg.machine_name      = self._machine_name.text().strip() or "my_machine"
        cfg.config_directory  = self._config_dir.text().strip()
        cfg.axis_config       = self._axis_config.currentText()
        cfg.include_spindle   = self._include_spindle.isChecked()
        cfg.units             = "metric" if self._units.currentIndex() == 0 else "imperial"
        cfg.servo_period_ns   = self._servo_period.value()

        io = cfg.io_port
        io.mesa0_enabled = self._mesa0_enabled.isChecked()
        io.mesa0_type    = self._mesa0_type.currentText()
        io.mesa0_card    = self._mesa0_card.currentText()
        io.mesa1_enabled = self._mesa1_enabled.isChecked()
        io.mesa1_type    = self._mesa1_type.currentText()
        io.mesa1_card    = self._mesa1_card.currentText()

        if self._pp_one.isChecked():   io.parport_mode = "one"
        elif self._pp_two.isChecked(): io.parport_mode = "two"
        else:                          io.parport_mode = "none"

        mo = cfg.machine_options
        mo.require_home_before_mdi          = self._opt_require_home.isChecked()
        mo.popup_toolchange_prompt          = self._opt_popup_toolchange.isChecked()
        mo.leave_spindle_on_toolchange      = self._opt_spindle_on_tc.isChecked()
        mo.force_individual_homing          = self._opt_force_individual.isChecked()
        mo.move_spindle_up_before_toolchange = self._opt_spindle_up_before.isChecked()
        mo.restore_joint_position_on_shutdown = self._opt_restore_joint.isChecked()
        mo.random_position_toolchanger      = self._opt_random_toolchanger.isChecked()

        cfg.ensure_axes()

    def validate(self):
        if not self._machine_name.text().strip():
            return False, "Machine name cannot be empty."
        if not self._config_dir.text().strip():
            return False, "Configuration directory cannot be empty."
        return True, ""
